"""
On-demand Video Dubbing Pipeline (FREE stack).

Combines:
  - Qwen / DashScope (OpenAI-compatible API) for translation
  - Edge-TTS (free, no API key) for speech synthesis
  - FFmpeg for audio assembly and muxing into the video

This module is invoked on demand (not part of the automatic ingestion
orchestrator). It reads the transcript produced by the audio_analysis stage,
translates each segment, synthesizes speech, assembles a full audio track that
respects the original timing, and muxes it back into the source video.
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
from typing import Dict, List, Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)


# Edge-TTS voice mapping per language code.
VOICE_MAP = {
    "ar": "ar-SA-HamedNeural",           # Arabic (Saudi) male
    "ar-female": "ar-SA-ZariyahNeural",  # Arabic female
    "en": "en-US-GuyNeural",             # English male
    "fr": "fr-FR-HenriNeural",           # French male
    "es": "es-ES-AlvaroNeural",          # Spanish male
    "de": "de-DE-ConradNeural",          # German male
    "ru": "ru-RU-DmitryNeural",          # Russian male
    "hi": "hi-IN-MadhurNeural",          # Hindi male
    "zh": "zh-CN-YunxiNeural",           # Chinese male
}

# Human-readable language names used in the translation prompt.
LANGUAGE_NAMES = {
    "ar": "Arabic",
    "en": "English",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "ru": "Russian",
    "hi": "Hindi",
    "zh": "Chinese",
}


async def dub_video(
    video_id: str,
    video_path: str,
    output_dir: str,
    target_language: str = "ar",
) -> dict:
    """
    Produce a dubbed version of a video in the target language.

    Args:
        video_id: The video identifier.
        video_path: Absolute path to the source video file.
        output_dir: The video's working directory (contains transcript.json).
        target_language: Target language code (e.g. "ar", "en", "fr").

    Returns:
        A dict describing the dubbing result. On success:
            {
                "status": "completed",
                "target_language": "ar",
                "audio_path": "dubbed/audio_ar.mp3",
                "video_path": "dubbed/video_ar.mp4",
                "segments": [...],
            }
        On failure a dict with "status": "failed" and an "error" message.
    """
    lang = (target_language or "ar").lower()
    voice = VOICE_MAP.get(lang)
    if not voice:
        return _error_result(lang, f"Unsupported target language '{lang}'")

    dubbed_dir = os.path.join(output_dir, "dubbed")
    os.makedirs(dubbed_dir, exist_ok=True)

    # Write an initial status file so the API can report progress.
    _write_status(dubbed_dir, lang, "processing", "Loading transcript")

    # ── 1. Load transcript ───────────────────────────────────────────
    transcript_path = os.path.join(output_dir, "transcript.json")
    if not os.path.exists(transcript_path):
        return _error_result(lang, "transcript.json not found", dubbed_dir)

    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript = json.load(f)
    except Exception as e:
        logger.error("Failed to read transcript for %s: %s", video_id, e)
        return _error_result(lang, f"Failed to read transcript: {e}", dubbed_dir)

    source_segments = transcript.get("segments") or []
    if not source_segments:
        return _error_result(lang, "Transcript has no segments", dubbed_dir)

    logger.info(
        "Dubbing %s -> %s (%d segments)", video_id, lang, len(source_segments)
    )

    # ── 2. Translate ─────────────────────────────────────────────────
    _write_status(dubbed_dir, lang, "processing", "Translating segments")
    try:
        translated_segments = await _translate_segments(source_segments, lang)
    except Exception as e:
        logger.error("Translation failed for %s: %s", video_id, e)
        return _error_result(lang, f"Translation failed: {e}", dubbed_dir)

    # Persist translated segments early so they are available even if TTS fails.
    segments_path = os.path.join(dubbed_dir, f"segments_{lang}.json")
    try:
        with open(segments_path, "w", encoding="utf-8") as f:
            json.dump(translated_segments, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning("Could not write segments file: %s", e)

    # ── 3. Synthesize speech per segment ─────────────────────────────
    _write_status(dubbed_dir, lang, "processing", "Synthesizing speech")
    tmp_dir = tempfile.mkdtemp(prefix=f"dub_{lang}_")
    try:
        seg_audio_paths = await _synthesize_all(translated_segments, voice, tmp_dir)

        # ── 4. Combine audio segments with timing/silence gaps ───────
        _write_status(dubbed_dir, lang, "processing", "Assembling audio track")
        audio_out = os.path.join(dubbed_dir, f"audio_{lang}.mp3")
        ok = await _assemble_audio(translated_segments, seg_audio_paths, audio_out, tmp_dir)
        if not ok:
            return _error_result(lang, "Failed to assemble dubbed audio track", dubbed_dir)

        # ── 5. Mux dubbed audio into the video ───────────────────────
        _write_status(dubbed_dir, lang, "processing", "Muxing audio into video")
        video_out = os.path.join(dubbed_dir, f"video_{lang}.mp4")
        ok = await _mux_audio_into_video(video_path, audio_out, video_out)
        if not ok:
            return _error_result(lang, "Failed to mux audio into video", dubbed_dir)
    finally:
        _cleanup_dir(tmp_dir)

    result = {
        "status": "completed",
        "target_language": lang,
        "audio_path": f"dubbed/audio_{lang}.mp3",
        "video_path": f"dubbed/video_{lang}.mp4",
        "segments": translated_segments,
    }
    _write_dubbing_json(dubbed_dir, lang, result)
    _write_status(dubbed_dir, lang, "completed", "Done")
    logger.info("Dubbing completed for %s -> %s", video_id, lang)
    return result


# ── Translation ──────────────────────────────────────────────────────

async def _translate_segments(
    segments: List[dict], lang: str
) -> List[dict]:
    """
    Translate every segment's text into the target language while preserving
    timing information. All segments are translated in a single API call using
    numbered markers, then split back apart (mirrors the existing router logic).
    """
    lang_name = LANGUAGE_NAMES.get(lang, lang)
    api_key = settings.DASHSCOPE_API_KEY
    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is not configured")

    joined = "\n".join(
        f"[SEG{i + 1}] {(seg.get('text') or '').strip()}"
        for i, seg in enumerate(segments)
    )

    system_prompt = (
        f"You are a professional translator. Translate the user's text into {lang_name}. "
        f"The text is split into segments, each prefixed with a marker like [SEG1], [SEG2]. "
        f"Translate ONLY the text after each marker into {lang_name}, and keep every marker "
        f"exactly as-is on the same line before its translation. Preserve the number and order "
        f"of segments. Return ONLY the translated segments with their markers, nothing else."
    )

    payload = {
        "model": settings.MODEL_TEXT,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": joined},
        ],
        "temperature": 0.3,
        "max_tokens": 4096,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    api_url = f"{settings.DASHSCOPE_BASE_URL}/chat/completions"

    content = None
    last_error = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(api_url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                break
            last_error = f"status {resp.status_code}: {resp.text[:300]}"
            logger.warning("Dub translation attempt %d failed: %s", attempt + 1, last_error)
        except Exception as e:
            last_error = str(e)
            logger.warning("Dub translation attempt %d error: %s", attempt + 1, last_error)
        await asyncio.sleep(2 ** attempt)

    if content is None:
        raise RuntimeError(f"Translation API failed: {last_error}")

    parsed = _parse_marked_segments(content, len(segments))

    translated = []
    for i, seg in enumerate(segments):
        text = parsed.get(i)
        translated.append({
            "start_time": seg.get("start_time", 0),
            "end_time": seg.get("end_time", 0),
            "text": (text if text else (seg.get("text") or "")),
            "original_text": seg.get("text") or "",
        })
    return translated


def _parse_marked_segments(content: str, count: int) -> Dict[int, str]:
    """Split model output back into per-segment translations using [SEGn] markers."""
    import re

    result: Dict[int, str] = {}
    matches = list(re.finditer(r"\[SEG(\d+)\]", content))
    for idx, m in enumerate(matches):
        seg_num = int(m.group(1))
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
        text = content[start:end].strip()
        if 1 <= seg_num <= count:
            result[seg_num - 1] = text
    return result


# ── Speech synthesis (Edge-TTS) ────────────────────────────────────────

async def synthesize_segment(text: str, voice: str, output_path: str) -> None:
    """Synthesize a single text segment to an audio file using Edge-TTS."""
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


async def _synthesize_all(
    segments: List[dict], voice: str, tmp_dir: str
) -> List[Optional[str]]:
    """
    Synthesize audio for every segment. Returns a list (aligned with segments)
    of file paths, or None where synthesis produced nothing (empty text/failure).
    """
    paths: List[Optional[str]] = []
    for i, seg in enumerate(segments):
        text = (seg.get("text") or "").strip()
        if not text:
            paths.append(None)
            continue

        out_path = os.path.join(tmp_dir, f"seg_{i:04d}.mp3")
        try:
            await synthesize_segment(text, voice, out_path)
            if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                paths.append(out_path)
            else:
                logger.warning("Edge-TTS produced empty audio for segment %d", i)
                paths.append(None)
        except Exception as e:
            logger.error("Edge-TTS failed for segment %d: %s", i, e)
            paths.append(None)
    return paths


# ── Audio assembly ─────────────────────────────────────────────────────

async def _assemble_audio(
    segments: List[dict],
    seg_audio_paths: List[Optional[str]],
    audio_out: str,
    tmp_dir: str,
) -> bool:
    """
    Assemble per-segment audio into a single track that respects the original
    timing. Each segment is placed at its start_time by prepending a silence
    gap equal to the space between the previous segment's placement and the
    current segment's start_time, then all pieces are concatenated.
    """
    loop = asyncio.get_event_loop()
    pieces: List[str] = []
    cursor = 0.0  # current position (seconds) in the assembled track

    for i, seg in enumerate(segments):
        seg_path = seg_audio_paths[i] if i < len(seg_audio_paths) else None
        if not seg_path:
            continue

        start = float(seg.get("start_time", 0) or 0)
        gap = start - cursor
        if gap > 0.05:
            silence_path = os.path.join(tmp_dir, f"sil_{i:04d}.mp3")
            if await _make_silence(silence_path, gap, loop):
                pieces.append(silence_path)

        pieces.append(seg_path)

        # Advance the cursor by the actual synthesized duration of this segment.
        dur = await _get_media_duration(seg_path, loop)
        cursor = max(start, cursor) + max(dur, 0.0)

    if not pieces:
        logger.error("No audio pieces to assemble")
        return False

    # Build an ffmpeg concat list file.
    concat_list = os.path.join(tmp_dir, "concat.txt")
    try:
        with open(concat_list, "w", encoding="utf-8") as f:
            for p in pieces:
                escaped = p.replace("'", "'\\''")
                f.write(f"file '{escaped}'\n")
    except Exception as e:
        logger.error("Failed to write concat list: %s", e)
        return False

    cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list,
        # Normalize every piece to a single, consistent format before encoding.
        # Edge-TTS emits 24kHz mono while generated silence may differ; feeding
        # frames with changing params straight to libmp3lame triggers
        # "inadequate AVFrame plane padding" and aborts the encode. The aresample
        # filter guarantees a uniform stream for the encoder.
        "-af", "aresample=44100",
        "-ar", "44100",
        "-ac", "2",
        "-c:a", "libmp3lame",
        "-q:a", "2",
        "-y",
        audio_out,
    ]

    def _run():
        return subprocess.run(cmd, capture_output=True, timeout=600)

    try:
        result = await loop.run_in_executor(None, _run)
        if result.returncode == 0 and os.path.exists(audio_out):
            return True
        logger.error(
            "ffmpeg audio assembly failed: %s",
            result.stderr.decode()[-800:] if result.stderr else "unknown",
        )
    except Exception as e:
        logger.error("ffmpeg audio assembly error: %s", e)
    return False


async def _make_silence(path: str, duration: float, loop) -> bool:
    """Generate a silent MP3 of the given duration using ffmpeg.

    The silence is produced in the same format Edge-TTS emits (24kHz mono) so
    that concatenating silence with speech segments does not force the encoder
    to reconfigure between frame formats.
    """
    cmd = [
        "ffmpeg",
        "-f", "lavfi",
        "-i", "anullsrc=channel_layout=mono:sample_rate=24000",
        "-t", f"{duration:.3f}",
        "-c:a", "libmp3lame",
        "-q:a", "2",
        "-y",
        path,
    ]

    def _run():
        return subprocess.run(cmd, capture_output=True, timeout=120)

    try:
        result = await loop.run_in_executor(None, _run)
        return result.returncode == 0 and os.path.exists(path)
    except Exception as e:
        logger.error("Failed to generate silence: %s", e)
        return False


async def _get_media_duration(path: str, loop) -> float:
    """Return the duration (seconds) of a media file via ffprobe."""
    def _probe():
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "json",
            path,
        ]
        return subprocess.run(cmd, capture_output=True, timeout=30)

    try:
        result = await loop.run_in_executor(None, _probe)
        if result.returncode == 0:
            data = json.loads(result.stdout.decode())
            return float(data.get("format", {}).get("duration", 0))
    except Exception as e:
        logger.warning("ffprobe duration failed for %s: %s", path, e)
    return 0.0


# ── Video muxing ───────────────────────────────────────────────────────

async def _mux_audio_into_video(
    video_path: str, audio_path: str, video_out: str
) -> bool:
    """
    Create a new video that keeps the original video stream but replaces the
    audio track with the dubbed audio. The output is trimmed to the shorter of
    the two streams so it does not hang on trailing silence.
    """
    loop = asyncio.get_event_loop()
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-i", audio_path,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-y",
        video_out,
    ]

    def _run():
        return subprocess.run(cmd, capture_output=True, timeout=900)

    try:
        result = await loop.run_in_executor(None, _run)
        if result.returncode == 0 and os.path.exists(video_out):
            return True
        logger.error(
            "ffmpeg mux failed: %s",
            result.stderr.decode()[:400] if result.stderr else "unknown",
        )
    except Exception as e:
        logger.error("ffmpeg mux error: %s", e)
    return False


# ── Helpers ────────────────────────────────────────────────────────────

def _write_status(dubbed_dir: str, lang: str, status: str, stage: str) -> None:
    """Write/update the per-language dubbing status file."""
    try:
        path = os.path.join(dubbed_dir, f"status_{lang}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {"target_language": lang, "status": status, "stage": stage},
                f, ensure_ascii=False, indent=2,
            )
    except Exception as e:
        logger.warning("Could not write dubbing status: %s", e)


def _write_dubbing_json(dubbed_dir: str, lang: str, result: dict) -> None:
    """Persist the full dubbing result summary as dubbing_{lang}.json."""
    try:
        path = os.path.join(dubbed_dir, f"dubbing_{lang}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning("Could not write dubbing.json: %s", e)


def _error_result(lang: str, message: str, dubbed_dir: Optional[str] = None) -> dict:
    """Build a failure result dict and, if possible, persist the failed status."""
    logger.error("Dubbing failed (%s): %s", lang, message)
    if dubbed_dir:
        _write_status(dubbed_dir, lang, "failed", message)
    return {
        "status": "failed",
        "target_language": lang,
        "error": message,
    }


def _cleanup_dir(path: str) -> None:
    """Best-effort removal of a temporary directory and its contents."""
    try:
        for name in os.listdir(path):
            try:
                os.remove(os.path.join(path, name))
            except OSError:
                pass
        os.rmdir(path)
    except OSError:
        pass

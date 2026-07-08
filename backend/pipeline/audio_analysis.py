"""
Stage 3: Audio Analysis / Speech-to-Text
Uses Qwen-Omni-Turbo via the native DashScope multimodal API for transcription.
Falls back to the dedicated ASR endpoint when available.
"""

import asyncio
import base64
import json
import logging
import os
import re
import subprocess
import tempfile
from typing import List, Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)

# Chunk duration in seconds (qwen-omni-turbo has audio length limits)
CHUNK_DURATION = 25

TRANSCRIPTION_PROMPT = (
    "Transcribe this audio completely and accurately. "
    "Include all speech in the original language (English and/or Arabic). "
    "Return ONLY the transcribed text, nothing else."
)

# Prompt variant that asks the model to differentiate speakers inline.
DIARIZATION_PROMPT = (
    "Transcribe this audio completely and accurately. "
    "Include all speech in the original language (English and/or Arabic). "
    "If multiple speakers are present, identify each distinct speaker and "
    "prefix their dialogue with a marker like [Speaker 1], [Speaker 2], etc. "
    "Always use the same speaker number for the same voice. "
    "If only one speaker is present, prefix everything with [Speaker 1]. "
    "Return ONLY the transcribed text with speaker markers, nothing else."
)

# Matches inline speaker markers such as "[Speaker 1]", "[speaker 2]:", "[SPEAKER 3]".
SPEAKER_MARKER_RE = re.compile(r"\[\s*speaker\s*(\d+)\s*\]\s*:?", re.IGNORECASE)


async def transcribe_audio(
    audio_path: str,
    api_key: str = "",
    model: str = "paraformer-v2",
) -> dict:
    """
    Transcribe audio from a local file.

    Primary: Split audio into chunks and transcribe via qwen-omni-turbo
    (native DashScope multimodal API with base64 audio).

    Args:
        audio_path: Local path to the audio file (WAV).
        api_key: DashScope API key.
        model: ASR model identifier (kept for compatibility).

    Returns:
        dict with segments, full_text, language, and speaker info.
    """
    api_key = api_key or settings.DASHSCOPE_API_KEY
    if not api_key:
        logger.warning("No API key provided, returning empty transcription")
        return _empty_result("No API key configured")

    if not os.path.exists(audio_path):
        logger.error("Audio file not found: %s", audio_path)
        return _empty_result(f"Audio file not found: {audio_path}")

    logger.info("Starting audio transcription for %s", audio_path)

    # Get audio duration
    duration = await _get_audio_duration(audio_path)
    if duration <= 0:
        return _empty_result("Could not determine audio duration")

    logger.info("Audio duration: %.1f seconds", duration)

    # Split audio into chunks and transcribe each
    chunks = await _split_audio(audio_path, duration, CHUNK_DURATION)
    if not chunks:
        return _empty_result("Failed to split audio into chunks")

    logger.info("Split audio into %d chunks of ~%ds each", len(chunks), CHUNK_DURATION)

    segments = []
    full_text_parts = []

    for i, (chunk_path, chunk_start, chunk_end) in enumerate(chunks):
        logger.info(
            "Transcribing chunk %d/%d (%.1fs - %.1fs)",
            i + 1, len(chunks), chunk_start, chunk_end,
        )

        text = await _transcribe_chunk(chunk_path, api_key)
        if text and text.strip() and text.strip() not in ("[Music]", "[music]", ""):
            segment = {
                "start_time": chunk_start,
                "end_time": chunk_end,
                "text": text.strip(),
                "speaker_id": "unknown",
                "language": "unknown",
                "words": [],
            }
            segments.append(segment)
            full_text_parts.append(text.strip())

        # Clean up chunk file
        try:
            os.remove(chunk_path)
        except OSError:
            pass

    if not segments:
        return _empty_result("No speech detected in audio")

    return {
        "segments": segments,
        "full_text": " ".join(full_text_parts),
        "language": "mixed",
        "speaker_count": 0,
    }


async def transcribe_with_diarization(audio_path: str, api_key: str = "") -> dict:
    """
    Transcribe a local audio file with speaker diarization.

    Reuses the chunk-based Qwen-Omni-Turbo transcription, but asks the model to
    prefix each speaker's dialogue with an inline ``[Speaker N]`` marker. The
    markers are parsed into per-speaker sub-segments with consistent integer
    ``speaker_id`` values ("0", "1", "2" ...) that the frontend maps to
    "Speaker N" labels.

    Falls back to :func:`transcribe_audio` (with ``speaker_id: "unknown"``) when
    no speaker markers are detected or the diarization pass produces no speech.

    Args:
        audio_path: Local path to the audio file (WAV).
        api_key: DashScope API key.

    Returns:
        dict with segments, full_text, language, and speaker_count.
    """
    api_key = api_key or settings.DASHSCOPE_API_KEY
    if not api_key:
        logger.warning("No API key provided, returning empty transcription")
        return _empty_result("No API key configured")

    if not os.path.exists(audio_path):
        logger.error("Audio file not found: %s", audio_path)
        return _empty_result(f"Audio file not found: {audio_path}")

    logger.info("Starting diarized audio transcription for %s", audio_path)

    duration = await _get_audio_duration(audio_path)
    if duration <= 0:
        return _empty_result("Could not determine audio duration")

    logger.info("Audio duration: %.1f seconds", duration)

    chunks = await _split_audio(audio_path, duration, CHUNK_DURATION)
    if not chunks:
        return _empty_result("Failed to split audio into chunks")

    logger.info(
        "Split audio into %d chunks of ~%ds each (diarization)",
        len(chunks), CHUNK_DURATION,
    )

    segments: List[dict] = []
    full_text_parts: List[str] = []
    speaker_ids = set()
    saw_any_marker = False

    for i, (chunk_path, chunk_start, chunk_end) in enumerate(chunks):
        logger.info(
            "Transcribing chunk %d/%d with diarization (%.1fs - %.1fs)",
            i + 1, len(chunks), chunk_start, chunk_end,
        )

        text = await _transcribe_chunk(chunk_path, api_key, prompt=DIARIZATION_PROMPT)

        try:
            os.remove(chunk_path)
        except OSError:
            pass

        if not text or not text.strip() or text.strip() in ("[Music]", "[music]"):
            continue

        parsed = _parse_speaker_segments(text)
        if parsed:
            saw_any_marker = True
            chunk_dur = max(chunk_end - chunk_start, 0.0)
            total_chars = sum(len(t) for _, t in parsed) or 1
            cursor = chunk_start
            for spk_num, spk_text in parsed:
                # 1-based markers -> 0-based speaker_id for the frontend.
                speaker_id = str(max(spk_num - 1, 0))
                frac = len(spk_text) / total_chars
                seg_end = min(cursor + chunk_dur * frac, chunk_end)
                if seg_end <= cursor:
                    seg_end = chunk_end
                segments.append({
                    "start_time": cursor,
                    "end_time": seg_end,
                    "text": spk_text,
                    "speaker_id": speaker_id,
                    "language": "unknown",
                    "words": [],
                })
                full_text_parts.append(spk_text)
                speaker_ids.add(speaker_id)
                cursor = seg_end
        else:
            # No markers in this chunk — keep the text with an unknown speaker.
            clean = text.strip()
            segments.append({
                "start_time": chunk_start,
                "end_time": chunk_end,
                "text": clean,
                "speaker_id": "unknown",
                "language": "unknown",
                "words": [],
            })
            full_text_parts.append(clean)

    if not segments:
        return _empty_result("No speech detected in audio")

    # If the model never produced a single speaker marker, diarization did not
    # work; fall back to the plain transcription so behaviour is unchanged.
    if not saw_any_marker:
        logger.info("No speaker markers detected; falling back to plain transcription")
        return await transcribe_audio(audio_path, api_key)

    return {
        "segments": segments,
        "full_text": " ".join(full_text_parts),
        "language": "mixed",
        "speaker_count": len(speaker_ids),
    }


def _parse_speaker_segments(text: str) -> List[tuple]:
    """Split diarized transcription text into ``(speaker_num, text)`` tuples.

    Uses inline ``[Speaker N]`` markers. Returns an empty list when no marker
    is present so callers can fall back to single-speaker handling.
    """
    matches = list(SPEAKER_MARKER_RE.finditer(text))
    if not matches:
        return []

    result: List[tuple] = []
    for idx, m in enumerate(matches):
        speaker_num = int(m.group(1))
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        seg_text = text[start:end].strip()
        if seg_text:
            result.append((speaker_num, seg_text))
    return result


async def _get_audio_duration(audio_path: str) -> float:
    """Get audio duration in seconds using ffprobe."""
    try:
        loop = asyncio.get_event_loop()

        def _probe():
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "json",
                audio_path,
            ]
            return subprocess.run(cmd, capture_output=True, timeout=30)

        result = await loop.run_in_executor(None, _probe)
        if result.returncode == 0:
            data = json.loads(result.stdout.decode())
            return float(data.get("format", {}).get("duration", 0))
    except Exception as e:
        logger.error("ffprobe failed: %s", e)
    return 0.0


async def _split_audio(
    audio_path: str, duration: float, chunk_secs: int
) -> List[tuple]:
    """
    Split audio file into chunks using ffmpeg.

    Returns list of (chunk_path, start_time, end_time) tuples.
    """
    tmp_dir = tempfile.mkdtemp(prefix="audio_chunks_")
    chunks = []
    loop = asyncio.get_event_loop()

    num_chunks = max(1, int(duration / chunk_secs) + (1 if duration % chunk_secs > 1 else 0))

    for i in range(num_chunks):
        start = i * chunk_secs
        end = min((i + 1) * chunk_secs, duration)
        if start >= duration:
            break

        chunk_path = os.path.join(tmp_dir, f"chunk_{i:03d}.wav")
        cmd = [
            "ffmpeg",
            "-i", audio_path,
            "-ss", str(start),
            "-t", str(chunk_secs),
            "-acodec", "pcm_s16le",
            "-ac", "1",
            "-ar", "16000",
            "-y",
            chunk_path,
        ]

        def _run(c=cmd):
            return subprocess.run(c, capture_output=True, timeout=60)

        try:
            result = await loop.run_in_executor(None, _run)
            if result.returncode == 0 and os.path.exists(chunk_path):
                chunks.append((chunk_path, start, end))
            else:
                logger.warning(
                    "Failed to extract audio chunk %d: %s",
                    i,
                    result.stderr.decode()[:200] if result.stderr else "unknown",
                )
        except Exception as e:
            logger.error("Error splitting chunk %d: %s", i, e)

    return chunks


async def _transcribe_chunk(
    chunk_path: str, api_key: str, prompt: str = TRANSCRIPTION_PROMPT
) -> Optional[str]:
    """
    Transcribe a single audio chunk using qwen-omni-turbo via the
    native DashScope multimodal generation API.
    """
    try:
        with open(chunk_path, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        logger.error("Failed to read chunk %s: %s", chunk_path, e)
        return None

    endpoint = (
        f"{settings.DASHSCOPE_API_URL}"
        f"/services/aigc/multimodal-generation/generation"
    )
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "qwen-omni-turbo",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"audio": f"data:audio/wav;base64,{audio_b64}"},
                        {"text": prompt},
                    ],
                }
            ]
        },
        "parameters": {"max_tokens": 2048},
    }

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(endpoint, json=payload, headers=headers)

            if resp.status_code == 200:
                data = resp.json()
                content = (
                    data.get("output", {})
                    .get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", [])
                )
                # content is a list of dicts like [{"text": "..."}]
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and "text" in item:
                            return item["text"]
                elif isinstance(content, str):
                    return content
                return None
            else:
                logger.error(
                    "Audio chunk transcription error (attempt %d/3): %s – %s",
                    attempt + 1,
                    resp.status_code,
                    resp.text[:300],
                )
        except Exception as e:
            logger.error(
                "Audio chunk transcription exception (attempt %d/3): %s",
                attempt + 1,
                e,
            )

        await asyncio.sleep(2 ** attempt)

    return None


def _empty_result(error_msg: str = "") -> dict:
    """Return an empty but well-structured transcription result."""
    return {
        "segments": [],
        "full_text": "",
        "language": "unknown",
        "speaker_count": 0,
        "error": error_msg,
    }

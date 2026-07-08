"""
Subtitle Generation
Converts transcript segments into WebVTT / SRT subtitle files and produces
translated subtitle tracks (EN + AR/FR/RU) using the DashScope Qwen text model.
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)

# Supported subtitle languages. "en" is the source (no translation needed).
SUPPORTED_LANGUAGES = ["en", "ar", "fr", "ru"]

_LANGUAGE_NAMES = {
    "ar": "Arabic",
    "fr": "French",
    "ru": "Russian",
}


# ── Timestamp helpers ───────────────────────────────────────────────

def _to_seconds(ts) -> float:
    """Convert a timestamp to numeric seconds.

    Accepts numeric values or strings like 'SS', 'MM:SS', or 'HH:MM:SS'.
    Returns 0.0 on any parse failure.
    """
    if isinstance(ts, (int, float)):
        return float(ts)
    if not isinstance(ts, str):
        return 0.0
    parts = ts.strip().split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        return float(parts[0])
    except (ValueError, IndexError):
        return 0.0


def _format_timestamp(seconds: float, separator: str = ".") -> str:
    """Format seconds as 'HH:MM:SS<sep>mmm'.

    Use '.' for WebVTT and ',' for SRT (the millisecond separator).
    """
    if seconds < 0:
        seconds = 0.0
    total_ms = int(round(seconds * 1000))
    hours, remainder = divmod(total_ms, 3600 * 1000)
    minutes, remainder = divmod(remainder, 60 * 1000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{millis:03d}"


# ── Subtitle formatters ─────────────────────────────────────────────

def _build_speaker_labels(segments: List[dict]) -> Dict[str, str]:
    """Map distinct non-'unknown' speaker_id values to "Speaker N" labels.

    Labels are assigned in order of first appearance, matching the frontend's
    speaker-numbering behaviour.
    """
    mapping: Dict[str, str] = {}
    counter = 0
    for seg in segments:
        sid = seg.get("speaker_id")
        if sid is None:
            continue
        sid = str(sid).strip()
        if not sid or sid.lower() == "unknown":
            continue
        if sid not in mapping:
            counter += 1
            mapping[sid] = f"Speaker {counter}"
    return mapping


def _speaker_label(seg: dict, mapping: Dict[str, str]) -> Optional[str]:
    """Return the display label for a segment's speaker, or None if unknown."""
    sid = seg.get("speaker_id")
    if sid is None:
        return None
    return mapping.get(str(sid).strip())


def generate_vtt(segments: List[dict], language: str = "en") -> str:
    """Convert transcript segments into a WebVTT subtitle document.

    When a segment carries a known ``speaker_id`` (not "unknown"), the cue text
    is wrapped in a WebVTT ``<v Speaker N>`` voice tag.
    """
    lines = ["WEBVTT", ""]
    speaker_map = _build_speaker_labels(segments)
    for seg in segments:
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        start = _to_seconds(seg.get("start_time", 0))
        end = _to_seconds(seg.get("end_time", start))
        if end <= start:
            end = start + 1.0
        lines.append(
            f"{_format_timestamp(start, '.')} --> {_format_timestamp(end, '.')}"
        )
        label = _speaker_label(seg, speaker_map)
        if label:
            lines.append(f"<v {label}>{text}</v>")
        else:
            lines.append(text)
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def generate_srt(segments: List[dict], language: str = "en") -> str:
    """Convert transcript segments into an SRT subtitle document.

    When a segment carries a known ``speaker_id`` (not "unknown"), the cue text
    is prefixed with "Speaker N: " (SRT has no voice tag).
    """
    lines = []
    index = 1
    speaker_map = _build_speaker_labels(segments)
    for seg in segments:
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        start = _to_seconds(seg.get("start_time", 0))
        end = _to_seconds(seg.get("end_time", start))
        if end <= start:
            end = start + 1.0
        lines.append(str(index))
        lines.append(
            f"{_format_timestamp(start, ',')} --> {_format_timestamp(end, ',')}"
        )
        label = _speaker_label(seg, speaker_map)
        if label:
            lines.append(f"{label}: {text}")
        else:
            lines.append(text)
        lines.append("")
        index += 1
    return "\n".join(lines).rstrip("\n") + "\n"


# ── Translation ─────────────────────────────────────────────────────

def _parse_marked_segments(content: str, count: int) -> Dict[int, str]:
    """Split model output back into per-segment translations using [SEGn] markers.

    Returns a dict mapping zero-based segment index -> translated text.
    """
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


async def translate_segments(
    segments: List[dict],
    language: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
) -> List[dict]:
    """Translate segment texts into a target language (ar/fr/ru) via Qwen text model.

    Returns a new list of segments with the same timing but translated text.
    Falls back to the original text for any segment that fails to translate.
    """
    lang_name = _LANGUAGE_NAMES.get(language)
    if not lang_name:
        raise ValueError(f"Unsupported language '{language}'. Use 'ar', 'fr', or 'ru'.")

    if not segments:
        return []

    api_key = api_key or settings.DASHSCOPE_API_KEY
    model = model or settings.MODEL_TEXT
    base_url = base_url or settings.DASHSCOPE_BASE_URL

    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is not configured on the server.")

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
        "model": model,
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
    api_url = f"{base_url}/chat/completions"

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
            logger.warning("Subtitle translation attempt %d failed: %s", attempt + 1, last_error)
        except Exception as e:
            last_error = str(e)
            logger.warning("Subtitle translation attempt %d error: %s", attempt + 1, last_error)
        await asyncio.sleep(2 ** attempt)

    if content is None:
        raise RuntimeError(f"Translation failed: {last_error}")

    parsed = _parse_marked_segments(content, len(segments))

    translated = []
    for i, seg in enumerate(segments):
        text = parsed.get(i)
        translated.append({
            "start_time": seg.get("start_time", 0),
            "end_time": seg.get("end_time", 0),
            "text": (text if text else (seg.get("text") or "")),
            "speaker_id": seg.get("speaker_id", "unknown"),
        })
    return translated


# ── File-based generation ───────────────────────────────────────────

def _load_transcript_segments(video_dir: str) -> List[dict]:
    """Load transcript segments from a video's transcript.json."""
    transcript_path = os.path.join(video_dir, "transcript.json")
    if not os.path.exists(transcript_path):
        raise FileNotFoundError(f"transcript.json not found in {video_dir}")
    with open(transcript_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("segments", []) or []


def _vtt_filename(language: str) -> str:
    return f"subtitles_{language}.vtt"


def _write_text(path: str, content: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


async def generate_all_subtitles(video_id: str, base_dir: Optional[str] = None) -> Dict[str, str]:
    """Generate WebVTT subtitle files for EN + translated versions (AR, FR, RU).

    Writes:
      - subtitles_en.vtt
      - subtitles_ar.vtt
      - subtitles_fr.vtt
      - subtitles_ru.vtt

    Returns a mapping of language -> generated file path (only for successes).
    Resilient: a failure translating one language does not stop the others.
    """
    base_dir = base_dir or settings.UPLOAD_DIR
    video_dir = os.path.join(base_dir, video_id)

    segments = _load_transcript_segments(video_dir)
    if not segments:
        logger.info("No transcript segments for %s; skipping subtitle generation", video_id)
        return {}

    generated: Dict[str, str] = {}

    # English (source) — no translation needed.
    en_path = os.path.join(video_dir, _vtt_filename("en"))
    try:
        _write_text(en_path, generate_vtt(segments, "en"))
        generated["en"] = en_path
        logger.info("Generated English subtitles for %s", video_id)
    except Exception as e:
        logger.error("Failed to write English subtitles for %s: %s", video_id, e)

    # Translated languages.
    for language in ("ar", "fr", "ru"):
        try:
            translated = await translate_segments(segments, language)
            out_path = os.path.join(video_dir, _vtt_filename(language))
            _write_text(out_path, generate_vtt(translated, language))
            generated[language] = out_path
            logger.info("Generated %s subtitles for %s", language, video_id)
        except Exception as e:
            logger.warning("Failed to generate %s subtitles for %s: %s", language, video_id, e)

    return generated


async def ensure_vtt(
    video_id: str,
    language: str,
    base_dir: Optional[str] = None,
) -> str:
    """Return the VTT content for a language, generating and caching it if missing.

    Raises FileNotFoundError if the transcript is missing and ValueError for
    unsupported languages.
    """
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language '{language}'.")

    base_dir = base_dir or settings.UPLOAD_DIR
    video_dir = os.path.join(base_dir, video_id)
    vtt_path = os.path.join(video_dir, _vtt_filename(language))

    # Serve cached file if present.
    if os.path.exists(vtt_path):
        with open(vtt_path, "r", encoding="utf-8") as f:
            return f.read()

    segments = _load_transcript_segments(video_dir)

    if language == "en":
        content = generate_vtt(segments, "en")
    else:
        translated = await translate_segments(segments, language)
        content = generate_vtt(translated, language)

    # Cache for next time (best-effort).
    try:
        _write_text(vtt_path, content)
    except Exception as e:
        logger.warning("Could not cache %s subtitles for %s: %s", language, video_id, e)

    return content


async def ensure_subtitle_content(
    video_id: str,
    language: str,
    fmt: str = "srt",
    base_dir: Optional[str] = None,
) -> str:
    """Return subtitle content in the requested format ('srt' or 'vtt').

    Reuses cached VTT (and its translation) as the source of truth so that
    translations are only computed once.
    """
    fmt = (fmt or "srt").lower()
    if fmt not in ("srt", "vtt"):
        raise ValueError(f"Unsupported format '{fmt}'. Use 'srt' or 'vtt'.")

    # ensure_vtt handles caching + translation for us.
    vtt_content = await ensure_vtt(video_id, language, base_dir=base_dir)
    if fmt == "vtt":
        return vtt_content

    # Convert the (possibly translated) segments to SRT. Rebuild from VTT source
    # segments to keep timing/text identical to the cached VTT.
    segments = _segments_from_vtt(vtt_content)
    return generate_srt(segments, language)


def _segments_from_vtt(vtt_content: str) -> List[dict]:
    """Parse a WebVTT document back into transcript-style segments."""
    import re

    segments: List[dict] = []
    blocks = re.split(r"\n\s*\n", vtt_content.strip())
    cue_re = re.compile(
        r"(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[.,]\d{3})"
    )
    for block in blocks:
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if not lines or lines[0].strip().upper() == "WEBVTT":
            continue
        # Find the timing line within the block.
        timing_idx = None
        for i, ln in enumerate(lines):
            if cue_re.search(ln):
                timing_idx = i
                break
        if timing_idx is None:
            continue
        m = cue_re.search(lines[timing_idx])
        start = _vtt_ts_to_seconds(m.group(1))
        end = _vtt_ts_to_seconds(m.group(2))
        text = "\n".join(lines[timing_idx + 1:]).strip()
        # Recover a WebVTT <v Speaker N> voice tag back into speaker_id so that
        # SRT conversion can re-apply the label without duplicating it.
        speaker_id = "unknown"
        vm = re.match(r"<v\s+([^>]+)>(.*)</v>\s*$", text, re.DOTALL)
        if vm:
            speaker_id = vm.group(1).strip()
            text = vm.group(2).strip()
        if text:
            segments.append({
                "start_time": start,
                "end_time": end,
                "text": text,
                "speaker_id": speaker_id,
            })
    return segments


def _vtt_ts_to_seconds(ts: str) -> float:
    """Convert 'HH:MM:SS.mmm' or 'HH:MM:SS,mmm' to seconds."""
    ts = ts.replace(",", ".")
    h, m, s = ts.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)

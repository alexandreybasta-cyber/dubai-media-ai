"""
Subtitle Generation
Converts transcript segments into WebVTT / SRT subtitle files and produces
translated subtitle tracks (EN + AR/FR/RU) using the DashScope Qwen text model.
"""

import asyncio
import json
import logging
import os
import re
from typing import Dict, List, Optional, Tuple

import httpx

from config import settings

logger = logging.getLogger(__name__)

# Supported subtitle languages. "en" is the source (no translation needed).
SUPPORTED_LANGUAGES = ["en", "ar", "fr", "ru"]

_LANGUAGE_NAMES = {
    "ar": "Modern Standard Arabic (العربية)",
    "fr": "French",
    "ru": "Russian",
}

# Maximum characters per subtitle cue (roughly two lines of on-screen text).
_MAX_CUE_CHARS = 90
# Minimum on-screen duration (seconds) for any single sub-cue.
_MIN_CUE_DURATION = 0.8


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


# ── Cue splitting ───────────────────────────────────────────────────

# Sentence-ending / clause boundaries for Latin + Arabic punctuation. Keep the
# delimiter attached to the preceding text via a look-behind split.
_BOUNDARY_RE = re.compile(r"(?<=[.!?؟。！？،,;:])\s+")


def _split_at_word(text: str, max_chars: int) -> Tuple[str, str]:
    """Split ``text`` at the last word boundary at/under ``max_chars``.

    Falls back to a hard character cut when a single word exceeds the limit.
    Returns ``(head, remainder)``.
    """
    if len(text) <= max_chars:
        return text, ""
    cut = text.rfind(" ", 0, max_chars + 1)
    if cut <= 0:
        cut = max_chars
    return text[:cut].strip(), text[cut:].strip()


def _split_text_into_chunks(text: str, max_chars: int = _MAX_CUE_CHARS) -> List[str]:
    """Break a long segment text into subtitle-sized chunks.

    Splits on sentence/clause boundaries (periods, question marks, commas, etc.)
    then greedily repacks the pieces so each chunk stays under ``max_chars``
    while keeping 1-2 sentences together where they fit.
    """
    text = " ".join((text or "").split())  # normalise whitespace
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    units = [u.strip() for u in _BOUNDARY_RE.split(text) if u.strip()]
    chunks: List[str] = []
    buf = ""
    for unit in units:
        # Hard-wrap any single clause that is itself longer than the limit.
        while len(unit) > max_chars:
            head, unit = _split_at_word(unit, max_chars)
            if buf:
                chunks.append(buf)
                buf = ""
            if head:
                chunks.append(head)
        if not unit:
            continue
        if not buf:
            buf = unit
        elif len(buf) + 1 + len(unit) <= max_chars:
            buf = f"{buf} {unit}"
        else:
            chunks.append(buf)
            buf = unit
    if buf:
        chunks.append(buf)
    return chunks


def _expand_segments(
    segments: List[dict], max_chars: int = _MAX_CUE_CHARS
) -> List[dict]:
    """Expand transcript segments into shorter sub-cues.

    Long segments (e.g. a full 25-second transcription chunk) are split into
    several sub-cues on sentence boundaries. The original time range is divided
    proportionally to each sub-cue's character length, and the ``speaker_id`` is
    preserved so speaker colouring still works.
    """
    expanded: List[dict] = []
    for seg in segments:
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        start = _to_seconds(seg.get("start_time", 0))
        end = _to_seconds(seg.get("end_time", start))
        if end <= start:
            end = start + 1.0
        speaker_id = seg.get("speaker_id", "unknown")

        chunks = _split_text_into_chunks(text, max_chars)
        if len(chunks) <= 1:
            expanded.append({
                "start_time": start,
                "end_time": end,
                "text": text,
                "speaker_id": speaker_id,
            })
            continue

        total_len = sum(len(c) for c in chunks) or 1
        span = end - start
        cursor = start
        for i, chunk in enumerate(chunks):
            if i == len(chunks) - 1:
                cue_end = end
            else:
                cue_end = cursor + span * (len(chunk) / total_len)
            if cue_end - cursor < _MIN_CUE_DURATION:
                cue_end = min(cursor + _MIN_CUE_DURATION, end)
            if cue_end <= cursor:
                cue_end = cursor + 0.1
            expanded.append({
                "start_time": cursor,
                "end_time": cue_end,
                "text": chunk,
                "speaker_id": speaker_id,
            })
            cursor = cue_end
    return expanded


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

    Long segments are first split into shorter sub-cues (see ``_expand_segments``)
    so on-screen text stays to 1-2 short lines. When a cue carries a known
    ``speaker_id`` (not "unknown"), the cue text is wrapped in a WebVTT
    ``<v Speaker N>`` voice tag.
    """
    lines = ["WEBVTT", ""]
    cues = _expand_segments(segments)
    speaker_map = _build_speaker_labels(cues)
    for cue in cues:
        text = (cue.get("text") or "").strip()
        if not text:
            continue
        start = _to_seconds(cue.get("start_time", 0))
        end = _to_seconds(cue.get("end_time", start))
        if end <= start:
            end = start + 1.0
        lines.append(
            f"{_format_timestamp(start, '.')} --> {_format_timestamp(end, '.')}"
        )
        label = _speaker_label(cue, speaker_map)
        if label:
            lines.append(f"<v {label}>{text}</v>")
        else:
            lines.append(text)
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def generate_srt(segments: List[dict], language: str = "en") -> str:
    """Convert transcript segments into an SRT subtitle document.

    Long segments are split into shorter sub-cues (see ``_expand_segments``).
    When a cue carries a known ``speaker_id`` (not "unknown"), the cue text is
    prefixed with "Speaker N: " (SRT has no voice tag).
    """
    lines = []
    index = 1
    cues = _expand_segments(segments)
    speaker_map = _build_speaker_labels(cues)
    for cue in cues:
        text = (cue.get("text") or "").strip()
        if not text:
            continue
        start = _to_seconds(cue.get("start_time", 0))
        end = _to_seconds(cue.get("end_time", start))
        if end <= start:
            end = start + 1.0
        lines.append(str(index))
        lines.append(
            f"{_format_timestamp(start, ',')} --> {_format_timestamp(end, ',')}"
        )
        label = _speaker_label(cue, speaker_map)
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

    # Some models (e.g. Qwen) may default to Chinese output; be explicit about
    # the target script/language to prevent that, especially for Arabic.
    extra = ""
    if language == "ar":
        extra = (
            " The target language is Modern Standard Arabic written in Arabic script (العربية). "
            "Do NOT translate to Chinese or any other language — every translated segment "
            "MUST be written in Arabic."
        )

    joined = "\n".join(
        f"[SEG{i + 1}] {(seg.get('text') or '').strip()}"
        for i, seg in enumerate(segments)
    )

    system_prompt = (
        f"You are a professional translator. Translate the user's text into {lang_name}.{extra} "
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

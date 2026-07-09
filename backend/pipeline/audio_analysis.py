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
import subprocess
import tempfile
from typing import List, Optional

import aiofiles
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

# DashScope Paraformer v2 ASR endpoints.
# NOTE: this deployment uses an international (ap-southeast-1) DashScope key, so
# the public host must be the international one (dashscope-intl.aliyuncs.com).
# The China host (dashscope.aliyuncs.com) rejects this key as InvalidApiKey.
PARAFORMER_SUBMIT_URL = (
    "https://dashscope-intl.aliyuncs.com/api/v1/services/audio/asr/transcription"
)
PARAFORMER_TASK_URL = "https://dashscope-intl.aliyuncs.com/api/v1/tasks/{task_id}"

# Max audio size for base64 inline submission (50 MB).
MAX_INLINE_AUDIO_BYTES = 50 * 1024 * 1024


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
    Transcribe audio with real acoustic speaker diarization using DashScope
    Paraformer v2.

    Submits an asynchronous ASR transcription task (with ``diarization_enabled``)
    to the DashScope Paraformer v2 service, polls until completion, and parses
    the per-sentence results into the standard segment format with integer
    ``speaker_id`` values assigned by the model's acoustic diarization.

    Falls back to :func:`transcribe_audio` (single-speaker, ``speaker_id:
    "unknown"``) if Paraformer fails or the audio is too large for inline
    base64 submission.

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

    logger.info("Starting Paraformer diarized transcription for %s", audio_path)

    # Guard against oversized inline base64 payloads.
    file_size = os.path.getsize(audio_path)
    if file_size > MAX_INLINE_AUDIO_BYTES:
        logger.warning(
            "Audio file too large for base64 (%d bytes), falling back", file_size
        )
        return await transcribe_audio(audio_path, api_key)

    try:
        # 1. Read audio file and encode as base64 data URL.
        async with aiofiles.open(audio_path, "rb") as f:
            audio_bytes = await f.read()
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        ext = os.path.splitext(audio_path)[1].lower().lstrip(".")
        if ext == "wav":
            mime = "audio/wav"
        elif ext == "mp3":
            mime = "audio/mpeg"
        else:
            mime = f"audio/{ext}"

        file_url = f"data:{mime};base64,{audio_b64}"

        # 2. Submit the asynchronous transcription task.
        async with httpx.AsyncClient(timeout=30) as client:
            submit_resp = await client.post(
                PARAFORMER_SUBMIT_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "X-DashScope-Async": "enable",
                },
                json={
                    "model": "paraformer-v2",
                    "input": {"file_urls": [file_url]},
                    "parameters": {
                        "diarization_enabled": True,
                        "language_hints": ["en", "ar"],
                    },
                },
            )
            submit_data = submit_resp.json()

        task_id = submit_data["output"]["task_id"]
        logger.info("Paraformer task submitted: %s", task_id)

        # 3. Poll for completion (up to ~5 minutes).
        max_polls = 60
        poll_data = None
        for _ in range(max_polls):
            await asyncio.sleep(5)
            async with httpx.AsyncClient(timeout=30) as client:
                poll_resp = await client.get(
                    PARAFORMER_TASK_URL.format(task_id=task_id),
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                poll_data = poll_resp.json()

            status = poll_data["output"]["task_status"]
            if status == "SUCCEEDED":
                break
            if status in ("FAILED", "CANCELED"):
                raise RuntimeError(f"Paraformer task {status}: {poll_data}")
            # PENDING or RUNNING -> keep polling.
        else:
            raise RuntimeError("Paraformer task timed out after polling")

        # 4. Fetch the transcription JSON from the result URL.
        transcription_url = poll_data["output"]["results"][0]["transcription_url"]
        async with httpx.AsyncClient(timeout=30) as client:
            result_resp = await client.get(transcription_url)
            result_json = result_resp.json()

        # 5. Parse into the standard segment format.
        transcripts = result_json.get("transcripts", [])
        if not transcripts:
            raise RuntimeError("No transcripts in Paraformer response")

        sentences = transcripts[0].get("sentences", [])
        segments: List[dict] = []
        for sentence in sentences:
            segments.append({
                "start_time": sentence["begin_time"] / 1000.0,
                "end_time": sentence["end_time"] / 1000.0,
                "text": sentence["text"].strip(),
                "speaker_id": str(sentence.get("speaker_id", "unknown")),
                "language": "unknown",
                "words": sentence.get("words", []),
            })

        if not segments:
            raise RuntimeError("No sentences in Paraformer response")

        full_text = transcripts[0].get(
            "text", " ".join(s["text"] for s in segments)
        )
        speaker_ids = set(
            s["speaker_id"] for s in segments if s["speaker_id"] != "unknown"
        )

        logger.info(
            "Paraformer diarization complete: %d segments, %d speakers",
            len(segments),
            len(speaker_ids),
        )

        return {
            "segments": segments,
            "full_text": full_text,
            "language": "mixed",
            "speaker_count": len(speaker_ids),
        }

    except Exception as e:
        logger.warning(
            "Paraformer diarization failed, falling back to standard "
            "transcription: %r",
            e,
        )
        return await transcribe_audio(audio_path, api_key)


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

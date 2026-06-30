"""
Stage 3: Audio Analysis / Speech-to-Text
Submits audio to DashScope ASR (paraformer-v2) for transcription with speaker diarization.
"""

import asyncio
import json
import logging
from typing import Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)


def _asr_submit_url() -> str:
    return f"{settings.DASHSCOPE_API_URL}/services/audio/asr/transcription"


def _task_status_url(task_id: str) -> str:
    return f"{settings.DASHSCOPE_API_URL}/tasks/{task_id}"


POLL_INTERVAL = 5  # seconds
MAX_POLL_ATTEMPTS = 120  # 10 minutes max


async def transcribe_audio(
    audio_url: str,
    api_key: str,
    model: str = "paraformer-v2",
) -> dict:
    """
    Submit audio to DashScope ASR for Arabic/English transcription with diarization.

    This is an async API: submit task, then poll until complete.

    Args:
        audio_url: Publicly accessible URL of the audio file (WAV).
        api_key: DashScope API key.
        model: ASR model identifier.

    Returns:
        dict with segments, full_text, language, and speaker info.
    """
    if not api_key:
        logger.warning("No API key provided, returning empty transcription")
        return _empty_result("No API key configured")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # --- Submit transcription task ---
    task_id = await _submit_task(audio_url, model, headers)
    if not task_id:
        return _empty_result("Failed to submit ASR task")

    # --- Poll for completion ---
    result = await _poll_task(task_id, headers)
    if result is None:
        return _empty_result(f"ASR task {task_id} did not complete")

    return _parse_transcript(result)


async def _submit_task(
    audio_url: str,
    model: str,
    headers: dict,
) -> Optional[str]:
    """Submit an ASR transcription task and return the task_id."""
    payload = {
        "model": model,
        "input": {"file_urls": [audio_url]},
        "parameters": {
            "language_hints": ["ar", "en"],
            "diarization_enabled": True,
        },
    }

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    _asr_submit_url(), json=payload, headers=headers
                )
                resp.raise_for_status()
                data = resp.json()

            task_id = data.get("output", {}).get("task_id")
            if task_id:
                logger.info("ASR task submitted: %s", task_id)
                return task_id

            logger.error("No task_id in ASR response: %s", data)
            return None

        except httpx.HTTPStatusError as e:
            logger.error(
                "ASR submit error (attempt %d/3): %s – %s",
                attempt + 1, e.response.status_code, e.response.text[:500],
            )
        except httpx.RequestError as e:
            logger.error(
                "ASR submit request error (attempt %d/3): %s",
                attempt + 1, e,
            )
        except Exception as e:
            logger.error(
                "ASR submit unexpected error (attempt %d/3): %s",
                attempt + 1, e,
            )

        await asyncio.sleep(2 ** attempt)

    return None


async def _poll_task(task_id: str, headers: dict) -> Optional[dict]:
    """Poll the task status until completion or timeout."""
    url = _task_status_url(task_id)

    for i in range(MAX_POLL_ATTEMPTS):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            status = data.get("output", {}).get("task_status", "")
            logger.debug("ASR task %s status: %s", task_id, status)

            if status == "SUCCEEDED":
                return data.get("output", {})
            elif status in ("FAILED", "CANCELED"):
                error_msg = data.get("output", {}).get("message", "Unknown error")
                logger.error("ASR task %s failed: %s", task_id, error_msg)
                return None

        except Exception as e:
            logger.warning("Poll error for task %s: %s", task_id, e)

        await asyncio.sleep(POLL_INTERVAL)

    logger.error("ASR task %s timed out after %d polls", task_id, MAX_POLL_ATTEMPTS)
    return None


def _parse_transcript(output: dict) -> dict:
    """Parse the ASR output into our structured format."""
    segments = []
    full_text_parts = []

    try:
        results = output.get("results", [])
        if not results:
            return _empty_result("No transcription results returned")

        # DashScope ASR returns a URL to the transcript JSON
        transcript_url = None
        for r in results:
            url = r.get("transcription_url")
            if url:
                transcript_url = url
                break

        if transcript_url:
            # Fetch the actual transcript
            transcript_data = _fetch_transcript_sync(transcript_url)
            if transcript_data:
                return _parse_transcript_data(transcript_data)

        # Fallback: try to parse inline results
        return _empty_result("Could not retrieve transcript data")

    except Exception as e:
        logger.error("Transcript parse error: %s", e)
        return _empty_result(f"Parse error: {e}")


def _fetch_transcript_sync(url: str) -> Optional[dict]:
    """Synchronously fetch transcript JSON from URL."""
    try:
        import httpx as httpx_sync
        with httpx_sync.Client(timeout=30.0) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.error("Failed to fetch transcript from %s: %s", url, e)
        return None


def _parse_transcript_data(data: dict) -> dict:
    """Parse the detailed transcript JSON into our format."""
    segments = []
    full_text_parts = []

    transcripts = data.get("transcripts", [data]) if isinstance(data, dict) else [data]

    for transcript in transcripts:
        sentences = transcript.get("sentences", transcript.get("segments", []))
        for sent in sentences:
            seg = {
                "start_time": sent.get("begin_time", sent.get("start", 0)) / 1000.0
                if sent.get("begin_time", sent.get("start", 0)) > 100
                else sent.get("begin_time", sent.get("start", 0)),
                "end_time": sent.get("end_time", sent.get("end", 0)) / 1000.0
                if sent.get("end_time", sent.get("end", 0)) > 100
                else sent.get("end_time", sent.get("end", 0)),
                "speaker_id": sent.get("speaker_id", "unknown"),
                "text": sent.get("text", ""),
                "language": sent.get("language", "unknown"),
                "words": [],
            }

            # Parse word-level timestamps if available
            for word in sent.get("words", []):
                seg["words"].append({
                    "word": word.get("text", word.get("word", "")),
                    "start": word.get("begin_time", word.get("start", 0)),
                    "end": word.get("end_time", word.get("end", 0)),
                })

            segments.append(seg)
            full_text_parts.append(seg["text"])

    return {
        "segments": segments,
        "full_text": " ".join(full_text_parts),
        "language": "mixed",
        "speaker_count": len(set(s["speaker_id"] for s in segments if s["speaker_id"] != "unknown")),
    }


def _empty_result(error_msg: str = "") -> dict:
    """Return an empty but well-structured transcription result."""
    return {
        "segments": [],
        "full_text": "",
        "language": "unknown",
        "speaker_count": 0,
        "error": error_msg,
    }

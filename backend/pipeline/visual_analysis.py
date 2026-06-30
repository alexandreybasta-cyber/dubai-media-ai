"""
Stage 2: Visual Analysis via Qwen-VL
Extracts keyframes from the video, encodes them as base64, and sends to
DashScope Qwen-VL model for comprehensive visual analysis.
"""

import asyncio
import base64
import json
import logging
import os
import re
import subprocess
import tempfile
from typing import List, Optional, Tuple

import httpx

from config import settings

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """Analyze these video keyframes comprehensively for a media archive system.
The images are keyframes extracted at regular intervals from a single video.
Frame timestamps are provided so you can reference specific moments.

Return ONLY valid JSON with this structure:
{
  "scenes": [
    {"timestamp": "MM:SS", "description_en": "...", "description_ar": "...", "scene_type": "interview|b-roll|aerial|ceremony|sport|news-anchor|documentary|other"}
  ],
  "objects": [
    {"timestamp": "MM:SS", "name": "...", "category": "person|vehicle|building|landmark|nature|technology|text|other", "confidence": 0.95}
  ],
  "landmarks": [
    {"timestamp": "MM:SS", "name": "...", "location": "city, country"}
  ],
  "faces": [
    {"timestamp": "MM:SS", "description": "physical description of person", "bbox": "approximate position", "age_estimate": "30-40", "gender": "male|female", "on_screen_name": "name if visible as overlay/lower-third near this person, null otherwise", "on_screen_title": "title/role if visible as overlay near this person, null otherwise", "source_channel": "channel/network logo visible in frame, null otherwise"}
  ],
  "text_ocr": [
    {"timestamp": "MM:SS", "text": "text visible on screen", "language": "ar|en|other"}
  ],
  "sensitive_content": [
    {"timestamp": "MM:SS", "type": "violence|nudity|political|religious|other", "severity": "low|medium|high"}
  ],
  "era_estimate": {"decade": "2020s", "confidence": 0.9, "visual_cues": ["modern buildings", "HD quality"]},
  "overall_summary_en": "Brief summary in English",
  "overall_summary_ar": "ملخص موجز بالعربية"
}

Be thorough. Identify all visible text (Arabic and English), landmarks (especially UAE landmarks like Burj Khalifa, Dubai Frame, etc.), and notable persons. For scenes, describe the visual content, mood, and camera work. For faces, provide detailed physical descriptions that could help with identification.

IMPORTANT: Pay special attention to on-screen text overlays such as lower-thirds (name + title text that appears over or below a person's face), chyrons, and channel logos. If a name label is visible near a person's face, ALWAYS include it in the on_screen_name field for that face entry. This is critical for person identification."""


async def analyze_video_visually(
    video_path: str,
    api_key: str = "",
    model: str = "",
    base_url: str = "",
) -> dict:
    """
    Analyze video by extracting keyframes and sending them as base64 images
    to the Qwen-VL model for comprehensive visual analysis.

    Args:
        video_path: Local path to the video file.
        api_key: DashScope API key.
        model: Model identifier (default qwen-vl-max).
        base_url: DashScope API base URL.

    Returns:
        Parsed JSON dict with scenes, objects, landmarks, faces, text_ocr, etc.
    """
    api_key = api_key or settings.DASHSCOPE_VIDEO_API_KEY
    model = model or settings.MODEL_VIDEO
    base_url = base_url or settings.DASHSCOPE_BASE_URL

    if not api_key:
        logger.warning("No API key provided, returning empty visual analysis")
        return _empty_result("No API key configured")

    if not os.path.exists(video_path):
        logger.error("Video file not found: %s", video_path)
        return _empty_result(f"Video file not found: {video_path}")

    # Extract keyframes from video
    logger.info("Extracting keyframes from %s", video_path)
    frames = await _extract_keyframes(video_path, max_frames=12)
    if not frames:
        return _empty_result("Failed to extract keyframes from video")

    logger.info("Extracted %d keyframes, encoding as base64", len(frames))

    # Build content array with base64 images
    content = []
    timestamp_text_parts = []
    for i, (frame_path, timestamp_sec) in enumerate(frames):
        b64_data = _encode_frame_base64(frame_path)
        if b64_data:
            mins = int(timestamp_sec) // 60
            secs = int(timestamp_sec) % 60
            ts_label = f"{mins:02d}:{secs:02d}"
            timestamp_text_parts.append(f"Frame {i+1}: {ts_label}")
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64_data}"},
            })

    if not content:
        return _empty_result("Failed to encode any keyframes")

    # Add text prompt with timestamp reference
    frame_list_text = "\n".join(timestamp_text_parts)
    prompt_text = (
        f"The following {len(content)} images are keyframes extracted from a video "
        f"at these timestamps:\n{frame_list_text}\n\n{ANALYSIS_PROMPT}"
    )
    content.append({"type": "text", "text": prompt_text})

    endpoint = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 4096,
    }

    logger.info("Sending %d frames to %s model for visual analysis", len(frames), model)

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                resp = await client.post(endpoint, json=payload, headers=headers)
                logger.info(
                    "Visual analysis API response status: %s", resp.status_code
                )
                if resp.status_code != 200:
                    logger.error(
                        "Visual analysis API error body: %s", resp.text[:1000]
                    )
                resp.raise_for_status()
                data = resp.json()

            raw_content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            logger.info(
                "Visual analysis raw response (first 500 chars): %s",
                raw_content[:500],
            )
            return _parse_analysis_json(raw_content)

        except httpx.HTTPStatusError as e:
            logger.error(
                "Visual analysis API error (attempt %d/3): %s – %s",
                attempt + 1,
                e.response.status_code,
                e.response.text[:500],
            )
            if attempt == 2:
                return _empty_result(f"API error: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(
                "Visual analysis request error (attempt %d/3): %s",
                attempt + 1,
                e,
            )
            if attempt == 2:
                return _empty_result(f"Request error: {e}")
        except Exception as e:
            logger.error(
                "Visual analysis unexpected error (attempt %d/3): %s",
                attempt + 1,
                e,
            )
            if attempt == 2:
                return _empty_result(f"Unexpected error: {e}")

        await asyncio.sleep(2 ** attempt)

    return _empty_result("All retry attempts exhausted")


async def _extract_keyframes(
    video_path: str, max_frames: int = 12
) -> List[Tuple[str, float]]:
    """
    Extract keyframes from a video at regular intervals using ffmpeg.

    Returns:
        List of (frame_file_path, timestamp_in_seconds) tuples.
    """
    try:
        # Get video duration via ffprobe
        duration = await _get_video_duration(video_path)
        if duration <= 0:
            logger.error("Could not determine video duration")
            return []

        # Calculate interval between frames
        interval = max(duration / max_frames, 1.0)
        actual_frames = min(max_frames, max(1, int(duration / interval)))

        logger.info(
            "Video duration: %.1fs, extracting %d frames at %.1fs intervals",
            duration,
            actual_frames,
            interval,
        )

        # Create temp dir for frames
        tmp_dir = tempfile.mkdtemp(prefix="visual_frames_")
        frames = []

        loop = asyncio.get_event_loop()

        for i in range(actual_frames):
            timestamp = i * interval
            if timestamp >= duration:
                break
            frame_path = os.path.join(tmp_dir, f"frame_{i:03d}.jpg")

            # Extract single frame at timestamp
            cmd = [
                "ffmpeg",
                "-ss", str(timestamp),
                "-i", video_path,
                "-vframes", "1",
                "-q:v", "3",
                "-y",
                frame_path,
            ]

            def _run_cmd(c=cmd):
                return subprocess.run(
                    c,
                    capture_output=True,
                    timeout=30,
                )

            result = await loop.run_in_executor(None, _run_cmd)
            if result.returncode == 0 and os.path.exists(frame_path):
                frames.append((frame_path, timestamp))
            else:
                logger.warning(
                    "Failed to extract frame at %.1fs: %s",
                    timestamp,
                    result.stderr.decode()[:200] if result.stderr else "unknown",
                )

        logger.info("Successfully extracted %d/%d keyframes", len(frames), actual_frames)
        return frames

    except Exception as e:
        logger.error("Keyframe extraction failed: %s", e)
        return []


async def _get_video_duration(video_path: str) -> float:
    """Get video duration in seconds using ffprobe."""
    try:
        loop = asyncio.get_event_loop()

        def _probe():
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "json",
                video_path,
            ]
            return subprocess.run(cmd, capture_output=True, timeout=30)

        result = await loop.run_in_executor(None, _probe)
        if result.returncode == 0:
            data = json.loads(result.stdout.decode())
            return float(data.get("format", {}).get("duration", 0))
    except Exception as e:
        logger.error("ffprobe failed: %s", e)

    return 0.0


def _encode_frame_base64(frame_path: str) -> Optional[str]:
    """Read a JPEG frame file and return its base64-encoded string."""
    try:
        with open(frame_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        logger.error("Failed to encode frame %s: %s", frame_path, e)
        return None


def _parse_analysis_json(content: str) -> dict:
    """Extract and parse JSON from the model's response text."""
    # Try direct parse first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from markdown code block
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding first { to last }
    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(content[start : end + 1])
        except json.JSONDecodeError:
            pass

    logger.warning("Could not parse JSON from visual analysis response")
    return _empty_result(f"Failed to parse response: {content[:200]}")


def _empty_result(error_msg: str = "") -> dict:
    """Return an empty but well-structured result."""
    return {
        "scenes": [],
        "objects": [],
        "landmarks": [],
        "faces": [],
        "text_ocr": [],
        "sensitive_content": [],
        "era_estimate": {"decade": "unknown", "confidence": 0, "visual_cues": []},
        "overall_summary_en": "",
        "overall_summary_ar": "",
        "error": error_msg,
    }

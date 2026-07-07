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
from pipeline.scene_detection import detect_scenes, extract_scene_frames

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """Analyze these video keyframes comprehensively for a media archive system.
Each image is the representative frame of one detected scene (shot) from a single video.
Scene numbers and their start-end time ranges are provided so you can reference specific moments.

Return ONLY valid JSON with this structure:
{
  "scenes": [
    {"scene_index": 0, "timestamp": "MM:SS", "description_en": "...", "description_ar": "...", "scene_type": "interview|b-roll|aerial|ceremony|sport|news-anchor|documentary|other"}
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

Be thorough. Identify all visible text (Arabic and English), landmarks (especially UAE landmarks like Burj Khalifa, Dubai Frame, etc.), and notable persons. Return EXACTLY one scene entry per detected scene (a scene may have two frames — describe it once), with scene_index matching the scene number. For scenes, describe the visual content, mood, and camera work. For faces, provide detailed physical descriptions that could help with identification.

CRITICAL — on-screen name labels: near-start frames often contain lower-thirds (a person's name + title overlaid on the lower part of the frame), chyrons, and captions. Read EVERY piece of overlay text character by character and include it in text_ocr. When a name/title label appears near a person's face, you MUST copy it into that face entry's on_screen_name and on_screen_title fields — this is the primary way people get identified. A face seen in one frame of a scene and named in another frame of the same scene is the same person: attach the name.

Keep the output compact so it fits the token budget: each description_en/description_ar under 25 words, reasoning-free, no markdown, no comments — pure JSON only."""


async def analyze_video_visually(
    video_path: str,
    api_key: str = "",
    model: str = "",
    base_url: str = "",
    output_dir: str = "",
) -> dict:
    """
    Analyze video by detecting scene boundaries, extracting one representative
    frame per scene, and sending them as base64 images to the Qwen-VL model.

    Args:
        video_path: Local path to the video file.
        api_key: DashScope API key.
        model: Model identifier (default qwen-vl-max).
        base_url: DashScope API base URL.
        output_dir: Directory where scene frames are persisted (served under
            /uploads); falls back to a temp dir when empty.

    Returns:
        Parsed JSON dict with scenes (incl. start/end/thumbnail), objects,
        landmarks, faces, text_ocr, etc.
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

    # Detect scene boundaries, then extract one frame per scene
    duration = await _get_video_duration(video_path)
    scene_segments = await detect_scenes(video_path, duration)
    if not scene_segments:
        return _empty_result("Failed to detect scenes in video")

    if output_dir:
        frames_dir = os.path.join(output_dir, "scenes")
    else:
        frames_dir = tempfile.mkdtemp(prefix="visual_frames_")

    logger.info("Detected %d scenes, extracting representative frames", len(scene_segments))
    frames = await extract_scene_frames(video_path, scene_segments, frames_dir)
    if not frames:
        return _empty_result("Failed to extract keyframes from video")

    # Build content array with base64 images. Long scenes contribute two
    # frames (near-start + middle); scene entries are still one per scene.
    segments_by_index = {seg["index"]: seg for seg in scene_segments}
    content = []
    timestamp_text_parts = []
    frame_scene_indices = []
    for frame_path, timestamp_sec, scene_index in frames:
        b64_data = _encode_frame_base64(frame_path)
        if b64_data:
            seg = segments_by_index[scene_index]
            midpoint = (seg["start"] + seg["end"]) / 2
            position = "near start of scene" if timestamp_sec < midpoint - 0.5 else "middle of scene"
            timestamp_text_parts.append(
                f"Frame {len(frame_scene_indices) + 1} → Scene {scene_index} "
                f"({_fmt_ts(seg['start'])}–{_fmt_ts(seg['end'])}), taken at "
                f"{_fmt_ts(timestamp_sec)} ({position})"
            )
            frame_scene_indices.append(scene_index)
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64_data}"},
            })

    if not content:
        return _empty_result("Failed to encode any keyframes")

    unique_scene_count = len(dict.fromkeys(frame_scene_indices))

    # Add text prompt with scene/timestamp reference
    frame_list_text = "\n".join(timestamp_text_parts)
    prompt_text = (
        f"The following {len(content)} images are frames from the "
        f"{unique_scene_count} detected scenes of a video (long scenes have two "
        f"frames — one near the start, one from the middle):\n{frame_list_text}\n\n"
        f"{ANALYSIS_PROMPT}"
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
        "max_tokens": 8192,
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
            analysis = _parse_analysis_json(raw_content)
            return _attach_scene_segments(
                analysis, scene_segments, frame_scene_indices, frames_dir, output_dir
            )

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


def _fmt_ts(seconds: float) -> str:
    """Format seconds as MM:SS."""
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins:02d}:{secs:02d}"


def _attach_scene_segments(
    analysis: dict,
    scene_segments: List[dict],
    frame_scene_indices: List[int],
    frames_dir: str,
    output_dir: str,
) -> dict:
    """
    Attach detected start/end boundaries and thumbnail URLs to the scenes
    returned by the vision model, matching by scene_index (or order as fallback).
    """
    segments_by_index = {seg["index"]: seg for seg in scene_segments}

    def _thumbnail_url(scene_index: int) -> str:
        if not output_dir:
            return ""
        frame_path = os.path.join(frames_dir, f"scene_{scene_index:03d}.jpg")
        if not os.path.exists(frame_path):
            return ""
        rel = os.path.relpath(frame_path, settings.UPLOAD_DIR)
        return "/uploads/" + rel.replace(os.sep, "/")

    # Fallback order-matching uses unique scene indices (a scene may have
    # contributed multiple frames)
    ordered_scene_indices = list(dict.fromkeys(frame_scene_indices))

    scenes = analysis.get("scenes") or []
    for order, scene in enumerate(scenes):
        idx = scene.get("scene_index")
        if not isinstance(idx, int) or idx not in segments_by_index:
            idx = ordered_scene_indices[order] if order < len(ordered_scene_indices) else None
        if idx is None or idx not in segments_by_index:
            continue
        seg = segments_by_index[idx]
        scene["scene_index"] = idx
        scene["start"] = seg["start"]
        scene["end"] = seg["end"]
        scene["timestamp"] = _fmt_ts(seg["start"])
        thumb = _thumbnail_url(idx)
        if thumb:
            scene["thumbnail"] = thumb

    analysis["scene_detection"] = {
        "method": "ffmpeg-scene-filter",
        "segments": scene_segments,
        "frame_count": len(frame_scene_indices),
    }
    return analysis


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

    # Response may be truncated mid-way (max_tokens) — repair by dropping the
    # incomplete tail and closing open brackets, keeping all complete entries.
    repaired = _repair_truncated_json(content)
    if repaired is not None:
        logger.warning("Visual analysis response was truncated; recovered partial JSON")
        return repaired

    logger.warning("Could not parse JSON from visual analysis response")
    return _empty_result(f"Failed to parse response: {content[:200]}")


def _repair_truncated_json(content: str) -> Optional[dict]:
    """
    Best-effort recovery of a truncated JSON object: cut back to the last
    complete value and append the missing closing brackets.
    """
    start = content.find("{")
    if start == -1:
        return None
    text = content[start:]

    # Candidate cut points: positions right after a '}' or ']' (end of a
    # complete nested value), scanned from the end.
    candidates = [m.end() for m in re.finditer(r"[}\]]", text)]
    for cut in reversed(candidates[-80:]):
        prefix = text[:cut]
        # Compute bracket balance outside of strings
        stack = []
        in_string = False
        escaped = False
        valid = True
        for ch in prefix:
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
            elif ch in "{[":
                stack.append(ch)
            elif ch in "}]":
                if not stack or {"}": "{", "]": "["}[ch] != stack[-1]:
                    valid = False
                    break
                stack.pop()
        if not valid or in_string:
            continue
        closing = "".join("}" if b == "{" else "]" for b in reversed(stack))
        try:
            result = json.loads(prefix + closing)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            continue
    return None


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

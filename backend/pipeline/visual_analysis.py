"""
Stage 2: Visual Analysis via Qwen-VL
Sends video to DashScope Qwen VL model for comprehensive visual analysis.
"""

import json
import logging
import re
from typing import Optional

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """Analyze this video comprehensively for a media archive system. Return ONLY valid JSON with this structure:
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
    {"timestamp": "MM:SS", "description": "physical description of person", "bbox": "approximate position", "age_estimate": "30-40", "gender": "male|female"}
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

Be thorough. Identify all visible text (Arabic and English), landmarks (especially UAE landmarks like Burj Khalifa, Dubai Frame, etc.), and notable persons. For scenes, describe the visual content, mood, and camera work. For faces, provide detailed physical descriptions that could help with identification."""


async def analyze_video_visually(
    video_url: str,
    api_key: str = "",
    model: str = "",
    base_url: str = "",
) -> dict:
    """
    Send video to Qwen VL model for comprehensive visual analysis.

    Args:
        video_url: Publicly accessible URL of the video.
        api_key: DashScope API key.
        model: Model identifier (default qwen-vl-max).
        base_url: DashScope API base URL.

    Returns:
        Parsed JSON dict with scenes, objects, landmarks, faces, text_ocr, etc.
    """
    # Use settings defaults if not explicitly provided
    api_key = api_key or settings.DASHSCOPE_VIDEO_API_KEY
    model = model or settings.MODEL_VIDEO
    base_url = base_url or settings.DASHSCOPE_BASE_URL

    if not api_key:
        logger.warning("No API key provided, returning empty visual analysis")
        return _empty_result("No API key configured")

    endpoint = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "video_url",
                        "video_url": {"url": video_url},
                        "fps": 1,
                    },
                    {
                        "type": "text",
                        "text": ANALYSIS_PROMPT,
                    },
                ],
            }
        ],
    }

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                resp = await client.post(endpoint, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            return _parse_analysis_json(content)

        except httpx.HTTPStatusError as e:
            logger.error(
                "Visual analysis API error (attempt %d/3): %s – %s",
                attempt + 1, e.response.status_code, e.response.text[:500],
            )
            if attempt == 2:
                return _empty_result(f"API error: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(
                "Visual analysis request error (attempt %d/3): %s",
                attempt + 1, e,
            )
            if attempt == 2:
                return _empty_result(f"Request error: {e}")
        except Exception as e:
            logger.error(
                "Visual analysis unexpected error (attempt %d/3): %s",
                attempt + 1, e,
            )
            if attempt == 2:
                return _empty_result(f"Unexpected error: {e}")

        # Exponential backoff
        import asyncio
        await asyncio.sleep(2 ** attempt)

    return _empty_result("All retry attempts exhausted")


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

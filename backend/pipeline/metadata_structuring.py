"""
Stage 5: Metadata Structuring
Generates structured broadcast metadata (EBUCore XML, IPTC Video Metadata Hub)
from aggregated analysis results using Qwen-Max.
"""

import asyncio
import json
import logging
import os
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
IPTC_TAXONOMY_PATH = os.path.join(DATA_DIR, "iptc_taxonomy.json")


def _load_iptc_taxonomy() -> dict:
    """Load IPTC taxonomy from JSON file."""
    try:
        with open(IPTC_TAXONOMY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("IPTC taxonomy file not found: %s", IPTC_TAXONOMY_PATH)
        return {}
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in IPTC taxonomy: %s", e)
        return {}


STRUCTURING_PROMPT = """You are a broadcast metadata specialist working for a UAE media organization. 
Given the following analysis results from a video, generate structured metadata.

VIDEO ANALYSIS DATA:
{analysis_json}

IPTC TAXONOMY (use codes from this list for topic classification):
{taxonomy_json}

Generate the following in a single JSON response:
{{
  "ebucore_xml": "<EBUCoreMainType>...</EBUCoreMainType>",
  "iptc_video_metadata": {{
    "videoContent": {{
      "headline": "...",
      "description_en": "...",
      "description_ar": "...",
      "dateCreated": "auto-detect or unknown",
      "creator": "Dubai Media Incorporated",
      "keywords_en": ["keyword1", "keyword2"],
      "keywords_ar": ["كلمة1", "كلمة2"],
      "language": ["ar", "en"],
      "genre": "news|documentary|interview|sport|entertainment|other",
      "duration": "PT{duration}S"
    }},
    "videoRights": {{
      "rightsOwner": "Dubai Media Incorporated",
      "copyrightNotice": "© Dubai Media Incorporated"
    }}
  }},
  "topic_codes": ["code1", "code2"],
  "topic_names_en": ["Topic 1 EN", "Topic 2 EN"],
  "topic_names_ar": ["الموضوع 1", "الموضوع 2"],
  "sentiment_tags": ["positive|negative|neutral", "formal|informal", "urgent|routine"],
  "tone": "informational|celebratory|somber|dramatic|casual",
  "content_rating": "G|PG|PG-13|R",
  "geographic_tags": ["Dubai", "UAE"],
  "persons_mentioned": [
    {{"name_en": "...", "name_ar": "...", "role": "..."}}
  ]
}}

For EBUCore XML, generate a valid but concise XML snippet following EBU Tech 3293 standard.
All Arabic text must be proper Arabic. Ensure bilingual metadata (English + Arabic)."""


async def structure_metadata(
    analysis_results: dict,
    api_key: str,
    model: str = "qwen-max",
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
) -> dict:
    """
    Generate structured broadcast metadata from analysis results.

    Args:
        analysis_results: Aggregated dict with visual analysis, transcript, faces, etc.
        api_key: DashScope API key.
        model: Text model for structuring.
        base_url: API base URL.

    Returns:
        dict with ebucore_xml, iptc_video_metadata, topic_codes, sentiment, etc.
    """
    if not api_key:
        logger.warning("No API key for metadata structuring")
        return _empty_result("No API key configured")

    taxonomy = _load_iptc_taxonomy()

    # Prepare a compact version of analysis results for the prompt
    compact_analysis = _compact_analysis(analysis_results)

    prompt = STRUCTURING_PROMPT.format(
        analysis_json=json.dumps(compact_analysis, ensure_ascii=False, indent=2),
        taxonomy_json=json.dumps(taxonomy, ensure_ascii=False, indent=2),
        duration=analysis_results.get("ingestion", {}).get("duration", 0),
    )

    endpoint = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(endpoint, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            return _parse_metadata_json(content)

        except httpx.HTTPStatusError as e:
            logger.error(
                "Metadata structuring API error (attempt %d/3): %s – %s",
                attempt + 1, e.response.status_code, e.response.text[:500],
            )
            if attempt == 2:
                return _empty_result(f"API error: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(
                "Metadata structuring request error (attempt %d/3): %s",
                attempt + 1, e,
            )
            if attempt == 2:
                return _empty_result(f"Request error: {e}")
        except Exception as e:
            logger.error(
                "Metadata structuring unexpected error (attempt %d/3): %s",
                attempt + 1, e,
            )
            if attempt == 2:
                return _empty_result(f"Unexpected error: {e}")

        await asyncio.sleep(2 ** attempt)

    return _empty_result("All retry attempts exhausted")


def _compact_analysis(results: dict) -> dict:
    """Create a compact version of analysis results for the prompt (avoid token overflow)."""
    compact = {}

    # Ingestion info
    ing = results.get("ingestion", {})
    compact["video_info"] = {
        "duration": ing.get("duration", 0),
        "resolution": ing.get("resolution", "unknown"),
        "fps": ing.get("fps", 0),
        "codec": ing.get("codec", "unknown"),
    }

    # Visual analysis (truncate if too many items)
    va = results.get("visual_analysis", {})
    compact["scenes"] = va.get("scenes", [])[:20]
    compact["objects"] = va.get("objects", [])[:30]
    compact["landmarks"] = va.get("landmarks", [])[:10]
    compact["text_ocr"] = va.get("text_ocr", [])[:15]
    compact["sensitive_content"] = va.get("sensitive_content", [])
    compact["era_estimate"] = va.get("era_estimate", {})
    compact["summary_en"] = va.get("overall_summary_en", "")
    compact["summary_ar"] = va.get("overall_summary_ar", "")

    # Transcript
    tr = results.get("transcript", {})
    compact["transcript_summary"] = tr.get("full_text", "")[:2000]
    compact["speaker_count"] = tr.get("speaker_count", 0)

    # Faces
    faces = results.get("faces", [])
    compact["identified_persons"] = [
        {
            "name_en": f.get("name_en"),
            "name_ar": f.get("name_ar"),
            "role": f.get("role"),
            "timestamp": f.get("timestamp"),
        }
        for f in faces
        if f.get("identified")
    ]

    return compact


def _parse_metadata_json(content: str) -> dict:
    """Extract and parse JSON from the model response."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(content[start : end + 1])
        except json.JSONDecodeError:
            pass

    logger.warning("Could not parse metadata JSON from response")
    return _empty_result(f"Parse error: {content[:200]}")


def _empty_result(error_msg: str = "") -> dict:
    """Return an empty but well-structured metadata result."""
    return {
        "ebucore_xml": "",
        "iptc_video_metadata": {},
        "topic_codes": [],
        "topic_names_en": [],
        "topic_names_ar": [],
        "sentiment_tags": [],
        "tone": "unknown",
        "content_rating": "unknown",
        "geographic_tags": [],
        "persons_mentioned": [],
        "error": error_msg,
    }

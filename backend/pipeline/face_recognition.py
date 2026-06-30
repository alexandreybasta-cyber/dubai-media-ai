"""
Stage 4: Face Recognition
Matches detected faces from visual analysis against a reference database
using Qwen text model for description-based matching.
"""

import asyncio
import json
import logging
import os
from typing import List, Optional

import httpx

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
REFERENCE_FACES_PATH = os.path.join(DATA_DIR, "reference_faces.json")


def _load_reference_faces() -> list:
    """Load reference face database from JSON file."""
    try:
        with open(REFERENCE_FACES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Reference faces file not found: %s", REFERENCE_FACES_PATH)
        return []
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in reference faces file: %s", e)
        return []


MATCH_PROMPT_TEMPLATE = """You are an expert at identifying people from physical descriptions.

Below is a description of a person detected in a video frame:
DETECTED FACE: {detected_description}
Additional context: Age estimate: {age_estimate}, Gender: {gender}, Timestamp: {timestamp}

Below is a list of reference persons (UAE public figures). Compare the detected face description against each reference and determine if there is a match.

REFERENCE DATABASE:
{reference_list}

If you find a match, respond with ONLY valid JSON:
{{"match": true, "reference_id": "ID", "confidence": 0.85, "reasoning": "brief explanation"}}

If no match is found, respond with:
{{"match": false, "reference_id": null, "confidence": 0, "reasoning": "no match found"}}

Only match if the description strongly suggests a specific person. Be conservative — do not guess."""


async def identify_faces(
    faces_detected: list,
    api_key: str,
    model: str = "qwen-max",
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
) -> list:
    """
    Match detected faces against reference database using Qwen text model.

    Args:
        faces_detected: List of face dicts from visual analysis
            (each with description, age_estimate, gender, timestamp, bbox).
        api_key: DashScope API key.
        model: Text model for matching.
        base_url: API base URL.

    Returns:
        List of enriched face dicts with identification info.
    """
    if not faces_detected:
        return []

    if not api_key:
        logger.warning("No API key for face recognition, returning unidentified faces")
        return [
            {**face, "identified": False, "name_en": None, "name_ar": None, "role": None, "confidence": 0}
            for face in faces_detected
        ]

    reference_faces = _load_reference_faces()
    if not reference_faces:
        logger.warning("No reference faces loaded, skipping identification")
        return [
            {**face, "identified": False, "name_en": None, "name_ar": None, "role": None, "confidence": 0}
            for face in faces_detected
        ]

    # Build reference list string
    ref_lines = []
    for ref in reference_faces:
        ref_lines.append(
            f"ID: {ref['id']} | Name: {ref['name_en']} ({ref['name_ar']}) | "
            f"Role: {ref['role']} | Description: {ref['description']}"
        )
    reference_list = "\n".join(ref_lines)

    enriched = []
    for face in faces_detected:
        result = await _match_single_face(
            face, reference_list, reference_faces, api_key, model, base_url
        )
        enriched.append(result)

    return enriched


async def _match_single_face(
    face: dict,
    reference_list: str,
    reference_faces: list,
    api_key: str,
    model: str,
    base_url: str,
) -> dict:
    """Attempt to match a single detected face against the reference database."""
    prompt = MATCH_PROMPT_TEMPLATE.format(
        detected_description=face.get("description", "No description"),
        age_estimate=face.get("age_estimate", "unknown"),
        gender=face.get("gender", "unknown"),
        timestamp=face.get("timestamp", "unknown"),
        reference_list=reference_list,
    )

    endpoint = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
    }

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(endpoint, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            match_result = _parse_match_response(content)

            if match_result.get("match"):
                ref_id = match_result["reference_id"]
                ref = next((r for r in reference_faces if r["id"] == ref_id), None)
                if ref:
                    return {
                        **face,
                        "identified": True,
                        "name_en": ref["name_en"],
                        "name_ar": ref["name_ar"],
                        "role": ref["role"],
                        "reference_id": ref_id,
                        "confidence": match_result.get("confidence", 0),
                        "reasoning": match_result.get("reasoning", ""),
                    }

            return {
                **face,
                "identified": False,
                "name_en": None,
                "name_ar": None,
                "role": None,
                "confidence": 0,
            }

        except httpx.HTTPStatusError as e:
            logger.error(
                "Face match API error (attempt %d/3): %s", attempt + 1, e.response.status_code
            )
        except Exception as e:
            logger.error(
                "Face match error (attempt %d/3): %s", attempt + 1, e
            )

        await asyncio.sleep(2 ** attempt)

    return {
        **face,
        "identified": False,
        "name_en": None,
        "name_ar": None,
        "role": None,
        "confidence": 0,
        "error": "Failed to match after retries",
    }


def _parse_match_response(content: str) -> dict:
    """Parse the match result JSON from model response."""
    import re

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    json_match = re.search(r"\{.*\}", content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    return {"match": False, "reference_id": None, "confidence": 0, "reasoning": "parse error"}

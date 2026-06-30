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


def _timestamp_to_seconds(ts: str) -> float:
    """Convert MM:SS timestamp to seconds."""
    try:
        parts = ts.split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
    except (ValueError, AttributeError):
        pass
    return 0.0


def _deduplicate_faces(enriched: list, video_duration: float) -> list:
    """
    Group faces by identity, compute merged appearance intervals,
    and return one entry per unique person.
    """
    if not enriched:
        return []

    # Calculate frame interval (12 keyframes extracted)
    interval = video_duration / 12 if video_duration > 0 else 0

    # Group faces by identity key
    groups: dict = {}
    for face in enriched:
        if face.get("identified"):
            key = face.get("name_en") or "unknown"
        else:
            key = f"_unidentified_{face.get('description', id(face))}"

        if key not in groups:
            groups[key] = []
        groups[key].append(face)

    # Build deduplicated output
    output = []
    for key, faces in groups.items():
        # Use first face as the representative entry
        rep = faces[0].copy()

        # Compute appearances from timestamps
        ranges = []
        for f in faces:
            ts = f.get("timestamp", "0:00")
            center = _timestamp_to_seconds(ts)
            half = interval / 2
            start = max(0, center - half)
            end = min(video_duration, center + half) if video_duration > 0 else center + half
            ranges.append((start, end))

        # Sort and merge overlapping/adjacent ranges
        ranges.sort()
        merged = []
        for start, end in ranges:
            if merged and start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))

        rep["appearances"] = [{"start": round(s, 1), "end": round(e, 1)} for s, e in merged]

        # Remove per-frame fields that don't apply to the merged entry
        for field in ["timestamp", "bbox", "frame_index", "on_screen_name", "on_screen_title"]:
            rep.pop(field, None)

        output.append(rep)

    return output


async def identify_faces(
    faces_detected: list,
    api_key: str,
    text_ocr: list = None,
    video_duration: float = 0,
    model: str = "qwen-max",
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
) -> list:
    """
    Match detected faces against reference database using Qwen text model.

    Args:
        faces_detected: List of face dicts from visual analysis
            (each with description, age_estimate, gender, timestamp, bbox).
        api_key: DashScope API key.
        text_ocr: List of OCR text detections from visual analysis.
        video_duration: Total video duration in seconds.
        model: Text model for matching.
        base_url: API base URL.

    Returns:
        List of enriched face dicts with identification info.
    """
    if not faces_detected:
        return []

    if not api_key:
        logger.warning("No API key for face recognition, returning unidentified faces")
        enriched = [
            {**face, "identified": False, "name_en": None, "name_ar": None, "role": None, "confidence": 0}
            for face in faces_detected
        ]
        return _deduplicate_faces(enriched, video_duration)

    reference_faces = _load_reference_faces()
    if not reference_faces:
        logger.warning("No reference faces loaded, skipping identification")
        enriched = [
            {**face, "identified": False, "name_en": None, "name_ar": None, "role": None, "confidence": 0}
            for face in faces_detected
        ]
        # Apply OCR fallback even without reference DB
        enriched = _apply_ocr_fallback(enriched, faces_detected)
        return _deduplicate_faces(enriched, video_duration)

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

    # Apply OCR name fallback for unidentified faces
    enriched = _apply_ocr_fallback(enriched, faces_detected)

    return _deduplicate_faces(enriched, video_duration)


def _apply_ocr_fallback(enriched: list, faces_detected: list) -> list:
    """For faces that remain unidentified, try OCR on_screen_name fallback."""
    result = []
    for i, face_result in enumerate(enriched):
        if not face_result.get("identified"):
            original_face = faces_detected[i] if i < len(faces_detected) else {}
            on_screen_name = original_face.get("on_screen_name") or face_result.get("on_screen_name")
            on_screen_title = original_face.get("on_screen_title") or face_result.get("on_screen_title")
            if on_screen_name:
                face_result = {
                    **face_result,
                    "identified": True,
                    "name_en": on_screen_name,
                    "name_ar": None,
                    "role": on_screen_title,
                    "confidence": 0.9,
                    "source": "ocr",
                }
        result.append(face_result)
    return result


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
                        "source": "reference_db",
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

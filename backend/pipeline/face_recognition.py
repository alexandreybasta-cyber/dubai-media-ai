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

BATCH_MATCH_PROMPT_TEMPLATE = """You are an expert at identifying people in news/archive footage from physical descriptions, on-screen text, and spoken context.

Below are persons detected in frames of ONE video. Each has a numeric index:
DETECTED FACES:
{faces_list}

On-screen text (OCR) captured in the same video — lower-thirds and captions often name the person shown around the same timestamp:
{ocr_context}

Spoken transcript of the video — narrators and interviewees often introduce people by name and title ("...says Jane Smith, CEO of Acme"):
{transcript_context}

Reference database of known persons:
{reference_list}

For EACH detected face, in order, determine:
1. "duplicate_of": if this face is clearly the SAME person as an earlier face in the list (e.g. described as "same woman as above", or same description at a different timestamp), give that earlier face_index; otherwise null.
2. "match"/"reference_id": whether it matches a person in the reference database (conservative — only on strong evidence).
3. "inferred_name"/"inferred_title": if the reference DB has no match but the person can still be named. "inferred_from" must state the evidence honestly:
   - "on-screen": the name literally appears in the OCR text or the face's on-screen label. Copy it EXACTLY as written.
   - "transcript": the name is spoken in the transcript near this person's timestamp. Use EXACTLY the name parts stated — do not complete a surname into a full name from outside knowledge.
   - "knowledge": the name appears NOWHERE in the provided context, but you are highly confident from general knowledge (well-known public figure whose role/setting matches, e.g. a named company's CEO being interviewed). Use sparingly.

Respond with ONLY a valid JSON array, one entry per detected face, same order:
[
  {{"face_index": 0, "duplicate_of": null, "match": false, "reference_id": null, "confidence": 0.9, "inferred_name": "Jane Smith", "inferred_title": "CEO, Acme Corp", "inferred_from": "on-screen", "reasoning": "lower-third 'JANE SMITH — CEO, ACME' in OCR at 01:07"}},
  {{"face_index": 1, "duplicate_of": null, "match": true, "reference_id": "3", "confidence": 0.85, "inferred_name": null, "inferred_title": null, "inferred_from": null, "reasoning": "matches reference description"}},
  {{"face_index": 2, "duplicate_of": 1, "match": false, "reference_id": null, "confidence": 0, "inferred_name": null, "inferred_title": null, "inferred_from": null, "reasoning": "same person as face 1"}}
]

Never claim "on-screen" or "transcript" unless the name text is actually present in the context above — mislabeling the evidence is worse than returning no name. Duplicates of an identified face inherit its identity automatically — just set duplicate_of."""


def _timestamp_to_seconds(ts: str) -> float:
    """Convert MM:SS timestamp to seconds."""
    try:
        parts = ts.split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
    except (ValueError, AttributeError):
        pass
    return 0.0


def _appearance_range(
    ts_seconds: float,
    video_duration: float,
    interval: float,
    scene_segments: Optional[list],
) -> tuple:
    """
    Appearance window for one detection. Prefer the real shot containing the
    timestamp (sub-shot when available, else the scene); fall back to a
    window around it.
    """
    if scene_segments:
        for seg in scene_segments:
            if seg.get("start", 0) <= ts_seconds < seg.get("end", 0):
                for shot in seg.get("shots", []):
                    if shot.get("start", 0) <= ts_seconds < shot.get("end", 0):
                        return (shot["start"], shot["end"])
                return (seg["start"], seg["end"])
    half = interval / 2
    start = max(0, ts_seconds - half)
    end = min(video_duration, ts_seconds + half) if video_duration > 0 else ts_seconds + half
    return (start, end)


def _deduplicate_faces(
    enriched: list,
    video_duration: float,
    scene_segments: Optional[list] = None,
) -> list:
    """
    Group faces by identity, compute merged appearance intervals,
    and return one entry per unique person.
    """
    if not enriched:
        return []

    # Fallback window when no scene boundaries are available
    distinct_frames = len({f.get("timestamp", "0:00") for f in enriched}) or 1
    interval = video_duration / distinct_frames if video_duration > 0 else 0

    # Group faces by identity key. Unidentified faces flagged as duplicates
    # of each other (by the batch matcher) share a _dup_root and merge too.
    groups: dict = {}
    for face in enriched:
        if face.get("identified"):
            key = face.get("name_en") or "unknown"
        elif face.get("_dup_root") is not None:
            key = f"_unidentified_group_{face['_dup_root']}"
        else:
            key = f"_unidentified_{face.get('description', id(face))}"

        if key not in groups:
            groups[key] = []
        groups[key].append(face)

    # Build deduplicated output
    output = []
    for key, faces in groups.items():
        # Prefer an identified detection as the representative entry
        rep = next((f for f in faces if f.get("identified")), faces[0]).copy()

        # Compute appearances (real shot boundaries when available)
        ranges = []
        for f in faces:
            ts = _timestamp_to_seconds(f.get("timestamp", "0:00"))
            ranges.append(_appearance_range(ts, video_duration, interval, scene_segments))

        # Sort and merge overlapping/adjacent ranges
        ranges.sort()
        merged = []
        for start, end in ranges:
            if merged and start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))

        rep["appearances"] = [{"start": round(s, 1), "end": round(e, 1)} for s, e in merged]

        # Remove per-frame/internal fields that don't apply to the merged entry
        for field in ["timestamp", "bbox", "frame_index", "on_screen_name", "on_screen_title", "_dup_root"]:
            rep.pop(field, None)

        output.append(rep)

    output.sort(key=lambda f: f["appearances"][0]["start"] if f.get("appearances") else 0)
    return output


async def identify_faces(
    faces_detected: list,
    api_key: str,
    text_ocr: list = None,
    transcript_segments: list = None,
    scene_segments: list = None,
    video_duration: float = 0,
    model: str = "qwen-max",
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
) -> list:
    """
    Identify detected faces using the reference database, on-screen text
    (lower-thirds/captions), and the spoken transcript.

    Args:
        faces_detected: List of face dicts from visual analysis
            (each with description, age_estimate, gender, timestamp, bbox).
        api_key: DashScope API key.
        text_ocr: List of OCR text detections from visual analysis.
        transcript_segments: Transcript segments (start_time/end_time/text)
            used to pick up spoken introductions ("...says X, CEO of Y").
        scene_segments: Detected scene boundaries; appearances snap to the
            containing shot instead of a crude window.
        video_duration: Total video duration in seconds.
        model: Text model for matching.
        base_url: API base URL.

    Returns:
        List of deduplicated person dicts with identification info.
    """
    if not faces_detected:
        return []

    if not api_key:
        logger.warning("No API key for face recognition, returning unidentified faces")
        enriched = [
            {**face, "identified": False, "name_en": None, "name_ar": None, "role": None, "confidence": 0}
            for face in faces_detected
        ]
        enriched = _apply_ocr_fallback(enriched, faces_detected)
        return _deduplicate_faces(enriched, video_duration, scene_segments)

    # Reference DB may be empty — the batch matcher can still name people
    # from OCR text and the transcript.
    reference_faces = _load_reference_faces()
    ref_lines = []
    for ref in reference_faces:
        ref_lines.append(
            f"ID: {ref['id']} | Name: {ref['name_en']} ({ref['name_ar']}) | "
            f"Role: {ref['role']} | Description: {ref['description']}"
        )
    reference_list = "\n".join(ref_lines) if ref_lines else "(empty)"

    # Match all faces in a single batched call (with OCR + transcript
    # context); fall back to per-face matching if the batch can't be parsed.
    enriched = await _match_faces_batch(
        faces_detected, reference_list, reference_faces, text_ocr or [],
        transcript_segments or [], api_key, model, base_url,
    )
    if enriched is None:
        logger.warning("Batch face matching failed, falling back to per-face matching")
        if reference_faces:
            enriched = []
            for face in faces_detected:
                result = await _match_single_face(
                    face, reference_list, reference_faces, api_key, model, base_url
                )
                enriched.append(result)
        else:
            enriched = [
                {**face, "identified": False, "name_en": None, "name_ar": None, "role": None, "confidence": 0}
                for face in faces_detected
            ]

    # Apply OCR name fallback for unidentified faces
    enriched = _apply_ocr_fallback(enriched, faces_detected)

    return _deduplicate_faces(enriched, video_duration, scene_segments)


def _format_transcript_context(transcript_segments: list, max_segments: int = 60) -> str:
    """Compact transcript listing with timestamps for the matching prompt."""
    lines = []
    for seg in transcript_segments[:max_segments]:
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        start = seg.get("start_time", seg.get("start", 0))
        try:
            start_s = float(start)
            ts = f"{int(start_s) // 60:02d}:{int(start_s) % 60:02d}"
        except (TypeError, ValueError):
            ts = str(start)
        lines.append(f"- [{ts}] {text}")
    return "\n".join(lines) if lines else "(no transcript available)"


async def _match_faces_batch(
    faces_detected: list,
    reference_list: str,
    reference_faces: list,
    text_ocr: list,
    transcript_segments: list,
    api_key: str,
    model: str,
    base_url: str,
) -> Optional[list]:
    """Match all detected faces in one LLM call. Returns None on failure."""
    face_lines = []
    for i, face in enumerate(faces_detected):
        parts = [
            f"[{i}] At {face.get('timestamp', 'unknown')}: {face.get('description', 'No description')}",
            f"age: {face.get('age_estimate', 'unknown')}, gender: {face.get('gender', 'unknown')}",
        ]
        if face.get("on_screen_name"):
            parts.append(f"on-screen name label: {face['on_screen_name']}")
        if face.get("on_screen_title"):
            parts.append(f"on-screen title: {face['on_screen_title']}")
        face_lines.append(" | ".join(parts))

    ocr_lines = [
        f"- At {item.get('timestamp', '?')}: {item.get('text', '')}"
        for item in text_ocr[:40]
        if item.get("text")
    ]

    prompt = BATCH_MATCH_PROMPT_TEMPLATE.format(
        faces_list="\n".join(face_lines),
        ocr_context="\n".join(ocr_lines) if ocr_lines else "(none captured)",
        transcript_context=_format_transcript_context(transcript_segments),
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
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(endpoint, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            matches = _parse_batch_response(content, len(faces_detected))
            if matches is None:
                logger.warning("Could not parse batch match response (attempt %d/3)", attempt + 1)
                continue

            # Corpora for verifying the model's claimed evidence
            ocr_corpus = " ".join(
                [item.get("text", "") for item in text_ocr]
                + [face.get("on_screen_name") or "" for face in faces_detected]
                + [face.get("on_screen_title") or "" for face in faces_detected]
            )
            transcript_corpus = " ".join(
                seg.get("text", "") for seg in transcript_segments
            )
            return _build_enriched_faces(
                faces_detected, matches, reference_faces,
                ocr_corpus_tokens=_tokenize(ocr_corpus),
                transcript_corpus_tokens=_tokenize(transcript_corpus),
            )

        except httpx.HTTPStatusError as e:
            logger.error(
                "Batch face match API error (attempt %d/3): %s",
                attempt + 1, e.response.status_code,
            )
        except Exception as e:
            logger.error("Batch face match error (attempt %d/3): %s", attempt + 1, e)

        await asyncio.sleep(2 ** attempt)

    return None


def _tokenize(text: str) -> set:
    """Lowercase word tokens (len > 2) for evidence verification."""
    import re
    return {t for t in re.split(r"\W+", text.lower()) if len(t) > 2}


def _normalize_caps(text: Optional[str]) -> Optional[str]:
    """
    Turn shouting lower-third text into readable casing:
    "CRAIG BILLINGS" → "Craig Billings", "CEO, WYNN RESORTS" → "CEO, Wynn Resorts".
    Short all-caps tokens (CEO, WSJ, UAE) are kept as acronyms.
    """
    if not text or not text.isupper():
        return text
    words = []
    for word in text.split(" "):
        core = word.strip(",.;:()")
        if len(core) <= 3:
            words.append(word)  # likely an acronym
        else:
            words.append(word.capitalize())
    return " ".join(words)


def _name_supported_by(name: str, corpus_tokens: set) -> bool:
    """True when every significant token of the name appears in the corpus."""
    name_tokens = _tokenize(name)
    return bool(name_tokens) and name_tokens.issubset(corpus_tokens)


def _build_enriched_faces(
    faces_detected: list,
    matches: dict,
    reference_faces: list,
    ocr_corpus_tokens: set = frozenset(),
    transcript_corpus_tokens: set = frozenset(),
) -> list:
    """
    Turn batch match results into enriched face dicts. Identity precedence:
    reference DB match > OCR/transcript inferred name > unidentified.
    Claimed evidence is verified against the actual context: names the model
    attributes to OCR/transcript but that aren't literally there get
    downgraded to low-confidence AI suggestions.
    Duplicate faces inherit the identity of their root face and share a
    _dup_root so deduplication merges them.
    """
    # Resolve duplicate_of chains to a root index per face
    dup_root: dict = {}

    def _resolve_root(i: int, seen: set) -> int:
        entry = matches.get(i, {})
        dup = entry.get("duplicate_of")
        if isinstance(dup, int) and 0 <= dup < len(faces_detected) and dup != i and dup not in seen:
            return _resolve_root(dup, seen | {dup})
        return i

    for i in range(len(faces_detected)):
        dup_root[i] = _resolve_root(i, {i})

    def _identity(i: int) -> dict:
        """Identity fields for face i based on its own match result."""
        match_result = matches.get(i, {})
        if match_result.get("match"):
            ref_id = str(match_result.get("reference_id", ""))
            ref = next((r for r in reference_faces if str(r["id"]) == ref_id), None)
            if ref:
                return {
                    "identified": True,
                    "name_en": ref["name_en"],
                    "name_ar": ref["name_ar"],
                    "role": ref["role"],
                    "reference_id": ref["id"],
                    "confidence": match_result.get("confidence", 0),
                    "reasoning": match_result.get("reasoning", ""),
                    "source": "reference_db",
                }
        inferred = (match_result.get("inferred_name") or "").strip() if isinstance(match_result.get("inferred_name"), str) else ""
        if inferred:
            inferred_from = match_result.get("inferred_from") or "on-screen"
            source_map = {
                "on-screen": ("ocr", 0.9),
                "transcript": ("transcript", 0.8),
                "knowledge": ("ai_suggestion", 0.6),
            }
            source, default_conf = source_map.get(inferred_from, ("ocr", 0.85))

            # Verify the claimed evidence: the name must literally appear in
            # the cited context, otherwise it's a knowledge-based suggestion
            # no matter what the model claims.
            if source == "ocr" and not _name_supported_by(inferred, ocr_corpus_tokens):
                source = "ai_suggestion"
            elif source == "transcript" and not _name_supported_by(inferred, transcript_corpus_tokens):
                source = "ai_suggestion"

            model_conf = match_result.get("confidence")
            confidence = model_conf if isinstance(model_conf, (int, float)) and model_conf > 0 else default_conf
            # Unverified/knowledge-based guesses are capped so they always
            # read as suggestions needing review
            if source == "ai_suggestion":
                confidence = min(confidence, 0.6)
            return {
                "identified": True,
                "name_en": _normalize_caps(inferred),
                "name_ar": None,
                "role": _normalize_caps(match_result.get("inferred_title") or None),
                "confidence": confidence,
                "reasoning": match_result.get("reasoning", ""),
                "source": source,
            }
        return {
            "identified": False,
            "name_en": None,
            "name_ar": None,
            "role": None,
            "confidence": 0,
        }

    enriched = []
    for i, face in enumerate(faces_detected):
        root = dup_root[i]
        identity = _identity(i)
        if not identity["identified"] and root != i:
            # Inherit the root face's identity (duplicates of a named person)
            identity = _identity(root)
        enriched.append({**face, **identity, "_dup_root": root})
    return enriched


def _parse_batch_response(content: str, expected_count: int) -> Optional[dict]:
    """Parse the batch match JSON array. Returns {face_index: entry} or None."""
    import re

    parsed = None
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        array_match = re.search(r"\[.*\]", content, re.DOTALL)
        if array_match:
            try:
                parsed = json.loads(array_match.group())
            except json.JSONDecodeError:
                pass

    if not isinstance(parsed, list):
        return None

    matches = {}
    for pos, entry in enumerate(parsed):
        if not isinstance(entry, dict):
            continue
        idx = entry.get("face_index")
        if not isinstance(idx, int) or not (0 <= idx < expected_count):
            idx = pos
        if 0 <= idx < expected_count:
            matches[idx] = entry
    return matches if matches else None


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
                    "name_en": _normalize_caps(on_screen_name),
                    "name_ar": None,
                    "role": _normalize_caps(on_screen_title),
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

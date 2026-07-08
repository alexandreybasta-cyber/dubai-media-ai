"""
Video processing API routes.
Handles upload, status tracking, metadata retrieval, search, and WebSocket progress.
"""

import json
import logging
import asyncio
import os
import subprocess
import sys
import uuid
from datetime import datetime
from typing import Dict, List, Optional

import aiofiles
import httpx
from fastapi import APIRouter, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel

from config import settings
from pipeline.orchestrator import PipelineOrchestrator
from pipeline.search_index import SearchIndex
from pipeline import subtitle_generation
from pipeline import dubbing

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["video"])

# Shared orchestrator and search index instances
_orchestrator = PipelineOrchestrator()

# Track active WebSocket connections per video_id for pipeline progress
_active_ws: Dict[str, list] = {}


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    type_filter: Optional[str] = None  # "scene" | "transcript" | "person"
    video_id: Optional[str] = None


class NameFaceRequest(BaseModel):
    face_index: int
    name_en: str
    name_ar: Optional[str] = None
    role: Optional[str] = None
    add_to_reference: bool = False


class TranslateSegmentInput(BaseModel):
    text: str
    start_time: float
    end_time: float


class TranslateRequest(BaseModel):
    language: str  # "ar", "fr", "ru"
    segments: List[TranslateSegmentInput]


# ── Upload ──────────────────────────────────────────────────────────

@router.post("/video/upload")
async def upload_video(
    file: UploadFile = File(...),
):
    """Upload a video file and start the processing pipeline in the background."""
    video_id = str(uuid.uuid4())

    # Save uploaded file to uploads directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_ext = os.path.splitext(file.filename or "video.mp4")[1] or ".mp4"
    saved_filename = f"{video_id}{file_ext}"
    video_path = os.path.join(settings.UPLOAD_DIR, saved_filename)

    try:
        async with aiofiles.open(video_path, "wb") as out:
            while chunk := await file.read(1024 * 1024):  # 1 MB chunks
                await out.write(chunk)
    except Exception as e:
        logger.error("Failed to save uploaded file: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    # Create initial status
    output_dir = os.path.join(settings.UPLOAD_DIR, video_id)
    os.makedirs(output_dir, exist_ok=True)
    initial_status = {
        "video_id": video_id,
        "status": "queued",
        "progress": 0,
        "stages": {
            "ingestion": "pending",
            "visual_analysis": "pending",
            "audio_analysis": "pending",
            "face_recognition": "pending",
            "metadata_structuring": "pending",
            "search_index": "pending",
        },
        "filename": file.filename,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    status_path = os.path.join(output_dir, "status.json")
    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(initial_status, f, ensure_ascii=False, indent=2)

    # Launch pipeline as a completely separate subprocess
    # This NEVER blocks the server regardless of pipeline duration or resource usage
    pipeline_log_path = os.path.join(output_dir, "pipeline.log")
    subprocess.Popen(
        [sys.executable, "run_pipeline.py", video_id, video_path],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        stdin=subprocess.DEVNULL,   # Prevent SIGTTIN from terminal
        stdout=open(pipeline_log_path, "w"),
        stderr=subprocess.STDOUT,
        start_new_session=True,  # Fully detach from parent process
    )
    logger.info("Launched pipeline subprocess for %s (log: %s)", video_id, pipeline_log_path)

    return {
        "video_id": video_id,
        "filename": file.filename,
        "status": "queued",
        "message": "Video uploaded successfully. Processing will begin shortly.",
    }


# ── Status ──────────────────────────────────────────────────────────

@router.get("/video/{video_id}/status")
async def get_video_status(video_id: str):
    """Read the current pipeline status for a video."""
    status_path = os.path.join(settings.UPLOAD_DIR, video_id, "status.json")

    if not os.path.exists(status_path):
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    try:
        # Use synchronous read for this tiny file to avoid thread pool contention
        with open(status_path, "r", encoding="utf-8") as f:
            content = f.read()
        return json.loads(content)
    except Exception as e:
        logger.error("Failed to read status for %s: %s", video_id, e)
        raise HTTPException(status_code=500, detail="Failed to read status")


# ── Metadata ────────────────────────────────────────────────────────

@router.get("/video/{video_id}/metadata")
async def get_video_metadata(video_id: str):
    """Retrieve the structured metadata for a processed video."""
    output_dir = os.path.join(settings.UPLOAD_DIR, video_id)

    if not os.path.isdir(output_dir):
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    result = {}

    # Load each result file if it exists
    for fname, key in [
        ("ingestion.json", "ingestion"),
        ("visual_analysis.json", "visual_analysis"),
        ("metadata.json", "metadata"),
        ("faces.json", "faces"),
    ]:
        fpath = os.path.join(output_dir, fname)
        if os.path.exists(fpath):
            try:
                async with aiofiles.open(fpath, "r", encoding="utf-8") as f:
                    content = await f.read()
                result[key] = json.loads(content)
            except Exception as e:
                logger.warning("Could not load %s: %s", fpath, e)
                result[key] = {"error": str(e)}

    if not result:
        raise HTTPException(status_code=404, detail="No metadata available yet")

    result["video_id"] = video_id
    video_file = _find_video_file(video_id)
    if video_file:
        result["video_url"] = f"/uploads/{video_file}"
    return result


def _find_video_file(video_id: str) -> Optional[str]:
    """Locate the uploaded media file for a video id (saved as <id>.<ext>)."""
    try:
        for fname in os.listdir(settings.UPLOAD_DIR):
            if fname.startswith(video_id + ".") and os.path.isfile(
                os.path.join(settings.UPLOAD_DIR, fname)
            ):
                return fname
    except OSError:
        pass
    return None


# ── Transcript ──────────────────────────────────────────────────────

@router.get("/video/{video_id}/transcript")
async def get_video_transcript(video_id: str):
    """Retrieve the transcript for a processed video."""
    transcript_path = os.path.join(settings.UPLOAD_DIR, video_id, "transcript.json")

    if not os.path.exists(transcript_path):
        raise HTTPException(status_code=404, detail=f"Transcript for {video_id} not found")

    try:
        async with aiofiles.open(transcript_path, "r", encoding="utf-8") as f:
            content = await f.read()
        data = json.loads(content)
        data["video_id"] = video_id
        return data
    except Exception as e:
        logger.error("Failed to read transcript for %s: %s", video_id, e)
        raise HTTPException(status_code=500, detail="Failed to read transcript")


# ── Transcript Translation ──────────────────────────────────────────

_LANGUAGE_NAMES = {
    "ar": "Modern Standard Arabic (العربية)",
    "fr": "French",
    "ru": "Russian",
}


@router.post("/video/{video_id}/translate-transcript")
async def translate_transcript(video_id: str, request: TranslateRequest):
    """
    Translate transcript segments into a target language (ar/fr/ru) using
    the DashScope Qwen text model. All segments are translated in a single
    API call by joining them with numbered markers, then splitting back.
    """
    lang_name = _LANGUAGE_NAMES.get(request.language)
    if not lang_name:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language '{request.language}'. Use 'ar', 'fr', or 'ru'.",
        )

    if not request.segments:
        return {"translations": [], "language": request.language}

    api_key = settings.DASHSCOPE_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="DASHSCOPE_API_KEY is not configured on the server.",
        )

    # Join all segment texts with numbered markers for a single API call.
    joined = "\n".join(
        f"[SEG{i + 1}] {seg.text}" for i, seg in enumerate(request.segments)
    )

    # Qwen may default to Chinese output; be explicit for Arabic.
    extra = ""
    if request.language == "ar":
        extra = (
            " The target language is Modern Standard Arabic written in Arabic script (العربية). "
            "Do NOT translate to Chinese or any other language — every translated segment "
            "MUST be written in Arabic."
        )

    system_prompt = (
        f"You are a professional translator. Translate the user's text into {lang_name}.{extra} "
        f"The text is split into segments, each prefixed with a marker like [SEG1], [SEG2]. "
        f"Translate ONLY the text after each marker into {lang_name}, and keep every marker "
        f"exactly as-is on the same line before its translation. Preserve the number and order "
        f"of segments. Return ONLY the translated segments with their markers, nothing else."
    )

    payload = {
        "model": settings.MODEL_TEXT,
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
    api_url = f"{settings.DASHSCOPE_BASE_URL}/chat/completions"

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
            logger.warning("Translation attempt %d failed: %s", attempt + 1, last_error)
        except Exception as e:
            last_error = str(e)
            logger.warning("Translation attempt %d error: %s", attempt + 1, last_error)
        await asyncio.sleep(2 ** attempt)

    if content is None:
        raise HTTPException(status_code=502, detail=f"Translation failed: {last_error}")

    # Parse the translated text back into segments using the markers.
    parsed = _parse_marked_segments(content, len(request.segments))

    translations = []
    for i, seg in enumerate(request.segments):
        text = parsed.get(i)
        translations.append({
            "start_time": seg.start_time,
            "end_time": seg.end_time,
            "text": (text if text else seg.text),
        })

    return {"translations": translations, "language": request.language}


def _parse_marked_segments(content: str, count: int) -> Dict[int, str]:
    """
    Split model output back into per-segment translations using [SEGn] markers.
    Returns a dict mapping zero-based segment index -> translated text.
    """
    import re

    result: Dict[int, str] = {}
    # Find each marker and capture text until the next marker or end of string.
    matches = list(re.finditer(r"\[SEG(\d+)\]", content))
    for idx, m in enumerate(matches):
        seg_num = int(m.group(1))
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
        text = content[start:end].strip()
        if 1 <= seg_num <= count:
            result[seg_num - 1] = text
    return result


# ── Subtitles ───────────────────────────────────────────────────────

_SUBTITLE_MIME = {
    "vtt": "text/vtt",
    "srt": "application/x-subrip",
}


@router.get("/video/{video_id}/subtitles")
async def get_subtitles(video_id: str, language: str = "en"):
    """Return WebVTT subtitle content for the video in the specified language.

    Supported languages: en, ar, fr, ru. If the VTT file doesn't exist yet it is
    generated on-the-fly from transcript.json and cached for future requests.
    """
    language = (language or "en").lower()
    if language not in subtitle_generation.SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language '{language}'. Use one of: en, ar, fr, ru.",
        )

    video_dir = os.path.join(settings.UPLOAD_DIR, video_id)
    if not os.path.isdir(video_dir):
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    try:
        content = await subtitle_generation.ensure_vtt(video_id, language)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Transcript for {video_id} not found",
        )
    except Exception as e:
        logger.error("Failed to build subtitles for %s (%s): %s", video_id, language, e)
        raise HTTPException(status_code=502, detail=f"Failed to generate subtitles: {e}")

    return Response(content=content, media_type="text/vtt")


@router.get("/video/{video_id}/subtitles/download")
async def download_subtitles(video_id: str, language: str = "en", format: str = "srt"):
    """Download subtitles as an SRT or VTT file (returned as an attachment)."""
    language = (language or "en").lower()
    fmt = (format or "srt").lower()

    if language not in subtitle_generation.SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language '{language}'. Use one of: en, ar, fr, ru.",
        )
    if fmt not in _SUBTITLE_MIME:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{fmt}'. Use 'srt' or 'vtt'.",
        )

    video_dir = os.path.join(settings.UPLOAD_DIR, video_id)
    if not os.path.isdir(video_dir):
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    try:
        content = await subtitle_generation.ensure_subtitle_content(
            video_id, language, fmt=fmt
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Transcript for {video_id} not found",
        )
    except Exception as e:
        logger.error("Failed to build subtitle download for %s (%s): %s", video_id, language, e)
        raise HTTPException(status_code=502, detail=f"Failed to generate subtitles: {e}")

    filename = f"{video_id}_{language}.{fmt}"
    return Response(
        content=content,
        media_type=_SUBTITLE_MIME[fmt],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Dubbing ─────────────────────────────────────────────────────────

# Track in-flight dubbing tasks to avoid launching duplicates AND to hold a
# strong reference to each asyncio.Task so it is not garbage-collected while
# still running: {(video_id, lang): asyncio.Task}
_active_dubbing: Dict = {}


def _supported_dub_languages() -> List[str]:
    """Parse the comma-separated supported dubbing languages from settings."""
    return [
        c.strip().lower()
        for c in settings.DUBBING_SUPPORTED_LANGUAGES.split(",")
        if c.strip()
    ]


async def _run_dubbing_task(video_id: str, video_path: str, output_dir: str, lang: str):
    """Background task wrapper that runs the dubbing pipeline and clears the lock."""
    try:
        await dubbing.dub_video(video_id, video_path, output_dir, lang)
    except Exception as e:
        logger.error("Dubbing task failed for %s (%s): %s", video_id, lang, e)
    finally:
        _active_dubbing.pop((video_id, lang), None)


@router.post("/video/{video_id}/dub")
async def request_dubbing(video_id: str, request: Request):
    """Request dubbing for a video. Body: {"target_language": "ar"}"""
    output_dir = os.path.join(settings.UPLOAD_DIR, video_id)
    if not os.path.isdir(output_dir):
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    try:
        body = await request.json()
    except Exception:
        body = {}
    lang = str(body.get("target_language") or settings.DUBBING_DEFAULT_LANGUAGE).lower()

    if lang not in _supported_dub_languages():
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language '{lang}'. Supported: {settings.DUBBING_SUPPORTED_LANGUAGES}",
        )

    # A transcript is required to dub.
    if not os.path.exists(os.path.join(output_dir, "transcript.json")):
        raise HTTPException(
            status_code=400,
            detail=f"Transcript for {video_id} not available yet",
        )

    # Return cached result if the dubbed video already exists.
    dubbed_video = os.path.join(output_dir, "dubbed", f"video_{lang}.mp4")
    if os.path.exists(dubbed_video):
        return {
            "status": "completed",
            "video_id": video_id,
            "target_language": lang,
            "cached": True,
            "video_path": f"/uploads/{video_id}/dubbed/video_{lang}.mp4",
        }

    # Avoid launching a duplicate task for the same video/language.
    if (video_id, lang) in _active_dubbing:
        return {"status": "processing", "video_id": video_id, "target_language": lang}

    video_file = _find_video_file(video_id)
    if not video_file:
        raise HTTPException(status_code=404, detail=f"Source video file for {video_id} not found")
    video_path = os.path.join(settings.UPLOAD_DIR, video_file)

    # Store a strong reference to the task to prevent it being garbage-collected
    # before it finishes (asyncio only keeps a weak reference otherwise).
    task = asyncio.create_task(_run_dubbing_task(video_id, video_path, output_dir, lang))
    _active_dubbing[(video_id, lang)] = task

    return {"status": "processing", "video_id": video_id, "target_language": lang}


@router.get("/video/{video_id}/dub/status")
async def get_dubbing_status(video_id: str, language: str = ""):
    """Get dubbing status for a video (optionally for a specific language)."""
    dubbed_dir = os.path.join(settings.UPLOAD_DIR, video_id, "dubbed")
    if not os.path.isdir(dubbed_dir):
        return {"video_id": video_id, "status": "not_started", "languages": []}

    lang = (language or settings.DUBBING_DEFAULT_LANGUAGE).lower()

    # Prefer the detailed dubbing_{lang}.json, fall back to status_{lang}.json.
    for fname in (f"dubbing_{lang}.json", f"status_{lang}.json"):
        data = _read_json(os.path.join(dubbed_dir, fname))
        if data is not None:
            data["video_id"] = video_id
            if (video_id, lang) in _active_dubbing:
                data["status"] = "processing"
            return data

    status = "processing" if (video_id, lang) in _active_dubbing else "not_started"
    return {"video_id": video_id, "target_language": lang, "status": status}


@router.get("/video/{video_id}/dub/languages")
async def get_available_languages(video_id: str):
    """Get list of available dubbed languages for a video."""
    dubbed_dir = os.path.join(settings.UPLOAD_DIR, video_id, "dubbed")
    available = []
    if os.path.isdir(dubbed_dir):
        for fname in os.listdir(dubbed_dir):
            if fname.startswith("video_") and fname.endswith(".mp4"):
                available.append(fname[len("video_"):-len(".mp4")])
    return {
        "video_id": video_id,
        "dubbed_languages": sorted(available),
        "supported_languages": _supported_dub_languages(),
    }


@router.get("/video/{video_id}/dubbed/{language}")
async def get_dubbed_video(video_id: str, language: str):
    """Stream the dubbed video file."""
    lang = (language or "").lower()
    dubbed_video = os.path.join(
        settings.UPLOAD_DIR, video_id, "dubbed", f"video_{lang}.mp4"
    )
    if not os.path.isfile(dubbed_video):
        raise HTTPException(
            status_code=404,
            detail=f"Dubbed video for {video_id} ({lang}) not found",
        )
    return FileResponse(
        dubbed_video,
        media_type="video/mp4",
        filename=f"{video_id}_{lang}.mp4",
    )


# ── Video Library ───────────────────────────────────────────────────

def _read_json(path: str) -> Optional[dict]:
    """Read a JSON file, returning None when missing or invalid."""
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Could not read %s: %s", path, e)
        return None


@router.get("/videos")
async def list_videos():
    """List all uploaded videos with their processing status and key metadata."""
    videos = []
    if not os.path.isdir(settings.UPLOAD_DIR):
        return {"videos": [], "total": 0}

    for entry in os.listdir(settings.UPLOAD_DIR):
        video_dir = os.path.join(settings.UPLOAD_DIR, entry)
        status = _read_json(os.path.join(video_dir, "status.json"))
        if not os.path.isdir(video_dir) or not status:
            continue

        ingestion = _read_json(os.path.join(video_dir, "ingestion.json")) or {}
        metadata = _read_json(os.path.join(video_dir, "metadata.json")) or {}
        visual = _read_json(os.path.join(video_dir, "visual_analysis.json")) or {}
        faces = _read_json(os.path.join(video_dir, "faces.json")) or []

        headline = (
            (metadata.get("iptc_video_metadata") or {})
            .get("videoContent", {})
            .get("headline", "")
        )
        thumbnail = ""
        if os.path.exists(os.path.join(video_dir, "thumbnail.jpg")):
            thumbnail = f"/uploads/{entry}/thumbnail.jpg"

        persons = []
        if isinstance(faces, list):
            persons = [
                f.get("name_en") for f in faces
                if isinstance(f, dict) and f.get("identified") and f.get("name_en")
            ]

        video_file = _find_video_file(entry)
        videos.append({
            "video_id": entry,
            "video_url": f"/uploads/{video_file}" if video_file else "",
            "filename": status.get("filename", ""),
            "title": headline or status.get("filename", "") or entry,
            "status": status.get("status", "unknown"),
            "progress": status.get("progress", 0),
            "created_at": status.get("created_at", ""),
            "duration": ingestion.get("duration", 0),
            "thumbnail": thumbnail,
            "scene_count": len(visual.get("scenes", []) if isinstance(visual, dict) else []),
            "persons": persons,
            "summary": visual.get("overall_summary_en", "") if isinstance(visual, dict) else "",
        })

    videos.sort(key=lambda v: v.get("created_at", ""), reverse=True)
    return {"videos": videos, "total": len(videos)}


# ── Person Naming ───────────────────────────────────────────────────

@router.post("/video/{video_id}/faces/name")
async def name_face(video_id: str, request: NameFaceRequest):
    """
    Assign or correct the name of a detected person, optionally saving them
    to the reference database so they are recognized in future videos.
    """
    output_dir = os.path.join(settings.UPLOAD_DIR, video_id)
    faces_path = os.path.join(output_dir, "faces.json")
    faces = _read_json(faces_path)
    if faces is None or not isinstance(faces, list):
        raise HTTPException(status_code=404, detail=f"No faces found for video {video_id}")

    if not (0 <= request.face_index < len(faces)):
        raise HTTPException(status_code=400, detail=f"Invalid face index {request.face_index}")

    name_en = request.name_en.strip()
    if not name_en:
        raise HTTPException(status_code=400, detail="Name cannot be empty")

    face = faces[request.face_index]
    face.update({
        "identified": True,
        "name_en": name_en,
        "name_ar": (request.name_ar or "").strip() or face.get("name_ar"),
        "role": (request.role or "").strip() or face.get("role"),
        "confidence": 1.0,
        "source": "manual",
    })

    with open(faces_path, "w", encoding="utf-8") as f:
        json.dump(faces, f, ensure_ascii=False, indent=2)

    # Keep combined results.json in sync so reindexing picks up the new name
    results_path = os.path.join(output_dir, "results.json")
    results = _read_json(results_path)
    if results is not None:
        results["faces"] = faces
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    # Optionally add to the reference database for future recognition
    added_to_reference = False
    if request.add_to_reference and face.get("description"):
        ref_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "reference_faces.json",
        )
        references = _read_json(ref_path) or []
        already_known = any(
            r.get("name_en", "").lower() == name_en.lower() for r in references
        )
        if not already_known:
            next_id = max(
                (int(r["id"]) for r in references if str(r.get("id", "")).isdigit()),
                default=0,
            ) + 1
            references.append({
                "id": str(next_id),
                "name_en": name_en,
                "name_ar": face.get("name_ar") or "",
                "role": face.get("role") or "",
                "description": face["description"],
            })
            with open(ref_path, "w", encoding="utf-8") as f:
                json.dump(references, f, ensure_ascii=False, indent=2)
            added_to_reference = True

    # Make the person findable via semantic search immediately
    try:
        appearances = face.get("appearances") or []
        first_seen = appearances[0]["start"] if appearances else 0
        await _orchestrator.search_index.add_video(video_id, [{
            "description_en": f"{name_en} ({face.get('role') or 'person'}) appears in this video",
            "timestamp": first_seen,
            "type": "person",
            "title": name_en,
            "thumbnail": f"/uploads/{video_id}/thumbnail.jpg",
            "persons": [name_en],
        }])
    except Exception as e:
        logger.warning("Could not index named person for %s: %s", video_id, e)

    return {
        "status": "ok",
        "face": face,
        "added_to_reference": added_to_reference,
    }


# ── Search ──────────────────────────────────────────────────────────

@router.post("/search")
async def semantic_search(request: SearchRequest):
    """Search across all indexed videos using natural language (POST)."""
    try:
        results = await _orchestrator.search_index.search(
            query=request.query,
            top_k=request.top_k,
            type_filter=request.type_filter,
            video_id=request.video_id,
        )
        return {
            "query": request.query,
            "results": results,
            "total": len(results),
        }
    except Exception as e:
        logger.error("Search failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")


@router.get("/search")
async def semantic_search_get(
    query: str,
    top_k: int = 5,
    type_filter: Optional[str] = None,
    video_id: Optional[str] = None,
):
    """Search across all indexed videos using natural language (GET)."""
    try:
        results = await _orchestrator.search_index.search(
            query=query,
            top_k=top_k,
            type_filter=type_filter,
            video_id=video_id,
        )
        return {
            "query": query,
            "results": results,
            "total": len(results),
        }
    except Exception as e:
        logger.error("Search failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")


# ── Reindex ────────────────────────────────────────────────────────────

@router.api_route("/reindex", methods=["GET", "POST"])
async def reindex_all():
    """Rebuild the search index from all existing processed video results."""
    import pickle
    try:
        # Clear existing index
        search_index = _orchestrator.search_index
        if search_index._use_faiss:
            import faiss
            search_index.index = faiss.IndexFlatIP(1024)
        else:
            from pipeline.search_index import _NumpyFlatIP
            search_index.index = _NumpyFlatIP(1024)
        search_index.metadata = []

        # Find all processed videos with results.json
        indexed_count = 0
        for video_id in os.listdir(settings.UPLOAD_DIR):
            results_path = os.path.join(settings.UPLOAD_DIR, video_id, "results.json")
            if not os.path.isfile(results_path):
                continue
            try:
                with open(results_path, "r", encoding="utf-8") as f:
                    results = json.load(f)
                segments = _orchestrator._build_searchable_segments(results)
                if segments:
                    await search_index.add_video(video_id, segments)
                    indexed_count += 1
                    logger.info("Reindexed video %s (%d segments)", video_id, len(segments))
            except Exception as e:
                logger.warning("Failed to reindex video %s: %s", video_id, e)

        return {
            "status": "ok",
            "videos_indexed": indexed_count,
            "total_vectors": search_index.index.ntotal,
        }
    except Exception as e:
        logger.error("Reindex failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Reindex failed: {e}")


# ── WebSocket ───────────────────────────────────────────────────────

@router.websocket("/ws/pipeline/{video_id}")
async def pipeline_websocket(websocket: WebSocket, video_id: str):
    """
    WebSocket endpoint for streaming pipeline progress events.
    Clients connect here to receive real-time updates while a video is processing.
    """
    await websocket.accept()

    # Register this connection
    if video_id not in _active_ws:
        _active_ws[video_id] = []
    _active_ws[video_id].append(websocket)

    try:
        # Send current status if available
        status_path = os.path.join(settings.UPLOAD_DIR, video_id, "status.json")
        if os.path.exists(status_path):
            with open(status_path, "r", encoding="utf-8") as f:
                current_status = json.load(f)
            await websocket.send_json({
                "video_id": video_id,
                "stage": "connected",
                "message": f"Connected. Current status: {current_status.get('status', 'unknown')}",
                "progress": current_status.get("progress", 0),
                "status": current_status.get("status", "unknown"),
            })

        # Keep connection alive until client disconnects or pipeline ends
        while True:
            # Wait for messages from client (e.g. pings or close)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug("WebSocket error for %s: %s", video_id, e)
    finally:
        # Unregister
        if video_id in _active_ws:
            try:
                _active_ws[video_id].remove(websocket)
            except ValueError:
                pass
            if not _active_ws[video_id]:
                del _active_ws[video_id]

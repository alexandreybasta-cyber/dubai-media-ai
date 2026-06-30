"""
Video processing API routes.
Handles upload, status tracking, metadata retrieval, search, and WebSocket progress.
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict

import aiofiles
from fastapi import APIRouter, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel

from config import settings
from pipeline.orchestrator import PipelineOrchestrator
from pipeline.search_index import SearchIndex

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["video"])

# Shared orchestrator and search index instances
_orchestrator = PipelineOrchestrator()

# Track active WebSocket connections per video_id for pipeline progress
_active_ws: Dict[str, list] = {}


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


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

    # Launch pipeline as background asyncio task (non-blocking)
    asyncio.create_task(_run_pipeline(video_id, video_path))

    return {
        "video_id": video_id,
        "filename": file.filename,
        "status": "queued",
        "message": "Video uploaded successfully. Processing will begin shortly.",
    }


async def _run_pipeline(video_id: str, video_path: str):
    """Background task that runs the full pipeline."""
    try:
        await _orchestrator.process_video(video_id, video_path, ws_callback=None)
    except Exception as e:
        logger.error("Pipeline failed for %s: %s", video_id, e)


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
    return result


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


# ── Search ──────────────────────────────────────────────────────────

@router.post("/search")
async def semantic_search(request: SearchRequest):
    """Search across all indexed videos using natural language (POST)."""
    try:
        results = await _orchestrator.search_index.search(
            query=request.query,
            top_k=request.top_k,
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
async def semantic_search_get(query: str, top_k: int = 5):
    """Search across all indexed videos using natural language (GET)."""
    try:
        results = await _orchestrator.search_index.search(
            query=query,
            top_k=top_k,
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

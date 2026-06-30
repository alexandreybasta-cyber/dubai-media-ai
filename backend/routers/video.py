import uuid
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["video"])


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


@router.post("/video/upload")
async def upload_video(file: UploadFile = File(...)):
    video_id = str(uuid.uuid4())
    return {
        "video_id": video_id,
        "filename": file.filename,
        "status": "queued",
        "message": "Video uploaded successfully. Processing will begin shortly.",
    }


@router.get("/video/{video_id}/status")
async def get_video_status(video_id: str):
    return {
        "video_id": video_id,
        "status": "completed",
        "progress": 100,
        "stages": {
            "upload": "completed",
            "frame_extraction": "completed",
            "scene_detection": "completed",
            "asr": "completed",
            "visual_analysis": "completed",
            "metadata_generation": "completed",
            "embedding": "completed",
        },
        "created_at": datetime.utcnow().isoformat(),
    }


@router.get("/video/{video_id}/metadata")
async def get_video_metadata(video_id: str):
    return {
        "video_id": video_id,
        "title": "Sample Media Archive Video",
        "duration_seconds": 185.4,
        "resolution": "1920x1080",
        "fps": 25.0,
        "codec": "h264",
        "scenes": [
            {
                "scene_id": 1,
                "start_time": 0.0,
                "end_time": 45.2,
                "description": "Opening aerial shot of Dubai skyline at sunset",
                "objects": ["buildings", "sky", "clouds", "city"],
                "mood": "establishing",
            },
            {
                "scene_id": 2,
                "start_time": 45.2,
                "end_time": 92.8,
                "description": "Interview segment with media executive in studio",
                "objects": ["person", "desk", "microphone", "studio lights"],
                "mood": "informational",
            },
            {
                "scene_id": 3,
                "start_time": 92.8,
                "end_time": 185.4,
                "description": "B-roll footage of media production workflow",
                "objects": ["cameras", "editing suite", "monitors", "crew"],
                "mood": "dynamic",
            },
        ],
        "summary": "A media archive segment covering Dubai's media landscape, featuring aerial cinematography, executive interviews, and production behind-the-scenes footage.",
        "tags": ["dubai", "media", "production", "interview", "aerial", "skyline"],
        "language": "en",
    }


@router.get("/video/{video_id}/transcript")
async def get_video_transcript(video_id: str):
    return {
        "video_id": video_id,
        "language": "en",
        "segments": [
            {
                "start": 46.0,
                "end": 52.3,
                "text": "Welcome to Dubai Media Incorporated. Today we're exploring the future of digital archiving.",
                "speaker": "Speaker 1",
            },
            {
                "start": 53.1,
                "end": 61.8,
                "text": "Our partnership with Alibaba Cloud brings cutting-edge AI capabilities to our media workflows.",
                "speaker": "Speaker 1",
            },
            {
                "start": 62.5,
                "end": 70.0,
                "text": "From automated metadata extraction to intelligent content search, the possibilities are transformative.",
                "speaker": "Speaker 1",
            },
        ],
        "full_text": (
            "Welcome to Dubai Media Incorporated. Today we're exploring the future of digital archiving. "
            "Our partnership with Alibaba Cloud brings cutting-edge AI capabilities to our media workflows. "
            "From automated metadata extraction to intelligent content search, the possibilities are transformative."
        ),
    }


@router.post("/search")
async def semantic_search(request: SearchRequest):
    return {
        "query": request.query,
        "results": [
            {
                "video_id": "sample-001",
                "score": 0.92,
                "scene_id": 1,
                "timestamp": 12.5,
                "description": "Aerial shot of Dubai skyline matching query context",
                "thumbnail_url": None,
            },
            {
                "video_id": "sample-001",
                "score": 0.85,
                "scene_id": 3,
                "timestamp": 105.0,
                "description": "Media production workflow segment",
                "thumbnail_url": None,
            },
        ],
        "total": 2,
    }


@router.websocket("/ws/pipeline/{video_id}")
async def pipeline_websocket(websocket: WebSocket, video_id: str):
    await websocket.accept()
    try:
        stages = [
            ("upload", "Upload received"),
            ("frame_extraction", "Extracting key frames"),
            ("scene_detection", "Detecting scenes"),
            ("asr", "Transcribing audio"),
            ("visual_analysis", "Analyzing visual content"),
            ("metadata_generation", "Generating metadata"),
            ("embedding", "Creating search embeddings"),
        ]
        for i, (stage, message) in enumerate(stages):
            progress = int(((i + 1) / len(stages)) * 100)
            await websocket.send_json({
                "video_id": video_id,
                "stage": stage,
                "message": message,
                "progress": progress,
                "status": "completed",
            })
        await websocket.send_json({
            "video_id": video_id,
            "stage": "done",
            "message": "Pipeline completed successfully",
            "progress": 100,
            "status": "completed",
        })
    except WebSocketDisconnect:
        pass

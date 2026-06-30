"""
Pipeline Orchestrator
Manages the full video processing pipeline execution with stage-by-stage progress tracking.
"""

import asyncio
import json
import logging
import os
import traceback
from datetime import datetime
from typing import Callable, Optional

from config import settings
from pipeline.ingestion import ingest_video
from pipeline.visual_analysis import analyze_video_visually
from pipeline.audio_analysis import transcribe_audio
from pipeline.face_recognition import identify_faces
from pipeline.metadata_structuring import structure_metadata
from pipeline.search_index import SearchIndex

logger = logging.getLogger(__name__)

STAGE_NAMES = [
    "ingestion",
    "visual_analysis",
    "audio_analysis",
    "face_recognition",
    "metadata_structuring",
    "search_index",
]


class PipelineOrchestrator:
    """Orchestrates the full video metadata extraction pipeline."""

    def __init__(self):
        self.search_index = SearchIndex(
            api_key=settings.DASHSCOPE_API_KEY,
            model=settings.MODEL_EMBEDDING,
            base_url=settings.DASHSCOPE_BASE_URL,
        )

    async def process_video(
        self,
        video_id: str,
        video_path: str,
        ws_callback: Optional[Callable] = None,
    ):
        """
        Run all pipeline stages sequentially, emitting progress via callback.

        Args:
            video_id: Unique identifier for this video.
            video_path: Path to the uploaded video file.
            ws_callback: Optional async callback(stage, message, progress, status)
                         for real-time progress updates.
        """
        output_dir = os.path.join(settings.UPLOAD_DIR, video_id)
        os.makedirs(output_dir, exist_ok=True)

        # Initialize status
        status = {
            "video_id": video_id,
            "status": "processing",
            "progress": 0,
            "stages": {name: "pending" for name in STAGE_NAMES},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "errors": {},
        }
        self._save_status(output_dir, status)

        results = {}

        # Compute video URL for API calls (served by nginx / static files mount)
        video_filename = os.path.basename(video_path)
        video_url = f"{settings.BASE_URL}/uploads/{video_filename}"
        audio_url = f"{settings.BASE_URL}/uploads/{video_id}/audio.wav"

        total_stages = len(STAGE_NAMES)

        # ── Stage 1: Ingestion ──────────────────────────────────────
        await self._run_stage(
            stage_name="ingestion",
            stage_index=0,
            total_stages=total_stages,
            status=status,
            output_dir=output_dir,
            results=results,
            ws_callback=ws_callback,
            coro_fn=lambda: ingest_video(video_path, output_dir),
            result_key="ingestion",
        )

        # ── Stage 2: Visual Analysis ───────────────────────────────
        await self._run_stage(
            stage_name="visual_analysis",
            stage_index=1,
            total_stages=total_stages,
            status=status,
            output_dir=output_dir,
            results=results,
            ws_callback=ws_callback,
            coro_fn=lambda: analyze_video_visually(
                video_url=video_url,
                api_key=settings.DASHSCOPE_API_KEY,
                model=settings.MODEL_VIDEO,
                base_url=settings.DASHSCOPE_BASE_URL,
            ),
            result_key="visual_analysis",
        )

        # ── Stage 3: Audio / STT ───────────────────────────────────
        await self._run_stage(
            stage_name="audio_analysis",
            stage_index=2,
            total_stages=total_stages,
            status=status,
            output_dir=output_dir,
            results=results,
            ws_callback=ws_callback,
            coro_fn=lambda: transcribe_audio(
                audio_url=audio_url,
                api_key=settings.DASHSCOPE_API_KEY,
                model=settings.MODEL_ASR,
            ),
            result_key="transcript",
        )

        # ── Stage 4: Face Recognition ──────────────────────────────
        faces_detected = results.get("visual_analysis", {}).get("faces", [])
        await self._run_stage(
            stage_name="face_recognition",
            stage_index=3,
            total_stages=total_stages,
            status=status,
            output_dir=output_dir,
            results=results,
            ws_callback=ws_callback,
            coro_fn=lambda: identify_faces(
                faces_detected=faces_detected,
                api_key=settings.DASHSCOPE_API_KEY,
                model=settings.MODEL_TEXT,
                base_url=settings.DASHSCOPE_BASE_URL,
            ),
            result_key="faces",
        )

        # ── Stage 5: Metadata Structuring ──────────────────────────
        await self._run_stage(
            stage_name="metadata_structuring",
            stage_index=4,
            total_stages=total_stages,
            status=status,
            output_dir=output_dir,
            results=results,
            ws_callback=ws_callback,
            coro_fn=lambda: structure_metadata(
                analysis_results=results,
                api_key=settings.DASHSCOPE_API_KEY,
                model=settings.MODEL_TEXT,
                base_url=settings.DASHSCOPE_BASE_URL,
            ),
            result_key="metadata",
        )

        # ── Stage 6: Search Index ──────────────────────────────────
        # Build searchable segments from scenes + transcript
        searchable_segments = self._build_searchable_segments(results)
        await self._run_stage(
            stage_name="search_index",
            stage_index=5,
            total_stages=total_stages,
            status=status,
            output_dir=output_dir,
            results=results,
            ws_callback=ws_callback,
            coro_fn=lambda: self.search_index.add_video(video_id, searchable_segments),
            result_key="search_index",
            save_result=False,
        )

        # ── Finalize ───────────────────────────────────────────────
        all_succeeded = all(
            status["stages"][s] == "completed" for s in STAGE_NAMES
        )
        status["status"] = "completed" if all_succeeded else "completed_with_errors"
        status["progress"] = 100
        status["updated_at"] = datetime.utcnow().isoformat()
        self._save_status(output_dir, status)

        # Save combined results
        self._save_json(output_dir, "results.json", results)

        if ws_callback:
            await ws_callback(
                stage="done",
                message="Pipeline completed" + (
                    "" if all_succeeded else " with some errors"
                ),
                progress=100,
                status="completed" if all_succeeded else "completed_with_errors",
            )

        logger.info("Pipeline completed for video %s (status: %s)", video_id, status["status"])

    async def _run_stage(
        self,
        stage_name: str,
        stage_index: int,
        total_stages: int,
        status: dict,
        output_dir: str,
        results: dict,
        ws_callback: Optional[Callable],
        coro_fn: Callable,
        result_key: str,
        save_result: bool = True,
    ):
        """Execute a single pipeline stage with error handling and progress tracking."""
        progress = int(((stage_index) / total_stages) * 100)
        status["stages"][stage_name] = "running"
        status["progress"] = progress
        status["updated_at"] = datetime.utcnow().isoformat()
        self._save_status(output_dir, status)

        if ws_callback:
            await ws_callback(
                stage=stage_name,
                message=f"Running {stage_name}...",
                progress=progress,
                status="running",
            )

        try:
            result = await coro_fn()
            results[result_key] = result

            if save_result and result is not None:
                self._save_json(output_dir, f"{result_key}.json", result)

            status["stages"][stage_name] = "completed"
            progress = int(((stage_index + 1) / total_stages) * 100)
            status["progress"] = progress
            status["updated_at"] = datetime.utcnow().isoformat()
            self._save_status(output_dir, status)

            if ws_callback:
                await ws_callback(
                    stage=stage_name,
                    message=f"{stage_name} completed",
                    progress=progress,
                    status="completed",
                )

            logger.info("Stage %s completed for %s", stage_name, output_dir)

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(
                "Stage %s failed: %s\n%s",
                stage_name, error_msg, traceback.format_exc(),
            )

            status["stages"][stage_name] = "failed"
            status["errors"][stage_name] = error_msg
            status["updated_at"] = datetime.utcnow().isoformat()
            self._save_status(output_dir, status)

            results[result_key] = {"error": error_msg}
            if save_result:
                self._save_json(output_dir, f"{result_key}.json", {"error": error_msg})

            if ws_callback:
                await ws_callback(
                    stage=stage_name,
                    message=f"{stage_name} failed: {error_msg}",
                    progress=status["progress"],
                    status="failed",
                )

    def _build_searchable_segments(self, results: dict) -> list:
        """Combine scenes and transcript into a flat list of searchable segments."""
        segments = []

        # Add scenes from visual analysis
        for scene in results.get("visual_analysis", {}).get("scenes", []):
            segments.append({
                "description_en": scene.get("description_en", ""),
                "timestamp": scene.get("timestamp", "0:00"),
                "scene_type": scene.get("scene_type", ""),
                "type": "scene",
            })

        # Add transcript segments
        for seg in results.get("transcript", {}).get("segments", []):
            if seg.get("text"):
                segments.append({
                    "description_en": seg["text"],
                    "timestamp": seg.get("start_time", 0),
                    "type": "transcript",
                })

        # Add identified persons
        for face in results.get("faces", []):
            if face.get("identified") and face.get("name_en"):
                segments.append({
                    "description_en": f"{face['name_en']} ({face.get('role', '')}) appears at {face.get('timestamp', 'unknown')}",
                    "timestamp": face.get("timestamp", "0:00"),
                    "type": "person",
                })

        return segments

    @staticmethod
    def _save_status(output_dir: str, status: dict):
        """Write status.json to disk."""
        path = os.path.join(output_dir, "status.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(status, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _save_json(output_dir: str, filename: str, data):
        """Write arbitrary JSON data to disk."""
        path = os.path.join(output_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

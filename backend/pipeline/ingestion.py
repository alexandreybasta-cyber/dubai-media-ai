"""
Stage 1: Video Ingestion
Extracts audio track, generates thumbnail, and retrieves video metadata using ffmpeg.
"""

import asyncio
import json
import logging
import os

import ffmpeg

logger = logging.getLogger(__name__)


async def ingest_video(video_path: str, output_dir: str) -> dict:
    """
    Extract audio track (WAV 16kHz mono), generate thumbnail, and get video metadata.

    Args:
        video_path: Path to the input video file.
        output_dir: Directory to write outputs (audio, thumbnail).

    Returns:
        dict with audio_path, thumbnail_path, duration, resolution, fps, codec.
    """
    os.makedirs(output_dir, exist_ok=True)
    audio_path = os.path.join(output_dir, "audio.wav")
    thumbnail_path = os.path.join(output_dir, "thumbnail.jpg")

    # --- Get video probe info ---
    probe_data = await _probe_video(video_path)
    duration = float(probe_data.get("duration", 0))
    resolution = probe_data.get("resolution", "unknown")
    fps = probe_data.get("fps", 0)
    codec = probe_data.get("codec", "unknown")

    # --- Extract audio (16kHz mono WAV for ASR) ---
    await _extract_audio(video_path, audio_path)

    # --- Generate thumbnail from first frame ---
    await _generate_thumbnail(video_path, thumbnail_path)

    return {
        "audio_path": audio_path,
        "thumbnail_path": thumbnail_path,
        "duration": duration,
        "resolution": resolution,
        "fps": fps,
        "codec": codec,
    }


async def _probe_video(video_path: str) -> dict:
    """Probe video file for metadata using ffprobe."""
    try:
        loop = asyncio.get_event_loop()
        probe = await loop.run_in_executor(None, lambda: ffmpeg.probe(video_path))

        video_streams = [
            s for s in probe.get("streams", []) if s.get("codec_type") == "video"
        ]
        if not video_streams:
            logger.warning("No video stream found in %s", video_path)
            return {"duration": 0, "resolution": "unknown", "fps": 0, "codec": "unknown"}

        vs = video_streams[0]
        width = vs.get("width", 0)
        height = vs.get("height", 0)
        codec = vs.get("codec_name", "unknown")

        # Parse fps from r_frame_rate (e.g. "25/1")
        fps_str = vs.get("r_frame_rate", "0/1")
        try:
            num, den = fps_str.split("/")
            fps = round(int(num) / int(den), 2)
        except (ValueError, ZeroDivisionError):
            fps = 0

        # Duration from format or stream
        duration = float(
            probe.get("format", {}).get("duration", 0)
            or vs.get("duration", 0)
        )

        return {
            "duration": duration,
            "resolution": f"{width}x{height}",
            "fps": fps,
            "codec": codec,
        }
    except ffmpeg.Error as e:
        logger.error("ffprobe failed for %s: %s", video_path, e.stderr)
        return {"duration": 0, "resolution": "unknown", "fps": 0, "codec": "unknown"}
    except Exception as e:
        logger.error("Unexpected probe error for %s: %s", video_path, e)
        return {"duration": 0, "resolution": "unknown", "fps": 0, "codec": "unknown"}


async def _extract_audio(video_path: str, audio_path: str) -> None:
    """Extract audio as 16kHz mono WAV."""
    try:
        loop = asyncio.get_event_loop()

        def _run():
            (
                ffmpeg
                .input(video_path)
                .output(audio_path, acodec="pcm_s16le", ac=1, ar=16000)
                .overwrite_output()
                .run(quiet=True)
            )

        await loop.run_in_executor(None, _run)
        logger.info("Audio extracted to %s", audio_path)
    except ffmpeg.Error as e:
        logger.error("Audio extraction failed: %s", e.stderr)
        raise
    except Exception as e:
        logger.error("Unexpected audio extraction error: %s", e)
        raise


async def _generate_thumbnail(video_path: str, thumbnail_path: str) -> None:
    """Generate a JPEG thumbnail from the first frame of the video."""
    try:
        loop = asyncio.get_event_loop()

        def _run():
            (
                ffmpeg
                .input(video_path, ss=0)
                .output(thumbnail_path, vframes=1, q=2)
                .overwrite_output()
                .run(quiet=True)
            )

        await loop.run_in_executor(None, _run)
        logger.info("Thumbnail generated at %s", thumbnail_path)
    except ffmpeg.Error as e:
        logger.error("Thumbnail generation failed: %s", e.stderr)
        raise
    except Exception as e:
        logger.error("Unexpected thumbnail error: %s", e)
        raise

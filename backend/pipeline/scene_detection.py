"""
Scene Detection
Detects real shot boundaries using ffmpeg's scene-change filter, then builds
scene segments with start/end times and extracts one representative frame
per scene for downstream visual analysis.
"""

import asyncio
import logging
import os
import re
import subprocess
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# ffmpeg scene-change score threshold (0-1). Lower = more sensitive.
# 0.25 also catches most dissolves/soft cuts, which score lower than hard cuts.
DEFAULT_THRESHOLD = 0.25
# Ignore cuts closer together than this (seconds) to avoid flash/strobe noise.
MIN_SCENE_LENGTH = 1.5
# Cap on scenes sent to the vision model (adjacent short scenes get merged).
MAX_SCENES = 14
# Long scenes get extra frames at this spacing — lower-thirds (name/title
# overlays) appear briefly and can sit anywhere within an interview shot.
EXTRA_FRAME_SPACING = 10.0
# Overall cap on frames sent to the vision model.
MAX_TOTAL_FRAMES = 26

_PTS_RE = re.compile(r"pts_time:(\d+(?:\.\d+)?)")


async def detect_scenes(
    video_path: str,
    duration: float,
    threshold: float = DEFAULT_THRESHOLD,
    min_scene_length: float = MIN_SCENE_LENGTH,
    max_scenes: int = MAX_SCENES,
) -> List[dict]:
    """
    Detect shot boundaries and return scene segments.

    Args:
        video_path: Path to the video file.
        duration: Video duration in seconds (from ffprobe).
        threshold: Scene-change score threshold for ffmpeg's select filter.
        min_scene_length: Minimum scene length; shorter cuts are dropped.
        max_scenes: Maximum number of segments returned (shortest merged first).

    Returns:
        List of dicts: {"index": int, "start": float, "end": float}.
        Falls back to uniform segmentation if detection fails or finds no cuts.
    """
    cuts = await _run_scene_filter(video_path, threshold)

    if cuts is None:
        logger.warning("Scene filter failed, falling back to uniform segmentation")
        return _uniform_segments(duration, max_scenes)

    # Drop cuts too close to the previous boundary
    boundaries = [0.0]
    for t in sorted(cuts):
        if t - boundaries[-1] >= min_scene_length and t < duration:
            boundaries.append(t)

    if duration > 0 and duration - boundaries[-1] >= 0.5:
        boundaries.append(duration)
    elif duration > 0:
        boundaries[-1] = duration

    if len(boundaries) < 3:
        # 0 or 1 usable cut — likely a single-shot video or detection miss.
        # Uniform segmentation still gives the vision model temporal coverage.
        logger.info(
            "Only %d cut(s) detected, using uniform segmentation", len(boundaries) - 2
        )
        return _uniform_segments(duration, min(6, max_scenes))

    # Raw shots (one per cut) are preserved inside the merged scenes — frame
    # sampling and person-appearance ranges need the fine-grained boundaries.
    segments = [
        {
            "start": boundaries[i],
            "end": boundaries[i + 1],
            "shots": [{"start": boundaries[i], "end": boundaries[i + 1]}],
        }
        for i in range(len(boundaries) - 1)
    ]
    segments = _merge_to_cap(segments, max_scenes)

    for i, seg in enumerate(segments):
        seg["index"] = i
        seg["start"] = round(seg["start"], 2)
        seg["end"] = round(seg["end"], 2)
        seg["shots"] = [
            {"start": round(s["start"], 2), "end": round(s["end"], 2)}
            for s in seg["shots"]
        ]

    logger.info(
        "Detected %d cuts → %d scene segments (threshold=%.2f)",
        len(cuts), len(segments), threshold,
    )
    return segments


async def extract_scene_frames(
    video_path: str,
    scenes: List[dict],
    frames_dir: str,
) -> List[Tuple[str, float, int]]:
    """
    Extract representative frames per scene: always one at the midpoint
    (used as the scene thumbnail), plus extra frames spaced through longer
    scenes — name/title lower-thirds appear briefly and can sit anywhere
    within an interview shot.

    Returns:
        List of (frame_path, timestamp_seconds, scene_index) tuples,
        ordered by timestamp.
    """
    os.makedirs(frames_dir, exist_ok=True)
    # Drop frames from previous runs so the directory reflects this analysis
    for old in os.listdir(frames_dir):
        if old.startswith("scene_") and old.endswith(".jpg"):
            try:
                os.remove(os.path.join(frames_dir, old))
            except OSError:
                pass
    loop = asyncio.get_event_loop()

    # Plan which frames to grab: (scene_index, timestamp, filename)
    # Always: the scene midpoint (canonical thumbnail). Extras: the start of
    # each substantial sub-shot inside the scene — that's where lower-thirds
    # (name/title overlays) are shown — plus spaced frames within very long
    # shots. Longest shots win when the budget runs out: they are the
    # interview/talking-head segments where identification matters most.
    plan: List[Tuple[int, float, str]] = []
    extra_candidates: List[Tuple[float, Tuple[int, float, str]]] = []
    for scene in scenes:
        idx = scene["index"]
        midpoint = (scene["start"] + scene["end"]) / 2
        plan.append((idx, midpoint, f"scene_{idx:03d}.jpg"))

        candidate_times = []
        for shot in scene.get("shots", [scene]):
            shot_len = shot["end"] - shot["start"]
            if shot_len < 6.0:
                continue
            t = shot["start"] + 1.5
            while t < shot["end"] - 1.0:
                candidate_times.append((shot_len, t))
                t += EXTRA_FRAME_SPACING

        for k, (shot_len, t) in enumerate(sorted(candidate_times, key=lambda c: c[1])):
            if abs(t - midpoint) > 1.0:
                extra_candidates.append(
                    (shot_len, (idx, t, f"scene_{idx:03d}_extra{k}.jpg"))
                )

    extra_candidates.sort(key=lambda item: -item[0])
    budget = max(0, MAX_TOTAL_FRAMES - len(plan))
    plan.extend(item for _, item in extra_candidates[:budget])

    frames = []
    for idx, timestamp, filename in plan:
        frame_path = os.path.join(frames_dir, filename)
        cmd = [
            "ffmpeg",
            "-ss", str(timestamp),
            "-i", video_path,
            "-vframes", "1",
            "-vf", "scale='min(960,iw)':-2",
            "-q:v", "3",
            "-y",
            frame_path,
        ]

        def _run(c=cmd):
            return subprocess.run(c, capture_output=True, timeout=30)

        try:
            result = await loop.run_in_executor(None, _run)
            if result.returncode == 0 and os.path.exists(frame_path):
                frames.append((frame_path, timestamp, idx))
            else:
                stderr = result.stderr.decode()[:200] if result.stderr else "unknown"
                logger.warning("Frame extraction failed at %.1fs: %s", timestamp, stderr)
        except Exception as e:
            logger.warning("Frame extraction error at %.1fs: %s", timestamp, e)

    frames.sort(key=lambda f: f[1])
    logger.info("Extracted %d frames for %d scenes", len(frames), len(scenes))
    return frames


async def _run_scene_filter(video_path: str, threshold: float) -> Optional[List[float]]:
    """Run ffmpeg's scene-change select filter and parse cut timestamps."""
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"select='gt(scene,{threshold})',showinfo",
        "-f", "null",
        "-",
    ]

    def _run():
        return subprocess.run(cmd, capture_output=True, timeout=300)

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _run)
        # showinfo logs to stderr
        stderr = result.stderr.decode(errors="replace") if result.stderr else ""
        if result.returncode != 0:
            logger.error("ffmpeg scene filter failed: %s", stderr[-300:])
            return None
        return [float(m) for m in _PTS_RE.findall(stderr)]
    except Exception as e:
        logger.error("Scene filter error: %s", e)
        return None


def _uniform_segments(duration: float, count: int) -> List[dict]:
    """Split the video into equal segments as a fallback."""
    if duration <= 0:
        return []
    count = max(1, min(count, int(duration) or 1))
    step = duration / count
    return [
        {
            "index": i,
            "start": round(i * step, 2),
            "end": round((i + 1) * step, 2),
            "shots": [{"start": round(i * step, 2), "end": round((i + 1) * step, 2)}],
        }
        for i in range(count)
    ]


def _merge_to_cap(segments: List[dict], max_scenes: int) -> List[dict]:
    """Merge the shortest segment into its shorter neighbor until under the
    cap, accumulating the original shot boundaries of merged segments."""
    segments = [dict(s) for s in segments]
    while len(segments) > max_scenes:
        shortest = min(
            range(len(segments)),
            key=lambda i: segments[i]["end"] - segments[i]["start"],
        )
        if shortest == 0:
            target = 1
        elif shortest == len(segments) - 1:
            target = shortest - 1
        else:
            left_len = segments[shortest - 1]["end"] - segments[shortest - 1]["start"]
            right_len = segments[shortest + 1]["end"] - segments[shortest + 1]["start"]
            target = shortest - 1 if left_len <= right_len else shortest + 1
        lo, hi = min(shortest, target), max(shortest, target)
        segments[lo] = {
            "start": segments[lo]["start"],
            "end": segments[hi]["end"],
            "shots": segments[lo].get("shots", []) + segments[hi].get("shots", []),
        }
        del segments[hi]
    return segments

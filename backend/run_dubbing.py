"""
Subprocess entry point for video dubbing.
Launched by the API router to avoid blocking the main event loop.
Usage: python run_dubbing.py <video_id> <target_language>
"""
import asyncio
import json
import os
import sys

# Ensure backend modules are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline.dubbing import dub_video
from config import settings


async def main():
    if len(sys.argv) < 3:
        print("Usage: python run_dubbing.py <video_id> <target_language>")
        sys.exit(1)

    video_id = sys.argv[1]
    target_language = sys.argv[2]

    video_path = os.path.join(settings.UPLOAD_DIR, f"{video_id}.mp4")
    output_dir = os.path.join(settings.UPLOAD_DIR, video_id)

    if not os.path.exists(video_path):
        print(f"ERROR: Video file not found: {video_path}")
        sys.exit(1)
    if not os.path.exists(output_dir):
        print(f"ERROR: Output directory not found: {output_dir}")
        sys.exit(1)

    result = await dub_video(
        video_id=video_id,
        video_path=video_path,
        output_dir=output_dir,
        target_language=target_language,
    )

    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result.get("status") == "completed" else 1)


if __name__ == "__main__":
    asyncio.run(main())

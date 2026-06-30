"""
Standalone pipeline runner - executed as a subprocess by the API server.
This runs in a completely separate process, so it can NEVER block the server.
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline.orchestrator import PipelineOrchestrator


async def main(video_id: str, video_path: str):
    orchestrator = PipelineOrchestrator()
    await orchestrator.process_video(video_id, video_path, ws_callback=None)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <video_id> <video_path>")
        sys.exit(1)

    video_id = sys.argv[1]
    video_path = sys.argv[2]

    asyncio.run(main(video_id, video_path))

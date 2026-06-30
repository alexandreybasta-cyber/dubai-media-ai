# Media Processing Pipeline

<cite>
**Referenced Files in This Document**
- [backend/pipeline/orchestrator.py](file://backend/pipeline/orchestrator.py)
- [backend/pipeline/ingestion.py](file://backend/pipeline/ingestion.py)
- [backend/pipeline/visual_analysis.py](file://backend/pipeline/visual_analysis.py)
- [backend/pipeline/audio_analysis.py](file://backend/pipeline/audio_analysis.py)
- [backend/pipeline/face_recognition.py](file://backend/pipeline/face_recognition.py)
- [backend/pipeline/metadata_structuring.py](file://backend/pipeline/metadata_structuring.py)
- [backend/pipeline/search_index.py](file://backend/pipeline/search_index.py)
- [backend/routers/video.py](file://backend/routers/video.py)
- [backend/config.py](file://backend/config.py)
- [backend/main.py](file://backend/main.py)
- [backend/data/reference_faces.json](file://backend/data/reference_faces.json)
- [backend/data/iptc_taxonomy.json](file://backend/data/iptc_taxonomy.json)
- [frontend/src/lib/useVideoProcessing.ts](file://frontend/src/lib/useVideoProcessing.ts)
- [frontend/src/components/archive/PipelineVisualizer.tsx](file://frontend/src/components/archive/PipelineVisualizer.tsx)
- [frontend/src/components/archive/VideoUpload.tsx](file://frontend/src/components/archive/VideoUpload.tsx)
</cite>

## Update Summary
**Changes Made**
- Updated Core Components section to highlight cooperative multitasking improvements
- Enhanced Performance Considerations section with detailed cooperative yielding explanations
- Added troubleshooting guidance for concurrent video processing scenarios
- Updated architecture diagrams to reflect improved concurrency handling
- Enhanced server responsiveness documentation with specific implementation details

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)
10. [Appendices](#appendices)

## Introduction
This document explains the 6-stage AI-powered media processing pipeline designed for automated metadata extraction and indexing of video archives. It covers the orchestration layer, each processing stage, AI model integrations, real-time progress tracking via WebSocket, and operational guidance for performance and reliability.

The pipeline transforms raw video into structured metadata, transcripts, face identifications, and a semantic search index, enabling efficient discovery and archival workflows. **Enhanced with cooperative multitasking support**, the pipeline now allows concurrent video processing while maintaining system responsiveness for all endpoints.

## Project Structure
The system is organized into:
- Backend: Orchestration, stage implementations, API routes, configuration, and data assets
- Frontend: Real-time UI for upload, progress visualization, and search

```mermaid
graph TB
subgraph "Backend"
CFG["Config (settings)"]
ORCH["PipelineOrchestrator"]
ST1["Ingestion"]
ST2["Visual Analysis"]
ST3["Audio Analysis (ASR)"]
ST4["Face Recognition"]
ST5["Metadata Structuring"]
ST6["Search Index"]
ROUTER["Video Router"]
MAIN["FastAPI App"]
end
subgraph "Data Assets"
REF["reference_faces.json"]
IPTC["iptc_taxonomy.json"]
end
subgraph "Frontend"
HOOK["useVideoProcessing hook"]
VIS["PipelineVisualizer"]
UP["VideoUpload"]
end
MAIN --> ROUTER
ROUTER --> ORCH
ORCH --> ST1
ORCH --> ST2
ORCH --> ST3
ORCH --> ST4
ORCH --> ST5
ORCH --> ST6
ST4 --> REF
ST5 --> IPTC
HOOK --> ROUTER
VIS --> HOOK
UP --> HOOK
```

**Diagram sources**
- [backend/main.py:1-44](file://backend/main.py#L1-L44)
- [backend/routers/video.py:1-268](file://backend/routers/video.py#L1-L268)
- [backend/pipeline/orchestrator.py:1-330](file://backend/pipeline/orchestrator.py#L1-L330)
- [backend/pipeline/ingestion.py:1-146](file://backend/pipeline/ingestion.py#L1-L146)
- [backend/pipeline/visual_analysis.py:1-342](file://backend/pipeline/visual_analysis.py#L1-L342)
- [backend/pipeline/audio_analysis.py:1-277](file://backend/pipeline/audio_analysis.py#L1-L277)
- [backend/pipeline/face_recognition.py:1-215](file://backend/pipeline/face_recognition.py#L1-L215)
- [backend/pipeline/metadata_structuring.py:1-252](file://backend/pipeline/metadata_structuring.py#L1-L252)
- [backend/pipeline/search_index.py:1-300](file://backend/pipeline/search_index.py#L1-L300)
- [backend/data/reference_faces.json:1-101](file://backend/data/reference_faces.json#L1-L101)
- [backend/data/iptc_taxonomy.json:1-28](file://backend/data/iptc_taxonomy.json#L1-L28)
- [frontend/src/lib/useVideoProcessing.ts:1-465](file://frontend/src/lib/useVideoProcessing.ts#L1-L465)
- [frontend/src/components/archive/PipelineVisualizer.tsx:1-181](file://frontend/src/components/archive/PipelineVisualizer.tsx#L1-L181)
- [frontend/src/components/archive/VideoUpload.tsx:1-221](file://frontend/src/components/archive/VideoUpload.tsx#L1-L221)

**Section sources**
- [backend/main.py:1-44](file://backend/main.py#L1-L44)
- [backend/routers/video.py:1-268](file://backend/routers/video.py#L1-L268)

## Core Components
- PipelineOrchestrator: Manages sequential stages, progress tracking, status persistence, and WebSocket notifications with cooperative multitasking support.
- Stage modules: Ingestion, Visual Analysis, Audio Analysis, Face Recognition, Metadata Structuring, Search Index.
- Router: Upload, status, metadata, transcript, search, and WebSocket endpoints.
- Config: Centralized settings for API keys, models, and base URLs.
- Frontend hook and components: Real-time progress, upload UX, and visualization.

Key orchestration responsibilities:
- Sequential stage execution with error containment
- Persistent status and intermediate results
- Real-time progress via WebSocket callback
- Building searchable segments for embedding
- **Enhanced server responsiveness through cooperative yielding mechanism**

**Updated** Enhanced server responsiveness through cooperative yielding mechanism using `await asyncio.sleep(0)` to prevent blocking the event loop during long-running operations. This enables concurrent video processing while maintaining system responsiveness for all endpoints.

**Section sources**
- [backend/pipeline/orchestrator.py:34-330](file://backend/pipeline/orchestrator.py#L34-L330)
- [backend/routers/video.py:37-268](file://backend/routers/video.py#L37-L268)
- [backend/config.py:4-21](file://backend/config.py#L4-L21)

## Architecture Overview
The pipeline is a server-side orchestration backed by external AI APIs and local file storage. The frontend connects via REST and WebSocket to observe progress and retrieve results. **With cooperative multitasking support**, the system can handle multiple concurrent video processing operations without sacrificing responsiveness.

```mermaid
sequenceDiagram
participant FE as "Frontend"
participant API as "FastAPI Router"
participant ORCH as "PipelineOrchestrator"
participant ST1 as "Ingestion"
participant ST2 as "Visual Analysis"
participant ST3 as "Audio Analysis"
participant ST4 as "Face Recognition"
participant ST5 as "Metadata Structuring"
participant ST6 as "Search Index"
FE->>API : POST /api/video/upload
API->>ORCH : process_video(video_id, video_path)
ORCH->>ST1 : ingest_video(video_path, output_dir)
ST1-->>ORCH : ingestion.json
ORCH->>ST2 : analyze_video_visually(video_url, api_key, model)
ST2-->>ORCH : visual_analysis.json
ORCH->>ST3 : transcribe_audio(audio_url, api_key, model)
ST3-->>ORCH : transcript.json
ORCH->>ST4 : identify_faces(faces_detected, api_key, model)
ST4-->>ORCH : faces.json
ORCH->>ST5 : structure_metadata(analysis_results, api_key, model)
ST5-->>ORCH : metadata.json
ORCH->>ST6 : SearchIndex.add_video(video_id, segments)
ST6-->>ORCH : index persisted
ORCH-->>FE : WebSocket "done" + status.json + results.json
```

**Diagram sources**
- [backend/routers/video.py:95-121](file://backend/routers/video.py#L95-L121)
- [backend/pipeline/orchestrator.py:44-206](file://backend/pipeline/orchestrator.py#L44-L206)
- [backend/pipeline/ingestion.py:16-51](file://backend/pipeline/ingestion.py#L16-L51)
- [backend/pipeline/visual_analysis.py:43-130](file://backend/pipeline/visual_analysis.py#L43-L130)
- [backend/pipeline/audio_analysis.py:22-59](file://backend/pipeline/audio_analysis.py#L22-L59)
- [backend/pipeline/face_recognition.py:54-107](file://backend/pipeline/face_recognition.py#L54-L107)
- [backend/pipeline/metadata_structuring.py:81-163](file://backend/pipeline/metadata_structuring.py#L81-L163)
- [backend/pipeline/search_index.py:88-154](file://backend/pipeline/search_index.py#L88-L154)

## Detailed Component Analysis

### PipelineOrchestrator
Responsibilities:
- Sequentially executes six stages with cooperative yielding for server responsiveness
- Tracks progress and status per stage
- Persists status.json and intermediate results
- Emits real-time progress via WebSocket callback
- Builds searchable segments for embedding

**Updated** Enhanced with cooperative yielding mechanism to improve server responsiveness during long-running video processing operations. The orchestrator yields control to the event loop using `await asyncio.sleep(0)` at the beginning of each stage execution, preventing blocking of other requests.

Inputs:
- video_id, video_path
- Optional ws_callback(stage, message, progress, status)

Outputs:
- status.json, results.json
- Per-stage artifacts under output_dir

Error handling:
- Catches exceptions per stage, records error in status.errors, and continues or completes depending on stage outcome

Progress calculation:
- Stage progress mapped linearly across 6 stages

```mermaid
flowchart TD
Start(["process_video"]) --> Init["Initialize status.json<br/>Create output_dir"]
Init --> Yield["await asyncio.sleep(0)<br/>Yield to event loop"]
Yield --> Stage1["Run ingestion"]
Stage1 --> Stage2["Run visual analysis"]
Stage2 --> Stage3["Run audio analysis"]
Stage3 --> Stage4["Run face recognition"]
Stage4 --> Stage5["Run metadata structuring"]
Stage5 --> Segments["Build searchable segments"]
Segments --> Stage6["Run search index"]
Stage6 --> Finalize["Finalize status (completed/completed_with_errors)"]
Finalize --> Done(["Return and notify WebSocket"])
```

**Diagram sources**
- [backend/pipeline/orchestrator.py:44-206](file://backend/pipeline/orchestrator.py#L44-L206)

**Section sources**
- [backend/pipeline/orchestrator.py:34-330](file://backend/pipeline/orchestrator.py#L34-L330)

### Stage 1: Ingestion
Purpose:
- Extract audio (16 kHz mono WAV), generate thumbnail, and probe metadata (duration, resolution, FPS, codec)

Inputs:
- video_path, output_dir

Outputs:
- ingestion.json with audio_path, thumbnail_path, duration, resolution, fps, codec

Error handling:
- Graceful fallback to unknown values on probe failure
- ffmpeg errors logged and re-raised to trigger stage failure

**Section sources**
- [backend/pipeline/ingestion.py:16-146](file://backend/pipeline/ingestion.py#L16-L146)

### Stage 2: Visual Analysis (Qwen-VL)
Purpose:
- Comprehensive visual understanding: scenes, objects, landmarks, faces, OCR, sensitive content, era estimation

Inputs:
- video_path, api_key, model, base_url

Outputs:
- visual_analysis.json with scenes, objects, landmarks, faces, OCR, sensitive content, era_estimate, summaries

AI integration:
- DashScope chat/completions with video_path payload and fps sampling

Error handling:
- Retries with exponential backoff
- Parses JSON from raw response (direct or fenced code block)
- Returns empty structured result on repeated failure

**Section sources**
- [backend/pipeline/visual_analysis.py:43-342](file://backend/pipeline/visual_analysis.py#L43-L342)

### Stage 3: Audio Analysis (ASR) - Paraformer-v2
Purpose:
- Speech-to-text with speaker diarization and language hints

Inputs:
- audio_path, api_key, model

Outputs:
- transcript.json with segments, full_text, speaker_count, language

Workflow:
- Submit task, poll status until SUCCEEDED or FAILED/CANCELED
- Fetch transcript JSON from returned URL and parse into segments

Error handling:
- Submission retries with backoff
- Polling with bounded attempts and interval
- Returns empty structured result on failure

**Section sources**
- [backend/pipeline/audio_analysis.py:22-277](file://backend/pipeline/audio_analysis.py#L22-L277)

### Stage 4: Face Recognition
Purpose:
- Match detected faces to a reference database using Qwen text model

Inputs:
- faces_detected (from visual analysis), api_key, model, base_url

Outputs:
- faces.json enriched with identification info (name_en, name_ar, role, confidence)

Data:
- Reference database loaded from reference_faces.json

Error handling:
- Loads reference faces and prompts model per face
- Conservative matching with retries and fallback to unidentified

**Section sources**
- [backend/pipeline/face_recognition.py:54-215](file://backend/pipeline/face_recognition.py#L54-L215)
- [backend/data/reference_faces.json:1-101](file://backend/data/reference_faces.json#L1-L101)

### Stage 5: Metadata Structuring (EBUCore/IPTC)
Purpose:
- Generate broadcast-ready metadata and IPTC topic codes

Inputs:
- analysis_results (aggregated), api_key, model, base_url

Outputs:
- metadata.json with EBUCore XML snippet, IPTC metadata, topic codes, sentiment, geographic tags, persons mentioned

Data:
- IPTC taxonomy loaded from iptc_taxonomy.json

Error handling:
- Compacts analysis to avoid token limits
- Retries with backoff and returns empty structured result on failure

**Section sources**
- [backend/pipeline/metadata_structuring.py:81-252](file://backend/pipeline/metadata_structuring.py#L81-L252)
- [backend/data/iptc_taxonomy.json:1-28](file://backend/data/iptc_taxonomy.json#L1-L28)

### Stage 6: Search Index (FAISS + Embeddings)
Purpose:
- Build a vector search index from scenes and transcript segments

Inputs:
- video_id, segments (built from visual_analysis scenes and transcript)

Outputs:
- Persisted FAISS index and metadata

AI integration:
- DashScope embeddings API for text-embedding-v3

Error handling:
- Batched embedding requests with backoff
- Saves index to disk; gracefully handles missing FAISS installation

**Section sources**
- [backend/pipeline/search_index.py:22-300](file://backend/pipeline/search_index.py#L22-L300)

### Real-time Progress Tracking and Status Reporting
- Router exposes WebSocket endpoint for live progress
- Orchestrator invokes ws_callback(stage, message, progress, status) per stage
- Frontend hook subscribes to WebSocket, updates stage statuses and elapsed times
- REST fallback polling supported when WebSocket fails

```mermaid
sequenceDiagram
participant FE as "Frontend"
participant WS as "WebSocket /ws/pipeline/{video_id}"
participant API as "Router"
participant ORCH as "PipelineOrchestrator"
FE->>WS : Connect
API->>ORCH : process_video(video_id, video_path, ws_callback)
ORCH->>WS : send_json({stage, message, progress, status})
FE-->>FE : Update PipelineVisualizer
ORCH-->>WS : send_json({stage : "done", message, progress : 100, status})
FE->>API : GET /api/video/{video_id}/metadata
API-->>FE : metadata.json + transcript.json
```

**Diagram sources**
- [backend/routers/video.py:220-268](file://backend/routers/video.py#L220-L268)
- [backend/routers/video.py:95-121](file://backend/routers/video.py#L95-L121)
- [backend/pipeline/orchestrator.py:208-282](file://backend/pipeline/orchestrator.py#L208-L282)
- [frontend/src/lib/useVideoProcessing.ts:215-276](file://frontend/src/lib/useVideoProcessing.ts#L215-L276)

**Section sources**
- [backend/routers/video.py:218-268](file://backend/routers/video.py#L218-L268)
- [frontend/src/lib/useVideoProcessing.ts:215-276](file://frontend/src/lib/useVideoProcessing.ts#L215-L276)
- [frontend/src/components/archive/PipelineVisualizer.tsx:88-181](file://frontend/src/components/archive/PipelineVisualizer.tsx#L88-L181)

## Dependency Analysis
- Orchestration depends on stage modules and SearchIndex
- Stages depend on external AI APIs and local data assets
- Router depends on Orchestrator and SearchIndex
- Frontend depends on Router and WebSocket

```mermaid
graph LR
ORCH["PipelineOrchestrator"] --> ST1["Ingestion"]
ORCH --> ST2["Visual Analysis"]
ORCH --> ST3["Audio Analysis"]
ORCH --> ST4["Face Recognition"]
ORCH --> ST5["Metadata Structuring"]
ORCH --> ST6["Search Index"]
ST4 --> REF["reference_faces.json"]
ST5 --> IPTC["iptc_taxonomy.json"]
ROUTER["Video Router"] --> ORCH
FEHOOK["useVideoProcessing"] --> ROUTER
```

**Diagram sources**
- [backend/pipeline/orchestrator.py:14-42](file://backend/pipeline/orchestrator.py#L14-L42)
- [backend/pipeline/face_recognition.py:21-32](file://backend/pipeline/face_recognition.py#L21-L32)
- [backend/pipeline/metadata_structuring.py:22-32](file://backend/pipeline/metadata_structuring.py#L22-L32)
- [backend/routers/video.py:17-26](file://backend/routers/video.py#L17-L26)
- [frontend/src/lib/useVideoProcessing.ts:1-10](file://frontend/src/lib/useVideoProcessing.ts#L1-L10)

**Section sources**
- [backend/pipeline/orchestrator.py:14-42](file://backend/pipeline/orchestrator.py#L14-L42)
- [backend/routers/video.py:17-26](file://backend/routers/video.py#L17-L26)

## Performance Considerations
- Stage durations:
  - Ingestion: O(1) with respect to video length; dominated by I/O
  - Visual Analysis: Heavily dependent on video length and fps sampling; expect linear increase with duration
  - Audio Analysis: Primarily network-bound; duration affects polling overhead
  - Face Recognition: Proportional to number of faces; conservative matching reduces false positives
  - Metadata Structuring: Prompt size controlled by compaction; mostly API latency
  - Search Index: Linear in segment count; embedding batch size capped at 25
- Memory usage:
  - Transcripts and metadata stored per stage; FAISS index grows with segment count
  - Embeddings normalized to unit vectors; index persists to disk
- Scalability:
  - Parallelize independent videos; current orchestration is sequential per video
  - Consider batching embedding calls and increasing batch size cautiously
  - Ensure adequate disk space for FAISS index and intermediate artifacts
- Network:
  - External APIs introduce latency and rate limits; implement retries and backoff
  - Mount uploads via static files for reliable video/audio access
- **Server Responsiveness**:
  - **Cooperative yielding**: The orchestrator uses `await asyncio.sleep(0)` to yield control back to the event loop, preventing long-running stages from blocking other requests
  - **Event loop fairness**: This ensures the server can handle incoming requests, WebSocket connections, and background tasks even during extended processing operations
  - **Concurrent processing**: Multiple videos can be processed simultaneously without impacting system responsiveness
  - **Non-blocking operations**: All stage functions are async and use cooperative yielding points

**Updated** Enhanced server responsiveness through cooperative yielding mechanism that prevents blocking the event loop during long-running video processing operations. The `await asyncio.sleep(0)` call at the beginning of each stage ensures that other requests can be processed while long-running operations are in progress.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common issues and recovery strategies:
- Missing API key:
  - Symptom: Stages return empty results with error markers
  - Action: Set DASHSCOPE_API_KEY and restart service
- ffprobe/ffmpeg failures during ingestion:
  - Symptom: Unknown metadata and thumbnail generation errors
  - Action: Verify media container and codecs; ensure ffmpeg is installed and accessible
- Visual Analysis API errors:
  - Symptom: Stage fails with API or request errors
  - Action: Retry; check base URL and model availability; reduce video length or fps sampling
- ASR task timeouts or failures:
  - Symptom: Task does not complete within max attempts
  - Action: Verify audio accessibility; ensure WAV format and URL reachability
- Face Recognition parsing failures:
  - Symptom: No matches despite clear descriptions
  - Action: Confirm reference_faces.json validity; adjust prompt temperature conservatively
- Metadata structuring parse errors:
  - Symptom: Empty metadata or parse warnings
  - Action: Reduce analysis compaction; shorten prompts; verify IPTC taxonomy
- Search index unavailable:
  - Symptom: FAISS not installed or index load failures
  - Action: Install faiss-cpu; ensure permissions for index_dir; rebuild index
- WebSocket disconnections:
  - Symptom: UI stops updating progress
  - Action: Use REST status polling as fallback; reconnect WebSocket; check server logs
- **Server responsiveness issues**:
  - Symptom: Slow response to new upload requests during long processing
  - Action: The cooperative yielding mechanism automatically addresses this; monitor event loop utilization
- **Concurrent processing conflicts**:
  - Symptom: Multiple videos causing resource contention
  - Action: Monitor system resources; consider rate limiting; ensure adequate CPU and memory allocation

**Updated** Added troubleshooting guidance for concurrent video processing scenarios, noting that the cooperative yielding mechanism automatically addresses slow response problems during long processing operations. Also added guidance for handling concurrent processing conflicts.

**Section sources**
- [backend/pipeline/visual_analysis.py:90-130](file://backend/pipeline/visual_analysis.py#L90-L130)
- [backend/pipeline/audio_analysis.py:77-142](file://backend/pipeline/audio_analysis.py#L77-L142)
- [backend/pipeline/face_recognition.py:138-195](file://backend/pipeline/face_recognition.py#L138-L195)
- [backend/pipeline/metadata_structuring.py:125-163](file://backend/pipeline/metadata_structuring.py#L125-L163)
- [backend/pipeline/search_index.py:61-70](file://backend/pipeline/search_index.py#L61-L70)
- [backend/routers/video.py:254-268](file://backend/routers/video.py#L254-L268)

## Conclusion
The pipeline provides a robust, modular, and observable framework for AI-driven media processing. Its sequential orchestration, persistent state, and real-time feedback enable reliable archival workflows. **Enhanced with cooperative multitasking support**, the pipeline now allows concurrent video processing while maintaining system responsiveness for all endpoints. The cooperative yielding mechanism ensures that long-running operations don't block the event loop, enabling multiple videos to be processed simultaneously without impacting system performance. By tuning stage parameters, ensuring adequate infrastructure, and leveraging retries and fallbacks, operators can achieve scalable and resilient media processing in production environments.

**Updated** The pipeline now includes enhanced server responsiveness through cooperative yielding, making it more suitable for production environments where multiple concurrent video processing operations may occur. The cooperative multitasking support ensures that the system remains responsive even when processing multiple videos simultaneously.

[No sources needed since this section summarizes without analyzing specific files]

## Appendices

### API Endpoints Overview
- POST /api/video/upload: Upload video and enqueue processing
- GET /api/video/{video_id}/status: Retrieve current pipeline status
- GET /api/video/{video_id}/metadata: Retrieve structured metadata
- GET /api/video/{video_id}/transcript: Retrieve speech transcript
- POST /api/search: Semantic search across indexed videos
- WebSocket /ws/pipeline/{video_id}: Real-time progress updates

**Section sources**
- [backend/routers/video.py:39-216](file://backend/routers/video.py#L39-L216)

### Example Workflows and Expected Times
- Short clip (< 2 minutes):
  - Ingestion: ~2–5s
  - Visual Analysis: ~30–60s
  - Audio Analysis: ~1–2min
  - Face Recognition: ~10–30s
  - Metadata Structuring: ~30–60s
  - Search Index: ~10–30s
  - Total: ~2–5min
- Medium clip (5–10 minutes):
  - Visual Analysis scales roughly linearly with duration
  - Expect ~5–15min total depending on API latency
- Large clip (> 30 minutes):
  - Consider chunking or reducing fps sampling
  - Total time can exceed 30min depending on stage throughput

**Updated** Server responsiveness improvements ensure consistent performance even with extended processing times for large video files. The cooperative multitasking support allows multiple videos to be processed concurrently without impacting system responsiveness.

[No sources needed since this section provides general guidance]
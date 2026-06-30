# Pipeline Overview and Architecture

<cite>
**Referenced Files in This Document**
- [orchestrator.py](file://backend/pipeline/orchestrator.py)
- [video.py](file://backend/routers/video.py)
- [config.py](file://backend/config.py)
- [ingestion.py](file://backend/pipeline/ingestion.py)
- [visual_analysis.py](file://backend/pipeline/visual_analysis.py)
- [audio_analysis.py](file://backend/pipeline/audio_analysis.py)
- [face_recognition.py](file://backend/pipeline/face_recognition.py)
- [metadata_structuring.py](file://backend/pipeline/metadata_structuring.py)
- [search_index.py](file://backend/pipeline/search_index.py)
- [main.py](file://backend/main.py)
- [useVideoProcessing.ts](file://frontend/src/lib/useVideoProcessing.ts)
- [PipelineVisualizer.tsx](file://frontend/src/components/archive/PipelineVisualizer.tsx)
- [APITransparencyPanel.tsx](file://frontend/src/components/archive/APITransparencyPanel.tsx)
- [reference_faces.json](file://backend/data/reference_faces.json)
- [iptc_taxonomy.json](file://backend/data/iptc_taxonomy.json)
</cite>

## Update Summary
**Changes Made**
- Enhanced pipeline orchestration with new OCR text detection extraction capabilities
- Improved video duration handling with robust ffprobe integration
- Enhanced search segment building with richer metadata including IPTC video metadata, titles, and thumbnails
- Updated face recognition module to utilize OCR text detection for person identification
- Improved metadata structuring with comprehensive IPTC taxonomy integration
- Enhanced search index building with enriched segment metadata

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Enhanced Concurrency Model](#enhanced-concurrency-model)
6. [Cooperative Multitasking Implementation](#cooperative-multitasking-implementation)
7. [Non-Blocking Execution Architecture](#non-blocking-execution-architecture)
8. [Detailed Component Analysis](#detailed-component-analysis)
9. [Dependency Analysis](#dependency-analysis)
10. [Performance Considerations](#performance-considerations)
11. [Troubleshooting Guide](#troubleshooting-guide)
12. [Conclusion](#conclusion)
13. [Appendices](#appendices)

## Introduction
This document explains the PipelineOrchestrator class and the end-to-end video processing pipeline with enhanced concurrency capabilities. The pipeline now implements a sophisticated asynchronous architecture featuring cooperative multitasking, non-blocking execution, and efficient resource utilization. It details the six-stage sequential workflow, the orchestrator's role in stage execution, progress tracking, and error handling. The pipeline has been updated to use local file path processing instead of URL-based communication, reducing potential failure points and improving reliability. It also documents the WebSocket callback mechanism for real-time progress updates, the status management system, and how the orchestrator coordinates between pipeline components. Practical examples illustrate pipeline initialization, execution flow, and status monitoring. Finally, it covers performance characteristics, memory usage patterns, and scalability implications of the enhanced asynchronous processing approach.

## Project Structure
The pipeline is implemented as a FastAPI service with a dedicated orchestration module and stage-specific modules. The frontend integrates with the backend via REST and WebSocket APIs to visualize progress and results. The orchestrator now processes local file paths directly, eliminating URL-based communication complexity. All stage modules have been enhanced with async implementations for optimal concurrency.

```mermaid
graph TB
subgraph "Backend"
A["FastAPI App<br/>main.py"]
B["Routers<br/>video.py"]
C["Pipeline Orchestrator<br/>orchestrator.py"]
D["Stage Modules<br/>ingestion.py<br/>visual_analysis.py<br/>audio_analysis.py<br/>face_recognition.py<br/>metadata_structuring.py<br/>search_index.py"]
E["Config<br/>config.py"]
end
subgraph "Frontend"
F["React Hooks<br/>useVideoProcessing.ts"]
G["UI Components<br/>PipelineVisualizer.tsx<br/>APITransparencyPanel.tsx"]
end
A --> B
B --> C
C --> D
B --> E
F --> B
G --> F
```

**Diagram sources**
- [main.py:1-44](file://backend/main.py#L1-L44)
- [video.py:1-268](file://backend/routers/video.py#L1-L268)
- [orchestrator.py:1-374](file://backend/pipeline/orchestrator.py#L1-L374)
- [config.py:1-30](file://backend/config.py#L1-L30)
- [useVideoProcessing.ts:1-438](file://frontend/src/lib/useVideoProcessing.ts#L1-L438)
- [PipelineVisualizer.tsx:1-181](file://frontend/src/components/archive/PipelineVisualizer.tsx#L1-L181)
- [APITransparencyPanel.tsx:1-170](file://frontend/src/components/archive/APITransparencyPanel.tsx#L1-L170)

**Section sources**
- [main.py:1-44](file://backend/main.py#L1-L44)
- [video.py:1-268](file://backend/routers/video.py#L1-L268)
- [config.py:1-30](file://backend/config.py#L1-L30)

## Core Components
- PipelineOrchestrator: Central coordinator that executes stages sequentially with async support, tracks progress, persists status, and emits WebSocket updates. Now uses local file paths for all stage operations with cooperative multitasking.
- Stage modules: Independent processing units for ingestion, visual analysis, audio transcription, face recognition, metadata structuring, and search index building, all enhanced with async implementations.
- Routers: REST endpoints for upload, status, metadata, transcript, search, and WebSocket progress streaming with async WebSocket handling.
- Frontend hooks and components: Real-time visualization of pipeline stages and results with async WebSocket subscriptions.

Key orchestration responsibilities:
- Initialize and persist status.json with async operations
- Compute stage progress percentages with cooperative yielding
- Forward progress via async WebSocket callback
- Aggregate results across stages with async coordination
- Persist combined results.json with async file operations
- Handle exceptions per stage and record errors with async error handling
- Manage local file path operations for all external API calls with non-blocking execution

**Section sources**
- [orchestrator.py:34-374](file://backend/pipeline/orchestrator.py#L34-L374)
- [video.py:25-120](file://backend/routers/video.py#L25-L120)

## Architecture Overview
The pipeline follows a strict sequential 6-stage workflow with enhanced asynchronous capabilities. The orchestrator coordinates each stage using cooperative multitasking, passing results forward and ensuring robust error handling. The frontend connects via WebSocket to receive live progress updates and later fetches structured metadata and transcripts. The orchestrator now processes local file paths directly, eliminating URL-based communication complexity. All stage operations are designed for non-blocking execution while maintaining the sequential processing guarantees.

```mermaid
sequenceDiagram
participant FE as "Frontend<br/>useVideoProcessing.ts"
participant API as "FastAPI Router<br/>video.py"
participant ORCH as "PipelineOrchestrator<br/>orchestrator.py"
participant ST1 as "Async Ingestion<br/>ingestion.py"
participant ST2 as "Async Visual Analysis<br/>visual_analysis.py"
participant ST3 as "Async Audio Analysis<br/>audio_analysis.py"
participant ST4 as "Async Face Recognition<br/>face_recognition.py"
participant ST5 as "Async Metadata Structuring<br/>metadata_structuring.py"
participant ST6 as "Async Search Index<br/>search_index.py"
FE->>API : "POST /api/video/upload"
API-->>FE : "200 OK {video_id, status}"
API->>ORCH : "process_video(video_id, video_path, ws_callback)"
ORCH->>ST1 : "await ingest_video(video_path, output_dir)"
ST1-->>ORCH : "results['ingestion']"
ORCH->>ST2 : "await analyze_video_visually(video_path, api_key, model, base_url)"
ST2-->>ORCH : "results['visual_analysis']"
ORCH->>ST3 : "await transcribe_audio(audio_path, api_key, model)"
ST3-->>ORCH : "results['transcript']"
ORCH->>ST4 : "await identify_faces(faces_detected, text_ocr, video_duration, api_key, model, base_url)"
ST4-->>ORCH : "results['faces']"
ORCH->>ST5 : "await structure_metadata(analysis_results, api_key, model, base_url)"
ST5-->>ORCH : "results['metadata']"
ORCH->>ST6 : "await search_index.add_video(video_id, segments)"
ST6-->>ORCH : "index updated"
ORCH-->>API : "final status.json + results.json"
API-->>FE : "WebSocket progress updates"
FE->>API : "GET /api/video/{video_id}/metadata"
FE->>API : "GET /api/video/{video_id}/transcript"
API-->>FE : "Structured metadata and transcript"
```

**Diagram sources**
- [video.py:39-120](file://backend/routers/video.py#L39-L120)
- [orchestrator.py:44-206](file://backend/pipeline/orchestrator.py#L44-L206)
- [ingestion.py:16-51](file://backend/pipeline/ingestion.py#L16-L51)
- [visual_analysis.py:55-120](file://backend/pipeline/visual_analysis.py#L55-L120)
- [audio_analysis.py:33-51](file://backend/pipeline/audio_analysis.py#L33-L51)
- [face_recognition.py:54-107](file://backend/pipeline/face_recognition.py#L54-L107)
- [metadata_structuring.py:81-163](file://backend/pipeline/metadata_structuring.py#L81-L163)
- [search_index.py:88-154](file://backend/pipeline/search_index.py#L88-L154)

## Enhanced Concurrency Model

The pipeline now implements a sophisticated concurrency model that balances sequential processing guarantees with asynchronous execution capabilities. This hybrid approach ensures predictable resource usage while maximizing throughput through cooperative multitasking.

### Key Concurrency Features:
- **Cooperative Multitasking**: Stages yield control to the event loop between operations to prevent blocking
- **Non-Blocking I/O**: All external API calls use async HTTP clients with proper timeout handling
- **Async File Operations**: File I/O operations leverage async file handling where appropriate
- **Thread Pool Integration**: CPU-intensive operations run in separate threads via asyncio event loop
- **Resource Isolation**: Each stage operates independently while sharing the orchestrator's event loop

### Concurrency Benefits:
- **Predictable Latency**: Sequential processing prevents resource contention between stages
- **Scalable Throughput**: Async operations allow multiple pipeline instances to run concurrently
- **Responsive Server**: Cooperative yielding keeps the FastAPI server responsive during long operations
- **Efficient Resource Usage**: Proper async handling reduces memory and CPU overhead

**Section sources**
- [orchestrator.py:206-282](file://backend/pipeline/orchestrator.py#L206-L282)
- [video.py:95-120](file://backend/routers/video.py#L95-L120)

## Cooperative Multitasking Implementation

The orchestrator implements cooperative multitasking through strategic yielding points that allow other coroutines to execute while maintaining processing continuity.

### Cooperative Yielding Strategy:
- **Stage Entry Points**: Each stage yields immediately upon entry to allow other tasks to run
- **Progress Updates**: WebSocket callbacks are awaited asynchronously to prevent blocking
- **Error Handling**: Exception handling yields control to prevent cascading failures
- **Result Persistence**: File I/O operations yield between writes to maintain responsiveness

### Implementation Details:
- **async def signatures**: All orchestrator methods use async definitions
- **await statements**: Stage functions are awaited with proper error handling
- **asyncio.sleep(0)**: Strategic yielding points ensure cooperative behavior
- **Non-blocking callbacks**: WebSocket callbacks are awaited without blocking the main loop

```mermaid
flowchart TD
Start(["process_video(video_id, video_path, ws_callback)"]) --> InitStatus["Initialize status.json<br/>pending stages, timestamps"]
InitStatus --> CreateOutputDir["Create output directory<br/>for video_id"]
CreateOutputDir --> LoopStages{"For each stage"}
LoopStages --> YieldControl["await asyncio.sleep(0)<br/>Cooperative yielding"]
YieldControl --> RunStage["_run_stage(stage_name, stage_index,<br/>total_stages, status, output_dir,<br/>results, ws_callback, coro_fn, result_key)"]
RunStage --> SaveStage["Save stage result file (optional)"]
SaveStage --> UpdateStatus["Update stage status + progress"]
UpdateStatus --> LoopStages
LoopStages --> |All stages done| Finalize["Finalize status (completed/completed_with_errors)<br/>persist results.json"]
Finalize --> Done(["Return"])
```

**Diagram sources**
- [orchestrator.py:44-206](file://backend/pipeline/orchestrator.py#L44-L206)
- [orchestrator.py:208-282](file://backend/pipeline/orchestrator.py#L208-L282)

**Section sources**
- [orchestrator.py:220-222](file://backend/pipeline/orchestrator.py#L220-L222)
- [orchestrator.py:206-282](file://backend/pipeline/orchestrator.py#L206-L282)

## Non-Blocking Execution Architecture

The pipeline implements a comprehensive non-blocking execution architecture that transforms traditional blocking operations into asynchronous equivalents while maintaining the sequential processing model.

### Non-Blocking Components:
- **Async HTTP Clients**: All external API calls use httpx.AsyncClient for non-blocking requests
- **Async File Operations**: File I/O leverages aiofiles for asynchronous file handling
- **Thread Pool Integration**: CPU-intensive operations run in separate threads via run_in_executor
- **Event Loop Coordination**: All async operations coordinate through the asyncio event loop
- **Timeout Management**: Proper timeout handling prevents hanging operations

### Execution Patterns:
- **Async I/O Bound Operations**: Network requests, file operations, and external API calls
- **Thread Pool Operations**: CPU-intensive tasks like video processing and audio analysis
- **Cooperative Yielding**: Strategic yielding points prevent blocking the event loop
- **Graceful Degradation**: Failed operations gracefully fall back to empty results

### Resource Management:
- **Connection Pooling**: HTTP clients reuse connections efficiently
- **Memory Management**: Async generators and proper cleanup prevent memory leaks
- **Thread Safety**: Thread pool operations are properly synchronized
- **Error Recovery**: Comprehensive error handling with retry mechanisms

**Section sources**
- [audio_analysis.py:6-277](file://backend/pipeline/audio_analysis.py#L6-L277)
- [face_recognition.py:6-319](file://backend/pipeline/face_recognition.py#L6-L319)
- [visual_analysis.py:7-344](file://backend/pipeline/visual_analysis.py#L7-L344)
- [ingestion.py:6-146](file://backend/pipeline/ingestion.py#L6-L146)
- [metadata_structuring.py:7-252](file://backend/pipeline/metadata_structuring.py#L7-L252)

## Detailed Component Analysis

### PipelineOrchestrator
The orchestrator defines the canonical stage order and manages execution, progress, and persistence with enhanced async capabilities. The orchestrator now processes local file paths directly instead of URL-based communication, with full async support.

- Stage names and order:
  1) ingestion
  2) visual_analysis
  3) audio_analysis
  4) face_recognition
  5) metadata_structuring
  6) search_index

- Execution pattern:
  - Initializes status.json with pending stages and timestamps
  - Computes progress as integer percentage based on stage index
  - Invokes _run_stage for each stage, forwarding a ws_callback
  - Aggregates results into a shared dictionary keyed by result_key
  - Builds searchable segments from earlier stages and adds to FAISS index
  - Finalizes status to completed or completed_with_errors, persists results.json

- Error handling:
  - Catches exceptions per stage, logs stack traces, marks stage as failed
  - Stores error messages under status.errors
  - Persists updated status and optional stage result file
  - Continues to next stage or completes pipeline accordingly

- Persistence:
  - Writes status.json after each stage and at completion
  - Writes individual stage result files and results.json at the end

- WebSocket callback contract:
  - Arguments: stage, message, progress, status
  - Sent to all registered WebSocket clients for the video_id

- Local file path processing:
  - All stage modules now accept local file paths instead of URLs
  - Audio extraction creates local audio.wav files for downstream stages
  - Visual analysis processes local video files directly
  - Face recognition loads reference databases from local JSON files
  - Metadata structuring loads taxonomy from local JSON files

```mermaid
flowchart TD
Start(["process_video(video_id, video_path, ws_callback)"]) --> InitStatus["Initialize status.json<br/>pending stages, timestamps"]
InitStatus --> CreateOutputDir["Create output directory<br/>for video_id"]
CreateOutputDir --> LoopStages{"For each stage"}
LoopStages --> RunStage["_run_stage(stage_name, stage_index,<br/>total_stages, status, output_dir,<br/>results, ws_callback, coro_fn, result_key)"]
RunStage --> SaveStage["Save stage result file (optional)"]
SaveStage --> UpdateStatus["Update stage status + progress"]
UpdateStatus --> LoopStages
LoopStages --> |All stages done| Finalize["Finalize status (completed/completed_with_errors)<br/>persist results.json"]
Finalize --> Done(["Return"])
```

**Diagram sources**
- [orchestrator.py:44-206](file://backend/pipeline/orchestrator.py#L44-L206)
- [orchestrator.py:208-282](file://backend/pipeline/orchestrator.py#L208-L282)

**Section sources**
- [orchestrator.py:24-31](file://backend/pipeline/orchestrator.py#L24-L31)
- [orchestrator.py:44-206](file://backend/pipeline/orchestrator.py#L44-L206)
- [orchestrator.py:208-282](file://backend/pipeline/orchestrator.py#L208-L282)

### Stage 1: Ingestion
- Extracts audio (16 kHz mono WAV), generates thumbnail, probes video metadata
- Returns duration, resolution, fps, codec, plus file paths for downstream stages
- Operates directly on local video file path with async ffmpeg integration
- Uses run_in_executor for CPU-intensive operations while maintaining async flow

**Section sources**
- [ingestion.py:16-51](file://backend/pipeline/ingestion.py#L16-L51)
- [ingestion.py:54-98](file://backend/pipeline/ingestion.py#L54-L98)
- [ingestion.py:100-146](file://backend/pipeline/ingestion.py#L100-L146)

### Stage 2: Visual Analysis
- Processes local video file directly using ffmpeg for keyframe extraction
- Encodes frames as base64 and sends to DashScope Qwen-VL for comprehensive scene/object/face/text detection
- Parses JSON from model response with robust fallbacks
- Returns scenes, faces, landmarks, OCR, sensitive content, and summaries
- Implements async HTTP client with proper timeout handling

**Section sources**
- [visual_analysis.py:55-120](file://backend/pipeline/visual_analysis.py#L55-L120)
- [visual_analysis.py:133-176](file://backend/pipeline/visual_analysis.py#L133-L176)

### Stage 3: Audio Analysis / Speech-to-Text
- Submits local audio file (WAV) directly to DashScope ASR paraformer-v2
- Polls task status with exponential backoff
- Fetches transcript JSON and normalizes to segments with speaker info and word timings
- Implements chunked processing with async file operations
- Uses run_in_executor for ffmpeg operations while maintaining async flow

**Section sources**
- [audio_analysis.py:33-51](file://backend/pipeline/audio_analysis.py#L33-L51)
- [audio_analysis.py:62-142](file://backend/pipeline/audio_analysis.py#L62-L142)
- [audio_analysis.py:145-241](file://backend/pipeline/audio_analysis.py#L145-L241)

### Stage 4: Face Recognition
- Matches detected faces against a reference database using Qwen text model
- Loads reference_faces.json from local data directory and compares descriptions to identify known figures
- Enriches face entries with name, role, confidence, and reasoning
- **Enhanced**: Now utilizes OCR text detection (text_ocr) for person identification fallback
- Implements async HTTP client with retry logic and exponential backoff
- Uses run_in_executor for file operations while maintaining async flow

**Section sources**
- [face_recognition.py:54-107](file://backend/pipeline/face_recognition.py#L54-L107)
- [face_recognition.py:110-196](file://backend/pipeline/face_recognition.py#L110-L196)
- [reference_faces.json:1-101](file://backend/data/reference_faces.json#L1-L101)

### Stage 5: Metadata Structuring
- Generates broadcast metadata (EBUCore XML, IPTC) from aggregated analysis results
- Uses iptc_taxonomy.json from local data directory for topic classification
- Returns bilingual metadata, sentiment tags, geographic tags, and mentioned persons
- **Enhanced**: Now includes comprehensive IPTC video metadata with rich topic codes and classifications
- Implements async HTTP client with proper error handling and retry logic
- Uses run_in_executor for file operations while maintaining async flow

**Section sources**
- [metadata_structuring.py:81-163](file://backend/pipeline/metadata_structuring.py#L81-L163)
- [metadata_structuring.py:166-208](file://backend/pipeline/metadata_structuring.py#L166-L208)
- [iptc_taxonomy.json:1-28](file://backend/data/iptc_taxonomy.json#L1-L28)

### Stage 6: Search Index
- Builds FAISS vector index using DashScope embeddings
- Converts scenes + transcript + identified persons into searchable segments
- **Enhanced**: Now builds richer search segments with IPTC metadata, titles, and thumbnails
- Supports semantic search across indexed videos
- Implements async embedding generation with batch processing
- Uses numpy fallback when FAISS is unavailable

**Section sources**
- [search_index.py:22-41](file://backend/pipeline/search_index.py#L22-L41)
- [search_index.py:88-154](file://backend/pipeline/search_index.py#L88-L154)
- [search_index.py:156-245](file://backend/pipeline/search_index.py#L156-L245)

### Enhanced Search Segment Building
The search segment building process has been significantly enhanced to include richer metadata:

- **IPTC Video Metadata**: Extracts headline and videoContent information for segment titles
- **Thumbnail Integration**: Adds thumbnail paths to all segment types for better UI experience
- **Person Identification**: Creates specialized person segments with role and timestamp information
- **Duration Handling**: Utilizes video duration for accurate timestamp calculations
- **Rich Metadata**: Includes scene types, person names, and thumbnail references in segment metadata

```mermaid
flowchart TD
Start(["Build Searchable Segments"]) --> ExtractMeta["Extract Metadata<br/>- IPTC headline<br/>- Thumbnail path<br/>- Person names"]
ExtractMeta --> ProcessScenes["Process Visual Scenes<br/>- Scene descriptions<br/>- Scene types<br/>- Timestamps"]
ProcessScenes --> ProcessTranscript["Process Transcript<br/>- Text segments<br/>- Word timings<br/>- Speaker info"]
ProcessTranscript --> ProcessFaces["Process Identified Faces<br/>- Person names<br/>- Roles<br/>- Appearances"]
ProcessFaces --> CombineSegments["Combine All Segments<br/>- Rich metadata<br/>- Thumbnails<br/>- Titles"]
CombineSegments --> ReturnSegments["Return Enhanced Segments"]
```

**Diagram sources**
- [orchestrator.py:307-359](file://backend/pipeline/orchestrator.py#L307-L359)

**Section sources**
- [orchestrator.py:307-359](file://backend/pipeline/orchestrator.py#L307-L359)

### WebSocket Progress Streaming
- Router registers WebSocket connections per video_id
- Orchestrator's ws_callback forwards progress updates to all connected clients
- Frontend hook subscribes to /ws/pipeline/{video_id} and updates stage statuses
- Implements async WebSocket handling with proper connection management

```mermaid
sequenceDiagram
participant FE as "Frontend<br/>useVideoProcessing.ts"
participant WS as "WebSocket<br/>/ws/pipeline/{video_id}"
participant API as "Router<br/>video.py"
participant ORCH as "Orchestrator<br/>orchestrator.py"
FE->>WS : "Connect"
API->>API : "Register client in _active_ws[video_id]"
API->>ORCH : "process_video(..., ws_callback)"
ORCH->>API : "await ws_callback(stage, message, progress, status)"
API->>WS : "await ws.send_json(payload)"
WS-->>FE : "Receive progress event"
FE->>API : "Optionally poll /api/video/{video_id}/status"
```

**Diagram sources**
- [video.py:220-268](file://backend/routers/video.py#L220-L268)
- [video.py:95-120](file://backend/routers/video.py#L95-L120)
- [orchestrator.py:228-282](file://backend/pipeline/orchestrator.py#L228-L282)

**Section sources**
- [video.py:220-268](file://backend/routers/video.py#L220-L268)
- [video.py:95-120](file://backend/routers/video.py#L95-L120)
- [useVideoProcessing.ts:215-276](file://frontend/src/lib/useVideoProcessing.ts#L215-L276)

### Status Management
- Initial status created on upload with queued state
- Orchestrator maintains status.json with:
  - video_id, status, progress, stages map, timestamps, errors
- Frontend polls status via REST when WebSocket is unavailable

**Section sources**
- [video.py:64-82](file://backend/routers/video.py#L64-L82)
- [orchestrator.py:63-71](file://backend/pipeline/orchestrator.py#L63-L71)
- [video.py:124-138](file://backend/routers/video.py#L124-L138)

## Dependency Analysis
The orchestrator depends on stage modules and the SearchIndex. The router composes the orchestrator and exposes REST/WebSocket endpoints. The frontend consumes these endpoints and renders progress and results. All stage modules now operate on local file paths instead of URLs with full async support.

```mermaid
graph LR
ORCH["PipelineOrchestrator<br/>orchestrator.py"] --> ST1["ingestion.py"]
ORCH --> ST2["visual_analysis.py"]
ORCH --> ST3["audio_analysis.py"]
ORCH --> ST4["face_recognition.py"]
ORCH --> ST5["metadata_structuring.py"]
ORCH --> ST6["search_index.py"]
ROUTER["Routers<br/>video.py"] --> ORCH
ROUTER --> CFG["Config<br/>config.py"]
FRONT["Frontend<br/>useVideoProcessing.ts"] --> ROUTER
```

**Diagram sources**
- [orchestrator.py:14-20](file://backend/pipeline/orchestrator.py#L14-L20)
- [video.py:17-19](file://backend/routers/video.py#L17-L19)
- [config.py:4-20](file://backend/config.py#L4-L20)
- [useVideoProcessing.ts:1-10](file://frontend/src/lib/useVideoProcessing.ts#L1-L10)

**Section sources**
- [orchestrator.py:14-20](file://backend/pipeline/orchestrator.py#L14-L20)
- [video.py:17-19](file://backend/routers/video.py#L17-L19)
- [config.py:4-20](file://backend/config.py#L4-L20)

## Performance Considerations
- Sequential processing characteristics:
  - Predictable resource usage per stage with async optimizations
  - Lower concurrent memory footprint compared to parallel pipelines
  - Longer total processing time due to lack of overlap, but with better resource isolation
- Enhanced async I/O optimization:
  - Direct file path processing reduces network overhead
  - Async HTTP clients improve connection reuse and reduce latency
  - Thread pool integration allows CPU-intensive operations without blocking
  - Cooperative yielding prevents event loop starvation
- External API dependencies:
  - Visual analysis, ASR, embedding calls are rate-limited and may require retries
  - Async HTTP clients handle timeouts more efficiently
  - Exponential backoff with async sleep prevents busy-waiting
- WebSocket scaling:
  - Each stage update triggers async send_json to all registered clients
  - Proper connection management prevents resource leaks
  - Async WebSocket handling scales better under high concurrency
- FAISS index:
  - Index loading/saving occurs on add_video and search with async operations
  - Memory usage grows with indexed segments; optimize batch sizes and refresh cadence
  - Async embedding generation improves throughput for large datasets
- Enhanced OCR Processing:
  - OCR text detection extraction provides additional person identification capabilities
  - Video duration handling ensures accurate timestamp processing for OCR results
  - Rich metadata integration improves search accuracy and user experience

## Troubleshooting Guide
Common issues and remedies:
- Missing API keys:
  - Many stages return empty results with error markers when API keys are absent
  - Verify environment variables and settings
- FFmpeg failures:
  - Probe, audio extraction, and thumbnail generation log errors and may raise exceptions
  - Ensure FFmpeg is installed and accessible
  - Check async thread pool configuration for CPU-intensive operations
- ASR task timeouts:
  - Long audio may exceed polling limits; adjust expectations or split input
  - Async HTTP clients handle timeouts more gracefully than blocking calls
- WebSocket disconnects:
  - Router removes disconnected clients automatically; frontend falls back to REST polling
  - Async WebSocket handling prevents connection leaks
- FAISS availability:
  - If FAISS is not installed, search/indexing is disabled; install faiss-cpu for full functionality
  - Async fallback to numpy implementation ensures graceful degradation
- Local file permissions:
  - Ensure the application has read/write permissions for the UPLOAD_DIR
  - Verify sufficient disk space for temporary files during processing
- Async operation failures:
  - Check event loop configuration and thread pool size
  - Monitor async resource usage and prevent memory leaks
  - Implement proper async context management
- OCR Text Detection Issues:
  - Visual analysis may fail to detect OCR text in certain video conditions
  - Face recognition can fallback to OCR-based identification when reference database is unavailable
  - Video duration probing failures can impact OCR timestamp accuracy

**Section sources**
- [visual_analysis.py:61-63](file://backend/pipeline/visual_analysis.py#L61-L63)
- [audio_analysis.py:40-42](file://backend/pipeline/audio_analysis.py#L40-L42)
- [face_recognition.py:76-81](file://backend/pipeline/face_recognition.py#L76-L81)
- [metadata_structuring.py:99-101](file://backend/pipeline/metadata_structuring.py#L99-L101)
- [search_index.py:61-64](file://backend/pipeline/search_index.py#L61-L64)
- [video.py:116-120](file://backend/routers/video.py#L116-L120)

## Conclusion
The PipelineOrchestrator provides a robust, transparent, and resilient framework for sequential video processing with enhanced concurrency capabilities. Its explicit stage ordering, comprehensive error handling, and real-time progress streaming enable reliable operation and excellent observability. The switch to local file path processing eliminates URL-based communication complexity and reduces potential failure points. The enhanced async implementation with cooperative multitasking and non-blocking execution architecture significantly improves throughput while maintaining the predictable resource usage characteristics of sequential processing. 

**Recent Enhancements:**
- **OCR Text Detection**: Enhanced face recognition with OCR-based person identification fallback
- **Improved Video Duration Handling**: Robust ffprobe integration for accurate duration processing
- **Richer Metadata**: Comprehensive IPTC video metadata integration with titles and thumbnails
- **Enhanced Search Segments**: Improved search index building with enriched segment metadata

While sequential processing trades throughput for simplicity and predictability, it remains practical for most media archival scenarios and can be scaled by increasing server capacity or splitting large inputs. The async enhancements make the system more responsive and efficient under various load conditions.

## Appendices

### Example: Pipeline Initialization and Execution Flow
- Upload a video via POST /api/video/upload; backend saves file and queues processing
- Background task invokes process_video with ws_callback
- Orchestrator runs ingestion → visual_analysis → audio_analysis → face_recognition → metadata_structuring → search_index
- Frontend receives WebSocket updates and switches to results view upon completion
- Users can fetch metadata and transcript via GET endpoints

**Section sources**
- [video.py:39-92](file://backend/routers/video.py#L39-L92)
- [video.py:95-120](file://backend/routers/video.py#L95-L120)
- [useVideoProcessing.ts:162-211](file://frontend/src/lib/useVideoProcessing.ts#L162-L211)

### Example: Status Monitoring
- Connect to /ws/pipeline/{video_id} to receive live progress
- Alternatively poll /api/video/{video_id}/status for current stage states
- After completion, fetch /api/video/{video_id}/metadata and /api/video/{video_id}/transcript

**Section sources**
- [video.py:220-268](file://backend/routers/video.py#L220-L268)
- [video.py:124-138](file://backend/routers/video.py#L124-L138)
- [video.py:143-174](file://backend/routers/video.py#L143-L174)
- [video.py:179-195](file://backend/routers/video.py#L179-L195)

### Frontend Visualization
- PipelineVisualizer displays stage icons, statuses, elapsed times, and progress bars
- APITransparencyPanel aggregates API call metrics for transparency

**Section sources**
- [PipelineVisualizer.tsx:88-181](file://frontend/src/components/archive/PipelineVisualizer.tsx#L88-L181)
- [APITransparencyPanel.tsx:20-170](file://frontend/src/components/archive/APITransparencyPanel.tsx#L20-L170)
- [useVideoProcessing.ts:106-118](file://frontend/src/lib/useVideoProcessing.ts#L106-L118)

### Enhanced Concurrency Examples
- **Async HTTP Client Usage**: All external API calls use httpx.AsyncClient with proper timeout handling
- **Thread Pool Integration**: CPU-intensive operations run via run_in_executor while maintaining async flow
- **Cooperative Yielding**: Strategic asyncio.sleep(0) calls ensure other coroutines can execute
- **Async File Operations**: aiofiles integration enables non-blocking file I/O operations
- **WebSocket Scaling**: Async WebSocket handling scales better under high concurrency scenarios

**Section sources**
- [audio_analysis.py:228-263](file://backend/pipeline/audio_analysis.py#L228-L263)
- [face_recognition.py:138-185](file://backend/pipeline/face_recognition.py#L138-L185)
- [visual_analysis.py:133-184](file://backend/pipeline/visual_analysis.py#L133-L184)
- [ingestion.py:57-121](file://backend/pipeline/ingestion.py#L57-L121)
- [metadata_structuring.py:125-161](file://backend/pipeline/metadata_structuring.py#L125-L161)

### Enhanced OCR and Metadata Processing
- **OCR Text Detection**: Visual analysis now extracts on-screen text for person identification
- **IPTC Metadata Integration**: Rich video metadata with topic codes and classifications
- **Thumbnail Enhancement**: All search segments now include thumbnail references
- **Person Identification Fallback**: OCR-based identification when reference database is unavailable

**Section sources**
- [visual_analysis.py:41-43](file://backend/pipeline/visual_analysis.py#L41-L43)
- [face_recognition.py:191-210](file://backend/pipeline/face_recognition.py#L191-L210)
- [metadata_structuring.py:47-64](file://backend/pipeline/metadata_structuring.py#L47-L64)
- [orchestrator.py:313-318](file://backend/pipeline/orchestrator.py#L313-L318)
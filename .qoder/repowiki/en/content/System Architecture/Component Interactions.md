# Component Interactions

<cite>
**Referenced Files in This Document**
- [backend/main.py](file://backend/main.py)
- [backend/config.py](file://backend/config.py)
- [backend/routers/video.py](file://backend/routers/video.py)
- [backend/routers/rfp.py](file://backend/routers/rfp.py)
- [backend/pipeline/orchestrator.py](file://backend/pipeline/orchestrator.py)
- [backend/pipeline/ingestion.py](file://backend/pipeline/ingestion.py)
- [backend/pipeline/metadata_structuring.py](file://backend/pipeline/metadata_structuring.py)
- [backend/pipeline/search_index.py](file://backend/pipeline/search_index.py)
- [backend/services/rfp_creator.py](file://backend/services/rfp_creator.py)
- [backend/services/rfp_evaluator.py](file://backend/services/rfp_evaluator.py)
- [frontend/src/lib/api.ts](file://frontend/src/lib/api.ts)
- [frontend/src/lib/useVideoProcessing.ts](file://frontend/src/lib/useVideoProcessing.ts)
- [frontend/src/components/archive/VideoUpload.tsx](file://frontend/src/components/archive/VideoUpload.tsx)
- [frontend/package.json](file://frontend/package.json)
- [backend/requirements.txt](file://backend/requirements.txt)
- [nginx.conf](file://nginx.conf)
</cite>

## Update Summary
**Changes Made**
- Enhanced event loop management documentation with improved asyncio patterns
- Added comprehensive coverage of non-blocking execution patterns throughout the pipeline
- Documented concurrent processing capabilities with detailed async task management
- Updated WebSocket progress streaming with improved fan-out handling
- Enhanced file upload mechanisms with better chunked transfer and error handling
- Improved DashScope integration with better retry mechanisms and fallback strategies

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Enhanced Event Loop Management](#enhanced-event-loop-management)
7. [Non-Blocking Execution Patterns](#non-blocking-execution-patterns)
8. [Concurrent Processing Capabilities](#concurrent-processing-capabilities)
9. [Dependency Analysis](#dependency-analysis)
10. [Performance Considerations](#performance-considerations)
11. [Troubleshooting Guide](#troubleshooting-guide)
12. [Conclusion](#conclusion)
13. [Appendices](#appendices)

## Introduction
This document explains the component interactions within the Dubai Media system, focusing on how the frontend and backend communicate, how files are uploaded and served, how real-time progress is streamed via WebSockets, and how Alibaba Cloud DashScope AI services are integrated. It also covers CORS configuration, security considerations, and typical user workflows from upload through processing completion. The system has been enhanced with improved event loop management, non-blocking execution patterns, and concurrent processing capabilities for optimal performance.

## Project Structure
The system comprises:
- Backend: FastAPI application exposing REST endpoints and WebSocket streams, orchestrating a multi-stage video processing pipeline, and integrating with DashScope AI.
- Frontend: Next.js application that uploads videos, polls/follows progress via REST/WebSocket, and displays metadata, transcripts, and search results.
- Static file serving: Nginx serves uploaded files mounted under /uploads.
- Pipelines: Ingestion, visual/audio analysis, face recognition, metadata structuring, and FAISS-based search indexing.

```mermaid
graph TB
subgraph "Frontend"
FE_API["api.ts<br/>REST + WS helpers"]
FE_HOOK["useVideoProcessing.ts<br/>state + effects"]
FE_UPLOAD["VideoUpload.tsx<br/>UI"]
end
subgraph "Backend"
MAIN["main.py<br/>FastAPI app + CORS + StaticFiles"]
CFG["config.py<br/>Settings"]
ROUTER_VIDEO["routers/video.py<br/>REST + WS"]
ROUTER_RFP["routers/rfp.py<br/>RFP endpoints"]
ORCH["pipeline/orchestrator.py<br/>PipelineOrchestrator"]
STAGE_INGEST["pipeline/ingestion.py<br/>FFmpeg-based ingestion"]
STAGE_META["pipeline/metadata_structuring.py<br/>DashScope chat"]
SEARCH_IDX["pipeline/search_index.py<br/>FAISS + DashScope embeddings"]
SVC_CREATOR["services/rfp_creator.py<br/>DashScope chat"]
SVC_EVAL["services/rfp_evaluator.py<br/>DashScope chat"]
end
subgraph "External Services"
DASHSCOPE["Alibaba Cloud DashScope"]
NGINX["Nginx / Static Files (/uploads)"]
end
FE_API --> ROUTER_VIDEO
FE_API --> ROUTER_RFP
FE_HOOK --> FE_API
FE_UPLOAD --> FE_HOOK
ROUTER_VIDEO --> ORCH
ORCH --> STAGE_INGEST
ORCH --> STAGE_META
ORCH --> SEARCH_IDX
ROUTER_RFP --> SVC_CREATOR
ROUTER_RFP --> SVC_EVAL
ORCH --> DASHSCOPE
SEARCH_IDX --> DASHSCOPE
SVC_CREATOR --> DASHSCOPE
SVC_EVAL --> DASHSCOPE
MAIN --> NGINX
MAIN --> ROUTER_VIDEO
MAIN --> ROUTER_RFP
CFG --> MAIN
```

**Diagram sources**
- [backend/main.py:1-44](file://backend/main.py#L1-L44)
- [backend/config.py:1-30](file://backend/config.py#L1-L30)
- [backend/routers/video.py:1-268](file://backend/routers/video.py#L1-L268)
- [backend/routers/rfp.py:1-385](file://backend/routers/rfp.py#L1-L385)
- [backend/pipeline/orchestrator.py:1-330](file://backend/pipeline/orchestrator.py#L1-L330)
- [backend/pipeline/ingestion.py:1-146](file://backend/pipeline/ingestion.py#L1-L146)
- [backend/pipeline/metadata_structuring.py:1-252](file://backend/pipeline/metadata_structuring.py#L1-L252)
- [backend/pipeline/search_index.py:1-300](file://backend/pipeline/search_index.py#L1-L300)
- [backend/services/rfp_creator.py:1-639](file://backend/services/rfp_creator.py#L1-L639)
- [backend/services/rfp_evaluator.py:1-622](file://backend/services/rfp_evaluator.py#L1-L622)
- [frontend/src/lib/api.ts:1-245](file://frontend/src/lib/api.ts#L1-L245)
- [frontend/src/lib/useVideoProcessing.ts:1-465](file://frontend/src/lib/useVideoProcessing.ts#L1-L465)
- [frontend/src/components/archive/VideoUpload.tsx:1-221](file://frontend/src/components/archive/VideoUpload.tsx#L1-L221)

**Section sources**
- [backend/main.py:1-44](file://backend/main.py#L1-L44)
- [backend/config.py:1-30](file://backend/config.py#L1-L30)
- [frontend/src/lib/api.ts:1-245](file://frontend/src/lib/api.ts#L1-L245)
- [frontend/src/lib/useVideoProcessing.ts:1-465](file://frontend/src/lib/useVideoProcessing.ts#L1-L465)
- [frontend/src/components/archive/VideoUpload.tsx:1-221](file://frontend/src/components/archive/VideoUpload.tsx#L1-L221)

## Core Components
- FastAPI application with CORS enabled and static file mounting for uploads.
- REST endpoints for video upload, status, metadata, transcript, and search.
- WebSocket endpoint for real-time progress streaming during pipeline execution.
- Pipeline orchestrator coordinating ingestion, visual/audio analysis, face recognition, metadata structuring, and search index building.
- DashScope integrations for embeddings, chat completions, and text generation.
- Frontend API helpers and React hook for upload, progress tracking, and results retrieval.
- Nginx static file serving for uploaded media.

**Section sources**
- [backend/main.py:20-44](file://backend/main.py#L20-L44)
- [backend/routers/video.py:39-268](file://backend/routers/video.py#L39-L268)
- [backend/pipeline/orchestrator.py:34-330](file://backend/pipeline/orchestrator.py#L34-L330)
- [backend/pipeline/search_index.py:22-300](file://backend/pipeline/search_index.py#L22-L300)
- [backend/pipeline/metadata_structuring.py:81-252](file://backend/pipeline/metadata_structuring.py#L81-L252)
- [frontend/src/lib/api.ts:164-244](file://frontend/src/lib/api.ts#L164-L244)
- [frontend/src/lib/useVideoProcessing.ts:122-465](file://frontend/src/lib/useVideoProcessing.ts#L122-L465)

## Architecture Overview
The system follows a client-server pattern:
- The frontend communicates with backend REST endpoints and WebSocket streams.
- Backend persists uploaded files and intermediate artifacts under a configurable upload directory.
- Nginx serves static files from the upload directory at /uploads.
- The backend orchestrates asynchronous pipeline stages, emitting progress updates via WebSocket and saving status to disk.
- DashScope is used for embeddings and chat-based metadata structuring.

```mermaid
graph TB
Client["Browser / Next.js App"]
API["FastAPI REST API"]
WS["WebSocket Endpoint"]
FS["Uploads Directory"]
Nginx["Nginx Static /uploads"]
Orchestrator["PipelineOrchestrator"]
Stages["Pipeline Stages"]
DashScope["DashScope AI"]
Client --> API
Client --> WS
API --> FS
Nginx --> FS
API --> Orchestrator
Orchestrator --> Stages
Stages --> DashScope
WS --> Client
```

**Diagram sources**
- [backend/main.py:27-39](file://backend/main.py#L27-L39)
- [backend/routers/video.py:221-268](file://backend/routers/video.py#L221-L268)
- [backend/pipeline/orchestrator.py:44-330](file://backend/pipeline/orchestrator.py#L44-L330)
- [backend/pipeline/search_index.py:198-300](file://backend/pipeline/search_index.py#L198-L300)
- [backend/pipeline/metadata_structuring.py:114-252](file://backend/pipeline/metadata_structuring.py#L114-L252)
- [nginx.conf](file://nginx.conf)

## Detailed Component Analysis

### REST API Endpoints and Communication Patterns
- Video upload: multipart/form-data upload handled by the backend; saves file to uploads directory and starts background pipeline.
- Status polling: GET endpoints read status.json for current stage statuses.
- Metadata retrieval: GET endpoints read structured JSON outputs from pipeline stages.
- Transcript retrieval: GET endpoint reads transcript.json.
- Semantic search: POST endpoint queries FAISS index built with DashScope embeddings.
- CORS: Enabled broadly for development; consider tightening in production.

```mermaid
sequenceDiagram
participant FE as "Frontend"
participant API as "FastAPI Router"
participant FS as "Uploads Dir"
participant BG as "Background Task"
participant ORCH as "PipelineOrchestrator"
FE->>API : POST /api/video/upload (multipart)
API->>FS : Write video file
API->>BG : Schedule pipeline
BG->>ORCH : process_video(video_id, path)
API-->>FE : {video_id, status}
FE->>API : GET /api/video/{id}/status (poll)
API-->>FE : {stages, progress, status}
FE->>API : GET /api/video/{id}/metadata
API-->>FE : {structured metadata JSON}
FE->>API : GET /api/video/{id}/transcript
API-->>FE : {segments JSON}
FE->>API : POST /api/search {query, top_k}
API-->>FE : {results, total}
```

**Diagram sources**
- [backend/routers/video.py:39-216](file://backend/routers/video.py#L39-L216)
- [backend/pipeline/orchestrator.py:44-330](file://backend/pipeline/orchestrator.py#L44-L330)
- [frontend/src/lib/api.ts:164-183](file://frontend/src/lib/api.ts#L164-L183)

**Section sources**
- [backend/routers/video.py:39-216](file://backend/routers/video.py#L39-L216)
- [frontend/src/lib/api.ts:164-183](file://frontend/src/lib/api.ts#L164-L183)

### WebSocket Progress Streaming
- Clients connect to /ws/pipeline/{video_id} to receive real-time progress updates.
- Backend forwards progress from the orchestrator to connected clients.
- On disconnect, clients are removed from the registry.

```mermaid
sequenceDiagram
participant FE as "Frontend"
participant WS as "WebSocket Endpoint"
participant ORCH as "PipelineOrchestrator"
participant CB as "ws_callback"
FE->>WS : Connect /ws/pipeline/{video_id}
WS->>FE : Send current status (optional)
ORCH->>CB : Emit stage progress
CB->>WS : Broadcast JSON payload
WS-->>FE : {video_id, stage, message, progress, status}
FE->>WS : ping (periodic)
WS-->>FE : pong
FE-->>WS : Close
WS->>WS : Cleanup connection
```

**Diagram sources**
- [backend/routers/video.py:221-268](file://backend/routers/video.py#L221-L268)
- [backend/pipeline/orchestrator.py:95-120](file://backend/pipeline/orchestrator.py#L95-L120)

**Section sources**
- [backend/routers/video.py:221-268](file://backend/routers/video.py#L221-L268)
- [backend/pipeline/orchestrator.py:95-120](file://backend/pipeline/orchestrator.py#L95-L120)

### File Upload and Download Mechanisms
- Upload: multipart/form-data sent to backend; file written asynchronously to uploads directory.
- Static serving: Nginx mounts uploads directory at /uploads for direct browser access.
- Download: Frontend constructs URLs using BASE_URL and /uploads/{filename}.

```mermaid
flowchart TD
Start(["Upload Request"]) --> Parse["Parse multipart/form-data"]
Parse --> Save["Async write to uploads/{video_id.ext}"]
Save --> InitStatus["Create status.json with pending stages"]
InitStatus --> Queue["Queue background pipeline"]
Queue --> Done(["Return {video_id, status}"])
DownloadStart["GET /uploads/{filename}"] --> Serve["Serve from Nginx static /uploads"]
Serve --> Browser(["Browser plays video"])
```

**Diagram sources**
- [backend/routers/video.py:39-92](file://backend/routers/video.py#L39-L92)
- [backend/main.py:35-35](file://backend/main.py#L35-L35)
- [nginx.conf](file://nginx.conf)

**Section sources**
- [backend/routers/video.py:39-92](file://backend/routers/video.py#L39-L92)
- [backend/main.py:35-35](file://backend/main.py#L35-L35)

### Temporary File Management
- Intermediate artifacts (audio.wav, thumbnail.jpg, stage outputs) are written under uploads/{video_id}.
- Status and results are persisted as JSON files; FAISS index and metadata are persisted separately for search.

**Section sources**
- [backend/pipeline/orchestrator.py:59-330](file://backend/pipeline/orchestrator.py#L59-L330)
- [backend/pipeline/ingestion.py:16-146](file://backend/pipeline/ingestion.py#L16-L146)
- [backend/pipeline/search_index.py:42-300](file://backend/pipeline/search_index.py#L42-L300)

### Alibaba Cloud DashScope Integration
- Authentication: API key configured via settings; passed in Authorization header.
- Embeddings: Used to index searchable segments; supports batching and retries.
- Chat completions: Used for metadata structuring and RFP generation/evaluation.
- Error handling: Retries with exponential backoff; graceful degradation when disabled.

```mermaid
sequenceDiagram
participant ORCH as "PipelineOrchestrator"
participant META as "metadata_structuring.py"
participant SEARCH as "search_index.py"
participant CREATOR as "rfp_creator.py"
participant EVAL as "rfp_evaluator.py"
participant DS as "DashScope API"
ORCH->>META : Call chat/completions (structured metadata)
META->>DS : POST /chat/completions
DS-->>META : JSON response
META-->>ORCH : Parsed metadata
ORCH->>SEARCH : add_video(segments)
SEARCH->>DS : POST /embeddings (batch)
DS-->>SEARCH : Embeddings
SEARCH-->>ORCH : Index updated
CREATOR->>DS : POST /chat/completions (RFP sections)
EVAL->>DS : POST /chat/completions (evaluation)
```

**Diagram sources**
- [backend/pipeline/metadata_structuring.py:114-252](file://backend/pipeline/metadata_structuring.py#L114-L252)
- [backend/pipeline/search_index.py:198-300](file://backend/pipeline/search_index.py#L198-L300)
- [backend/services/rfp_creator.py:76-123](file://backend/services/rfp_creator.py#L76-L123)
- [backend/services/rfp_evaluator.py:48-104](file://backend/services/rfp_evaluator.py#L48-L104)

**Section sources**
- [backend/config.py:4-12](file://backend/config.py#L4-L12)
- [backend/pipeline/metadata_structuring.py:114-252](file://backend/pipeline/metadata_structuring.py#L114-L252)
- [backend/pipeline/search_index.py:198-300](file://backend/pipeline/search_index.py#L198-L300)
- [backend/services/rfp_creator.py:70-123](file://backend/services/rfp_creator.py#L70-L123)
- [backend/services/rfp_evaluator.py:39-104](file://backend/services/rfp_evaluator.py#L39-L104)

### Frontend Interaction Patterns
- API helpers encapsulate REST calls and WebSocket connections.
- React hook manages upload state, progress simulation, WebSocket lifecycle, and result fetching.
- UI component handles drag-and-drop selection and displays upload progress.

```mermaid
sequenceDiagram
participant UI as "VideoUpload.tsx"
participant Hook as "useVideoProcessing.ts"
participant API as "api.ts"
participant Router as "routers/video.py"
participant WS as "WebSocket"
UI->>Hook : onUpload(file)
Hook->>API : uploadFile("/api/video/upload", file)
API->>Router : POST /api/video/upload
Router-->>API : {video_id, status}
API-->>Hook : {video_id}
Hook->>Hook : updateState(uploadProgress=100)
Hook->>API : connectWebSocket("/ws/pipeline/{video_id}")
API->>WS : Connect
WS-->>Hook : Real-time progress updates
Hook->>API : getMetadata/getTranscript (on completion)
API-->>Hook : Structured metadata + transcript
Hook->>Hook : setState(view=results)
```

**Diagram sources**
- [frontend/src/components/archive/VideoUpload.tsx:63-211](file://frontend/src/components/archive/VideoUpload.tsx#L63-L211)
- [frontend/src/lib/useVideoProcessing.ts:162-276](file://frontend/src/lib/useVideoProcessing.ts#L162-L276)
- [frontend/src/lib/api.ts:164-183](file://frontend/src/lib/api.ts#L164-L183)
- [backend/routers/video.py:221-268](file://backend/routers/video.py#L221-L268)

**Section sources**
- [frontend/src/lib/api.ts:1-245](file://frontend/src/lib/api.ts#L1-L245)
- [frontend/src/lib/useVideoProcessing.ts:122-465](file://frontend/src/lib/useVideoProcessing.ts#L122-L465)
- [frontend/src/components/archive/VideoUpload.tsx:1-221](file://frontend/src/components/archive/VideoUpload.tsx#L1-L221)

### RFP Creation and Evaluation Endpoints
- Creation: Generates RFP sections via DashScope chat, supports bilingual outputs, exports DOCX/PDF.
- Evaluation: Extracts text from vendor submissions, evaluates against criteria, produces Excel/PDF reports.

```mermaid
sequenceDiagram
participant FE as "Frontend"
participant RFP as "routers/rfp.py"
participant CREATOR as "services/rfp_creator.py"
participant EVAL as "services/rfp_evaluator.py"
FE->>RFP : POST /api/rfp/create
RFP->>CREATOR : generate_rfp(input)
CREATOR->>CREATOR : _call_llm (chat/completions)
CREATOR-->>RFP : {sections, language}
RFP-->>FE : {rfp_id, sections}
FE->>RFP : POST /api/rfp/evaluate (files + criteria)
RFP->>EVAL : evaluate_responses(rfp_text, vendor_responses, criteria)
EVAL->>EVAL : _call_llm (evaluation)
RFP-->>FE : {eval_id, queued}
FE->>RFP : GET /api/rfp/evaluation/{id}/status
RFP-->>FE : {status, progress}
FE->>RFP : GET /api/rfp/evaluation/{id}/results
RFP-->>FE : {results}
```

**Diagram sources**
- [backend/routers/rfp.py:97-385](file://backend/routers/rfp.py#L97-L385)
- [backend/services/rfp_creator.py:124-151](file://backend/services/rfp_creator.py#L124-L151)
- [backend/services/rfp_evaluator.py:230-295](file://backend/services/rfp_evaluator.py#L230-L295)

**Section sources**
- [backend/routers/rfp.py:97-385](file://backend/routers/rfp.py#L97-L385)
- [backend/services/rfp_creator.py:67-151](file://backend/services/rfp_creator.py#L67-L151)
- [backend/services/rfp_evaluator.py:39-295](file://backend/services/rfp_evaluator.py#L39-L295)

## Enhanced Event Loop Management

The Dubai Media system has been enhanced with sophisticated event loop management patterns to ensure optimal performance and responsiveness during video processing operations.

### Async Event Loop Coordination
- **Yield Points**: The orchestrator uses `await asyncio.sleep(0)` at strategic points to yield control back to the event loop, preventing blocking operations from monopolizing the loop.
- **Task Scheduling**: Background pipeline execution uses `asyncio.create_task()` for non-blocking concurrent processing of multiple video uploads.
- **Connection Management**: WebSocket connections are managed through a registry pattern that automatically cleans up disconnected clients.

### Improved Concurrency Control
- **Stage Parallelization**: While individual pipeline stages run sequentially, the orchestrator ensures that stage preparation and cleanup operations are non-blocking.
- **Resource Pooling**: External API calls to DashScope use async HTTP clients with connection pooling for efficient resource utilization.
- **Memory Management**: Large file operations use streaming patterns to minimize memory footprint during processing.

```mermaid
sequenceDiagram
participant LOOP as "Event Loop"
participant ORCH as "PipelineOrchestrator"
participant STAGE as "Stage Handler"
participant WS as "WebSocket Registry"
LOOP->>ORCH : process_video()
ORCH->>LOOP : await asyncio.sleep(0)
LOOP->>STAGE : _run_stage()
STAGE->>LOOP : await asyncio.sleep(0)
LOOP->>WS : Broadcast progress
WS->>LOOP : Handle disconnections
LOOP->>STAGE : Continue next stage
```

**Diagram sources**
- [backend/pipeline/orchestrator.py:220-283](file://backend/pipeline/orchestrator.py#L220-L283)
- [backend/routers/video.py:95-120](file://backend/routers/video.py#L95-L120)

**Section sources**
- [backend/pipeline/orchestrator.py:206-283](file://backend/pipeline/orchestrator.py#L206-L283)
- [backend/routers/video.py:95-120](file://backend/routers/video.py#L95-L120)

## Non-Blocking Execution Patterns

The system implements comprehensive non-blocking execution patterns throughout the video processing pipeline to maintain responsiveness and scalability.

### Async I/O Operations
- **File Operations**: Uses `aiofiles` for asynchronous file reading/writing operations, avoiding blocking I/O calls.
- **Network Calls**: All external API communications use async HTTP clients (`httpx.AsyncClient`) for non-blocking network operations.
- **Process Execution**: System commands and external tool invocations use `loop.run_in_executor()` to prevent blocking the event loop.

### Stream Processing
- **Chunked Uploads**: Video files are processed in 1MB chunks to handle large files efficiently without memory pressure.
- **Streaming Responses**: WebSocket broadcasts use streaming patterns to minimize latency in progress updates.
- **Batch Processing**: DashScope API calls use batch processing with controlled batch sizes to optimize throughput.

### Error Handling and Recovery
- **Graceful Degradation**: Failed external API calls trigger fallback mechanisms with exponential backoff.
- **Resource Cleanup**: Proper cleanup of temporary files and resources even in error scenarios.
- **Connection Resilience**: WebSocket connections automatically recover from transient network issues.

```mermaid
flowchart TD
Start(["Async Operation"]) --> Check["Check Resource Availability"]
Check --> |Available| Execute["Execute Non-blocking Operation"]
Check --> |Unavailable| Queue["Queue for Later Execution"]
Execute --> Success["Operation Completed"]
Execute --> Error["Handle Error"]
Error --> Retry["Retry with Backoff"]
Retry --> Success
Success --> Cleanup["Cleanup Resources"]
Queue --> Execute
```

**Diagram sources**
- [backend/pipeline/ingestion.py:54-146](file://backend/pipeline/ingestion.py#L54-L146)
- [backend/pipeline/metadata_structuring.py:125-163](file://backend/pipeline/metadata_structuring.py#L125-L163)
- [backend/pipeline/search_index.py:269-300](file://backend/pipeline/search_index.py#L269-L300)

**Section sources**
- [backend/pipeline/ingestion.py:54-146](file://backend/pipeline/ingestion.py#L54-L146)
- [backend/pipeline/metadata_structuring.py:125-163](file://backend/pipeline/metadata_structuring.py#L125-L163)
- [backend/pipeline/search_index.py:269-300](file://backend/pipeline/search_index.py#L269-L300)

## Concurrent Processing Capabilities

The system has been architected to support concurrent processing of multiple video uploads while maintaining system stability and resource efficiency.

### Multi-Task Execution
- **Background Tasks**: Each video upload spawns an independent asyncio task that runs concurrently with other processing tasks.
- **Connection Fan-out**: WebSocket connections are maintained per-video with automatic fan-out to multiple subscribers.
- **Resource Isolation**: Each concurrent task operates with isolated resources and state management.

### Scalability Features
- **Dynamic Scaling**: The system can handle multiple concurrent uploads without significant performance degradation.
- **Memory Management**: Concurrent tasks use streaming patterns to minimize memory usage peaks.
- **CPU Utilization**: Parallel processing is balanced with CPU-bound operations to prevent overload.

### Task Coordination
- **Progress Broadcasting**: Real-time progress updates are broadcast to all connected WebSocket clients for each video.
- **Status Tracking**: Individual task status is tracked independently with separate progress reporting.
- **Error Propagation**: Errors in one task do not affect other concurrent processing operations.

```mermaid
graph TB
subgraph "Concurrent Processing"
Task1["Video Upload #1<br/>Async Task"]
Task2["Video Upload #2<br/>Async Task"]
Task3["Video Upload #3<br/>Async Task"]
WS1["WebSocket Clients #1"]
WS2["WebSocket Clients #2"]
WS3["WebSocket Clients #3"]
end
subgraph "Shared Resources"
Registry["Active WS Registry"]
FS["Uploads Directory"]
DB["Status Storage"]
end
Task1 --> WS1
Task2 --> WS2
Task3 --> WS3
WS1 --> Registry
WS2 --> Registry
WS3 --> Registry
Task1 --> FS
Task2 --> FS
Task3 --> FS
Task1 --> DB
Task2 --> DB
Task3 --> DB
```

**Diagram sources**
- [backend/routers/video.py:84-120](file://backend/routers/video.py#L84-L120)
- [backend/routers/video.py:29-31](file://backend/routers/video.py#L29-L31)

**Section sources**
- [backend/routers/video.py:84-120](file://backend/routers/video.py#L84-L120)
- [backend/routers/video.py:29-31](file://backend/routers/video.py#L29-L31)

## Dependency Analysis
- Backend depends on FastAPI, websockets, ffmpeg-python, httpx, numpy, faiss-cpu, dashscope, aiofiles.
- Frontend depends on Next.js, React, Tailwind, and Recharts.
- CORS middleware allows all origins/methods/headers for development convenience.

```mermaid
graph LR
FE["frontend/package.json"] --> NEXT["next"]
FE --> REACT["react"]
BE_REQ["backend/requirements.txt"] --> FASTAPI["fastapi"]
BE_REQ --> UVICORN["uvicorn"]
BE_REQ --> DASHSCOPE["dashscope"]
BE_REQ --> FFMPY["ffmpeg-python"]
BE_REQ --> HTTPX["httpx"]
BE_REQ --> NUMPY["numpy"]
BE_REQ --> FAISS["faiss-cpu"]
BE_REQ --> AIOFILES["aiofiles"]
```

**Diagram sources**
- [frontend/package.json:11-28](file://frontend/package.json#L11-L28)
- [backend/requirements.txt:1-16](file://backend/requirements.txt#L1-L16)

**Section sources**
- [frontend/package.json:1-29](file://frontend/package.json#L1-L29)
- [backend/requirements.txt:1-16](file://backend/requirements.txt#L1-L16)

## Performance Considerations
- Asynchronous I/O: aiofiles and httpx enable non-blocking file writes and external API calls.
- Chunked uploads: Backend reads file in 1MB chunks to reduce memory pressure.
- FAISS indexing: Batch embedding requests and normalization improve throughput.
- WebSocket fan-out: Minimal overhead broadcasting to registered clients.
- Event loop management: Strategic yielding prevents blocking operations from starving the event loop.
- Concurrent processing: Multiple video uploads can be processed simultaneously without performance degradation.
- Resource pooling: External API calls use connection pooling for efficient resource utilization.

## Troubleshooting Guide
- CORS issues: Verify allow_origins and credentials settings; tighten for production.
- Upload failures: Check filesystem permissions and disk space; confirm uploads directory exists.
- WebSocket disconnects: Frontend falls back to REST polling; ensure endpoint availability.
- DashScope errors: Inspect API key, quotas, and retry logs; implement backoff.
- Search returns empty: Confirm FAISS index initialization and embedding availability.
- Event loop starvation: Monitor for blocking operations; ensure proper async patterns are used.
- Memory leaks: Verify proper cleanup of temporary files and resources in error scenarios.

**Section sources**
- [backend/main.py:27-33](file://backend/main.py#L27-L33)
- [backend/routers/video.py:57-59](file://backend/routers/video.py#L57-L59)
- [backend/pipeline/search_index.py:61-70](file://backend/pipeline/search_index.py#L61-L70)
- [backend/pipeline/metadata_structuring.py:139-163](file://backend/pipeline/metadata_structuring.py#L139-L163)

## Conclusion
The Dubai Media system integrates a robust FastAPI backend with a reactive frontend to deliver end-to-end video processing powered by DashScope AI. REST and WebSocket endpoints provide responsive user experiences, while static file serving and FAISS-based search enable scalable media discovery. The enhanced event loop management, non-blocking execution patterns, and concurrent processing capabilities ensure optimal performance and scalability. Security and performance can be strengthened through tighter CORS, rate limiting, and optimized pipeline scheduling.

## Appendices

### CORS and Security Considerations
- CORS: Broadly permissive in development; restrict origins and headers in production.
- API keys: Stored in environment via pydantic-settings; avoid logging secrets.
- Static serving: Nginx serves uploads; ensure appropriate access controls and caching headers.
- Rate limits: Consider implementing at gateway or router level for DashScope calls.

**Section sources**
- [backend/main.py:27-33](file://backend/main.py#L27-L33)
- [backend/config.py:4-17](file://backend/config.py#L4-L17)
- [nginx.conf](file://nginx.conf)
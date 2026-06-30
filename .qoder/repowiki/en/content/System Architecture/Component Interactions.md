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
This document explains the component interactions within the Dubai Media system, focusing on how the frontend and backend communicate, how files are uploaded and served, how real-time progress is streamed via WebSockets, and how Alibaba Cloud DashScope AI services are integrated. It also covers CORS configuration, security considerations, and typical user workflows from upload through processing completion.

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
- [backend/config.py:1-21](file://backend/config.py#L1-L21)
- [backend/routers/video.py:1-267](file://backend/routers/video.py#L1-L267)
- [backend/routers/rfp.py:1-385](file://backend/routers/rfp.py#L1-L385)
- [backend/pipeline/orchestrator.py:1-329](file://backend/pipeline/orchestrator.py#L1-L329)
- [backend/pipeline/ingestion.py:1-146](file://backend/pipeline/ingestion.py#L1-L146)
- [backend/pipeline/metadata_structuring.py:1-252](file://backend/pipeline/metadata_structuring.py#L1-L252)
- [backend/pipeline/search_index.py:1-245](file://backend/pipeline/search_index.py#L1-L245)
- [backend/services/rfp_creator.py:1-639](file://backend/services/rfp_creator.py#L1-L639)
- [backend/services/rfp_evaluator.py:1-622](file://backend/services/rfp_evaluator.py#L1-L622)
- [frontend/src/lib/api.ts:1-245](file://frontend/src/lib/api.ts#L1-L245)
- [frontend/src/lib/useVideoProcessing.ts:1-421](file://frontend/src/lib/useVideoProcessing.ts#L1-L421)
- [frontend/src/components/archive/VideoUpload.tsx:1-221](file://frontend/src/components/archive/VideoUpload.tsx#L1-L221)

**Section sources**
- [backend/main.py:1-44](file://backend/main.py#L1-L44)
- [backend/config.py:1-21](file://backend/config.py#L1-L21)
- [frontend/src/lib/api.ts:1-245](file://frontend/src/lib/api.ts#L1-L245)
- [frontend/src/lib/useVideoProcessing.ts:1-421](file://frontend/src/lib/useVideoProcessing.ts#L1-L421)
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
- [backend/routers/video.py:39-267](file://backend/routers/video.py#L39-L267)
- [backend/pipeline/orchestrator.py:34-207](file://backend/pipeline/orchestrator.py#L34-L207)
- [backend/pipeline/search_index.py:22-196](file://backend/pipeline/search_index.py#L22-L196)
- [backend/pipeline/metadata_structuring.py:81-164](file://backend/pipeline/metadata_structuring.py#L81-L164)
- [frontend/src/lib/api.ts:164-244](file://frontend/src/lib/api.ts#L164-L244)
- [frontend/src/lib/useVideoProcessing.ts:122-420](file://frontend/src/lib/useVideoProcessing.ts#L122-L420)

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
- [backend/routers/video.py:220-267](file://backend/routers/video.py#L220-L267)
- [backend/pipeline/orchestrator.py:44-207](file://backend/pipeline/orchestrator.py#L44-L207)
- [backend/pipeline/search_index.py:198-244](file://backend/pipeline/search_index.py#L198-L244)
- [backend/pipeline/metadata_structuring.py:114-163](file://backend/pipeline/metadata_structuring.py#L114-L163)
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
- [backend/pipeline/orchestrator.py:44-207](file://backend/pipeline/orchestrator.py#L44-L207)
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
- [backend/routers/video.py:220-267](file://backend/routers/video.py#L220-L267)
- [backend/pipeline/orchestrator.py:95-120](file://backend/pipeline/orchestrator.py#L95-L120)

**Section sources**
- [backend/routers/video.py:220-267](file://backend/routers/video.py#L220-L267)
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
- [backend/pipeline/orchestrator.py:59-195](file://backend/pipeline/orchestrator.py#L59-L195)
- [backend/pipeline/ingestion.py:16-51](file://backend/pipeline/ingestion.py#L16-L51)
- [backend/pipeline/search_index.py:42-87](file://backend/pipeline/search_index.py#L42-L87)

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
- [backend/pipeline/metadata_structuring.py:114-163](file://backend/pipeline/metadata_structuring.py#L114-L163)
- [backend/pipeline/search_index.py:198-244](file://backend/pipeline/search_index.py#L198-L244)
- [backend/services/rfp_creator.py:76-123](file://backend/services/rfp_creator.py#L76-L123)
- [backend/services/rfp_evaluator.py:48-104](file://backend/services/rfp_evaluator.py#L48-L104)

**Section sources**
- [backend/config.py:4-12](file://backend/config.py#L4-L12)
- [backend/pipeline/metadata_structuring.py:114-163](file://backend/pipeline/metadata_structuring.py#L114-L163)
- [backend/pipeline/search_index.py:198-244](file://backend/pipeline/search_index.py#L198-L244)
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
- [backend/routers/video.py:220-267](file://backend/routers/video.py#L220-L267)

**Section sources**
- [frontend/src/lib/api.ts:1-245](file://frontend/src/lib/api.ts#L1-L245)
- [frontend/src/lib/useVideoProcessing.ts:122-420](file://frontend/src/lib/useVideoProcessing.ts#L122-L420)
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
- Recommendations:
  - Limit concurrent uploads and pipeline runs based on CPU/IO capacity.
  - Tune FAISS index persistence and batch sizes.
  - Consider rate limiting and circuit breakers for DashScope.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
- CORS issues: Verify allow_origins and credentials settings; tighten for production.
- Upload failures: Check filesystem permissions and disk space; confirm uploads directory exists.
- WebSocket disconnects: Frontend falls back to REST polling; ensure endpoint availability.
- DashScope errors: Inspect API key, quotas, and retry logs; implement backoff.
- Search returns empty: Confirm FAISS index initialization and embedding availability.

**Section sources**
- [backend/main.py:27-33](file://backend/main.py#L27-L33)
- [backend/routers/video.py:57-59](file://backend/routers/video.py#L57-L59)
- [backend/pipeline/search_index.py:61-70](file://backend/pipeline/search_index.py#L61-L70)
- [backend/pipeline/metadata_structuring.py:139-163](file://backend/pipeline/metadata_structuring.py#L139-L163)

## Conclusion
The Dubai Media system integrates a robust FastAPI backend with a reactive frontend to deliver end-to-end video processing powered by DashScope AI. REST and WebSocket endpoints provide responsive user experiences, while static file serving and FAISS-based search enable scalable media discovery. Security and performance can be strengthened through tighter CORS, rate limiting, and optimized pipeline scheduling.

[No sources needed since this section summarizes without analyzing specific files]

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
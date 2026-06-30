# Video Processing Endpoints

<cite>
**Referenced Files in This Document**
- [backend/routers/video.py](file://backend/routers/video.py)
- [backend/pipeline/orchestrator.py](file://backend/pipeline/orchestrator.py)
- [backend/pipeline/search_index.py](file://backend/pipeline/search_index.py)
- [backend/config.py](file://backend/config.py)
- [backend/main.py](file://backend/main.py)
- [backend/pipeline/ingestion.py](file://backend/pipeline/ingestion.py)
- [backend/pipeline/audio_analysis.py](file://backend/pipeline/audio_analysis.py)
- [backend/pipeline/metadata_structuring.py](file://backend/pipeline/metadata_structuring.py)
- [frontend/src/lib/api.ts](file://frontend/src/lib/api.ts)
- [frontend/src/lib/useVideoProcessing.ts](file://frontend/src/lib/useVideoProcessing.ts)
- [frontend/src/components/archive/VideoUpload.tsx](file://frontend/src/components/archive/VideoUpload.tsx)
- [README.md](file://README.md)
</cite>

## Update Summary
**Changes Made**
- Added comprehensive documentation for XMLHttpRequest-based upload progress tracking with real-time percentage updates
- Documented dual HTTP method support for search endpoints (GET/POST) with identical functionality
- Added detailed documentation for the new /api/reindex endpoint for rebuilding search indexes from existing processed videos
- Updated architecture overview to reflect real-time upload progress tracking and enhanced search capabilities
- Revised frontend integration examples to demonstrate XMLHttpRequest-based progress monitoring
- Enhanced troubleshooting guidance for upload progress tracking and search endpoint usage

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
This document provides comprehensive API documentation for the video processing endpoints that power the AI-powered media archive. It covers:
- POST /api/video/upload for video file uploads with XMLHttpRequest-based real-time progress tracking
- GET /api/video/{video_id}/status for retrieving processing pipeline status with detailed progress information
- GET /api/video/{video_id}/metadata for accessing structured metadata results from all pipeline stages
- GET /api/video/{video_id}/transcript for retrieving speech-to-text transcripts
- GET/POST /api/search for semantic search with dual HTTP method support
- POST /api/reindex for rebuilding search indexes from existing processed videos

The documentation includes request/response schemas, error codes, file upload handling with real-time progress tracking, and practical examples using curl commands and JavaScript implementations with XMLHttpRequest callbacks.

## Project Structure
The video processing system consists of:
- FastAPI backend with routers and pipeline orchestration using asyncio task execution
- AI pipeline stages powered by Alibaba Cloud DashScope models
- Frontend client utilities for uploading with real-time progress tracking and consuming the APIs

```mermaid
graph TB
subgraph "Frontend"
FE_API["api.ts<br/>XMLHttpRequest-based upload progress"]
FE_HOOK["useVideoProcessing.ts<br/>React hook"]
FE_UPLOAD["VideoUpload.tsx<br/>UI component"]
end
subgraph "Backend"
MAIN["main.py<br/>FastAPI app"]
ROUTER["routers/video.py<br/>Video endpoints"]
ORCH["pipeline/orchestrator.py<br/>Pipeline orchestrator"]
CFG["config.py<br/>Settings"]
SI["pipeline/search_index.py<br/>Search index"]
end
subgraph "Pipeline Stages"
ING["ingestion.py<br/>FFmpeg extraction"]
AUD["audio_analysis.py<br/>ASR transcription"]
META["metadata_structuring.py<br/>EBUCore/IPTC metadata"]
end
FE_API --> ROUTER
FE_HOOK --> FE_API
FE_UPLOAD --> FE_HOOK
MAIN --> ROUTER
ROUTER --> ORCH
ORCH --> ING
ORCH --> AUD
ORCH --> META
ORCH --> SI
CFG --> ORCH
```

**Diagram sources**
- [backend/main.py:1-44](file://backend/main.py#L1-L44)
- [backend/routers/video.py:1-268](file://backend/routers/video.py#L1-L268)
- [backend/pipeline/orchestrator.py:1-330](file://backend/pipeline/orchestrator.py#L1-L330)
- [backend/config.py:1-21](file://backend/config.py#L1-L21)
- [backend/pipeline/search_index.py:1-306](file://backend/pipeline/search_index.py#L1-L306)

**Section sources**
- [README.md:148-168](file://README.md#L148-L168)
- [backend/main.py:1-44](file://backend/main.py#L1-L44)

## Core Components
- Video upload router: Handles multipart/form-data uploads with XMLHttpRequest-based progress tracking, saves files, initializes status, and starts the background pipeline using asyncio tasks for non-blocking execution
- Pipeline orchestrator: Coordinates six stages with progress tracking and error handling using async/await patterns
- Search index: Manages FAISS-based vector search with DashScope text embeddings and rebuild capability
- Frontend API utilities: Provide XMLHttpRequest-based upload progress tracking with real-time percentage updates and typed helpers for uploads, status polling, and WebSocket progress streaming

Key capabilities:
- Real-time upload progress via XMLHttpRequest onprogress callback with percentage calculation
- Real-time progress via WebSocket with optimized connection management
- Structured metadata generation (EBUCore XML, IPTC)
- Speech-to-text with speaker diarization
- Semantic search with dual HTTP method support (GET/POST)
- Batch reindexing from existing processed videos

**Section sources**
- [backend/routers/video.py:39-92](file://backend/routers/video.py#L39-L92)
- [backend/pipeline/orchestrator.py:44-206](file://backend/pipeline/orchestrator.py#L44-L206)
- [backend/pipeline/search_index.py:59-306](file://backend/pipeline/search_index.py#L59-L306)
- [frontend/src/lib/api.ts:43-95](file://frontend/src/lib/api.ts#L43-L95)

## Architecture Overview
The system follows a staged pipeline architecture with asyncio task execution and real-time upload progress tracking:
1. Upload endpoint receives multipart/form-data via XMLHttpRequest with onprogress callback for real-time percentage updates
2. Asyncio task runs the orchestrator which executes stages sequentially with optimized status updates
3. Progress updates are streamed via WebSocket and persisted to status.json
4. Results are saved as individual JSON artifacts per stage
5. Search index is built incrementally during processing and can be rebuilt via /api/reindex

**Updated** The system now uses XMLHttpRequest for upload progress tracking instead of standard fetch requests, providing accurate real-time percentage updates. The search endpoints now support both GET and POST methods with identical functionality, allowing flexible client implementations.

```mermaid
sequenceDiagram
participant Client as "Client"
participant API as "FastAPI Router"
participant XHR as "XMLHttpRequest"
participant FS as "Filesystem"
participant Task as "Asyncio Task"
participant Orchestrator as "Pipeline Orchestrator"
participant Stage as "Pipeline Stage"
participant WS as "WebSocket"
Client->>XHR : "XMLHttpRequest upload with onprogress"
XHR->>API : "POST /api/video/upload (multipart/form-data)"
API->>FS : "Save video file"
API->>Task : "asyncio.create_task(_run_pipeline)"
Task->>Orchestrator : "process_video(video_id, video_path)"
Orchestrator->>Stage : "Run ingestion"
Stage-->>Orchestrator : "Stage result"
Orchestrator->>FS : "Write status.json"
Orchestrator->>WS : "Send progress event"
Orchestrator->>Stage : "Run next stage"
Stage-->>Orchestrator : "Stage result"
Orchestrator->>FS : "Write status.json"
Orchestrator->>WS : "Send progress event"
Orchestrator-->>Task : "Pipeline complete"
Task-->>API : "Return queued response"
API-->>XHR : "{video_id, status}"
XHR-->>Client : "onload callback with upload result"
```

**Diagram sources**
- [backend/routers/video.py:39-92](file://backend/routers/video.py#L39-L92)
- [backend/routers/video.py:95-120](file://backend/routers/video.py#L95-L120)
- [backend/pipeline/orchestrator.py:44-206](file://backend/pipeline/orchestrator.py#L44-L206)
- [frontend/src/lib/api.ts:43-95](file://frontend/src/lib/api.ts#L43-L95)

## Detailed Component Analysis

### POST /api/video/upload
Purpose: Upload a video file with real-time progress tracking using XMLHttpRequest and start the processing pipeline using asyncio task execution.

- Method: POST
- Path: /api/video/upload
- Content-Type: multipart/form-data
- Request Body:
  - file: binary video file (required)
- Response:
  - video_id: unique identifier for the video
  - filename: original filename
  - status: "queued"
  - message: informational message

**Updated** Upload progress tracking now uses XMLHttpRequest with onprogress callback for accurate real-time percentage updates. The frontend implementation calculates progress as (event.loaded / event.total) * 100 and passes it to the onProgress callback for immediate UI updates.

Behavior:
- Validates and saves the uploaded file to the configured upload directory using async file operations
- Creates initial status.json with pending stages
- Launches pipeline as asyncio task using asyncio.create_task() for non-blocking execution
- Returns immediately with queued status

Supported formats and limits:
- Frontend accepts MP4, MOV, AVI
- Maximum file size indicated as 2GB in UI
- Backend does not enforce explicit size limits in the upload handler

Error codes:
- 400: Invalid request (missing file)
- 500: Failed to save uploaded file

curl example:
```bash
curl -X POST "http://localhost:8000/api/video/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/video.mp4"
```

JavaScript XMLHttpRequest example:
```javascript
const formData = new FormData();
formData.append("file", fileBlob);

// XMLHttpRequest with real progress tracking
const xhr = new XMLHttpRequest();
xhr.open("POST", "http://localhost:8000/api/video/upload");

xhr.upload.onprogress = (event) => {
  if (event.lengthComputable) {
    const percent = Math.round((event.loaded / event.total) * 100);
    console.log(`Upload progress: ${percent}%`);
  }
};

xhr.onload = () => {
  if (xhr.status >= 200 && xhr.status < 300) {
    const result = JSON.parse(xhr.responseText);
    console.log("video_id:", result.video_id);
  }
};

xhr.send(formData);
```

**Section sources**
- [backend/routers/video.py:39-92](file://backend/routers/video.py#L39-L92)
- [frontend/src/lib/api.ts:43-95](file://frontend/src/lib/api.ts#L43-L95)
- [frontend/src/components/archive/VideoUpload.tsx:23-24](file://frontend/src/components/archive/VideoUpload.tsx#L23-L24)

### GET /api/video/{video_id}/status
Purpose: Retrieve the current pipeline status and progress using optimized synchronous file reading.

- Method: GET
- Path: /api/video/{video_id}/status
- Path Parameters:
  - video_id: UUID of the video
- Response Schema:
  - video_id: string
  - status: "queued" | "processing" | "completed" | "completed_with_errors"
  - progress: number (0-100)
  - stages: object with stage names as keys and statuses as values
  - filename: string
  - created_at: ISO timestamp
  - updated_at: ISO timestamp
  - errors: object mapping failed stages to error messages

**Updated** Status retrieval now uses synchronous file reading for the tiny status.json file to avoid thread pool contention, providing optimal performance for frequent status checks. This optimization ensures minimal CPU overhead during high-frequency polling scenarios.

curl example:
```bash
curl "http://localhost:8000/api/video/<video_id>/status"
```

JavaScript fetch example:
```javascript
const response = await fetch("http://localhost:8000/api/video/<video_id>/status");
const status = await response.json();
console.log("progress:", status.progress);
console.log("stages:", status.stages);
```

WebSocket alternative:
- Connect to ws://localhost:8000/ws/pipeline/{video_id}
- Receive real-time progress updates during processing with improved connection management
- Automatic fallback to REST polling when WebSocket connections fail

**Section sources**
- [backend/routers/video.py:124-139](file://backend/routers/video.py#L124-L139)
- [backend/routers/video.py:220-268](file://backend/routers/video.py#L220-L268)
- [backend/pipeline/orchestrator.py:62-72](file://backend/pipeline/orchestrator.py#L62-L72)

### GET /api/video/{video_id}/metadata
Purpose: Access structured metadata results from all pipeline stages.

- Method: GET
- Path: /api/video/{video_id}/metadata
- Path Parameters:
  - video_id: UUID of the video
- Response Schema:
  - video_id: string
  - ingestion: object (from ingestion stage)
  - visual_analysis: object (from visual analysis stage)
  - metadata: object (from metadata structuring stage)
  - faces: object (from face recognition stage)
  - Any missing stage results are omitted or include an error field

Typical ingestion fields:
- audio_path: string
- thumbnail_path: string
- duration: number
- resolution: string
- fps: number
- codec: string

Typical visual_analysis fields:
- scenes: array of scene objects
- objects: array of detected objects
- landmarks: array of landmarks
- text_ocr: array of OCR text
- sensitive_content: array of sensitive content flags
- overall_summary_en/ar: strings
- era_estimate: object

Typical metadata fields:
- ebucore_xml: string (EBUCore XML)
- iptc_video_metadata: object (IPTC Video Metadata Hub)
- topic_codes: array of strings
- topic_names_en/ar: arrays of strings
- sentiment_tags: array of strings
- tone: string
- content_rating: string
- geographic_tags: array of strings
- persons_mentioned: array of person objects

curl example:
```bash
curl "http://localhost:8000/api/video/<video_id>/metadata"
```

JavaScript fetch example:
```javascript
const response = await fetch("http://localhost:8000/api/video/<video_id>/metadata");
const metadata = await response.json();
console.log("topics:", metadata.metadata.topic_codes);
```

**Section sources**
- [backend/routers/video.py:143-174](file://backend/routers/video.py#L143-L174)
- [backend/pipeline/ingestion.py:44-51](file://backend/pipeline/ingestion.py#L44-L51)
- [backend/pipeline/metadata_structuring.py:81-163](file://backend/pipeline/metadata_structuring.py#L81-L163)

### GET /api/video/{video_id}/transcript
Purpose: Retrieve speech-to-text transcripts with speaker diarization.

- Method: GET
- Path: /api/video/{video_id}/transcript
- Path Parameters:
  - video_id: UUID of the video
- Response Schema:
  - video_id: string
  - segments: array of segment objects
  - full_text: string
  - language: string
  - speaker_count: number

Each segment object typically includes:
- start_time: number (seconds)
- end_time: number (seconds)
- speaker_id: string
- text: string
- words: array of word objects with word, start, end

curl example:
```bash
curl "http://localhost:8000/api/video/<video_id>/transcript"
```

JavaScript fetch example:
```javascript
const response = await fetch("http://localhost:8000/api/video/<video_id>/transcript");
const transcript = await response.json();
console.log("segments count:", transcript.segments.length);
```

**Section sources**
- [backend/routers/video.py:179-195](file://backend/routers/video.py#L179-L195)
- [backend/pipeline/audio_analysis.py:22-59](file://backend/pipeline/audio_analysis.py#L22-L59)

### GET/POST /api/search
Purpose: Perform semantic search across all indexed videos with dual HTTP method support.

**Updated** Search endpoints now support both GET and POST methods with identical functionality:
- GET /api/search?query=your+query&top_k=5
- POST /api/search with JSON body containing query and top_k

Both methods accept the same SearchRequest model:
- query: string (required)
- top_k: integer (optional, default: 5)

Response Schema:
- query: string (original query)
- results: array of search result objects
- total: integer (count of results)

Each search result typically includes:
- video_id: string
- title: string
- timestamp: number (seconds)
- description: string
- score: number
- thumbnail: string (optional)

curl GET example:
```bash
curl "http://localhost:8000/api/search?query=climate+change&top_k=5"
```

curl POST example:
```bash
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{"query":"climate change","top_k":5}'
```

JavaScript fetch example:
```javascript
// GET method
const response = await fetch("http://localhost:8000/api/search?query=climate+change&top_k=5");
const results = await response.json();

// POST method  
const response = await fetch("http://localhost:8000/api/search", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    query: "climate change",
    top_k: 5
  })
});
const results = await response.json();
```

**Section sources**
- [backend/routers/video.py:201-234](file://backend/routers/video.py#L201-L234)
- [backend/routers/video.py:33-35](file://backend/routers/video.py#L33-L35)

### POST /api/reindex
Purpose: Rebuild the search index from all existing processed video results.

- Method: POST
- Path: /api/reindex
- Content-Type: application/json
- Request Body: None
- Response Schema:
  - status: "ok"
  - videos_indexed: number (count of videos successfully indexed)
  - total_vectors: number (total vectors in the rebuilt index)

**Updated** The reindex endpoint now supports both GET and POST methods via @router.api_route decorator, providing flexibility for different client implementations.

Behavior:
- Clears existing search index (FAISS or numpy fallback)
- Scans all processed videos in the upload directory
- Loads results.json for each processed video
- Builds searchable segments using orchestrator's _build_searchable_segments method
- Adds segments to the search index with text embeddings
- Persists the rebuilt index to disk

**Important**: This endpoint requires existing processed videos with results.json files. Videos that haven't completed processing will be skipped.

Error codes:
- 500: Failed to rebuild search index (various internal errors)

curl example:
```bash
curl -X POST "http://localhost:8000/api/reindex"
```

JavaScript fetch example:
```javascript
const response = await fetch("http://localhost:8000/api/reindex", {
  method: "POST",
});
const result = await response.json();
console.log("Indexed videos:", result.videos_indexed);
console.log("Total vectors:", result.total_vectors);
```

**Section sources**
- [backend/routers/video.py:239-278](file://backend/routers/video.py#L239-L278)
- [backend/pipeline/orchestrator.py:307-367](file://backend/pipeline/orchestrator.py#L307-L367)
- [backend/pipeline/search_index.py:143-213](file://backend/pipeline/search_index.py#L143-L213)

## Dependency Analysis
The video processing endpoints depend on:
- FastAPI routing with asyncio task execution
- Filesystem for saving uploads and results
- External AI services (DashScope) for vision, ASR, and text generation
- FFmpeg for local video/audio processing
- FAISS or numpy for vector search indexing

**Updated** The system now depends on XMLHttpRequest for upload progress tracking in the frontend, providing accurate real-time percentage updates. The search endpoints utilize the same SearchRequest model for both GET and POST methods, ensuring consistent validation and error handling.

```mermaid
graph LR
Router["routers/video.py"] --> Orchestrator["pipeline/orchestrator.py"]
Orchestrator --> Config["config.py"]
Orchestrator --> Ingestion["pipeline/ingestion.py"]
Orchestrator --> Audio["pipeline/audio_analysis.py"]
Orchestrator --> Metadata["pipeline/metadata_structuring.py"]
Orchestrator --> SearchIndex["pipeline/search_index.py"]
FrontendAPI["frontend/src/lib/api.ts"] --> Router
FrontendHook["frontend/src/lib/useVideoProcessing.ts"] --> FrontendAPI
FrontendUpload["frontend/src/components/archive/VideoUpload.tsx"] --> FrontendHook
```

**Diagram sources**
- [backend/routers/video.py:17-19](file://backend/routers/video.py#L17-L19)
- [backend/pipeline/orchestrator.py:14-21](file://backend/pipeline/orchestrator.py#L14-L21)
- [backend/config.py:4-12](file://backend/config.py#L4-L12)
- [frontend/src/lib/api.ts:164-183](file://frontend/src/lib/api.ts#L164-L183)

**Section sources**
- [backend/main.py:35-38](file://backend/main.py#L35-L38)
- [backend/routers/video.py:25-27](file://backend/routers/video.py#L25-L27)

## Performance Considerations
- Large video files increase processing time; consider chunked uploads and compression
- ASR transcription is asynchronous and may take several minutes for long audio
- Real-time progress streaming via WebSocket reduces polling overhead with optimized connection management
- XMLHttpRequest-based upload progress tracking provides accurate percentage updates without blocking the main thread
- Results are persisted as JSON files; ensure sufficient disk space for large archives
- FFmpeg operations require adequate CPU/memory resources
- **Updated** Optimized status retrieval uses synchronous file reading for tiny status.json files to avoid thread pool contention
- **Updated** XMLHttpRequest upload progress tracking uses onprogress callback for real-time updates without additional polling overhead
- **Updated** Dual HTTP method support for search endpoints eliminates the need for separate endpoint implementations
- **Updated** Reindex operation processes all existing videos sequentially; consider running during maintenance windows for large archives

## Troubleshooting Guide
Common issues and resolutions:
- 404 Not Found: Video ID not found or status file missing
- 500 Internal Server Error: File save failures or pipeline exceptions
- API key errors: Ensure DASHSCOPE_API_KEY is configured
- WebSocket disconnects: Use fallback REST polling with automatic retry
- **Updated** Upload progress stuck at 0%: Verify XMLHttpRequest onprogress callback is properly attached and event.lengthComputable is true
- **Updated** Upload progress not updating: Check that the server responds with Content-Length header and that the client handles onprogress events correctly
- **Updated** Search endpoint errors: Verify both GET and POST methods are properly formatted with the SearchRequest model
- **Updated** Reindex failures: Check that videos have been fully processed and contain results.json files

Error handling patterns:
- Upload failures return HTTP 500 with detailed error messages
- Pipeline stage failures are recorded in status.errors
- Frontend gracefully handles WebSocket errors by falling back to REST polling
- XMLHttpRequest upload progress tracking handles network errors and timeouts appropriately
- Search endpoints validate the SearchRequest model and return descriptive error messages
- Reindex operation logs warnings for videos that fail to index and continues processing

**Section sources**
- [backend/routers/video.py:57-59](file://backend/routers/video.py#L57-L59)
- [backend/routers/video.py:129-131](file://backend/routers/video.py#L129-L131)
- [backend/routers/video.py:184-185](file://backend/routers/video.py#L184-L185)
- [backend/pipeline/orchestrator.py:259-282](file://backend/pipeline/orchestrator.py#L259-L282)
- [frontend/src/lib/api.ts:43-95](file://frontend/src/lib/api.ts#L43-L95)

## Conclusion
The video processing endpoints provide a robust foundation for AI-powered media archive workflows. They support efficient uploads with real-time progress tracking, real-time progress monitoring, and comprehensive metadata extraction with structured outputs suitable for broadcasting standards and semantic search. The updated XMLHttpRequest-based upload progress tracking provides accurate real-time percentage updates, while the dual HTTP method support for search endpoints offers flexibility for different client implementations. The new reindex endpoint allows administrators to rebuild search indexes from existing processed videos, ensuring search functionality remains available even after system migrations or index corruption.

## Appendices

### Request/Response Schemas

Upload response:
- video_id: string
- filename: string
- status: "queued"
- message: string

Status response:
- video_id: string
- status: "queued"|"processing"|"completed"|"completed_with_errors"
- progress: number
- stages: object with stage names as keys
- filename: string
- created_at: string (ISO timestamp)
- updated_at: string (ISO timestamp)
- errors: object

Metadata response:
- video_id: string
- ingestion: object
- visual_analysis: object
- metadata: object
- faces: object

Transcript response:
- video_id: string
- segments: array
- full_text: string
- language: string
- speaker_count: number

Search response:
- query: string
- results: array
- total: number

Reindex response:
- status: "ok"
- videos_indexed: number
- total_vectors: number

### Practical Examples

curl upload:
```bash
curl -X POST "http://localhost:8000/api/video/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample.mp4"
```

JavaScript XMLHttpRequest upload:
```javascript
const formData = new FormData();
formData.append("file", fileBlob);

const xhr = new XMLHttpRequest();
xhr.open("POST", "http://localhost:8000/api/video/upload");

xhr.upload.onprogress = (event) => {
  if (event.lengthComputable) {
    const percent = Math.round((event.loaded / event.total) * 100);
    console.log(`Upload progress: ${percent}%`);
  }
};

xhr.onload = () => {
  if (xhr.status >= 200 && xhr.status < 300) {
    const result = JSON.parse(xhr.responseText);
    console.log("video_id:", result.video_id);
  }
};

xhr.send(formData);
```

JavaScript status polling:
```javascript
const response = await fetch(`http://localhost:8000/api/video/${videoId}/status`);
const status = await response.json();
```

JavaScript WebSocket progress:
```javascript
const ws = new WebSocket("ws://localhost:8000/ws/pipeline/" + videoId);
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Stage ${data.stage}: ${data.message}`);
};
```

JavaScript search (GET):
```javascript
const response = await fetch("http://localhost:8000/api/search?query=climate+change&top_k=5");
const results = await response.json();
```

JavaScript search (POST):
```javascript
const response = await fetch("http://localhost:8000/api/search", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    query: "climate change",
    top_k: 5
  })
});
const results = await response.json();
```

curl reindex:
```bash
curl -X POST "http://localhost:8000/api/reindex"
```

JavaScript reindex:
```javascript
const response = await fetch("http://localhost:8000/api/reindex", {
  method: "POST",
});
const result = await response.json();
console.log("Indexed videos:", result.videos_indexed);
```
# API Integration & State Management

<cite>
**Referenced Files in This Document**
- [api.ts](file://frontend/src/lib/api.ts)
- [useVideoProcessing.ts](file://frontend/src/lib/useVideoProcessing.ts)
- [VideoUpload.tsx](file://frontend/src/components/archive/VideoUpload.tsx)
- [archive/page.tsx](file://frontend/src/app/archive/page.tsx)
- [PipelineVisualizer.tsx](file://frontend/src/components/archive/PipelineVisualizer.tsx)
- [rfp-creator/page.tsx](file://frontend/src/app/rfp-creator/page.tsx)
- [RFPForm.tsx](file://frontend/src/components/rfp/RFPForm.tsx)
- [rfp-evaluator/page.tsx](file://frontend/src/app/rfp-evaluator/page.tsx)
- [video.py](file://backend/routers/video.py)
- [face_recognition.py](file://backend/pipeline/face_recognition.py)
- [reference_faces.json](file://backend/data/reference_faces.json)
- [faces.json](file://backend/uploads/32cf9631-ba74-4f0b-8a7c-c14bccf5a132/faces.json)
- [visual_analysis.json](file://backend/uploads/32cf9631-ba74-4f0b-8a7c-c14bccf5a132/visual_analysis.json)
- [rfp.py](file://backend/routers/rfp.py)
- [main.py](file://backend/main.py)
</cite>

## Update Summary
**Changes Made**
- Enhanced Data Transformation Layer documentation with comprehensive face recognition data mapping
- Added detailed intelligent fallback mechanisms for unnamed persons
- Updated data transformation patterns section with sophisticated backend-to-frontend mapping examples
- Expanded API endpoint mapping section with detailed response structure documentation
- Added comprehensive transformation examples showing backend response to frontend interface mapping
- Documented automatic numbering for unnamed persons and appearance synthesis
- Added intelligent fallbacks for face recognition data transformation

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

## Introduction
This document explains the frontend API integration layer and state management patterns used in the Dubai Media project. It covers the typed HTTP client library, WebSocket integration for real-time progress updates, and the custom React hook that orchestrates video processing workflows. It also documents API endpoint mapping, request/response schemas, error handling, and integration patterns with the backend services.

## Project Structure
The frontend integrates with two primary backend domains:
- Video processing pipeline: upload, status tracking, metadata retrieval, transcripts, search, and WebSocket progress streaming
- RFP creation and evaluation: AI-powered proposal generation, regeneration, export, and vendor evaluation workflows

```mermaid
graph TB
subgraph "Frontend"
A["api.ts<br/>HTTP client + WebSocket"]
B["useVideoProcessing.ts<br/>React hook"]
C["Components<br/>Archive, RFP, Evaluator"]
end
subgraph "Backend"
D["FastAPI main.py"]
E["Video Router<br/>video.py"]
F["RFP Router<br/>rfp.py"]
G["Face Recognition Pipeline<br/>face_recognition.py"]
H["Reference Database<br/>reference_faces.json"]
end
A --> D
B --> A
C --> A
D --> E
D --> F
E --> G
G --> H
```

**Diagram sources**
- [api.ts:1-245](file://frontend/src/lib/api.ts#L1-L245)
- [useVideoProcessing.ts:1-497](file://frontend/src/lib/useVideoProcessing.ts#L1-L497)
- [main.py:1-44](file://backend/main.py#L1-L44)
- [video.py:1-268](file://backend/routers/video.py#L1-L268)
- [rfp.py:1-385](file://backend/routers/rfp.py#L1-L385)
- [face_recognition.py:1-319](file://backend/pipeline/face_recognition.py#L1-L319)
- [reference_faces.json:1-101](file://backend/data/reference_faces.json#L1-L101)

**Section sources**
- [api.ts:1-245](file://frontend/src/lib/api.ts#L1-L245)
- [useVideoProcessing.ts:1-497](file://frontend/src/lib/useVideoProcessing.ts#L1-L497)
- [main.py:1-44](file://backend/main.py#L1-L44)

## Core Components
This section documents the core API integration and state management building blocks.

### HTTP Client Library (api.ts)
The client provides:
- Base URL configuration from environment variables
- Typed fetch wrapper with URL parameter support
- File upload helper for multipart/form-data
- WebSocket connection helper with message parsing
- Strongly typed request/response interfaces for RFP and evaluation workflows
- Convenience API facade exposing endpoints for video and RFP operations

Key capabilities:
- HTTP request configuration: JSON content-type header, optional query parameters
- Error handling: parses JSON error bodies and throws descriptive errors
- Authentication: no explicit auth headers; relies on backend CORS policy
- Response processing: JSON parsing with typed return values
- WebSocket: connects to ws:// base URL derived from http base URL

**Section sources**
- [api.ts:1-39](file://frontend/src/lib/api.ts#L1-L39)
- [api.ts:42-64](file://frontend/src/lib/api.ts#L42-L64)
- [api.ts:66-99](file://frontend/src/lib/api.ts#L66-L99)
- [api.ts:101-161](file://frontend/src/lib/api.ts#L101-L161)
- [api.ts:162-244](file://frontend/src/lib/api.ts#L162-L244)

### Real-Time WebSocket Integration
The WebSocket helper:
- Establishes connections to ws://host/ws/pipeline/{video_id}
- Parses incoming JSON messages into a standardized shape
- Invokes callbacks for messages, errors, and close events
- Provides a typed message interface for progress tracking

**Section sources**
- [api.ts:66-99](file://frontend/src/lib/api.ts#L66-L99)
- [api.ts:68-74](file://frontend/src/lib/api.ts#L68-L74)

### React Hook for Video Processing (useVideoProcessing.ts)
The hook manages:
- Upload lifecycle: progress simulation, file URL creation, error handling
- WebSocket pipeline updates: stage transitions, timing, completion detection
- Fallback polling: REST status polling when WebSocket fails
- Result fetching: metadata and transcript retrieval after pipeline completion
- Search: semantic search across processed videos
- Video timeline synchronization: current time tracking and seeking
- State cleanup: WebSocket closure and object URL revocation

State structure:
- View modes: upload, processing, results
- Upload state: idle, uploading, uploaded, error
- Pipeline stages: ingestion, visual_analysis, audio_speech, face_recognition, metadata_structuring, search_index
- Metadata: faces, scenes, objects, landmarks, sensitive content indicators
- Transcript segments with speaker, timestamps, and optional language
- Search results: video_id, title, timestamp, description, score
- Error tracking and current playback time

**Section sources**
- [useVideoProcessing.ts:88-104](file://frontend/src/lib/useVideoProcessing.ts#L88-L104)
- [useVideoProcessing.ts:106-113](file://frontend/src/lib/useVideoProcessing.ts#L106-L113)
- [useVideoProcessing.ts:122-497](file://frontend/src/lib/useVideoProcessing.ts#L122-L497)

## Architecture Overview
The frontend communicates with backend endpoints through a typed HTTP client and real-time WebSocket channels. The video processing workflow combines asynchronous uploads, background pipeline execution, and live progress updates.

```mermaid
sequenceDiagram
participant UI as "UI Components"
participant Hook as "useVideoProcessing"
participant API as "api.ts"
participant WS as "WebSocket"
participant BE as "Backend"
UI->>Hook : "uploadVideo(file)"
Hook->>API : "uploadFile('/api/video/upload', file)"
API-->>Hook : "{video_id, status}"
Hook->>Hook : "updateState(uploading, progress)"
Hook->>API : "connectWebSocket('/ws/pipeline/' + video_id)"
API->>WS : "new WebSocket()"
WS-->>Hook : "onmessage {stage,status,message,progress}"
Hook->>Hook : "setState(stages, view)"
WS-->>Hook : "onerror/onclose"
Hook->>API : "getStatus(videoId) (polling fallback)"
API-->>Hook : "{stages}"
Hook->>API : "getMetadata/getTranscript"
API-->>Hook : "metadata, transcript"
Hook->>Hook : "setState(results)"
```

**Diagram sources**
- [useVideoProcessing.ts:162-211](file://frontend/src/lib/useVideoProcessing.ts#L162-L211)
- [useVideoProcessing.ts:215-276](file://frontend/src/lib/useVideoProcessing.ts#L215-L276)
- [useVideoProcessing.ts:313-348](file://frontend/src/lib/useVideoProcessing.ts#L313-L348)
- [useVideoProcessing.ts:280-309](file://frontend/src/lib/useVideoProcessing.ts#L280-L309)
- [api.ts:42-64](file://frontend/src/lib/api.ts#L42-L64)
- [api.ts:66-99](file://frontend/src/lib/api.ts#L66-L99)

## Detailed Component Analysis

### API Endpoint Mapping and Schemas
The frontend exposes convenience methods grouped under an API facade. These map to backend endpoints and models.

- Video endpoints
  - POST /api/video/upload: uploads a file and starts background processing
  - GET /api/video/{video_id}/status: retrieves pipeline status
  - GET /api/video/{video_id}/metadata: retrieves structured metadata
  - GET /api/video/{video_id}/transcript: retrieves transcript segments
  - POST /api/search: performs semantic search across videos
  - WS /ws/pipeline/{video_id}: streams progress events

- RFP endpoints
  - POST /api/rfp/create: generates an RFP from structured input
  - POST /api/rfp/regenerate-section: regenerates a specific section
  - GET /api/rfp/{rfp_id}/export/docx: exports RFP as DOCX
  - GET /api/rfp/{rfp_id}/export/pdf: exports RFP as PDF
  - POST /api/rfp/evaluate: evaluates vendor proposals asynchronously
  - GET /api/rfp/evaluation/{eval_id}/status: polls evaluation progress
  - GET /api/rfp/evaluation/{eval_id}/results: retrieves evaluation results
  - GET /api/rfp/evaluation/{eval_id}/export/xlsx: exports evaluation as XLSX
  - GET /api/rfp/evaluation/{eval_id}/export/pdf: exports evaluation as PDF

Typed request/response models:
- RFPCreatePayload: project metadata, evaluation criteria, timeline, budget, compliance, language, tone
- RFPCreateResponse: generated RFP identifier, title, status, sections, language
- EvaluationResults: vendor results, recommendation, follow-up questions
- WSMessage: standardized progress message for pipeline stages

**Section sources**
- [api.ts:164-244](file://frontend/src/lib/api.ts#L164-L244)
- [api.ts:101-161](file://frontend/src/lib/api.ts#L101-L161)
- [api.ts:68-74](file://frontend/src/lib/api.ts#L68-L74)
- [video.py:39-92](file://backend/routers/video.py#L39-L92)
- [video.py:124-138](file://backend/routers/video.py#L124-L138)
- [video.py:143-174](file://backend/routers/video.py#L143-L174)
- [video.py:179-195](file://backend/routers/video.py#L179-L195)
- [video.py:200-215](file://backend/routers/video.py#L200-L215)
- [video.py:220-268](file://backend/routers/video.py#L220-L268)
- [rfp.py:97-130](file://backend/routers/rfp.py#L97-L130)
- [rfp.py:133-167](file://backend/routers/rfp.py#L133-L167)
- [rfp.py:243-311](file://backend/routers/rfp.py#L243-L311)
- [rfp.py:314-329](file://backend/routers/rfp.py#L314-L329)
- [rfp.py:332-346](file://backend/routers/rfp.py#L332-L346)

### Data Transformation Patterns
**Updated** Comprehensive frontend data transformation layer implementation with detailed mapping logic for backend responses to VideoMetadata interface, including sophisticated face recognition data processing.

The data transformation layer in useVideoProcessing.ts implements sophisticated mapping logic to convert backend response structures into frontend-friendly interfaces, with particular emphasis on face recognition data transformation.

#### Backend Response Structure to Frontend Interface Mapping
The backend returns metadata in a hierarchical structure with enhanced face recognition capabilities:
```json
{
  "video_id": "string",
  "ingestion": {
    "duration": number
  },
  "visual_analysis": {
    "scenes": [...],
    "objects": [...],
    "landmarks": [...],
    "sensitive_content": [...],
    "faces": [...],
    "era_estimate": {
      "decade": "string"
    }
  },
  "metadata": {
    "title": "string",
    "topic": "string",
    "sentiment_tags": ["string"],
    "ebucore_xml": "string",
    "iptc_video_metadata": {}
  },
  "faces": ["detected_face_objects"]
}
```

The transformation logic maps this to the VideoMetadata interface with intelligent fallback mechanisms:

#### Enhanced Face Recognition Data Transformation
**Updated** The face recognition transformation now includes sophisticated fallback mechanisms and automatic numbering for unnamed persons:

1. **Dual Source Priority**: Prioritizes faces from top-level faces array over visual analysis faces
2. **Intelligent Naming**: Automatically assigns names to unnamed persons using sequential numbering
3. **Appearance Synthesis**: Creates synthetic appearance intervals from timestamps when direct data is unavailable
4. **Fallback Mechanisms**: Implements OCR-based naming fallback for unidentified faces
5. **Automatic Color Assignment**: Assigns deterministic colors from predefined palette

#### Key Transformation Examples
1. **Face Detection Priority**: `const sourceFaces = rawFaces.length > 0 ? rawFaces : rawVisualFaces;`
2. **Intelligent Naming**: `if (!name) { unknownCount++; name = `Person ${unknownCount}`; }`
3. **Appearance Synthesis**: `const parts = ts.split(":"); const seconds = (parseInt(parts[0] || "0") * 60) + parseInt(parts[1] || "0"); appearances = [{ start: seconds, end: seconds + 15 }];`
4. **OCR Fallback**: `_apply_ocr_fallback` function for unnamed persons
5. **Automatic Numbering**: Sequential Person 1, Person 2, Person 3 naming scheme

#### Transformation Implementation Details
The `fetchResults` function (lines 284-372) orchestrates the complete transformation with enhanced face processing:

```typescript
// Enhanced face transformation with fallbacks
let unknownCount = 0;
const mappedFaces: DetectedFace[] = sourceFaces.map((face) => {
  // Map name_en → name, with fallback
  let name = (face.name_en as string) || (face.name as string) || "";
  if (!name) {
    unknownCount++;
    name = `Person ${unknownCount}`;
  }

  // Map appearances or synthesize from timestamp
  let appearances = face.appearances as { start: number; end: number }[] | undefined;
  if (!appearances || appearances.length === 0) {
    const ts = face.timestamp as string;
    if (ts) {
      const parts = ts.split(":");
      const seconds = (parseInt(parts[0] || "0") * 60) + parseInt(parts[1] || "0");
      appearances = [{ start: seconds, end: seconds + 15 }];
    } else {
      appearances = [];
    }
  }

  return {
    name,
    name_ar: (face.name_ar as string) || undefined,
    appearances,
    color: "",
  };
});
```

#### Automatic Face Color Assignment Strategy
Deterministic color assignment ensures consistent visualization:
- Uses predefined color palette: `["#3B82F6", "#10B981", "#8B5CF6", "#F59E0B", "#EF4444", "#06B6D4", "#EC4899", "#14B8A6"]`
- Applies modulo arithmetic for cyclic color assignment
- Preserves existing face colors when present in backend data

#### Transcript Transformation
Simple but effective transformation:
- Extracts segments array from backend response
- Ensures proper typing with TranscriptSegment interface
- Handles missing segments gracefully with empty array fallback

**Section sources**
- [useVideoProcessing.ts:284-372](file://frontend/src/lib/useVideoProcessing.ts#L284-L372)
- [useVideoProcessing.ts:291-316](file://frontend/src/lib/useVideoProcessing.ts#L291-L316)
- [useVideoProcessing.ts:318-325](file://frontend/src/lib/useVideoProcessing.ts#L318-L325)
- [useVideoProcessing.ts:327-329](file://frontend/src/lib/useVideoProcessing.ts#L327-L329)
- [useVideoProcessing.ts:115-118](file://frontend/src/lib/useVideoProcessing.ts#L115-L118)
- [face_recognition.py:191-210](file://backend/pipeline/face_recognition.py#L191-L210)
- [reference_faces.json:1-101](file://backend/data/reference_faces.json#L1-L101)
- [faces.json:1-52](file://backend/uploads/32cf9631-ba74-4f0b-8a7c-c14bccf5a132/faces.json#L1-L52)

### Async Operations, Loading States, Error Boundaries, and Retry Mechanisms
- Upload: sets uploading state, simulates progress, handles errors, and transitions to processing view upon success
- WebSocket: receives real-time updates; on error or close, falls back to REST polling
- Polling: periodic status checks until all stages complete; triggers result fetch when done
- Search: debounced UI-triggered search with isSearching flag and empty results on failure
- Evaluation: background submission with periodic status polling; clears intervals on cleanup and error

**Section sources**
- [useVideoProcessing.ts:162-211](file://frontend/src/lib/useVideoProcessing.ts#L162-L211)
- [useVideoProcessing.ts:215-276](file://frontend/src/lib/useVideoProcessing.ts#L215-L276)
- [useVideoProcessing.ts:313-348](file://frontend/src/lib/useVideoProcessing.ts#L313-L348)
- [useVideoProcessing.ts:352-368](file://frontend/src/lib/useVideoProcessing.ts#L352-L368)
- [rfp-evaluator/page.tsx:27-98](file://frontend/src/app/rfp-evaluator/page.tsx#L27-L98)

### Caching Strategies, Optimistic Updates, and Offline Handling
- Caching: no explicit client-side cache; relies on backend static file serving for exports
- Optimistic updates: pipeline stage status updates are applied immediately upon receiving WebSocket messages
- Offline handling: WebSocket fallback to REST polling; search results cleared on error; evaluation polling stops on error and resets UI

**Section sources**
- [useVideoProcessing.ts:223-262](file://frontend/src/lib/useVideoProcessing.ts#L223-L262)
- [useVideoProcessing.ts:263-271](file://frontend/src/lib/useVideoProcessing.ts#L263-L271)
- [useVideoProcessing.ts:343-348](file://frontend/src/lib/useVideoProcessing.ts#L343-L348)
- [useVideoProcessing.ts:365-368](file://frontend/src/lib/useVideoProcessing.ts#L365-L368)

### Integration with Backend APIs and Real-Time Data Synchronization
- Backend CORS: configured to allow cross-origin requests
- Static file serving: uploads served via mounted static directory
- Pipeline orchestration: background tasks manage pipeline stages and broadcast progress via WebSocket
- Evaluation workflow: background evaluation updates status and results persisted to disk
- Face recognition pipeline: sophisticated AI-powered face matching with reference database integration

**Section sources**
- [main.py:27-35](file://backend/main.py#L27-L35)
- [main.py:35-44](file://backend/main.py#L35-L44)
- [video.py:95-120](file://backend/routers/video.py#L95-L120)
- [video.py:218-268](file://backend/routers/video.py#L218-L268)
- [rfp.py:219-238](file://backend/routers/rfp.py#L219-L238)
- [face_recognition.py:124-188](file://backend/pipeline/face_recognition.py#L124-L188)

## Dependency Analysis
The frontend components depend on the API client and the video processing hook. The hook encapsulates all integration logic, while components remain presentation-focused.

```mermaid
graph LR
UI_A["VideoUpload.tsx"] --> Hook["useVideoProcessing.ts"]
UI_B["archive/page.tsx"] --> Hook
UI_C["PipelineVisualizer.tsx"] --> Hook
UI_D["RFPForm.tsx"] --> API["api.ts"]
UI_E["rfp-creator/page.tsx"] --> API
UI_F["rfp-evaluator/page.tsx"] --> API
Hook --> API
API --> Backend["Backend Routers"]
Backend --> FacePipeline["Face Recognition Pipeline"]
FacePipeline --> ReferenceDB["Reference Faces Database"]
```

**Diagram sources**
- [VideoUpload.tsx:1-221](file://frontend/src/components/archive/VideoUpload.tsx#L1-L221)
- [archive/page.tsx:1-129](file://frontend/src/app/archive/page.tsx#L1-L129)
- [PipelineVisualizer.tsx:1-181](file://frontend/src/components/archive/PipelineVisualizer.tsx#L1-L181)
- [RFPForm.tsx:1-411](file://frontend/src/components/rfp/RFPForm.tsx#L1-L411)
- [rfp-creator/page.tsx:1-159](file://frontend/src/app/rfp-creator/page.tsx#L1-L159)
- [rfp-evaluator/page.tsx:1-178](file://frontend/src/app/rfp-evaluator/page.tsx#L1-L178)
- [useVideoProcessing.ts:1-497](file://frontend/src/lib/useVideoProcessing.ts#L1-L497)
- [api.ts:1-245](file://frontend/src/lib/api.ts#L1-L245)
- [video.py:1-268](file://backend/routers/video.py#L1-L268)
- [rfp.py:1-385](file://backend/routers/rfp.py#L1-L385)
- [face_recognition.py:1-319](file://backend/pipeline/face_recognition.py#L1-L319)
- [reference_faces.json:1-101](file://backend/data/reference_faces.json#L1-L101)

**Section sources**
- [useVideoProcessing.ts:122-497](file://frontend/src/lib/useVideoProcessing.ts#L122-L497)
- [api.ts:162-244](file://frontend/src/lib/api.ts#L162-L244)

## Performance Considerations
- WebSocket vs polling: WebSocket provides real-time updates; polling serves as a robust fallback
- Parallelization: metadata and transcript fetches occur concurrently after pipeline completion
- UI responsiveness: progress simulation during upload prevents blocking; skeleton loaders for RFP preview
- Cleanup: WebSocket and object URLs are released on component unmount to prevent memory leaks
- Data transformation optimization: efficient mapping reduces computational overhead during state updates
- Face recognition optimization: intelligent fallbacks reduce redundant processing for unnamed persons

## Troubleshooting Guide
Common issues and resolutions:
- Upload failures: verify backend upload directory permissions and network connectivity; inspect error messages propagated from API
- WebSocket errors: confirm backend CORS configuration and that the WebSocket endpoint is reachable; fallback polling ensures continued progress tracking
- Evaluation timeouts: adjust polling interval and handle transient errors gracefully; ensure sufficient vendor files and valid JSON inputs
- Search failures: validate query length and backend search index availability; clear search results on error
- Export failures: confirm backend export endpoints and file system permissions
- Data transformation errors: verify backend response structure consistency; check for missing fields in transformed data
- Face recognition failures: verify reference database availability and API key configuration; check OCR fallback mechanisms

**Section sources**
- [useVideoProcessing.ts:202-208](file://frontend/src/lib/useVideoProcessing.ts#L202-L208)
- [useVideoProcessing.ts:263-271](file://frontend/src/lib/useVideoProcessing.ts#L263-L271)
- [useVideoProcessing.ts:343-348](file://frontend/src/lib/useVideoProcessing.ts#L343-L348)
- [rfp-evaluator/page.tsx:86-98](file://frontend/src/app/rfp-evaluator/page.tsx#L86-L98)

## Conclusion
The frontend API integration layer provides a clean, typed interface to backend services with robust real-time capabilities. The useVideoProcessing hook centralizes state management, error handling, and integration logic, enabling responsive UIs for video processing and RFP workflows. The comprehensive data transformation layer ensures seamless mapping between backend response structures and frontend interface requirements, with particular emphasis on sophisticated face recognition data processing including intelligent fallbacks, automatic numbering for unnamed persons, and appearance synthesis. The design balances optimistic updates, fallback mechanisms, and clear separation of concerns between presentation and data access, while the enhanced face recognition pipeline provides reliable person identification with robust error handling and fallback strategies.
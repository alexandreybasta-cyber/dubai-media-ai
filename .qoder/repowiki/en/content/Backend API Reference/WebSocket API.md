# WebSocket API

<cite>
**Referenced Files in This Document**
- [backend/main.py](file://backend/main.py)
- [backend/routers/video.py](file://backend/routers/video.py)
- [backend/pipeline/orchestrator.py](file://backend/pipeline/orchestrator.py)
- [backend/config.py](file://backend/config.py)
- [frontend/src/lib/api.ts](file://frontend/src/lib/api.ts)
- [frontend/src/lib/useVideoProcessing.ts](file://frontend/src/lib/useVideoProcessing.ts)
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

## Introduction
This document describes the WebSocket real-time progress tracking system for video pipeline processing. It focuses on the `/ws/pipeline/{video_id}` endpoint that streams progress updates, completion notifications, and stage transitions to connected clients. It also covers client-side integration patterns, connection lifecycle management, error handling, reconnection strategies, and troubleshooting guidance.

## Project Structure
The WebSocket system spans backend and frontend components:
- Backend FastAPI router defines the WebSocket endpoint and orchestrates pipeline progress callbacks.
- Backend pipeline orchestrator emits progress events to registered WebSocket clients.
- Frontend API module provides a typed WebSocket connection helper and message interface.
- Frontend hook manages connection lifecycle, state updates, and fallback polling.

```mermaid
graph TB
subgraph "Backend"
A["FastAPI App<br/>backend/main.py"]
B["Video Router<br/>backend/routers/video.py"]
C["Pipeline Orchestrator<br/>backend/pipeline/orchestrator.py"]
D["Config<br/>backend/config.py"]
end
subgraph "Frontend"
E["API Client<br/>frontend/src/lib/api.ts"]
F["Video Processing Hook<br/>frontend/src/lib/useVideoProcessing.ts"]
end
A --> B
B --> C
B --> D
E --> F
```

**Diagram sources**
- [backend/main.py:1-44](file://backend/main.py#L1-L44)
- [backend/routers/video.py:1-267](file://backend/routers/video.py#L1-L267)
- [backend/pipeline/orchestrator.py:1-329](file://backend/pipeline/orchestrator.py#L1-L329)
- [backend/config.py:1-21](file://backend/config.py#L1-L21)
- [frontend/src/lib/api.ts:1-245](file://frontend/src/lib/api.ts#L1-L245)
- [frontend/src/lib/useVideoProcessing.ts:1-421](file://frontend/src/lib/useVideoProcessing.ts#L1-L421)

**Section sources**
- [backend/main.py:1-44](file://backend/main.py#L1-L44)
- [backend/routers/video.py:1-267](file://backend/routers/video.py#L1-L267)
- [frontend/src/lib/api.ts:1-245](file://frontend/src/lib/api.ts#L1-L245)
- [frontend/src/lib/useVideoProcessing.ts:1-421](file://frontend/src/lib/useVideoProcessing.ts#L1-L421)

## Core Components
- WebSocket Endpoint (`/ws/pipeline/{video_id}`)
  - Accepts WebSocket connections and registers them per video_id.
  - Sends initial status snapshot if available.
  - Responds to client ping messages with pong replies.
  - Unregisters connections on disconnect or cleanup.
- Pipeline Orchestrator
  - Executes pipeline stages sequentially and emits progress via callback to all connected WebSocket clients.
  - Emits stage transitions, progress percentages, and completion notifications.
- Frontend API Client
  - Provides a typed WebSocket connection helper with onmessage, onerror, and onclose handlers.
  - Defines the `WSMessage` interface for incoming progress events.
- Frontend Hook
  - Manages connection lifecycle, updates UI state based on progress, and falls back to REST polling on WebSocket errors/closures.

Key WebSocket message format:
- Fields: `video_id`, `stage`, `message`, `progress`, `status`
- Example scenarios:
  - Initial connection: `stage="connected"`, `status` reflects current pipeline status.
  - Stage progress: `stage` equals a pipeline stage id, `status` indicates processing state.
  - Completion: `stage="done"` with final status and 100% progress.

**Section sources**
- [backend/routers/video.py:220-266](file://backend/routers/video.py#L220-L266)
- [backend/pipeline/orchestrator.py:44-206](file://backend/pipeline/orchestrator.py#L44-L206)
- [frontend/src/lib/api.ts:68-99](file://frontend/src/lib/api.ts#L68-L99)
- [frontend/src/lib/useVideoProcessing.ts:215-276](file://frontend/src/lib/useVideoProcessing.ts#L215-L276)

## Architecture Overview
The WebSocket pipeline streams progress from the orchestrator to clients. The backend maintains active connections per video and broadcasts updates when the orchestrator invokes the callback.

```mermaid
sequenceDiagram
participant Client as "Client App"
participant WS as "WebSocket Endpoint<br/>/ws/pipeline/{video_id}"
participant Orchestrator as "Pipeline Orchestrator"
participant Storage as "status.json"
Client->>WS : "Connect"
WS->>Storage : "Read current status"
WS-->>Client : "Initial progress event"
loop "Pipeline stages"
Orchestrator->>WS : "Callback(stage, message, progress, status)"
WS-->>Client : "Progress event"
end
Orchestrator->>WS : "Callback(stage='done', status, progress=100)"
WS-->>Client : "Completion event"
Client->>WS : "Send 'ping'"
WS-->>Client : "Reply 'pong' twice"
Client-->>WS : "Close"
WS->>WS : "Unregister connection"
```

**Diagram sources**
- [backend/routers/video.py:220-266](file://backend/routers/video.py#L220-L266)
- [backend/pipeline/orchestrator.py:95-206](file://backend/pipeline/orchestrator.py#L95-L206)
- [frontend/src/lib/api.ts:76-99](file://frontend/src/lib/api.ts#L76-L99)

## Detailed Component Analysis

### WebSocket Endpoint (`/ws/pipeline/{video_id}`)
Responsibilities:
- Accept connections and register per-video client lists.
- Send initial status snapshot if present.
- Handle keepalive via ping/pong.
- Gracefully unregister on disconnect or cleanup.

Behavior highlights:
- On connect: registers the WebSocket under the given video_id.
- On disconnect: removes the WebSocket from the registry.
- On error: logs debug info and continues cleanup.

```mermaid
flowchart TD
Start(["Connect"]) --> Accept["Accept WebSocket"]
Accept --> Register["Register connection by video_id"]
Register --> CheckStatus{"status.json exists?"}
CheckStatus --> |Yes| SendSnapshot["Send initial progress event"]
CheckStatus --> |No| AwaitPing["Await client ping"]
SendSnapshot --> AwaitPing
AwaitPing --> ReceiveText["Receive client text"]
ReceiveText --> IsPing{"Is 'ping'?"}
IsPing --> |Yes| ReplyPong["Send two 'pong' events"]
ReplyPong --> AwaitPing
IsPing --> |No| AwaitPing
AwaitPing --> Disconnect["Client disconnect or error"]
Disconnect --> Unregister["Remove from active registry"]
Unregister --> End(["End"])
```

**Diagram sources**
- [backend/routers/video.py:220-266](file://backend/routers/video.py#L220-L266)

**Section sources**
- [backend/routers/video.py:220-266](file://backend/routers/video.py#L220-L266)

### Pipeline Orchestrator Progress Callback
Responsibilities:
- Execute pipeline stages sequentially.
- Emit progress updates to all registered WebSocket clients.
- Persist status to disk after each stage and on completion.

Message emission pattern:
- For each stage: emits `{stage, message, progress, status}`.
- On completion: emits `{stage="done", message, progress=100, status}`.

```mermaid
sequenceDiagram
participant Orchestrator as "Pipeline Orchestrator"
participant Registry as "_active_ws registry"
participant WS as "WebSocket Clients"
Orchestrator->>Registry : "Get clients for video_id"
Orchestrator->>WS : "send_json({stage, message, progress, status})"
Orchestrator->>Registry : "Handle send failures"
Orchestrator->>WS : "On completion : send_json({stage='done', progress=100, status})"
```

**Diagram sources**
- [backend/pipeline/orchestrator.py:95-206](file://backend/pipeline/orchestrator.py#L95-L206)
- [backend/routers/video.py:95-120](file://backend/routers/video.py#L95-L120)

**Section sources**
- [backend/pipeline/orchestrator.py:44-206](file://backend/pipeline/orchestrator.py#L44-L206)
- [backend/routers/video.py:95-120](file://backend/routers/video.py#L95-L120)

### Frontend WebSocket Client Integration
Responsibilities:
- Establish WebSocket connections using a typed helper.
- Parse incoming progress events and update UI state.
- Implement fallback polling via REST status endpoint on WebSocket errors/closures.
- Manage connection lifecycle and cleanup.

Client-side patterns:
- Connection: use `connectWebSocket('/ws/pipeline/{video_id}', onMessage, onError, onClose)`.
- Message handling: update stage status, timestamps, and view state.
- Fallback: on error/close, poll `/api/video/{video_id}/status` and optionally fetch results.

```mermaid
sequenceDiagram
participant Hook as "useVideoProcessing"
participant API as "API Client"
participant WS as "WebSocket"
participant REST as "REST Status"
Hook->>API : "connectWebSocket('/ws/pipeline/{videoId}')"
API->>WS : "new WebSocket()"
WS-->>Hook : "onmessage (WSMessage)"
Hook->>Hook : "Update stages and view"
WS-->>Hook : "onerror/onclose"
Hook->>REST : "pollStatus(videoId)"
REST-->>Hook : "Stage statuses"
Hook->>Hook : "Update stages and view"
```

**Diagram sources**
- [frontend/src/lib/api.ts:76-99](file://frontend/src/lib/api.ts#L76-L99)
- [frontend/src/lib/useVideoProcessing.ts:215-276](file://frontend/src/lib/useVideoProcessing.ts#L215-L276)

**Section sources**
- [frontend/src/lib/api.ts:68-99](file://frontend/src/lib/api.ts#L68-L99)
- [frontend/src/lib/useVideoProcessing.ts:215-276](file://frontend/src/lib/useVideoProcessing.ts#L215-L276)

### Message Formats and Stage Transitions
- Initial connection event:
  - `stage="connected"`
  - `status`: current pipeline status
  - `progress`: current progress percentage
- Stage progress events:
  - `stage`: one of pipeline stage ids
  - `status`: "running", "completed", or "failed"
  - `progress`: cumulative percentage
- Completion event:
  - `stage="done"`
  - `status`: final pipeline status
  - `progress`: 100

Frontend state mapping:
- Updates stage status, timestamps, and view transitions based on received events.
- Triggers result fetch upon completion.

**Section sources**
- [backend/routers/video.py:239-245](file://backend/routers/video.py#L239-L245)
- [backend/pipeline/orchestrator.py:228-281](file://backend/pipeline/orchestrator.py#L228-L281)
- [frontend/src/lib/useVideoProcessing.ts:223-261](file://frontend/src/lib/useVideoProcessing.ts#L223-L261)

## Dependency Analysis
- Backend dependencies:
  - FastAPI app mounts the video router.
  - Video router depends on the orchestrator and configuration.
  - Orchestrator depends on stage modules and writes status to disk.
- Frontend dependencies:
  - API client provides WebSocket helper and REST wrappers.
  - Hook consumes API client and manages UI state.

```mermaid
graph LR
Config["Config<br/>backend/config.py"] --> Router["Video Router<br/>backend/routers/video.py"]
Router --> Orchestrator["Pipeline Orchestrator<br/>backend/pipeline/orchestrator.py"]
App["FastAPI App<br/>backend/main.py"] --> Router
API["API Client<br/>frontend/src/lib/api.ts"] --> Hook["useVideoProcessing<br/>frontend/src/lib/useVideoProcessing.ts"]
```

**Diagram sources**
- [backend/main.py:1-44](file://backend/main.py#L1-L44)
- [backend/routers/video.py:1-267](file://backend/routers/video.py#L1-L267)
- [backend/pipeline/orchestrator.py:1-329](file://backend/pipeline/orchestrator.py#L1-L329)
- [backend/config.py:1-21](file://backend/config.py#L1-L21)
- [frontend/src/lib/api.ts:1-245](file://frontend/src/lib/api.ts#L1-L245)
- [frontend/src/lib/useVideoProcessing.ts:1-421](file://frontend/src/lib/useVideoProcessing.ts#L1-L421)

**Section sources**
- [backend/main.py:1-44](file://backend/main.py#L1-L44)
- [backend/routers/video.py:1-267](file://backend/routers/video.py#L1-L267)
- [backend/pipeline/orchestrator.py:1-329](file://backend/pipeline/orchestrator.py#L1-L329)
- [frontend/src/lib/api.ts:1-245](file://frontend/src/lib/api.ts#L1-L245)
- [frontend/src/lib/useVideoProcessing.ts:1-421](file://frontend/src/lib/useVideoProcessing.ts#L1-L421)

## Performance Considerations
- Connection scaling:
  - Active connections are tracked per video_id. Ensure appropriate cleanup to avoid memory leaks.
- Broadcast efficiency:
  - The orchestrator sends updates to all registered clients. Consider batching or throttling if many clients are expected.
- Disk I/O:
  - Status persistence occurs frequently during stages. Ensure storage performance is adequate for concurrent writes.
- Network resilience:
  - Client-side ping/pong keeps connections alive. Monitor for excessive reconnects indicating network instability.
- Frontend rendering:
  - Frequent state updates can trigger re-renders. Use memoization and minimal state updates where possible.

## Troubleshooting Guide
Common issues and resolutions:
- Connection fails immediately:
  - Verify backend CORS settings and that the WebSocket URL uses the correct scheme (ws/wss).
  - Confirm the endpoint path matches `/ws/pipeline/{video_id}`.
- No progress events received:
  - Ensure the pipeline is running and that `status.json` exists for the video_id.
  - Check that the orchestrator callback is invoked and that `_active_ws` contains the connection.
- Frequent reconnections:
  - Implement client-side exponential backoff and jitter for reconnection attempts.
  - Validate server-side keepalive behavior and network stability.
- Inconsistent state:
  - Use REST polling fallback (`/api/video/{video_id}/status`) when WebSocket is unavailable.
  - Ensure the frontend updates stages based on the latest received status.
- Completion not detected:
  - Listen for `stage="done"` with `progress=100` and `status` reflecting final outcome.
  - Trigger result fetch for metadata and transcript after completion.

Operational checks:
- Backend health: GET `/api/health` to confirm service availability.
- Status file: Verify presence of `status.json` under the video directory.
- Environment configuration: Ensure `BASE_URL`, `UPLOAD_DIR`, and API keys are set appropriately.

**Section sources**
- [backend/routers/video.py:220-266](file://backend/routers/video.py#L220-L266)
- [backend/pipeline/orchestrator.py:95-206](file://backend/pipeline/orchestrator.py#L95-L206)
- [frontend/src/lib/useVideoProcessing.ts:313-348](file://frontend/src/lib/useVideoProcessing.ts#L313-L348)

## Conclusion
The WebSocket progress tracking system provides real-time visibility into video pipeline execution. The backend streams structured progress events, while the frontend integrates them into a responsive UI with robust fallback mechanisms. Following the documented patterns ensures reliable, scalable, and maintainable real-time updates.
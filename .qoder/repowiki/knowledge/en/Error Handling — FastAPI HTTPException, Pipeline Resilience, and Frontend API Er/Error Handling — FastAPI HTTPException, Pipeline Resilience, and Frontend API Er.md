---
kind: error_handling
name: Error Handling — FastAPI HTTPException, Pipeline Resilience, and Frontend API Error Propagation
category: error_handling
scope:
    - '**'
source_files:
    - backend/routers/video.py
    - backend/routers/rfp.py
    - backend/pipeline/orchestrator.py
    - backend/services/rfp_creator.py
    - backend/services/rfp_evaluator.py
    - frontend/src/lib/api.ts
    - frontend/src/lib/useVideoProcessing.ts
---

# Error Handling System

This codebase employs a **layered error handling strategy** across its FastAPI backend and Next.js frontend, combining framework-native exception mechanisms with custom resilience patterns for long-running AI pipelines.

## Backend: FastAPI HTTPException Pattern

### Core Mechanism
The backend uses **FastAPI's `HTTPException`** as the primary error signaling mechanism. All router endpoints raise `HTTPException` with appropriate HTTP status codes and human-readable `detail` messages:

- **400 Bad Request**: Validation failures, missing inputs, malformed JSON (e.g., invalid vendor names, insufficient vendor files)
- **404 Not Found**: Missing resources (video IDs, RFPs, transcripts, evaluations)
- **500 Internal Server Error**: Unexpected runtime failures (file I/O errors, export generation failures, search failures)
- **502 Bad Gateway**: External service failures (DashScope API errors propagated from services)

### Status Code Conventions by Layer

| Layer | Pattern | Example |
|-------|---------|---------|
| **Routers** (`backend/routers/`) | Catch exceptions from services/pipeline, convert to `HTTPException` | `raise HTTPException(status_code=404, detail=f"Video {video_id} not found")` |
| **Services** (`backend/services/`) | Raise `ValueError` / `RuntimeError` for domain-level errors | `raise ValueError("DASHSCOPE_API_KEY is not configured")` |
| **Pipeline** (`backend/pipeline/`) | Swallow exceptions internally, record in status.json | Stage failures stored as `{"error": "..."}` in results |

### Service-Level Exception Translation

Services (`rfp_creator.py`, `rfp_evaluator.py`) do **not** use `HTTPException`. Instead they raise standard Python exceptions:

- **`ValueError`**: Configuration or input validation errors (e.g., missing API key)
- **`RuntimeError`**: External service failures after retries exhausted

Routers catch these and translate them:
```python
try:
    rfp_data = await rfp_creator.generate_rfp(input_data)
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except RuntimeError as e:
    raise HTTPException(status_code=502, detail=str(e))
```

This separation keeps services framework-agnostic and testable.

## Pipeline Resilience: Per-Stage Error Isolation

The **`PipelineOrchestrator`** (`backend/pipeline/orchestrator.py`) implements a **fault-tolerant, stage-by-stage execution model**:

### Key Design Decisions

1. **Non-fatal stage failures**: Each pipeline stage (ingestion, visual_analysis, audio_analysis, face_recognition, metadata_structuring, search_index) is wrapped in a try/except block. A failure in one stage does **not** abort the entire pipeline.

2. **Error recording**: Failed stages store their error message in `status["errors"][stage_name]` and write `{"error": error_msg}` to the corresponding result JSON file.

3. **Completion with errors**: The final pipeline status is `"completed_with_errors"` if any stage failed, versus `"completed"` if all succeeded.

4. **WebSocket progress notifications**: Errors are broadcast to connected WebSocket clients via the `ws_callback` with `status="failed"`.

5. **Background task isolation**: The `_run_pipeline` background task in `video.py` catches all exceptions at the top level and logs them, preventing unhandled promise rejections from crashing the server:
```python
async def _run_pipeline(video_id: str, video_path: str):
    try:
        await _orchestrator.process_video(video_id, video_path, ws_callback=ws_callback)
    except Exception as e:
        logger.error("Pipeline failed for %s: %s", video_id, e)
```

### Status File as Error Source of Truth

Each video processing job maintains a `status.json` file that serves as the persistent error state:
```json
{
  "status": "completed_with_errors",
  "stages": {
    "visual_analysis": "failed",
    "audio_analysis": "completed"
  },
  "errors": {
    "visual_analysis": "RuntimeError: DashScope API failed after 3 attempts: ..."
  }
}
```

## External Service Retry Logic

Both `RFPCreator` and `RFPEvaluator` implement **exponential backoff retry** for DashScope API calls:

- **Max retries**: 3 attempts
- **Backoff**: `2^attempt` seconds between retries
- **Rate limit handling**: Special handling for HTTP 429 responses with extended wait times
- **Fallback evaluation**: When JSON parsing of LLM responses fails, a `_fallback_evaluation()` method provides default scores to prevent total evaluation failure

## Frontend: Typed Error Propagation

### API Client Error Handling (`frontend/src/lib/api.ts`)

The `apiFetch` and `uploadFile` helpers check `response.ok` and extract error details from the JSON response:

```typescript
if (!response.ok) {
  const error = await response.json().catch(() => ({}));
  throw new Error(
    error.detail || `API Error: ${response.status} ${response.statusText}`
  );
}
```

This ensures FastAPI's `HTTPException.detail` messages propagate to the UI.

### Component-Level Error State

Frontend pages use React state to track and display errors:

- **`useVideoProcessing` hook**: Maintains `state.error` for upload/pipeline errors
- **RFP Creator page**: Uses `useState<string | null>(null)` for error display with dismissible error banners
- **RFP Evaluator page**: Polls evaluation status and displays `status.error` from the backend

### WebSocket Fallback Strategy

When WebSocket connections fail, the frontend falls back to **HTTP polling** every 3 seconds via `startPollingFallback()`. This ensures pipeline progress tracking continues even if real-time updates are unavailable.

## Developer Rules and Conventions

1. **Routers must catch service exceptions**: Never let `ValueError` or `RuntimeError` escape a router endpoint. Always translate to `HTTPException` with an appropriate status code.

2. **Use specific status codes**: Prefer 400 for client errors, 404 for missing resources, 502 for upstream service failures, and 500 only for unexpected internal errors.

3. **Pipeline stages must not crash the server**: All stage-level exceptions are caught and recorded. The orchestrator continues to subsequent stages.

4. **Log errors before raising**: Use `logger.error()` or `logger.warning()` before raising exceptions to ensure diagnostic context is preserved.

5. **Frontend errors should be user-friendly**: Extract `error.detail` from API responses and display concise messages. Avoid exposing raw stack traces to users.

6. **Background tasks must have top-level exception handlers**: Any `asyncio.create_task()` call should wrap its coroutine in a try/except to prevent silent failures.

7. **Services should remain framework-agnostic**: Services raise standard Python exceptions; routers handle the FastAPI-specific `HTTPException` conversion.

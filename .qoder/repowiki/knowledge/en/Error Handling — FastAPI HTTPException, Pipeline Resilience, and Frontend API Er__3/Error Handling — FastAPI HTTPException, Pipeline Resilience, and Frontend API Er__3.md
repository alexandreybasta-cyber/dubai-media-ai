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
    - backend/pipeline/ingestion.py
    - frontend/src/lib/api.ts
    - frontend/src/lib/useVideoProcessing.ts
---

## Overview

This codebase employs a **layered error handling strategy** combining FastAPI's `HTTPException` for API-level errors, try-catch resilience in the video processing pipeline (with graceful degradation), retry-with-backoff for external AI service calls, and centralized error propagation on the frontend via a typed fetch wrapper.

---

## Backend Error Handling

### 1. FastAPI HTTPException Pattern

All API routers (`backend/routers/video.py`, `backend/routers/rfp.py`) use FastAPI's built-in `HTTPException` to signal client-facing errors with appropriate HTTP status codes:

- **404 Not Found**: Resource not found (e.g., missing video ID, RFP ID, transcript)
- **400 Bad Request**: Invalid input (e.g., JSON parse failures, mismatched vendor counts, empty extracted text)
- **500 Internal Server Error**: Unexpected server-side failures (file I/O, export generation)
- **502 Bad Gateway**: External AI service failures (DashScope API)

Example from `routers/video.py`:
```python
if not os.path.exists(status_path):
    raise HTTPException(status_code=404, detail=f"Video {video_id} not found")
```

Example from `routers/rfp.py`:
```python
try:
    rfp_data = await rfp_creator.generate_rfp(input_data)
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except RuntimeError as e:
    raise HTTPException(status_code=502, detail=str(e))
```

### 2. Service-Level Exception Translation

Services (`rfp_creator.py`, `rfp_evaluator.py`) raise Python exceptions that are caught and translated at the router layer:

- **`ValueError`**: Configuration or validation errors (e.g., missing `DASHSCOPE_API_KEY`)
- **`RuntimeError`**: External service failures after retries exhausted

The `_call_llm` method in both services implements **exponential backoff retry logic** (up to 3 attempts) with specific handling for:
- HTTP timeout (`httpx.TimeoutException`)
- Rate limiting (HTTP 429 in `rfp_evaluator.py`)
- Generic network/parse errors

After all retries fail, a `RuntimeError` is raised with the last error message.

### 3. Pipeline Resilience (Graceful Degradation)

The `PipelineOrchestrator` (`pipeline/orchestrator.py`) implements **per-stage error isolation**. Each of the 6 pipeline stages runs inside `_run_stage()`, which wraps execution in a try-catch block:

- On failure, the stage is marked `"failed"` and the error message is stored in `status["errors"][stage_name]`
- The pipeline **continues to subsequent stages** rather than aborting entirely
- Failed stages save `{"error": error_msg}` to their result JSON file
- Final status is `"completed_with_errors"` if any stage failed

This design ensures partial results are still available even when individual AI analysis stages fail.

### 4. Logging Strategy

All modules use Python's standard `logging` module with module-level loggers:
```python
logger = logging.getLogger(__name__)
```

- `logger.error()` for failures (with full traceback in orchestrator)
- `logger.warning()` for recoverable issues (e.g., missing metadata files)
- `logger.info()` for stage completions
- `logger.debug()` for transient WebSocket errors

---

## Frontend Error Handling

### 1. Centralized API Error Wrapper

`frontend/src/lib/api.ts` provides two core functions (`apiFetch`, `uploadFile`) that check `response.ok` and throw a unified `Error` with the backend's `detail` field:

```typescript
if (!response.ok) {
  const error = await response.json().catch(() => ({}));
  throw new Error(
    error.detail || `API Error: ${response.status} ${response.statusText}`
  );
}
```

This pattern is replicated inline for the `evaluate` endpoint due to its FormData-based request.

### 2. React Hook Error State

`useVideoProcessing.ts` maintains an `error: string | null` field in state. Errors from upload, search, or result-fetching operations are captured via try-catch and stored:

```typescript
} catch (err) {
  updateState({
    uploadState: "error",
    uploadProgress: 0,
    error: err instanceof Error ? err.message : "Upload failed",
  });
}
```

### 3. WebSocket Fallback to Polling

If the WebSocket connection fails or closes, the hook automatically falls back to HTTP polling (`startPollingFallback`) every 3 seconds. Polling errors are silently ignored to avoid UI noise, relying on the next poll attempt.

### 4. Graceful Result Fetching

When fetching metadata/transcript after pipeline completion, errors are logged to console but do not crash the UI:
```typescript
} catch (err) {
  console.error("Failed to fetch results:", err);
}
```

---

## Key Conventions for Developers

1. **Always use `HTTPException` in routers** — never let raw Python exceptions propagate to the client. Translate service exceptions into appropriate HTTP status codes.

2. **Use specific exception types in services** — `ValueError` for validation/config issues, `RuntimeError` for external service failures. This enables precise translation at the router layer.

3. **Implement retry with backoff for external calls** — the `_call_llm` pattern (3 attempts, exponential backoff, rate-limit awareness) should be reused for any new external API integrations.

4. **Pipeline stages must not crash the entire pipeline** — use the `_run_stage` pattern to isolate failures. Store errors in the status object so clients can display partial results.

5. **Frontend errors should be user-friendly** — extract the `detail` field from API errors. Use type guards (`err instanceof Error`) to handle unknown error types safely.

6. **Log at the right level** — `error` for failures requiring investigation, `warning` for expected edge cases, `info` for normal flow milestones.

7. **No global error middleware** — this codebase does not use FastAPI exception handlers or custom middleware. All error handling is explicit at the route/service level.

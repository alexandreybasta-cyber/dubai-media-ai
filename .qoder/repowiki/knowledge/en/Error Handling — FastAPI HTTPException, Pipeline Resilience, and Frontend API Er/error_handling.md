## Overview

The Dubai Media AI Platform uses a pragmatic, layered error handling strategy across its backend (FastAPI) and frontend (Next.js). There is no centralized error module or custom exception hierarchy. Instead, the codebase relies on:

1. **FastAPI's `HTTPException`** for API-level error signaling in routers.
2. **Python standard exceptions** (`ValueError`, `RuntimeError`) raised from service layers and caught at router boundaries.
3. **Try/except blocks with logging** throughout pipeline stages to ensure fault isolation — individual stage failures do not abort the entire video processing pipeline.
4. **Frontend `apiFetch` wrapper** that converts non-OK HTTP responses into JavaScript `Error` objects using the `detail` field from FastAPI error responses.

---

## Backend: Router Layer (`backend/routers/`)

### Pattern: Raise `HTTPException` with semantic status codes

All API endpoints use FastAPI's `HTTPException` to signal errors to clients. Status codes are chosen semantically:

| Status Code | Usage |
|-------------|-------|
| `400` | Invalid input, missing data, JSON parse errors, validation failures |
| `404` | Resource not found (video, RFP, evaluation, transcript) |
| `500` | Internal server errors (file I/O failures, export generation failures) |
| `502` | Upstream service failure (DashScope API errors propagated from services) |

**Example from `routers/video.py`:**
```python
if not os.path.exists(status_path):
    raise HTTPException(status_code=404, detail=f"Video {video_id} not found")
```

**Example from `routers/rfp.py`:**
```python
try:
    rfp_data = await rfp_creator.generate_rfp(input_data)
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except RuntimeError as e:
    raise HTTPException(status_code=502, detail=str(e))
```

### Convention: Catch broad `Exception` for I/O operations

File read/write operations are wrapped in try/except blocks that log the error and raise a generic `HTTPException(500)`:

```python
try:
    async with aiofiles.open(video_path, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            await out.write(chunk)
except Exception as e:
    logger.error("Failed to save uploaded file: %s", e)
    raise HTTPException(status_code=500, detail="Failed to save uploaded file")
```

This pattern appears consistently in `video.py` (upload, status read, metadata load, transcript read) and `rfp.py` (export endpoints).

---

## Backend: Service Layer (`backend/services/`)

### Pattern: Raise `ValueError` for configuration errors, `RuntimeError` for upstream failures

Services (`RFPCreator`, `RFPEvaluator`) do NOT catch errors internally for API calls. Instead:

- **`ValueError`** is raised when required configuration is missing (e.g., `DASHSCOPE_API_KEY` not set).
- **`RuntimeError`** is raised after exhausting retries against the DashScope API.

These exceptions propagate to the router layer, where they are caught and converted to appropriate `HTTPException` responses.

**Example from `services/rfp_creator.py`:**
```python
async def _call_llm(self, messages: list[dict], temperature: float = 0.7) -> str:
    if not self.api_key:
        raise ValueError("DASHSCOPE_API_KEY is not configured...")
    # ... retry loop ...
    raise RuntimeError(f"DashScope API failed after {self.max_retries} attempts: {last_error}")
```

### Retry with exponential backoff

Both `RFPCreator` and `RFPEvaluator` implement a 3-attempt retry loop with `await asyncio.sleep(2 ** attempt)` between attempts. The `RFPEvaluator` additionally handles HTTP 429 (rate limiting) with special wait logic.

### Fallback evaluation

When JSON parsing of LLM output fails in `RFPEvaluator.evaluate_single_vendor()`, a `_fallback_evaluation()` method produces a safe default result rather than crashing:

```python
except json.JSONDecodeError:
    logger.error(f"Failed to parse evaluation JSON for {vendor_name}")
    result = self._fallback_evaluation(criteria)
```

---

## Backend: Pipeline Layer (`backend/pipeline/`)

### Architecture: Fault-isolating orchestrator

The `PipelineOrchestrator` (`pipeline/orchestrator.py`) is the most sophisticated error handling component. It executes six sequential stages (ingestion, visual analysis, audio analysis, face recognition, metadata structuring, search index) and ensures that **a failure in one stage does not abort the entire pipeline**.

**Key mechanism in `_run_stage()`:**
```python
try:
    result = await coro_fn()
    results[result_key] = result
    status["stages"][stage_name] = "completed"
except Exception as e:
    error_msg = f"{type(e).__name__}: {str(e)}"
    logger.error("Stage %s failed: %s\n%s", stage_name, error_msg, traceback.format_exc())
    status["stages"][stage_name] = "failed"
    status["errors"][stage_name] = error_msg
    results[result_key] = {"error": error_msg}
```

After all stages complete, the orchestrator sets the overall status to either `"completed"` or `"completed_with_errors"` based on whether any stage failed.

### Stage-specific error patterns

| Module | Error Strategy |
|--------|---------------|
| `ingestion.py` | `_probe_video()` catches `ffmpeg.Error` and returns safe defaults; `_extract_audio()` and `_generate_thumbnail()` re-raise exceptions to fail the stage |
| `audio_analysis.py` | Returns `_empty_result(error_msg)` dicts instead of raising; 3-attempt retry on ASR submission; graceful timeout after 120 polls |
| `face_recognition.py` | Returns unidentified face dicts with `identified: False` on API failure; 3-attempt retry per face |
| `visual_analysis.py` | (Not read, but follows similar retry/fallback pattern based on grep results) |

### Logging convention

All pipeline modules use Python's `logging` module with `logger.error()` for failures and `logger.warning()` for non-critical issues. The orchestrator includes full tracebacks via `traceback.format_exc()`.

---

## Frontend: API Client (`frontend/src/lib/api.ts`)

### Pattern: Centralized `apiFetch` wrapper

All API calls go through `apiFetch<T>()` or `uploadFile<T>()`, which check `response.ok` and throw a JavaScript `Error` with the `detail` field from the FastAPI response:

```typescript
if (!response.ok) {
  const error = await response.json().catch(() => ({}));
  throw new Error(error.detail || `API Error: ${response.status} ${response.statusText}`);
}
```

This means React components using these functions must wrap calls in try/catch or use error boundaries.

### WebSocket error handling

The `connectWebSocket()` helper logs errors to `console.error` and invokes optional `onError`/`onClose` callbacks. No automatic reconnection is implemented.

---

## Rules Developers Should Follow

1. **Router layer**: Always raise `HTTPException` with an appropriate status code. Never let raw Python exceptions escape to the client.
2. **Service layer**: Raise `ValueError` for invalid inputs/configuration, `RuntimeError` for unrecoverable upstream failures. Let routers convert these to HTTP responses.
3. **Pipeline stages**: Never let exceptions escape `_run_stage()`. Capture errors, log them, store them in the status object, and continue to the next stage.
4. **External API calls**: Implement 3-attempt retry with exponential backoff (`2 ** attempt`). Handle rate limiting (HTTP 429) separately if applicable.
5. **File I/O**: Wrap in try/except, log the error, and raise `HTTPException(500)` with a generic message (do not expose internal paths or stack traces).
6. **Frontend**: Use `apiFetch` for all API calls. Handle errors at the component level with try/catch or error boundaries. Do not call `fetch` directly for API endpoints.
7. **Logging**: Use `logger.error()` for failures, `logger.warning()` for degraded-but-functional states, `logger.info()` for normal progress. Include context (video_id, stage name) in log messages.

---

## Key Files

- `backend/routers/video.py` — Video upload, status, metadata, search endpoints with HTTPException usage
- `backend/routers/rfp.py` — RFP creation/evaluation endpoints with ValueError/RuntimeError → HTTPException mapping
- `backend/pipeline/orchestrator.py` — Fault-isolating pipeline orchestrator with per-stage error capture
- `backend/services/rfp_creator.py` — LLM service with retry/backoff and ValueError/RuntimeError raises
- `backend/services/rfp_evaluator.py` — Evaluation service with retry/backoff, rate-limit handling, and fallback evaluation
- `backend/pipeline/ingestion.py` — FFmpeg-based ingestion with ffmpeg.Error catching
- `backend/pipeline/audio_analysis.py` — ASR polling with empty-result fallback pattern
- `frontend/src/lib/api.ts` — Centralized API client with error-to-Error conversion
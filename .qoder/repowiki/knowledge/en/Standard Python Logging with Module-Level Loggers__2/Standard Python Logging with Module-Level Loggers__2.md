---
kind: logging_system
name: Standard Python Logging with Module-Level Loggers
category: logging_system
scope:
    - '**'
source_files:
    - backend/pipeline/orchestrator.py
    - backend/pipeline/ingestion.py
    - backend/pipeline/visual_analysis.py
    - backend/pipeline/search_index.py
    - backend/routers/video.py
    - backend/services/rfp_creator.py
    - backend/config.py
    - backend/main.py
---

## Overview

The backend uses **Python's built-in `logging` module** exclusively — no third-party structured logging framework (e.g., structlog, loguru) is configured. Every Python module in the `backend/` tree follows the same convention: a module-level logger created via `logging.getLogger(__name__)`. There is **no centralized logging configuration** (`logging.basicConfig`, `dictConfig`, handlers, or formatters) anywhere in the codebase; the application relies entirely on Python's default root logger behavior.

## Key Files and Packages

All logging usage lives in the FastAPI backend under `backend/`. The pattern is applied uniformly across three layers:

| Layer | Representative files |
|---|---|
| **Pipeline stages** | `backend/pipeline/orchestrator.py`, `ingestion.py`, `visual_analysis.py`, `audio_analysis.py`, `face_recognition.py`, `metadata_structuring.py`, `search_index.py` |
| **API routers** | `backend/routers/video.py` |
| **Services** | `backend/services/rfp_creator.py`, `rfp_evaluator.py` |

No frontend (`frontend/`) logging infrastructure exists — the Next.js client does not use any dedicated logging library.

## Architecture and Conventions

### Logger instantiation
Every module declares its logger at module scope:
```python
import logging
logger = logging.getLogger(__name__)
```
This produces hierarchical logger names that mirror the package structure (e.g., `pipeline.orchestrator`, `routers.video`, `services.rfp_creator`).

### Log levels used
- **`logger.info`** — routine operational events: stage completion, keyframe extraction counts, index load/save, API response status codes.
- **`logger.warning`** — non-fatal degradations: missing API keys, empty search index, ffprobe returning no video stream, fallback to numpy when FAISS is unavailable.
- **`logger.error`** — failures that disrupt normal flow: file I/O errors, API HTTP errors, ffmpeg/ffprobe failures, pipeline stage exceptions (always accompanied by `traceback.format_exc()`).
- **`logger.debug`** — minimal usage; only seen in WebSocket disconnect/error handling (`routers/video.py`).

There is **no `CRITICAL` level** usage and **no `FATAL`** usage.

### Message formatting
All log calls use **percent-style (`%s`) formatting** with arguments passed as separate parameters rather than f-string interpolation. This defers string construction until the message is actually emitted:
```python
logger.info("Stage %s completed for %s", stage_name, output_dir)
logger.error("Failed to save uploaded file: %s", e)
```

### Error context
When an exception is caught, the orchestrator logs the full traceback:
```python
logger.error(
    "Stage %s failed: %s\n%s",
    stage_name, error_msg, traceback.format_exc(),
)
```
Other modules typically log just the exception message (`%s` with `e`) without the stack trace.

### No structured fields
Log records carry **no additional structured fields** (no JSON payload, no request IDs, no correlation IDs, no video_id injection into the log record itself). Context such as `video_id` is interpolated into the human-readable message string only.

### No handler / formatter configuration
A grep for `basicConfig`, `dictConfig`, `StreamHandler`, `FileHandler`, and `Formatter` across all `backend/**/*.py` files returns zero matches. Consequently:
- Output goes to `stderr` via the default `StreamHandler` attached to the root logger.
- The default format is `levelname:logger_name:message` (or similar, depending on the Python runtime's defaults).
- Log level filtering is controlled by whatever the runtime or container sets on the root logger (typically `WARNING` unless overridden externally via environment variables or command-line flags not present in this repo).

## Rules Developers Should Follow

1. **Always use `logging.getLogger(__name__)`** at module scope. Never instantiate `logging.Logger` directly or create child loggers with hardcoded string names.
2. **Use `%`-style parameterized messages**, not f-strings, to avoid unnecessary string construction when the log level is disabled.
3. **Choose log levels consistently:**
   - `info` for expected lifecycle events (stage start/complete, file written, API call made).
   - `warning` for recoverable anomalies (missing optional config, empty results, fallback paths).
   - `error` for failures that cause a stage or request to fail; include `traceback.format_exc()` when catching broad `Exception`.
   - `debug` sparingly for high-frequency diagnostic detail.
4. **Do not add print statements** for diagnostic output — use the module logger instead.
5. **Do not introduce a third-party logging framework** unless there is a coordinated decision to add centralized configuration (handlers, formatters, structured output) across the entire backend.
6. **If structured logging is needed in the future**, consider adding a shared initialization function in `backend/config.py` or a new `backend/logging_config.py` that calls `logging.config.dictConfig()` once at application startup, configuring JSON-formatted output and attaching file/console handlers.

---
kind: logging_system
name: Standard Python Logging with Module-Level Loggers
category: logging_system
scope:
    - '**'
source_files:
    - backend/pipeline/audio_analysis.py
    - backend/pipeline/face_recognition.py
    - backend/pipeline/ingestion.py
    - backend/pipeline/orchestrator.py
    - backend/routers/video.py
    - backend/main.py
---

The Dubai Media AI Platform Orchestrator backend uses Python's built-in `logging` module for all server-side logging. There is no external logging framework (e.g., `loguru`, `structlog`) or centralized logging configuration file.

### System Approach
- **Framework**: Standard library `logging`.
- **Logger Initialization**: Each module initializes its own logger using `logger = logging.getLogger(__name__)`. This follows the standard Python convention of hierarchical loggers named after the module path (e.g., `pipeline.audio_analysis`, `routers.video`).
- **Configuration**: No explicit `logging.basicConfig()` or dictionary configuration is found in the codebase. The application relies on the default logging behavior provided by the runtime environment (likely FastAPI/Uvicorn defaults when run via `uvicorn main:app`). This means log output format, level, and destination are controlled by the ASGI server's configuration rather than application code.

### Key Files and Patterns
- **Pipeline Modules**: `backend/pipeline/audio_analysis.py`, `backend/pipeline/face_recognition.py`, `backend/pipeline/ingestion.py`, and `backend/pipeline/orchestrator.py` extensively use `logger.info`, `logger.warning`, `logger.error`, and `logger.debug` to track the progress of long-running AI tasks (ASR transcription, face matching, video ingestion).
- **API Routers**: `backend/routers/video.py` uses `logger.error` for request-level failures (upload errors, search failures) and `logger.warning` for non-critical issues (missing metadata files).
- **Log Levels**:
  - `INFO`: Successful completion of stages (e.g., "Audio extracted", "Stage X completed").
  - `WARNING`: Non-fatal issues like missing API keys, missing reference data, or missing optional files.
  - `ERROR`: API failures, timeouts, parsing errors, and unexpected exceptions. Stack traces are included in error logs within the orchestrator using `traceback.format_exc()`.
  - `DEBUG`: High-frequency polling status updates (e.g., ASR task status checks).

### Architecture and Conventions
- **Decentralized Logging**: Logging is handled locally within each module. There is no central logging service or middleware injecting correlation IDs or request context into logs.
- **Structured Data**: Logs are primarily unstructured text strings using %-formatting (e.g., `logger.error("ASR submit error: %s", e)`). There is no enforced JSON structured logging format in the application code.
- **Error Handling**: The `PipelineOrchestrator` captures exceptions at each stage, logs the full traceback, and continues execution where possible, recording the error in a local `status.json` file for the frontend to display.

### Rules for Developers
1. **Use `__name__` for Logger Names**: Always initialize loggers with `logging.getLogger(__name__)` to maintain hierarchy and module identification.
2. **Prefer %-Formatting**: Use lazy %-formatting for log messages (e.g., `logger.info("Value: %s", val)`) rather than f-strings to avoid performance overhead when the log level is disabled.
3. **Log Exceptions with Tracebacks**: In `except` blocks handling unexpected errors, use `logger.error(..., exc_info=True)` or manually include `traceback.format_exc()` to ensure stack traces are captured for debugging.
4. **No Hardcoded Config**: Do not add `basicConfig` calls in modules. Logging configuration should be managed at the entry point (`main.py`) or via the ASGI server (Uvicorn) configuration.
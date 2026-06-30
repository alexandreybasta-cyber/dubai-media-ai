## Overview

The Dubai Media AI Video Processing & RFP Toolkit uses **Python's built-in `logging` module** for all backend logging. The approach follows standard Python conventions with module-level loggers created via `logging.getLogger(__name__)`. There is no centralized logging configuration, structured logging framework, or custom log handlers — the system relies entirely on Python's default logging behavior.

## System Architecture

### Framework and Approach
- **Framework**: Python standard library `logging` module (no third-party logging libraries)
- **Pattern**: Module-level logger instances using `logger = logging.getLogger(__name__)`
- **Configuration**: None explicitly defined; relies on Python's default root logger configuration
- **Output**: Logs are emitted to stderr/stdout via the default `StreamHandler` attached by Python when no configuration exists

### Key Characteristics
- No `logging.basicConfig()` call anywhere in the codebase
- No file-based log handlers configured
- No JSON or structured log formatting
- No log level configuration in environment variables or config files
- No log rotation or archival strategy
- No correlation IDs or request tracing

## Key Files

All backend Python modules follow the same pattern:

| File | Logger Declaration |
|------|-------------------|
| `backend/pipeline/orchestrator.py` | `logger = logging.getLogger(__name__)` |
| `backend/pipeline/ingestion.py` | `logger = logging.getLogger(__name__)` |
| `backend/pipeline/visual_analysis.py` | `logger = logging.getLogger(__name__)` |
| `backend/pipeline/audio_analysis.py` | `logger = logging.getLogger(__name__)` |
| `backend/pipeline/face_recognition.py` | `logger = logging.getLogger(__name__)` |
| `backend/pipeline/metadata_structuring.py` | `logger = logging.getLogger(__name__)` |
| `backend/pipeline/search_index.py` | `logger = logging.getLogger(__name__)` |
| `backend/routers/video.py` | `logger = logging.getLogger(__name__)` |
| `backend/services/rfp_creator.py` | `logger = logging.getLogger(__name__)` |
| `backend/services/rfp_evaluator.py` | `logger = logging.getLogger(__name__)` |

## Logging Conventions

### Log Level Usage

The codebase uses four log levels consistently:

1. **`logger.info()`** — Normal operational events:
   - Stage completion: `"Stage %s completed for %s"`
   - Pipeline lifecycle: `"Pipeline completed for video %s (status: %s)"`
   - Process milestones: `"Audio extracted to %s"`, `"Thumbnail generated at %s"`
   - API interactions: `"Sending %d frames to %s model for visual analysis"`, `"Visual analysis API response status: %s"`

2. **`logger.warning()`** — Non-critical issues that don't halt execution:
   - Missing optional resources: `"No API key provided, returning empty visual analysis"`
   - Degraded operation: `"No reference faces loaded, skipping identification"`
   - Parse failures: `"Could not parse JSON from visual analysis response"`
   - FFmpeg warnings: `"Failed to extract frame at %.1fs"`

3. **`logger.error()`** — Failures requiring attention:
   - API errors with context: `"Visual analysis API error (attempt %d/3): %s – %s"`
   - File/system errors: `"ffprobe failed for %s: %s"`, `"Failed to save uploaded file: %s"`
   - Exception details with tracebacks in orchestrator: `logger.error("Stage %s failed: %s\n%s", stage_name, error_msg, traceback.format_exc())`

4. **`logger.debug()`** — Minimal usage (only in WebSocket error handling):
   - `logger.debug("WebSocket error for %s: %s", video_id, e)`

### Message Formatting

All log messages use **printf-style formatting** (percent-formatting) rather than f-strings or `.format()`:
```python
logger.info("Stage %s completed for %s", stage_name, output_dir)
logger.error("Pipeline failed for %s: %s", video_id, e)
```

This is the recommended Python logging practice as it defers string interpolation until the message is actually emitted.

### Error Context

Error logs consistently include:
- **Resource identifiers**: `video_id`, `video_path`, `audio_path`
- **Attempt counts**: `"(attempt %d/3)"` for retry logic
- **Exception details**: `type(e).__name__`, `str(e)`, and full tracebacks via `traceback.format_exc()` in critical paths
- **API response data**: Status codes and truncated response bodies (`resp.text[:500]`, `resp.text[:1000]`)

## Rules for Developers

### Required Patterns

1. **Always use module-level loggers**: Declare `logger = logging.getLogger(__name__)` at module scope, never create loggers inline or use the root logger directly.

2. **Use printf-style formatting**: Pass format arguments as separate parameters to avoid unnecessary string construction:
   ```python
   # Correct
   logger.info("Processing video %s", video_id)
   # Avoid
   logger.info(f"Processing video {video_id}")
   ```

3. **Include contextual identifiers**: Always log `video_id`, file paths, or other relevant identifiers so logs can be correlated to specific operations.

4. **Log exceptions with tracebacks in critical paths**: Use `traceback.format_exc()` when catching exceptions in pipeline stages where debugging context is essential.

5. **Match log level to severity**:
   - `info`: Normal progress and successful completions
   - `warning`: Degraded but non-failing conditions
   - `error`: Actual failures, API errors, file errors
   - `debug`: Transient issues like WebSocket disconnections

### Current Limitations

- **No production-ready log routing**: Logs go to stdout/stderr only. For containerized deployments (Docker Compose), logs are captured by Docker's logging driver but not persisted or rotated.
- **No structured logging**: Log entries are plain text, making them difficult to parse programmatically in log aggregation systems.
- **No configurable log levels**: Cannot adjust verbosity without modifying code or setting the `LOGGING` environment variable externally.
- **No request correlation**: WebSocket connections and background tasks cannot be traced across log entries beyond manual `video_id` matching.

### Recommendations for Enhancement

If production deployment requires enhanced logging:
1. Add `logging.basicConfig(level=logging.INFO)` in `backend/main.py` to establish explicit defaults
2. Consider adding a JSON formatter (e.g., `python-json-logger`) for structured output
3. Configure log levels via environment variables in `config.py`
4. Add request/correlation IDs for distributed tracing across pipeline stages

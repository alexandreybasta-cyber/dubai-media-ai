## Configuration System Overview

This repository uses a **layered configuration approach** combining environment variables, Pydantic Settings for backend validation, and Docker Compose for service orchestration. The system supports both local development and containerized deployment.

---

## Architecture and Approach

### Backend: Pydantic Settings Pattern

The backend (`backend/config.py`) uses **`pydantic-settings`** (v2.4.0) to define a typed `Settings` class that:

1. **Loads from `.env` file**: Configured via `model_config` with `env_file="../.env"` pointing to the root-level `.env` file.
2. **Provides sensible defaults**: All DashScope API endpoints, model names, and paths have default values suitable for local development.
3. **Supports environment variable overrides**: Any setting can be overridden by setting an environment variable with the same name (e.g., `DASHSCOPE_API_KEY`).
4. **Implements post-validation logic**: A `@model_validator` ensures `DASHSCOPE_VIDEO_API_KEY` falls back to `DASHSCOPE_API_KEY` if not explicitly set, reducing configuration duplication.

```python
class Settings(BaseSettings):
    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_BASE_URL: str = "https://ws-gk4cdiq85mzbjrvp.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"
    UPLOAD_DIR: str = "./uploads"
    BASE_URL: str = "http://localhost:8000"
    # ... more settings

    model_config = {
        "env_file": "../.env",
        "env_file_encoding": "utf-8",
    }
```

A singleton instance `settings = Settings()` is exported and imported throughout the backend (e.g., `backend/main.py`, pipeline modules).

### Frontend: Next.js Environment Variables

The frontend uses **Next.js standard environment variable conventions**:

- **`NEXT_PUBLIC_API_URL`**: Exposed to the browser via `process.env.NEXT_PUBLIC_API_URL`. Defaults to `http://localhost:8000` if not set.
- Defined in `docker-compose.yml` under the `frontend` service's `environment` section.
- Consumed in `frontend/src/lib/api.ts` to construct API and WebSocket URLs dynamically.

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_BASE_URL = API_BASE_URL.replace(/^http/, "ws");
```

### Infrastructure: Docker Compose + Nginx

**`docker-compose.yml`** orchestrates three services:

| Service | Configuration Source | Key Settings |
|---------|---------------------|--------------|
| `backend` | `.env` file via `env_file` | All DashScope keys, model names, upload directory |
| `frontend` | Inline `environment` block | `NEXT_PUBLIC_API_URL=http://localhost:8000` |
| `nginx` | `nginx.conf` volume mount | Reverse proxy rules, CORS headers, timeouts |

**`nginx.conf`** provides:
- Static file serving for `/uploads/` with CORS headers and 7-day cache
- API proxy to `backend:8000` with 300s read timeout (for long AI operations)
- WebSocket proxy with 3600s timeout and upgrade headers
- 2GB max body size for large video uploads

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/config.py` | Pydantic Settings class — single source of truth for backend config |
| `.env.example` | Template for required environment variables (API keys, URLs, model names) |
| `.env` | Actual secrets and overrides (gitignored) |
| `docker-compose.yml` | Service orchestration, env file injection, volume mounts |
| `nginx.conf` | Reverse proxy, static file serving, CORS, timeout tuning |
| `frontend/src/lib/api.ts` | Frontend API client using `NEXT_PUBLIC_API_URL` |
| `backend/requirements.txt` | Pins `pydantic-settings==2.4.0` |

---

## Configuration Layers (Priority Order)

1. **Environment variables** (highest priority) — set in shell or Docker Compose
2. **`.env` file** — loaded by Pydantic Settings from project root
3. **Default values** in `Settings` class — fallback for local development

---

## Developer Conventions

### Adding New Backend Configuration

1. Add a field to `Settings` in `backend/config.py` with a type annotation and default value.
2. If the value is secret or environment-specific, add it to `.env.example` as a template.
3. Access via the singleton: `from config import settings; settings.YOUR_SETTING`.
4. For Docker deployment, ensure the variable is either in `.env` or passed via `docker-compose.yml`.

### Adding New Frontend Configuration

1. Prefix with `NEXT_PUBLIC_` if the value must be accessible in browser code.
2. Add to `docker-compose.yml` under `frontend.environment` for containerized runs.
3. Access via `process.env.NEXT_PUBLIC_YOUR_VAR` in TypeScript files.
4. Provide a fallback default in code (as done in `api.ts`).

### Secrets Management

- **Never commit `.env`** — it is listed in `.gitignore`.
- Use `.env.example` as a template with placeholder values (`sk-your-api-key-here`).
- In production, inject secrets via Docker secrets, Kubernetes ConfigMaps/Secrets, or CI/CD variable injection — do not rely on `.env` files.

### Model Name Configuration

All AI model names are configurable via environment variables:
- `MODEL_VIDEO` (default: `qwen-vl-max`)
- `MODEL_ASR` (default: `paraformer-v2`)
- `MODEL_TEXT` (default: `qwen-max`)
- `MODEL_EMBEDDING` (default: `text-embedding-v3`)

This allows switching models without code changes, supporting A/B testing or cost optimization.

---

## Deployment Considerations

- The `.env` file is mounted into the `backend` container via `env_file` in Docker Compose.
- Nginx configuration is mounted as a read-only volume (`:ro`) for safety.
- Uploads are persisted via a named Docker volume (`uploads`) shared between backend and nginx.
- For production, replace the inline `NEXT_PUBLIC_API_URL` with the actual backend domain and configure proper CORS origins instead of `allow_origins=["*"]`.
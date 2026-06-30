## Configuration System Overview

The Dubai Media AI Video Processing & RFP Toolkit uses a **layered configuration approach** combining Pydantic Settings for type-safe backend configuration, environment variables for secrets management, and Docker Compose for service orchestration.

---

## Architecture and Approach

### Backend Configuration (Pydantic Settings)

The backend uses `pydantic-settings` to define a centralized `Settings` class in `backend/config.py`. This provides:

- **Type-safe configuration**: All settings are strongly typed with defaults
- **Environment variable injection**: Automatic loading from `.env` file and OS environment
- **Singleton pattern**: A global `settings` instance is exported for import across modules
- **Model validation**: Custom validator provides automatic fallback for `DASHSCOPE_VIDEO_API_KEY` → `DASHSCOPE_API_KEY`

Key configuration categories:
- **API credentials**: `DASHSCOPE_API_KEY`, `DASHSCOPE_VIDEO_API_KEY`
- **Service endpoints**: `DASHSCOPE_BASE_URL`, `DASHSCOPE_API_URL`, `BASE_URL`
- **Model identifiers**: `MODEL_VIDEO`, `MODEL_ASR`, `MODEL_TEXT`, `MODEL_EMBEDDING`
- **Infrastructure paths**: `UPLOAD_DIR`

### Frontend Configuration (Next.js Environment Variables)

The frontend relies on Next.js's built-in environment variable handling:

- `NEXT_PUBLIC_API_URL`: Determines the backend endpoint (injected at build/runtime via Docker Compose)
- Fallback to `http://localhost:8000` if not set, ensuring local development works out-of-the-box
- WebSocket URL derived automatically by replacing `http` → `ws` in the API base URL

### Orchestration Layer (Docker Compose + Nginx)

**Docker Compose** (`docker-compose.yml`) manages three services:
- **backend**: Loads `.env` file directly via `env_file` directive, mounts uploads volume
- **frontend**: Sets `NEXT_PUBLIC_API_URL` as an environment variable, depends on backend
- **nginx**: Reverse proxy mounting `nginx.conf`, shares uploads volume read-only

**Nginx** (`nginx.conf`) acts as the routing layer:
- `/api/` → proxied to `backend:8000` with 300s read timeout for long-running AI operations
- `/ws/` → WebSocket upgrade support with 3600s timeout
- `/uploads/` → static file serving with CORS headers and 7-day cache
- `client_max_body_size 2G` for large video uploads

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/config.py` | Centralized Pydantic Settings class with env loading |
| `.env.example` | Template documenting required environment variables |
| `.env` | Actual secrets (gitignored) |
| `docker-compose.yml` | Service orchestration with env injection |
| `nginx.conf` | Reverse proxy routing, timeouts, CORS |
| `frontend/src/lib/api.ts` | Frontend API client reading `NEXT_PUBLIC_API_URL` |
| `backend/main.py` | FastAPI app importing and using `settings` |

---

## Developer Conventions and Rules

1. **Never commit `.env`**: Use `.env.example` as reference; actual secrets stay in `.env` (gitignored)
2. **Import `settings`, not `os.environ`**: Always use `from config import settings` in backend code for type safety and default handling
3. **Frontend uses `api` helper**: Import from `frontend/src/lib/api.ts` which resolves base URL automatically
4. **Local development**: Ensure `.env` exists at project root; run `docker-compose up` for full stack
5. **Production secrets**: Store API keys in secrets management (Docker secrets, platform secret stores), not plain `.env` files
6. **CORS in production**: Replace wildcard `*` origins with trusted domains
7. **Model selection**: Change model identifiers via environment variables rather than hardcoding

---

## Configuration Loading Flow

```
.env file (project root)
    ↓
backend/config.py (pydantic-settings loads ../.env relative to config.py)
    ↓
global settings instance
    ↓
imported by: main.py, pipeline/*, services/*, routers/*
```

Frontend flow:
```
NEXT_PUBLIC_API_URL (env var or docker-compose)
    ↓
frontend/src/lib/api.ts (API_BASE_URL constant)
    ↓
all API calls and WebSocket connections
```

---

## Notable Design Decisions

- **Dual API key system**: Separate keys for general LLM calls vs. video analysis, with automatic fallback
- **Separate DashScope endpoints**: `DASHSCOPE_BASE_URL` for chat completions, `DASHSCOPE_API_URL` for ASR/task management
- **Relative .env path**: Config loads from `../.env` relative to `config.py`, placing secrets at project root
- **No feature flags**: Configuration is flat; no runtime feature toggling system detected
- **No secrets rotation**: No automated key rotation or vault integration implemented

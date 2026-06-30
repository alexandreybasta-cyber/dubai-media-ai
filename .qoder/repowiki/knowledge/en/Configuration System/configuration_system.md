The Dubai Media AI Platform Orchestrator uses a layered configuration system combining environment variables, Pydantic Settings for backend validation, and Docker Compose for service orchestration.

### Backend Configuration (Python/FastAPI)
- **Framework**: `pydantic-settings` is used in `backend/config.py` to define a `Settings` class. This provides type-safe configuration loading with automatic environment variable injection.
- **Source**: Configuration is loaded from a `.env` file located at the project root (`../.env` relative to `config.py`) and can be overridden by environment variables.
- **Key Settings**: Includes API keys (`DASHSCOPE_API_KEY`), model identifiers (`MODEL_VIDEO`, `MODEL_ASR`, etc.), and infrastructure URLs (`BASE_URL`, `DASHSCOPE_BASE_URL`).
- **Singleton Pattern**: A global `settings` instance is exported from `config.py` for easy import across the backend modules.

### Frontend Configuration (Next.js)
- **Environment Variables**: The frontend relies on `NEXT_PUBLIC_API_URL` to determine the backend endpoint. This is injected at build time or runtime via Docker Compose.
- **Fallbacks**: `frontend/src/lib/api.ts` defines a fallback URL (`http://localhost:8000`) if the environment variable is missing, ensuring local development works out-of-the-box.
- **Next.js Config**: `frontend/next.config.ts` is minimal, relying on default Next.js behavior for environment variable handling.

### Orchestration & Infrastructure
- **Docker Compose**: `docker-compose.yml` manages the multi-service environment. It injects the `.env` file into the `backend` service and sets `NEXT_PUBLIC_API_URL` for the `frontend` service.
- **Nginx**: `nginx.conf` acts as a reverse proxy, handling routing for `/api/` (to backend), `/ws/` (WebSockets), and `/uploads/` (static files). It also configures CORS headers and upload size limits (`client_max_body_size 2G`).
- **Environment Template**: `.env.example` serves as the documentation for required environment variables, particularly the Alibaba DashScope API key and model selections.

### Developer Conventions
1. **Secrets Management**: Sensitive keys like `DASHSCOPE_API_KEY` must be placed in a `.env` file (gitignored) and never committed. Use `.env.example` as a reference.
2. **Backend Access**: Always import `settings` from `backend/config.py` rather than accessing `os.environ` directly to ensure type safety and default value handling.
3. **Frontend API Calls**: Use the `api` helper in `frontend/src/lib/api.ts` which automatically resolves the base URL from `NEXT_PUBLIC_API_URL`.
4. **Local Development**: Ensure `.env` exists at the root. Run `docker-compose up` to start all services with correct networking and environment injection.
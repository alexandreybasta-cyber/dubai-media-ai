The project employs a **Docker Compose-centric** build and deployment strategy, orchestrating a hybrid Next.js (frontend) and FastAPI (backend) architecture with an Nginx reverse proxy. It eschews traditional build tools like Makefiles in favor of containerized service definitions and standard language-specific package managers.

### Core Build Components
1. **Container Orchestration**: The root-level `docker-compose.yml` defines three services:
   - **Backend**: Built from `./backend`, using volume mounts and `uvicorn --reload` for hot-reloading during development.
   - **Frontend**: Built from `./frontend`, mounting source code for live updates.
   - **Nginx**: An `nginx:alpine` instance acting as a reverse proxy and static file server for uploaded media.

2. **Reverse Proxy Configuration**: The `nginx.conf` file handles routing logic:
   - Proxies `/api/` requests to the backend on port 8000.
   - Serves uploaded media directly from a shared Docker volume (`/uploads/`) to improve performance.
   - Configures CORS headers and increases `client_max_body_size` to 2G for large video uploads.
   - Manages WebSocket connections for real-time pipeline feedback.

3. **Dependency Management**:
   - **Backend**: Uses `pip` with exact version pinning (`==`) in `backend/requirements.txt` (e.g., `fastapi==0.115.0`, `dashscope==1.20.0`).
   - **Frontend**: Uses `npm` with `package.json` and `package-lock.json` (lockfileVersion 3) for deterministic builds (e.g., `next@16.2.9`, `tailwindcss@^4`).

### Architecture & Conventions
- **Service Separation**: Strict separation between the AI-processing backend and the React-based frontend, communicating via REST and WebSocket APIs.
- **Shared Volumes**: A named Docker volume `uploads` is shared between the backend (writer) and Nginx (reader), allowing efficient access to processed media without copying files between containers.
- **Environment Configuration**: Centralized in a root `.env` file, consumed by Docker Compose and the backend's `pydantic-settings`.
- **No CI/CD Pipeline**: There are no visible GitHub Actions or other CI configurations; deployment is currently manual or script-based (e.g., `push-via-api.sh`).

### Developer Rules
- **Build Command**: Use `docker compose up --build` to start the entire stack.
- **Local Development**: Developers can run services manually using `uvicorn main:app --reload` (backend) and `npm run dev` (frontend).
- **Missing Dockerfiles**: The `docker-compose.yml` references `Dockerfile`s in both `backend/` and `frontend/` directories. Developers must ensure these files exist and are correctly configured for containerized builds.
- **Dependency Pinning**: Always use exact version pins (`==`) for backend dependencies and commit `package-lock.json` for the frontend to ensure reproducibility.
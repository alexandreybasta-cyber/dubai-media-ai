The project utilizes a **Docker Compose**-centric build and deployment strategy, orchestrated by a root-level `docker-compose.yml` file. This approach replaces traditional build scripts (like Makefiles) with containerized service definitions for the backend, frontend, and an Nginx reverse proxy.

### Core Build Components
1. **Container Orchestration**: The `docker-compose.yml` defines three primary services:
   - **Backend**: A FastAPI application built from `./backend`. It uses volume mounting (`./backend:/app`) and the `--reload` flag for hot-reloading during development.
   - **Frontend**: A Next.js application built from `./frontend`, also using volume mounts for live source updates.
   - **Nginx**: An `nginx:alpine` instance that serves as a reverse proxy and static file server.

2. **Reverse Proxy Configuration**: The `nginx.conf` file handles routing logic:
   - Proxies `/api/` requests to the backend service on port 8000.
   - Serves uploaded media files directly from a shared Docker volume at `/uploads/` to improve performance.
   - Configures CORS headers and increases `client_max_body_size` to 2G to support large video uploads.
   - Manages WebSocket connections for real-time pipeline feedback.

3. **Dependency Management**:
   - **Backend**: Uses `pip` with pinned versions in `backend/requirements.txt` (e.g., `fastapi==0.115.0`, `dashscope==1.20.0`).
   - **Frontend**: Uses `npm` with `package.json` and `package-lock.json` for deterministic builds (e.g., `next@16.2.9`, `tailwindcss@^4`).

### Architecture & Conventions
- **Service Separation**: The architecture strictly separates the AI-processing backend from the React-based frontend, communicating via REST and WebSocket APIs.
- **Shared Volumes**: A named Docker volume `uploads` is shared between the backend (writer) and Nginx (reader), allowing efficient access to processed media without copying files between containers.
- **Environment Configuration**: Centralized in a root `.env` file, which is consumed by Docker Compose and the backend's `pydantic-settings`.

### Developer Rules
- **Build Command**: Use `docker compose up --build` to start the entire stack.
- **Local Development**: Developers can run services manually using `uvicorn main:app --reload` (backend) and `npm run dev` (frontend).
- **Missing Dockerfiles**: The `docker-compose.yml` references `Dockerfile`s in both `backend/` and `frontend/` directories. Developers must ensure these files exist and are correctly configured for containerized builds, as they are not currently present in the root directory tree.
- **No CI/CD Pipeline**: There are no visible GitHub Actions or other CI configurations; deployment is currently manual or script-based (e.g., `push-via-api.sh`).
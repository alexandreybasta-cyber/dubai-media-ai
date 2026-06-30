The Dubai Media AI Platform Orchestrator uses a **Docker Compose**-centric build and deployment strategy, supplemented by an **Nginx** reverse proxy for unified access and static file serving. There are no dedicated `Makefile`s or complex CI/CD pipelines visible in the repository; the build process is driven primarily by `docker-compose.yml` and standard language-specific package managers (`pip` for Python, `npm` for Node.js).

### Build System Components

1.  **Container Orchestration (Docker Compose)**:
    -   The root-level `docker-compose.yml` defines three services: `backend` (FastAPI), `frontend` (Next.js), and `nginx`.
    -   It relies on local `Dockerfile`s in both `backend/` and `frontend/` directories (though these files are not present in the current tree, they are referenced in the compose config).
    -   **Development Mode**: The backend service uses `--reload` and volume mounts (`./backend:/app`) to support hot-reloading during development. The frontend also mounts source code for live updates.
    -   **Environment Management**: Uses a shared `.env` file for configuration (e.g., `DASHSCOPE_API_KEY`).

2.  **Reverse Proxy (Nginx)**:
    -   An `nginx.conf` file is mounted into an `nginx:alpine` container.
    -   It handles routing: `/api/` requests are proxied to the backend service, while `/uploads/` are served directly from a shared Docker volume for efficiency.
    -   It manages CORS headers and large file upload limits (`client_max_body_size 2G`).

3.  **Dependency Management**:
    -   **Backend**: Managed via `backend/requirements.txt` using `pip`. Key dependencies include `fastapi`, `uvicorn`, `dashscope`, and `ffmpeg-python`.
    -   **Frontend**: Managed via `frontend/package.json` using `npm`. Key dependencies include `next`, `react`, and `tailwindcss`.

4.  **Build & Run Commands**:
    -   **Production/Unified**: `docker compose up --build`
    -   **Manual Development**:
        -   Backend: `uvicorn main:app --reload --port 8000`
        -   Frontend: `npm run dev`

### Architecture & Conventions

-   **Service Separation**: Clear separation between the AI-processing backend and the React-based frontend, communicating via REST/WebSocket APIs.
-   **Shared Volumes**: A named Docker volume `uploads` is used to share uploaded media files between the backend (writer) and Nginx (reader), avoiding the need to copy large files between containers.
-   **Configuration**: Centralized environment variables in `.env` at the root, consumed by both Docker Compose and the backend's `pydantic-settings`.

### Developer Rules

-   **No Makefile**: Developers should use `docker compose` commands directly or standard language tools (`npm`, `pip`) for local development.
-   **Env File**: Always create a `.env` file from `.env.example` before running the application.
-   **Port Mapping**: 
    -   Frontend: `3000`
    -   Backend: `8000`
    -   Nginx Proxy: `8080`
-   **Dockerfiles Required**: To run via Docker Compose, developers must ensure valid `Dockerfile`s exist in `backend/` and `frontend/`, as they are referenced but not currently tracked in the provided directory tree.
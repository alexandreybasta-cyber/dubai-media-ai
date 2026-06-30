## Overview

This repository employs a **dual-stack dependency management** strategy, maintaining separate dependency ecosystems for the Python-based backend and Next.js-based frontend. Both stacks use **exact version pinning** to ensure reproducible builds across environments.

## Backend: Python/pip with requirements.txt

### Manifest File
- **Location**: `backend/requirements.txt`
- **Format**: Flat list of packages with exact version pins using `==` operator

### Key Dependencies (all pinned)
- **Web Framework**: `fastapi==0.115.0`, `uvicorn[standard]==0.30.0`
- **AI Processing**: `dashscope==1.20.0` (Alibaba Cloud Qwen/DashScope SDK)
- **Media Processing**: `ffmpeg-python==0.2.0`
- **Document Generation**: `python-docx==1.1.0`, `reportlab==4.2.0`, `openpyxl==3.1.5`, `pdfplumber==0.11.0`
- **Search/Indexing**: `faiss-cpu==1.8.0`, `numpy==1.26.4`
- **Async/HTTP**: `websockets==12.0`, `aiofiles==24.1.0`, `httpx==0.27.0`
- **Configuration**: `pydantic-settings==2.4.0`
- **File Upload**: `python-multipart==0.0.9`

### Installation
```bash
cd backend
pip install -r requirements.txt
```

### Virtual Environment
A local virtual environment exists at `backend/venv/`, indicating developers are expected to isolate dependencies per-project rather than relying on system-wide Python packages.

## Frontend: npm with package-lock.json

### Manifest Files
- **Primary**: `frontend/package.json` — declares direct dependencies with semantic version ranges
- **Lockfile**: `frontend/package-lock.json` (7,228 lines) — locks entire dependency tree with exact versions and integrity hashes

### Direct Dependencies
- **Framework**: `next@16.2.9`, `react@19.2.4`, `react-dom@19.2.4`
- **UI Icons**: `@heroicons/react@^2.2.0`
- **Charts**: `recharts@^3.9.0`

### Dev Dependencies
- **Styling**: `tailwindcss@^4`, `@tailwindcss/postcss@^4`
- **TypeScript**: `typescript@^5`, `@types/node@^20`, `@types/react@^19`, `@types/react-dom@^19`
- **Linting**: `eslint@^9`, `eslint-config-next@16.2.9`

### Lockfile Strategy
The `package-lock.json` uses **lockfileVersion 3**, which supports modern npm features including:
- Integrity hashes (SHA-512) for supply chain security
- Peer dependency resolution
- Workspace support (though not currently used)

All transitive dependencies are fully resolved and pinned, ensuring identical installs across machines.

### Installation
```bash
cd frontend
npm install
```

Note: The `.gitignore` includes Yarn-specific entries (`.yarn/*`, `yarn-debug.log*`), suggesting Yarn was considered or previously used, but the active toolchain is npm.

## Docker Orchestration

### docker-compose.yml
The project uses Docker Compose to orchestrate three services:
- **backend**: Built from `./backend` context, mounts source code and uploads volume
- **frontend**: Built from `./frontend` context, mounts source code for hot-reload
- **nginx**: Reverse proxy using `nginx:alpine` image

Dependencies between services are declared via `depends_on`, ensuring correct startup order.

### Volume Strategy
- Source code is mounted as volumes for development hot-reload
- `uploads` named volume persists processed video artifacts across container restarts

## Conventions and Rules for Developers

1. **Never commit `node_modules/` or `venv/`** — both are gitignored; rely on lockfiles and manifests for reproducibility
2. **Pin all backend dependencies** — use `==` in `requirements.txt`; avoid `>=` or `~=` unless there's a specific compatibility reason
3. **Commit `package-lock.json`** — this is the source of truth for frontend dependency resolution; never delete or ignore it
4. **Update dependencies deliberately** — when upgrading, test thoroughly before committing new pins; document breaking changes
5. **Use virtual environments** — always activate `backend/venv` before installing or running Python code
6. **Docker for production parity** — use `docker-compose up` to replicate production-like environments locally
7. **No vendoring** — neither stack vendors dependencies; all third-party code comes from public registries (PyPI, npm)

## Registry Configuration

- **Python**: Uses default PyPI registry (no custom `pip.conf` or private registry configuration found)
- **Node.js**: Uses default npm registry (`https://registry.npmjs.org`); no `.npmrc` with custom registries detected
- No GOPRIVATE or Go module configuration (this is not a Go project)

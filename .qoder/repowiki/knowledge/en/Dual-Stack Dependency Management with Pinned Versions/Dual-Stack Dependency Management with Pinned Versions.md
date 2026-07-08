---
kind: dependency_management
name: Dual-Stack Dependency Management with Pinned Versions
category: dependency_management
scope:
    - '**'
source_files:
    - backend/requirements.txt
    - frontend/package.json
    - frontend/package-lock.json
    - docker-compose.yml
    - .env.example
    - README.md
---

# Dual-Stack Dependency Management

This repository uses a **dual-stack architecture** with separate dependency management systems for the Python backend (FastAPI) and Node.js frontend (Next.js). Both stacks employ **exact version pinning** for reproducibility, combined with lockfiles for deterministic builds.

## Backend: Python/pip with requirements.txt

### Manifest File
- **`backend/requirements.txt`** — All 15 dependencies are pinned to exact versions using `==` syntax:
  - Core framework: `fastapi==0.115.0`, `uvicorn[standard]==0.30.0`
  - AI integration: `dashscope==1.20.0` (Alibaba Cloud Qwen/DashScope SDK)
  - Media processing: `ffmpeg-python==0.2.0`
  - Document generation: `python-docx==1.1.0`, `reportlab==4.2.0`, `openpyxl==3.1.5`, `pdfplumber==0.11.0`
  - Vector search: `faiss-cpu==1.8.0`, `numpy==1.26.4`
  - Configuration & async: `pydantic-settings==2.4.0`, `aiofiles==24.1.0`, `httpx==0.27.0`
  - Utilities: `python-multipart==0.0.9`, `websockets==12.0`

### Installation Strategy
- Dependencies are installed via `pip install -r requirements.txt` into a local virtual environment (`backend/venv/`)
- No `pyproject.toml` or `setup.py` is present — the project uses the flat `requirements.txt` approach
- No `requirements-dev.txt` or separate test dependencies file exists
- No pip lockfile (`requirements-lock.txt` or `Pipfile.lock`) is generated; version pinning in `requirements.txt` serves as the primary reproducibility mechanism

### Docker Integration
- `docker-compose.yml` references a `Dockerfile` in `./backend`, but no Dockerfile currently exists in the repository. The compose file expects one to be created for containerized deployment.

## Frontend: npm with package.json + package-lock.json

### Manifest Files
- **`frontend/package.json`** — Declares direct dependencies with semantic versioning:
  - Runtime: `next@16.2.9` (exact), `react@19.2.4` (exact), `react-dom@19.2.4` (exact)
  - UI libraries: `@heroicons/react@^2.2.0`, `recharts@^3.9.0`
  - Dev tooling: `tailwindcss@^4`, `@tailwindcss/postcss@^4`, `eslint@^9`, `typescript@^5`, `@types/*` packages

- **`frontend/package-lock.json`** (7,228 lines) — Full transitive dependency tree with integrity hashes, providing deterministic installs. Uses lockfileVersion 3 (npm v7+ format).

### Installation Strategy
- Standard npm workflow: `npm install` reads `package-lock.json` to resolve exact versions of all ~320 packages in `node_modules/`
- The lockfile includes platform-specific optional dependencies (e.g., `@img/sharp-*` for image processing across darwin/linux/win32 architectures)
- No Yarn or pnpm configuration files exist — npm is the sole package manager

### Build Tooling
- Next.js handles its own build pipeline via `next build` / `next dev` scripts
- TypeScript compilation is configured via `tsconfig.json`
- ESLint configuration via `eslint.config.mjs` (ESLint v9 flat config format)
- PostCSS configuration via `postcss.config.mjs` for Tailwind CSS v4 integration

## Cross-Cutting Conventions

### Version Pinning Philosophy
Both stacks prioritize **reproducibility over automatic updates**:
- Python: All versions use `==` (exact pin)
- Node.js: Core framework packages (`next`, `react`, `react-dom`) use exact versions; UI/dev libraries use `^` (caret) for minor/patch updates

### No Private Registry Configuration
- All dependencies come from public registries (PyPI for Python, npm registry for Node.js)
- No `.npmrc`, `GOPRIVATE`, or private PyPI index configuration is present
- The DashScope SDK (`dashscope==1.20.0`) is a public PyPI package, not a private Alibaba registry

### No Automated Dependency Updates
- No Dependabot, Renovate, or similar automated update configuration exists
- No CI/CD pipeline files (`.github/workflows/`, `.gitlab-ci.yml`) are present to enforce dependency scanning or updates
- Dependency updates are manual: edit `requirements.txt` or `package.json`, then regenerate lockfiles

### Environment Isolation
- Backend: Local virtual environment (`backend/venv/`) listed in `.gitignore`
- Frontend: `node_modules/` directory listed in `.gitignore`
- Docker Compose provides container-level isolation for production-like environments

## Developer Rules

1. **Never commit `venv/` or `node_modules/`** — both are gitignored; rely on manifest files for reproducible installs
2. **Pin new Python dependencies with `==`** — add exact versions to `requirements.txt` after testing compatibility
3. **Commit `package-lock.json` changes** — any `npm install` that modifies the lockfile must be committed to ensure team consistency
4. **Test dependency upgrades in isolation** — no automated test suite exists to catch breaking changes; manual verification via the demo walkthrough is required
5. **Sync `.env` with dependency changes** — new API integrations may require additional environment variables (see `.env.example`)
6. **Docker builds require Dockerfiles** — the `docker-compose.yml` references Dockerfiles that do not yet exist; create them before attempting `docker compose up --build`

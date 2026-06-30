## Overview

This repository uses a dual-stack dependency management approach, with separate systems for the Python backend and Node.js frontend, orchestrated through Docker Compose.

## Backend (Python)

**Package Manager:** pip via `requirements.txt`

**Key File:** `backend/requirements.txt`

**Versioning Strategy:** All dependencies use **exact version pinning** (`==` operator), ensuring deterministic builds:
- FastAPI 0.115.0, uvicorn 0.30.0 for the web framework
- dashscope 1.20.0 for Alibaba Cloud AI services
- faiss-cpu 1.8.0, numpy 1.26.4 for vector search
- Document processing: python-docx, reportlab, openpyxl, pdfplumber
- No lockfile (no `requirements.lock` or `Pipfile.lock`) — relies on exact pins in requirements.txt

**Virtual Environment:** A `venv/` directory exists in `backend/`, indicating local development uses Python virtual environments. However, there is no automated setup script or Makefile to manage venv creation.

**Missing:** No `pyproject.toml`, no `setup.py`, no `Pipfile`. The project uses the legacy `requirements.txt` approach without modern Python packaging tooling.

## Frontend (Node.js/TypeScript)

**Package Manager:** npm

**Key Files:**
- `frontend/package.json` — declares direct dependencies with semantic versioning
- `frontend/package-lock.json` — auto-generated lockfile (7228 lines) ensuring reproducible installs

**Versioning Strategy:** Mixed approach in `package.json`:
- Direct dependencies use caret ranges (`^`) for minor/patch updates: `@heroicons/react ^2.2.0`, `recharts ^3.9.0`
- Core framework packages pinned exactly: `next 16.2.9`, `react 19.2.4`, `react-dom 19.2.4`
- DevDependencies similarly mixed: TypeScript `^5`, ESLint `^9`, types `^19`/`^20`

The `package-lock.json` (lockfileVersion 3) captures the full transitive dependency tree with integrity hashes, providing deterministic builds despite the caret ranges in package.json.

**Module Resolution:** TypeScript configured with `moduleResolution: "bundler"` and path alias `@/*` → `./src/*`.

## Orchestration Layer

**Docker Compose:** `docker-compose.yml` defines three services (backend, frontend, nginx) but references Dockerfiles that do not exist in the repository yet. This means:
- Dependency installation during container builds is not yet defined
- The `command` field for backend runs `uvicorn main:app --reload` directly, suggesting development-mode usage
- Volume mounts (`./backend:/app`, `./frontend/src:/app/src`) indicate source code is mounted into containers rather than baked in

**No CI/CD dependency caching:** No GitHub Actions, GitLab CI, or other pipeline configuration files found for dependency caching or automated updates.

## Conventions and Developer Rules

1. **Backend:** Add new Python dependencies to `requirements.txt` with exact versions (`pip install pkg==X.Y.Z`). Run inside the `venv/` virtual environment.

2. **Frontend:** Use `npm install <pkg>` to add dependencies — npm will update both `package.json` and `package-lock.json`. Commit both files.

3. **No dependency update automation:** No Dependabot, Renovate, or similar tooling configured. Updates are manual.

4. **No private registry configuration:** All dependencies come from public registries (PyPI, npmjs.org). No `.npmrc`, `GOPRIVATE`, or private index URLs configured.

5. **No vendoring:** Neither stack vendors third-party code. Dependencies are fetched at install time.

6. **Environment variables:** Backend uses `pydantic-settings` loading from `../.env` file. Frontend uses `NEXT_PUBLIC_API_URL` environment variable passed via docker-compose.
# Dubai Media × Alibaba Cloud AI

AI-powered tools for Dubai Media Incorporated: video archive metadata extraction, RFP creation, and proposal evaluation — built on Alibaba Cloud DashScope.

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- DashScope API key ([get one here](https://dashscope.console.aliyun.com/))

### 1. Environment Setup
```bash
cp .env.example .env
# Edit .env and add your DASHSCOPE_API_KEY
```

### 2. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

### 4. Docker (alternative)
```bash
docker compose up --build
```

## Architecture

| Service | Port | Description |
|---------|------|-------------|
| Backend | 8000 | FastAPI + DashScope AI pipeline |
| Frontend | 3000 | Next.js 14 App Router + Tailwind |
| Nginx | 8080 | Static file serving + reverse proxy |

## Tools

- **Archive Metadata** — Upload videos, extract scenes, transcripts, and searchable metadata
- **RFP Creator** — Generate professional RFP documents with AI assistance
- **RFP Evaluator** — Score and compare vendor proposals against criteria

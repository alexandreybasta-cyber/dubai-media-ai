# Dubai Media × Alibaba Cloud AI — MVP

An AI-powered proof-of-concept demonstrating three intelligent tools for **Dubai Media Incorporated**, built entirely on Alibaba Cloud's Qwen model family via DashScope.

---

## What's Included

| # | Tool | Description |
|---|------|-------------|
| 1 | **Video Archive Metadata** | Upload a video and run a 6-stage AI pipeline: ingestion → visual analysis → Arabic/English STT → face recognition → metadata structuring (EBUCore/IPTC) → semantic search indexing. |
| 2 | **RFP Creator** | Generate professional, bilingual (EN/AR) Request for Proposal documents with 10 structured sections, customizable evaluation criteria, timeline, and DOCX/PDF export. |
| 3 | **RFP Evaluator** | Upload an RFP plus vendor proposals (PDF/DOCX), get AI-scored comparisons with weighted matrices, narrative recommendations, and exportable XLSX/PDF reports. |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Browser (User)                          │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / WebSocket
┌──────────────────────────▼──────────────────────────────────┐
│              Next.js Frontend (:3000)                        │
│  /archive  ·  /rfp-creator  ·  /rfp-evaluator               │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API / WS
┌──────────────────────────▼──────────────────────────────────┐
│              FastAPI Backend (:8000)                         │
│  Routers: video, rfp                                        │
│  Services: rfp_creator, rfp_evaluator                       │
│  Pipeline: orchestrator → 6 stages                          │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS
┌──────────────────────────▼──────────────────────────────────┐
│          Alibaba Cloud DashScope API                        │
│  Qwen-VL Max · Paraformer v2 · Qwen-Max · Embedding v3     │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | Next.js (React) | 16.x |
| Styling | Tailwind CSS | 4.x |
| Charts | Recharts | 3.x |
| Icons | Heroicons | 2.x |
| Backend | FastAPI (Python) | 0.115 |
| AI Models | DashScope (Qwen family) | — |
| Video Processing | FFmpeg (via ffmpeg-python) | 0.2 |
| Vector Search | FAISS (faiss-cpu) | 1.8 |
| Doc Generation | python-docx, ReportLab | — |
| PDF Parsing | pdfplumber | 0.11 |
| Spreadsheets | openpyxl | 3.1 |
| Containerization | Docker Compose | — |

---

## Prerequisites

- **Python** 3.11+
- **Node.js** 20+
- **FFmpeg** installed and available in `$PATH`
- **DashScope API Key** (Alibaba Cloud Model Studio)

---

## Setup Instructions

### Option 1: Docker Compose (recommended)

```bash
# 1. Clone the repository
git clone <repo-url> && cd "Dubai Media"

# 2. Create your .env from the example
cp .env.example .env
# Edit .env and add your DASHSCOPE_API_KEY

# 3. Run everything
docker compose up --build
```

Frontend → http://localhost:3000  
Backend API → http://localhost:8000  
Nginx proxy → http://localhost:8080

### Option 2: Manual (development)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## Environment Variables

Create a `.env` file at the project root (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `DASHSCOPE_API_KEY` | Your Alibaba Cloud DashScope API key | *(required)* |
| `DASHSCOPE_BASE_URL` | DashScope API base URL | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `MODEL_VIDEO` | Vision-language model for video analysis | `qwen-vl-max` |
| `MODEL_ASR` | Speech-to-text model | `paraformer-v2` |
| `MODEL_TEXT` | Text generation model | `qwen-max` |
| `MODEL_EMBEDDING` | Text embedding model | `text-embedding-v3` |
| `BASE_URL` | Backend base URL (for self-referencing uploaded files) | `http://localhost:8000` |

---

## API Key Setup

1. Go to [Alibaba Cloud Model Studio](https://dashscope.console.aliyun.com/)
2. Sign up / sign in and navigate to **API Keys**
3. Create a new key and copy it
4. Set `DASHSCOPE_API_KEY=sk-your-key` in your `.env` file

---

## Demo Walkthrough

1. **Upload a video** at `/archive` — select any MP4/MOV file (short clips work best for demo speed)
2. **Watch the 6-stage pipeline** run in real-time via WebSocket progress indicators
3. **Review extracted metadata** — visual scenes, transcript, detected faces, EBUCore XML, IPTC topics
4. **Try semantic search** — type natural-language queries (e.g. "aerial shot of Dubai skyline") to find relevant segments
5. **Create an RFP** at `/rfp-creator` — fill in project details, add criteria and timeline, generate bilingual document
6. **Evaluate vendors** at `/rfp-evaluator` — upload the RFP plus 2+ vendor PDFs to get AI-scored comparison matrix

---

## API Endpoints Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/video/upload` | Upload video, start pipeline |
| `GET` | `/api/video/{id}/status` | Pipeline progress status |
| `GET` | `/api/video/{id}/metadata` | Extracted metadata |
| `GET` | `/api/video/{id}/transcript` | STT transcript |
| `POST` | `/api/search` | Semantic search across videos |
| `WS` | `/ws/pipeline/{id}` | Real-time pipeline progress |
| `POST` | `/api/rfp/create` | Generate RFP document |
| `POST` | `/api/rfp/regenerate-section` | Regenerate single section |
| `GET` | `/api/rfp/{id}/export/docx` | Download RFP as DOCX |
| `GET` | `/api/rfp/{id}/export/pdf` | Download RFP as PDF |
| `POST` | `/api/rfp/evaluate` | Start vendor evaluation |
| `GET` | `/api/rfp/evaluation/{id}/status` | Evaluation progress |
| `GET` | `/api/rfp/evaluation/{id}/results` | Evaluation results |
| `GET` | `/api/rfp/evaluation/{id}/export/xlsx` | Download evaluation XLSX |
| `GET` | `/api/rfp/evaluation/{id}/export/pdf` | Download evaluation PDF |
| `GET` | `/api/health` | Health check |

---

## Models Used

| Model | Purpose |
|-------|---------|
| **Qwen-VL Max** | Video/image understanding — scene detection, object recognition, OCR, landmark identification |
| **Paraformer v2** | Automatic speech recognition — bilingual Arabic + English with speaker diarization |
| **Qwen-Max** | Text generation — RFP writing, face matching, metadata structuring, vendor evaluation |
| **Text Embedding v3** | 1024-dim embeddings for semantic vector search across video archive |

---

## Limitations & Known Issues

- **Video must be accessible via URL** for DashScope vision models — the backend serves uploaded files via its static mount, but in production a CDN or object storage URL is needed
- **Large videos** (>10 min) may hit DashScope token/time limits for visual analysis
- **ASR is async** — transcription can take several minutes for long audio
- **No persistent database** — status and results are stored as JSON files (sufficient for MVP demo)
- **No authentication** — the MVP has no user auth; add API key middleware for production
- **Face recognition** is description-based (not embedding-based) — accuracy depends on reference database quality

---

## Project Structure

```
Dubai Media/
├── backend/
│   ├── pipeline/
│   │   ├── orchestrator.py        # Pipeline coordinator
│   │   ├── ingestion.py           # Stage 1: FFmpeg extraction
│   │   ├── visual_analysis.py     # Stage 2: Qwen-VL analysis
│   │   ├── audio_analysis.py      # Stage 3: Paraformer STT
│   │   ├── face_recognition.py    # Stage 4: Face matching
│   │   ├── metadata_structuring.py# Stage 5: EBUCore/IPTC
│   │   └── search_index.py        # Stage 6: FAISS indexing
│   ├── routers/
│   │   ├── video.py               # Video API endpoints
│   │   └── rfp.py                 # RFP API endpoints
│   ├── services/
│   │   ├── rfp_creator.py         # RFP generation service
│   │   └── rfp_evaluator.py       # Vendor evaluation service
│   ├── data/                      # Reference data (IPTC taxonomy, faces)
│   ├── config.py                  # Settings via pydantic-settings
│   ├── main.py                    # FastAPI application entry
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx           # Landing dashboard
│   │   │   ├── archive/           # Video archive tool
│   │   │   ├── rfp-creator/       # RFP creation tool
│   │   │   └── rfp-evaluator/     # RFP evaluation tool
│   │   ├── components/            # Reusable UI components
│   │   └── lib/
│   │       ├── api.ts             # API client & types
│   │       └── useVideoProcessing.ts
│   └── package.json
├── docker-compose.yml
├── nginx.conf
├── .env.example
├── DEMO_SCRIPT.md
└── README.md
```

---

## License

Internal MVP — Dubai Media Incorporated × Alibaba Cloud. Not for redistribution.

---
kind: design
name: Implement hybrid Next.js/FastAPI architecture with local Nginx media serving
source: session
category: adr
---

# Implement hybrid Next.js/FastAPI architecture with local Nginx media serving

_Source: coding plans from commit period 48346fd → 7c1f746 — records intent at planning time; the implementation may lag or differ._

**Status:** accepted

## Context
The MVP requires a responsive frontend for video visualization and a robust backend for heavy video processing pipelines. DashScope APIs require accessible URLs for video input, necessitating a local serving mechanism during development and demo.

## Decision drivers
- Real-time pipeline progress updates
- External API URL accessibility for video files
- Separation of UI and heavy processing logic
- Local development simplicity

## Considered options
- **Next.js Frontend + FastAPI Backend + Nginx Media Server** — pros: Next.js provides rich interactive UI (Tailwind/React); FastAPI handles async video processing and WebSocket updates; Nginx serves local video files via HTTP URLs required by DashScope APIs.; cons: Requires managing three services in Docker Compose.
- **Monolithic Next.js API Routes** _(rejected)_ — pros: Simpler deployment.; cons: Python video processing libraries (FFmpeg, DashScope SDK) are not natively supported in Next.js serverless/edge environments; difficult to manage long-running WebSocket connections for pipeline status.

## Decision
Use a decoupled architecture: Next.js for the frontend, Python FastAPI for the backend pipeline, and Nginx to serve uploaded video files locally. This allows the FastAPI backend to provide public URLs to DashScope APIs while maintaining real-time WebSocket communication with the frontend.

## Consequences
Development environment requires Docker Compose to orchestrate Backend, Frontend, and Nginx. Video uploads are stored locally and served via Nginx rather than cloud storage for the MVP phase. The backend must expose WebSocket endpoints for real-time stage updates (Ingestion, Visual Analysis, ASR, etc.).
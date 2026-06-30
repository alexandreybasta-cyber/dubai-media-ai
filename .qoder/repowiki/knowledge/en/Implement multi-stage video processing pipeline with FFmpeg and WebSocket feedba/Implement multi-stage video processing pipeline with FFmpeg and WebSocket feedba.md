---
kind: design
name: Implement multi-stage video processing pipeline with FFmpeg and WebSocket feedback
source: session
category: adr
---

# Implement multi-stage video processing pipeline with FFmpeg and WebSocket feedback

_Source: coding plans from commit period 6146649 → 235091f — records intent at planning time; the implementation may lag or differ._

**Status:** accepted

## Context
Processing archive video requires heavy computational steps (frame extraction, audio separation, AI inference) that cannot happen synchronously in a single HTTP request. Users need real-time visibility into the long-running process.

## Decision drivers
- Asynchronous processing requirement for large media files
- Need for real-time user feedback during long operations
- Separation of concerns between media prep and AI inference

## Considered options
- **Synchronous HTTP Request** _(rejected)_ — pros: Simple implementation; cons: Timeouts for large videos, no progress visibility, poor UX
- **Async Pipeline with WebSocket Updates** — pros: Non-blocking, real-time progress tracking (Stage 1-6), scalable; cons: Increased complexity in state management and connection handling

## Decision
Build a six-stage asynchronous pipeline in Python FastAPI. Use FFmpeg for local media preparation (frame extraction, audio isolation) and WebSockets to push real-time stage completion status to the Next.js frontend. Video files are served via local Nginx to allow DashScope APIs to access them via URL.

## Consequences
The backend requires persistent storage for video files and a mechanism to map WebSocket sessions to processing jobs. FFmpeg becomes a critical infrastructure dependency. The frontend must implement a WebSocket client to render the 'Processing Pipeline Visualizer'.
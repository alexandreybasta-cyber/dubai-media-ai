---
kind: design
name: Adopt Alibaba Cloud Qwen/DashScope stack for AI video processing
source: session
category: adr
---

# Adopt Alibaba Cloud Qwen/DashScope stack for AI video processing

_Source: coding plans from commit period 48346fd → 7c1f746 — records intent at planning time; the implementation may lag or differ._

**Status:** accepted

## Context
Dubai Media requires an MVP to demonstrate AI-powered metadata enrichment (facial recognition, Arabic STT, scene detection) for historical archive videos. The solution must support Arabic dialects, ensure data sovereignty, and integrate with broadcast standards (EBUCore/IPTC).

## Decision drivers
- Arabic language proficiency (MSA + dialects)
- Data sovereignty (Singapore/Dubai region availability)
- Single vendor commercial relationship
- Broadcast-native output compatibility (EBUCore/IPTC)

## Considered options
- **Alibaba Cloud Qwen/DashScope Stack** — pros: Class-leading Arabic support, single vendor for understanding and generation, DashScope Singapore region ensures data stays in-region, native EBUCore/IPTC output capabilities.; cons: Vendor lock-in to Alibaba ecosystem.
- **Competitor Models (GPT/Claude)** _(rejected)_ — pros: General purpose capability.; cons: Inferior Arabic dialect support compared to Qwen, potential data sovereignty concerns depending on provider regions.

## Decision
Select the Alibaba Cloud Qwen model stack (Qwen3.7-Plus, Qwen3-VL-Plus, Fun-ASR) via DashScope APIs. This choice prioritizes Arabic-first processing and regional data compliance while enabling a unified video-to-metadata pipeline.

## Consequences
The backend will rely on the `dashscope` SDK and specific models (Fun-ASR for audio, Qwen-VL for visual). The system must handle API key management (`DASHSCOPE_API_KEY`) and serve local video files via Nginx to allow DashScope URL access. Output metadata will be structured as EBUCore-compliant XML for MAM integration.
---
kind: design
name: Adopt Alibaba Cloud Qwen/DashScope stack for AI processing
source: session
category: adr
---

# Adopt Alibaba Cloud Qwen/DashScope stack for AI processing

_Source: coding plans from commit period 6146649 → 235091f — records intent at planning time; the implementation may lag or differ._

**Status:** accepted

## Context
Dubai Media requires an MVP to demonstrate AI-powered metadata enrichment for historical UAE archive videos and an RFP toolkit. The solution must handle Arabic speech/text natively, ensure data sovereignty (content staying in-region), and integrate with broadcast-standard MAM systems (Dalet/Avid).

## Decision drivers
- Arabic language proficiency (MSA + dialects)
- Data sovereignty (Singapore/Dubai region availability)
- Single vendor commercial relationship
- Broadcast-native output compatibility (EBUCore/IPTC)

## Considered options
- **Alibaba Cloud Qwen/DashScope Stack** — pros: Class-leading Arabic support, data residency options, single vendor for understanding and generation, direct EBUCore/IPTC XML output capability; cons: Vendor lock-in to Alibaba ecosystem, dependency on DashScope API availability
- **Western LLMs (GPT-4/Claude) + Specialized ASR** _(rejected)_ — pros: Broad general knowledge, established ecosystem; cons: Inferior Arabic dialect handling, potential data sovereignty concerns, requires multiple vendors for video/ASR/text tasks

## Decision
Select the Alibaba Cloud Qwen model stack (Qwen3.7-Plus, Qwen3-VL-Plus, Fun-ASR) via DashScope APIs. This choice consolidates video understanding, Arabic speech-to-text, and metadata structuring under one provider while meeting strict Arabic-language and data-residency requirements.

## Consequences
The backend must integrate the `dashscope` SDK and handle specific model constraints (e.g., URL-based video access via local Nginx). Output formats are constrained to EBUCore/IPTC standards for MAM integration. Future scaling depends on DashScope's regional capacity and pricing.
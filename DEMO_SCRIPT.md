# Demo Script — Dubai Media × Alibaba Cloud AI MVP

A step-by-step guide for presenting the MVP to technical evaluators.

**Total demo time:** ~15–20 minutes + Q&A

---

## Pre-Demo Checklist

- [ ] `.env` file has a valid `DASHSCOPE_API_KEY`
- [ ] Backend is running (`uvicorn main:app --port 8000` or `docker compose up`)
- [ ] Frontend is running (`npm run dev` on port 3000 or via Docker)
- [ ] FFmpeg is installed (required for video ingestion)
- [ ] Sample video ready (30–120 seconds MP4, ideally with Arabic speech and visible landmarks)
- [ ] Two sample vendor proposal PDFs ready (1–3 pages each, in English or Arabic)
- [ ] Browser open at `http://localhost:3000`

---

## Demo Part 1: Video Archive Metadata (5–7 min)

### Setup
Navigate to **http://localhost:3000/archive**

### Steps

1. **Upload a video**
   - Click "Upload Video" and select your sample MP4
   - Point out: file is uploaded to the backend and the 6-stage pipeline starts automatically

2. **Watch the pipeline progress** (real-time WebSocket updates)
   - **Stage 1 – Ingestion:** "FFmpeg extracts the audio track as 16kHz WAV and generates a thumbnail. This runs locally — no API call needed."
   - **Stage 2 – Visual Analysis:** "We send the video to Qwen-VL Max. It returns scene descriptions, detected objects, landmarks, visible text (OCR), and face descriptions — all structured as JSON."
   - **Stage 3 – Speech-to-Text:** "Audio is submitted to Paraformer v2 for bilingual Arabic + English transcription with speaker diarization."
   - **Stage 4 – Face Recognition:** "Detected face descriptions are matched against our reference database of public figures using Qwen-Max as a reasoning engine."
   - **Stage 5 – Metadata Structuring:** "All extracted data is synthesized into broadcast-standard formats: EBUCore XML and IPTC Video Metadata Hub — with bilingual keywords."
   - **Stage 6 – Search Indexing:** "Scene descriptions and transcript segments are embedded using Text Embedding v3 and stored in a FAISS vector index for semantic search."

3. **Review results**
   - Switch to the **Timeline** view — show scene-by-scene breakdown with timestamps
   - Open the **Transcript** panel — highlight speaker labels and bilingual text
   - Open the **Metadata** panel — show EBUCore XML snippet, IPTC topics, sentiment tags
   - Point out the **API Transparency** panel — every DashScope call is logged with model, latency, and token count

4. **Semantic Search**
   - Type a natural-language query, e.g.: *"person speaking about technology"* or *"aerial view of buildings"*
   - Show results with relevance scores and timestamps
   - Emphasize: "This isn't keyword search — it's semantic understanding via embeddings."

### Key Points to Highlight
- Fully bilingual (Arabic + English) at every stage
- Broadcast-standard output (EBUCore, IPTC) — ready for MAM integration
- Real-time progress via WebSocket — no page refresh needed
- Semantic search enables content discovery across the entire archive

---

## Demo Part 2: RFP Creator (3–5 min)

### Setup
Navigate to **http://localhost:3000/rfp-creator**

### Sample Input
- **Project Title:** "AI-Powered Content Management System for Dubai Media"
- **Project Overview:** "Dubai Media seeks a vendor to implement an intelligent content management and metadata tagging system for its archive of 50,000+ broadcast hours."
- **Technical Requirements:** Cloud-native, Arabic NLP support, API-first architecture
- **Evaluation Criteria:** Technical capability (40%), Experience (25%), Price (20%), Timeline (15%)
- **Timeline:** 6 months, with milestones at requirements, development, UAT, go-live
- **Language:** Bilingual (English + Arabic)

### Steps

1. Fill in the form with the sample data above
2. Click **Generate RFP**
3. While generating (~30–60 seconds): "Qwen-Max generates each of the 10 sections individually — Executive Summary, Scope of Work, Technical Requirements, Evaluation Criteria, Timeline, Budget terms, Compliance, Submission Guidelines, and Terms & Conditions."
4. Review the generated sections in the preview panel
5. Demonstrate **section regeneration** — click regenerate on any section with custom instructions (e.g., "Make the technical requirements more specific to media workflows")
6. Click **Export DOCX** — open the downloaded file to show professional formatting
7. Click **Export PDF** — show the branded, paginated output

### Key Points to Highlight
- Full Arabic translation for every section
- Professional tone aligned with UAE government procurement standards
- Weighted evaluation criteria matrix
- Customizable — regenerate any section without losing others

---

## Demo Part 3: RFP Evaluator (5 min)

### Setup
Navigate to **http://localhost:3000/rfp-evaluator**

### Sample Data
- **RFP file:** Use the PDF exported from Part 2, or any sample RFP PDF
- **Vendor Response 1:** A 1–3 page PDF proposal (can be a simple text document saved as PDF)
- **Vendor Response 2:** A second proposal PDF from a different "vendor"

### Steps

1. Upload the **RFP document** (PDF or DOCX)
2. Add **two vendor responses** with names (e.g., "TechCorp Solutions", "MediaAI Systems")
3. Define **evaluation criteria** with weights (or use defaults from the RFP)
4. Click **Start Evaluation**
5. While processing: "The system extracts text from all PDFs, then Qwen-Max evaluates each vendor against each criterion with evidence-based scoring."
6. Show the **Comparison Matrix** — color-coded scores across all criteria
7. Show individual **Vendor Scorecards** — strengths, gaps, and risks
8. Show the **AI Recommendation** narrative — ranked vendors with justification
9. Click **Export XLSX** — open to show the spreadsheet with multiple tabs
10. Click **Export PDF** — show the formatted evaluation report

### Key Points to Highlight
- Handles PDF and DOCX input — automatic text extraction
- Criterion-by-criterion scoring with justifications and evidence quotes
- Explainable AI — every score has a "why" and a "where in the document"
- Weighted total enables objective comparison
- Follow-up questions generated for each vendor's gaps

---

## Q&A Talking Points

### Pricing
- "DashScope uses pay-per-token pricing. Qwen-Max is approximately $0.004/1K tokens. A full video pipeline run costs roughly $0.10–0.50 depending on video length. RFP generation is about $0.05–0.10 per document."

### Data Sovereignty
- "Alibaba Cloud has a UAE region (Dubai). DashScope API calls can be routed to regional endpoints, ensuring data never leaves UAE jurisdiction."

### Customization for Production
- "This is an MVP. For production: add user authentication, connect to Alibaba Cloud OSS for video storage, deploy on ECS/ACK, and integrate with your existing MAM system via the REST API."

### Arabic Performance
- "Qwen models are trained on extensive Arabic corpora. Paraformer v2 specifically supports Arabic speech recognition with dialect handling. The bilingual metadata output is production-quality."

### Scaling
- "The pipeline is async and can process multiple videos concurrently. FAISS can be swapped for Alibaba Cloud OpenSearch for managed vector search at scale."

### Comparison to Other Vendors
- "Unlike GPT-4 or Gemini, Alibaba Cloud offers: UAE data residency, unified billing through one cloud provider, and Arabic-first model training rather than English-first with Arabic as secondary."

---

## Emergency Fallbacks

If the API is slow or returns errors during the live demo:

1. **Pre-process a video beforehand** — the results are stored as JSON files in `backend/uploads/{video_id}/`. The UI will display cached results instantly.
2. **RFP generation taking too long** — have a pre-generated RFP JSON file ready to show the preview/export flow.
3. **Network issues** — the system gracefully shows error states and allows retry. Mention "In production, we'd add queue-based retry with exponential backoff."

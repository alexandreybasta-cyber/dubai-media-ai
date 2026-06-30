# Visual Analysis Stage

<cite>
**Referenced Files in This Document**
- [visual_analysis.py](file://backend/pipeline/visual_analysis.py)
- [config.py](file://backend/config.py)
- [orchestrator.py](file://backend/pipeline/orchestrator.py)
- [video.py](file://backend/routers/video.py)
- [README.md](file://README.md)
- [requirements.txt](file://backend/requirements.txt)
- [useVideoProcessing.ts](file://frontend/src/lib/useVideoProcessing.ts)
- [VideoTimeline.tsx](file://frontend/src/components/archive/VideoTimeline.tsx)
</cite>

## Update Summary
**Changes Made**
- Complete rewrite of visual analysis module to use direct file path processing instead of URL-based approach
- Added ffmpeg-based keyframe extraction with configurable frame count and timing
- Implemented base64 image encoding for Qwen-VL model consumption
- Enhanced reliability by eliminating network dependency issues for video access
- Updated from URL-based to file path-based processing approach with improved error handling

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)
10. [Appendices](#appendices)

## Introduction
This document explains the visual analysis stage powered by Alibaba Cloud DashScope's Qwen-VL model. The stage has been completely redesigned to use direct file path processing with ffmpeg-based keyframe extraction and base64 image encoding, replacing the previous URL-based approach. It covers video scene detection, object recognition, visual content analysis, AI model integration, API parameters, response handling, and how results integrate with downstream pipeline stages. It also provides examples of scene segmentation, visual description generation, and timestamp mapping, along with performance characteristics, resource requirements, and troubleshooting strategies for model-related failures.

## Project Structure
The visual analysis stage is part of a six-stage pipeline orchestrated by the backend. The stage integrates with DashScope's Qwen-VL model to analyze video content and produce structured metadata including scenes, objects, landmarks, faces, OCR text, sensitive content flags, era estimation, and summaries. The new implementation processes local video files directly using ffmpeg for keyframe extraction.

```mermaid
graph TB
subgraph "Backend"
CFG["Config (settings)"]
ORCH["Pipeline Orchestrator"]
VA["Visual Analysis (Qwen-VL)"]
ASR["Audio Analysis (ASR)"]
FR["Face Recognition"]
MS["Metadata Structuring"]
SI["Search Index"]
end
subgraph "Local System"
FFMPEG["FFmpeg"]
TMP["Temporary Files"]
end
subgraph "External"
DS["DashScope API"]
end
CFG --> ORCH
ORCH --> VA
ORCH --> ASR
ORCH --> FR
ORCH --> MS
ORCH --> SI
VA --> FFMPEG
VA --> TMP
VA --> DS
ASR --> DS
FR --> DS
MS --> DS
```

**Diagram sources**
- [config.py:4-21](file://backend/config.py#L4-L21)
- [orchestrator.py:44-206](file://backend/pipeline/orchestrator.py#L44-L206)
- [visual_analysis.py:43-131](file://backend/pipeline/visual_analysis.py#L43-L131)

**Section sources**
- [README.md:17-40](file://README.md#L17-L40)
- [README.md:193-233](file://README.md#L193-L233)

## Core Components
- **Visual Analysis Module**: Processes local video files directly using ffmpeg for keyframe extraction, encodes frames as base64, and sends them to DashScope's Qwen-VL model for comprehensive analysis.
- **Configuration**: Provides API keys, base URLs, and model identifiers with intelligent fallback mechanisms.
- **Orchestrator**: Coordinates pipeline stages and passes local video file paths to the visual analysis stage.
- **Frontend Integration**: Visualizes scenes and timestamps on a timeline.

Key responsibilities:
- **Direct file processing**: The stage accepts local video file paths instead of public URLs, eliminating network dependency issues.
- **Keyframe extraction**: Uses ffmpeg to extract evenly distributed keyframes at configurable intervals.
- **Base64 encoding**: Converts extracted frames to base64 format for model consumption.
- **Prompt engineering**: The prompt instructs the model to return a strict JSON schema covering scenes, objects, landmarks, faces, OCR, sensitive content, era estimate, and summaries.
- **Robust parsing**: Handles direct JSON, fenced code blocks, and bracket-delimited JSON fragments.
- **Intelligent fallback**: Automatically uses configuration defaults when parameters are not explicitly provided.
- **Retry and backoff**: Implements exponential backoff for transient network errors.

**Section sources**
- [visual_analysis.py:15-41](file://backend/pipeline/visual_analysis.py#L15-L41)
- [visual_analysis.py:43-131](file://backend/pipeline/visual_analysis.py#L43-L131)
- [config.py:4-21](file://backend/config.py#L4-L21)
- [orchestrator.py:96-112](file://backend/pipeline/orchestrator.py#L96-L112)

## Architecture Overview
The visual analysis stage is invoked by the orchestrator after ingestion. It now processes local video files directly using ffmpeg for keyframe extraction, converting frames to base64 format for DashScope's Qwen-VL model. The stage constructs a DashScope chat-completion request containing:
- Local video file path processed through ffmpeg for keyframe extraction
- Base64-encoded image data with timestamp references
- A text prompt requesting a specific JSON structure

The stage uses intelligent fallback mechanisms to automatically apply configuration defaults when parameters are not explicitly provided. The model responds with a JSON payload embedded in the model's text response. The stage extracts and parses the JSON, returning a normalized dictionary to the orchestrator.

```mermaid
sequenceDiagram
participant Client as "Client"
participant Router as "FastAPI Router"
participant Orchestrator as "Pipeline Orchestrator"
participant VA as "Visual Analysis"
participant FFmpeg as "FFmpeg Process"
participant DS as "DashScope API"
Client->>Router : "POST /api/video/upload"
Router->>Orchestrator : "_run_pipeline(video_id, video_path)"
Note over Orchestrator : "Passes local video_path to stage"
Orchestrator->>VA : "analyze_video_visually(video_path, api_key, model, base_url)"
Note over VA : "Direct file processing : <br/>- Extract keyframes via ffmpeg<br/>- Encode frames as base64<br/>- Build content array with timestamps"
VA->>FFmpeg : "Extract keyframes at intervals"
FFmpeg-->>VA : "Frame files with timestamps"
VA->>VA : "Encode frames as base64"
VA->>DS : "POST {base_url}/chat/completions (base64 images + prompt)"
DS-->>VA : "JSON in model response"
VA-->>Orchestrator : "Parsed results dict"
Orchestrator-->>Router : "Stage result"
Router-->>Client : "Queued response"
```

**Diagram sources**
- [video.py:95-120](file://backend/routers/video.py#L95-L120)
- [orchestrator.py:96-112](file://backend/pipeline/orchestrator.py#L96-L112)
- [visual_analysis.py:65-88](file://backend/pipeline/visual_analysis.py#L65-L88)

## Detailed Component Analysis

### Visual Analysis Module
**Updated** Complete rewrite to use direct file path processing with ffmpeg-based keyframe extraction and base64 encoding.

Responsibilities:
- **Validate video file existence** with direct path checking instead of URL validation.
- **Extract keyframes using ffmpeg** at configurable intervals based on video duration.
- **Encode frames as base64** for model consumption instead of URL-based processing.
- **Construct DashScope request payload** with base64 image data and timestamp references.
- **Use configured base URL** for API endpoint construction instead of hardcoded values.
- **Send the request** with a generous timeout and retry with exponential backoff.
- **Parse the model's response**, handling various JSON encodings.
- **Return a standardized dictionary** with empty placeholders on failure.

Key improvements:
- **Eliminates network dependency** by processing local files directly
- **Uses ffmpeg for reliable keyframe extraction** with configurable frame count
- **Encodes frames as base64** for model consumption without external URL access
- **Maintains backward compatibility** with existing API parameters

Response schema highlights:
- Scenes: timestamp (MM:SS), multilingual descriptions, scene_type
- Objects: timestamp (seconds), name, category, confidence
- Landmarks: timestamp (seconds), name, location
- Faces: timestamp (seconds), description, bbox, age_estimate, gender
- OCR: timestamp (seconds), text, language
- Sensitive content: timestamp (seconds), type, severity
- Era estimate: decade, confidence, visual cues
- Summaries: overall_summary_en, overall_summary_ar

Timestamp mapping:
- All entries include a timestamp field aligned with the video timeline.
- Scenes and OCR entries use MM:SS strings; other entries use seconds.

```mermaid
flowchart TD
Start(["Entry: analyze_video_visually"]) --> CheckKey["Check API key present"]
CheckKey --> |Missing| FallbackKey["Use settings.DASHSCOPE_VIDEO_API_KEY"]
CheckKey --> |Present| CheckModel["Check model parameter"]
CheckModel --> |Missing| FallbackModel["Use settings.MODEL_VIDEO"]
CheckModel --> |Present| CheckBaseURL["Check base_url parameter"]
CheckBaseURL --> |Missing| FallbackBaseURL["Use settings.DASHSCOPE_BASE_URL"]
CheckBaseURL --> |Present| CheckVideo["Check video_path exists"]
FallbackKey --> CheckModel
FallbackModel --> CheckBaseURL
FallbackBaseURL --> CheckVideo
CheckVideo --> |Missing| Empty["Return empty result"]
CheckVideo --> |Present| ExtractFrames["Extract keyframes via ffmpeg"]
ExtractFrames --> FramesOK{"Frames extracted?"}
FramesOK --> |No| Empty
FramesOK --> |Yes| EncodeFrames["Encode frames as base64"]
EncodeFrames --> BuildPayload["Build payload with base64 images + prompt<br/>Include timestamp references"]
BuildPayload --> CallAPI["POST chat/completions"]
CallAPI --> RespOK{"HTTP 200?"}
RespOK --> |No| LogErr["Log error and retry (exp backoff)"]
LogErr --> Attempts{"Attempts left?"}
Attempts --> |Yes| CallAPI
Attempts --> |No| Empty
RespOK --> |Yes| Parse["Parse JSON from response"]
Parse --> Parsed{"Parsed OK?"}
Parsed --> |Yes| Return["Return parsed dict"]
Parsed --> |No| Fallback["Try markdown block or bracket extraction"]
Fallback --> Parsed2{"Parsed OK?"}
Parsed2 --> |Yes| Return
Parsed2 --> |No| Empty
```

**Diagram sources**
- [visual_analysis.py:43-131](file://backend/pipeline/visual_analysis.py#L43-L131)
- [visual_analysis.py:133-159](file://backend/pipeline/visual_analysis.py#L133-L159)

**Section sources**
- [visual_analysis.py:15-41](file://backend/pipeline/visual_analysis.py#L15-L41)
- [visual_analysis.py:43-131](file://backend/pipeline/visual_analysis.py#L43-L131)
- [visual_analysis.py:133-159](file://backend/pipeline/visual_analysis.py#L133-L159)

### Keyframe Extraction and Processing
**New** Comprehensive ffmpeg-based keyframe extraction system.

The stage now uses ffmpeg to extract keyframes at regular intervals from the video file:

- **Duration-based extraction**: Calculates optimal frame intervals based on video duration
- **Configurable frame count**: Maximum 12 frames by default, scaled to video length
- **Base64 encoding**: Converts each extracted frame to base64 for model consumption
- **Timestamp preservation**: Maintains accurate timestamps for each frame
- **Error handling**: Graceful degradation if ffmpeg fails or frames cannot be extracted

```mermaid
flowchart TD
VideoPath["Input: video_path"] --> GetDuration["Get video duration via ffprobe"]
GetDuration --> CalcInterval["Calculate interval = duration / max_frames"]
CalcInterval --> ExtractLoop["Extract frames at intervals"]
ExtractLoop --> Frame1["Extract frame at timestamp 0"]
ExtractLoop --> FrameN["Extract frame at timestamp n*interval"]
Frame1 --> Encode1["Encode as base64"]
FrameN --> EncodeN["Encode as base64"]
Encode1 --> BuildContent["Build content array with timestamps"]
EncodeN --> BuildContent
BuildContent --> Return["Return frames with timestamps"]
```

**Diagram sources**
- [visual_analysis.py:189-262](file://backend/pipeline/visual_analysis.py#L189-L262)

**Section sources**
- [visual_analysis.py:189-262](file://backend/pipeline/visual_analysis.py#L189-L262)

### Configuration and Settings
- **DASHSCOPE_API_KEY**: Primary API key for all DashScope calls.
- **DASHSCOPE_VIDEO_API_KEY**: Dedicated API key for video analysis (auto-fallback from DASHSCOPE_API_KEY).
- **DASHSCOPE_BASE_URL**: Base URL for DashScope API endpoints (defaults to compatible-mode v1).
- **DASHSCOPE_API_URL**: Alternative API URL for different service endpoints.
- **MODEL_VIDEO**: Default model identifier (qwen-vl-max).
- **MODEL_ASR**: Default speech-to-text model.
- **MODEL_TEXT**: Default text processing model.
- **MODEL_EMBEDDING**: Default embedding model.
- **UPLOAD_DIR**: Directory for storing uploaded files.
- **BASE_URL**: Used to construct public URLs for uploaded files.

These settings are consumed by the orchestrator and passed to the visual analysis stage with intelligent fallback mechanisms.

**Section sources**
- [config.py:4-21](file://backend/config.py#L4-L21)
- [orchestrator.py:105-110](file://backend/pipeline/orchestrator.py#L105-L110)

### Orchestrator Integration
- The orchestrator passes local video file paths directly to the visual analysis stage.
- Results are persisted and made available to downstream stages (e.g., face recognition and metadata structuring).

```mermaid
sequenceDiagram
participant Orchestrator as "Orchestrator"
participant VA as "Visual Analysis"
participant FS as "Filesystem"
Orchestrator->>FS : "Compute local video path"
Orchestrator->>VA : "analyze_video_visually(video_path, api_key, model, base_url)"
Note over VA : "Parameters : <br/>- video_path : local file path<br/>- api_key : settings.DASHSCOPE_API_KEY<br/>- model : settings.MODEL_VIDEO<br/>- base_url : settings.DASHSCOPE_BASE_URL"
VA-->>Orchestrator : "visual_analysis.json"
Orchestrator->>FS : "Save visual_analysis.json"
```

**Diagram sources**
- [orchestrator.py:76-112](file://backend/pipeline/orchestrator.py#L76-L112)
- [visual_analysis.py:43-131](file://backend/pipeline/visual_analysis.py#L43-L131)

**Section sources**
- [orchestrator.py:76-112](file://backend/pipeline/orchestrator.py#L76-L112)

### Frontend Visualization
- The frontend receives metadata including scenes, faces, and objects.
- A timeline component maps scene boundaries to timestamps and displays hover overlays.

```mermaid
graph LR
Meta["VideoMetadata (scenes, faces, objects)"] --> TL["VideoTimeline"]
TL --> Hover["Hover scene at timestamp"]
TL --> Seek["Click to seek video"]
```

**Diagram sources**
- [useVideoProcessing.ts:59-75](file://frontend/src/lib/useVideoProcessing.ts#L59-L75)
- [VideoTimeline.tsx:77-82](file://frontend/src/components/archive/VideoTimeline.tsx#L77-L82)

**Section sources**
- [useVideoProcessing.ts:59-75](file://frontend/src/lib/useVideoProcessing.ts#L59-L75)
- [VideoTimeline.tsx:77-82](file://frontend/src/components/archive/VideoTimeline.tsx#L77-L82)

## Dependency Analysis
- **External dependencies**:
  - DashScope SDK and HTTP client for API calls.
  - FFmpeg for video processing (via ffmpeg-python wrapper).
  - Base64 encoding for image data transmission.
- **Internal dependencies**:
  - Config module supplies settings to the orchestrator.
  - Orchestrator coordinates stage execution and passes results.

```mermaid
graph TB
VA["visual_analysis.py"] --> HTTPX["httpx"]
VA --> LOG["logging"]
VA --> SUBPROC["subprocess"]
VA --> BASE64["base64"]
VA --> TEMPFILE["tempfile"]
ORCH["orchestrator.py"] --> VA
ORCH --> CFG["config.py"]
ROUTER["video.py"] --> ORCH
```

**Diagram sources**
- [visual_analysis.py:11-13](file://backend/pipeline/visual_analysis.py#L11-L13)
- [requirements.txt:5,15](file://backend/requirements.txt#L5,L15)
- [orchestrator.py:14-20](file://backend/pipeline/orchestrator.py#L14-L20)
- [video.py:17-19](file://backend/routers/video.py#L17-L19)

**Section sources**
- [requirements.txt:1-16](file://backend/requirements.txt#L1-L16)
- [visual_analysis.py:11-13](file://backend/pipeline/visual_analysis.py#L11-L13)
- [orchestrator.py:14-20](file://backend/pipeline/orchestrator.py#L14-L20)
- [video.py:17-19](file://backend/routers/video.py#L17-L19)

## Performance Considerations
- **Direct file processing**: Eliminates network dependency issues and reduces latency compared to URL-based approaches.
- **Keyframe optimization**: The stage extracts 12 frames maximum, scaled by video duration, reducing processing time while maintaining scene coverage.
- **Base64 encoding overhead**: Converting frames to base64 increases payload size by approximately 33% compared to raw JPEG data.
- **Timeout and retries**: The stage uses a 300-second timeout and exponential backoff to handle transient network issues.
- **Parameter fallback**: Intelligent fallback reduces configuration overhead while maintaining flexibility.
- **Large videos**: Very long videos may still exceed token/time limits for visual analysis; consider pre-segmenting or trimming.
- **Cost and rate limits**: DashScope may throttle or limit usage; monitor quotas and adjust batch sizes accordingly.

**Section sources**
- [README.md:182-189](file://README.md#L182-L189)
- [visual_analysis.py:79,92-94](file://backend/pipeline/visual_analysis.py#L79,L92-L94)

## Troubleshooting Guide
**Updated** Enhanced troubleshooting for the new file-based processing approach.

Common issues and resolutions:
- **Missing API key**:
  - Symptom: Empty visual analysis result with an error marker.
  - Resolution: Set DASHSCOPE_API_KEY in environment. The system will automatically use DASHSCOPE_VIDEO_API_KEY if DASHSCOPE_VIDEO_API_KEY is not set.
- **FFmpeg not installed**:
  - Symptom: Keyframe extraction fails with ffmpeg command not found errors.
  - Resolution: Install FFmpeg and ensure it's available in PATH. The system requires both ffmpeg and ffprobe executables.
- **Video file not found**:
  - Symptom: "Video file not found" error in logs.
  - Resolution: Verify the video_path parameter points to an existing file. Check file permissions and path correctness.
- **Network errors**:
  - Symptom: HTTP status errors or request timeouts during API calls.
  - Resolution: Verify connectivity, retry later, and check base URL correctness. The system automatically falls back to configured base URL if not provided.
- **Malformed JSON from model**:
  - Symptom: Parser warnings and fallback parsing attempts.
  - Resolution: Ensure the prompt remains unchanged; confirm model compliance.
- **Base64 encoding failures**:
  - Symptom: Failed to encode frame errors in logs.
  - Resolution: Check available disk space in temporary directory and verify frame files are readable.
- **Excessive processing time**:
  - Symptom: Long wait times for visual analysis.
  - Resolution: Reduce video length, trim to key segments, or increase server resources.
- **Parameter fallback issues**:
  - Symptom: Unexpected model or endpoint usage.
  - Resolution: Verify configuration settings. The system automatically applies fallbacks when parameters are not explicitly provided.

Operational tips:
- Monitor logs for "Visual analysis API error" and "Visual analysis request error" entries.
- Confirm the public URL construction in the orchestrator.
- Validate that the prompt structure matches the expected JSON schema.
- Check configuration precedence: explicit parameters override settings, which override defaults.
- Verify FFmpeg installation and PATH configuration for keyframe extraction.

**Section sources**
- [visual_analysis.py:61-63,104-124](file://backend/pipeline/visual_analysis.py#L61-L63,L104-L124)
- [orchestrator.py:76-78](file://backend/pipeline/orchestrator.py#L76-L78)
- [README.md:182-189](file://README.md#L182-L189)

## Conclusion
The visual analysis stage has been completely redesigned to leverage direct file path processing with ffmpeg-based keyframe extraction and base64 image encoding. This eliminates network dependency issues while maintaining the robust operation with minimal configuration overhead. The stage integrates tightly with the orchestrator and DashScope APIs, returning a standardized schema that enables downstream stages such as face recognition, metadata structuring, and semantic search. The enhanced intelligent fallback mechanisms and improved configuration management provide reliable operation for specialized deployments.

## Appendices

### API Parameters and Payload
**Updated** Modified to reflect base64 image data format.

- **Endpoint**: {base_url}/chat/completions (constructed from configuration)
- **Headers**:
  - Authorization: Bearer <DASHSCOPE_API_KEY>
  - Content-Type: application/json
- **Payload**:
  - model: MODEL_VIDEO (default qwen-vl-max)
  - messages:
    - role: user
    - content:
      - type: image_url
      - image_url.url: data:image/jpeg;base64,<base64_encoded_frame>
      - type: text
      - text: ANALYSIS_PROMPT with timestamp references

**Section sources**
- [visual_analysis.py:65-88](file://backend/pipeline/visual_analysis.py#L65-L88)
- [config.py:5-7](file://backend/config.py#L5-L7)

### Example Outputs and Timestamp Mapping
- **Scene segmentation**:
  - Field: scenes[].timestamp (MM:SS)
  - Fields: description_en, description_ar, scene_type
- **Visual description generation**:
  - Field: overall_summary_en, overall_summary_ar
- **Object recognition**:
  - Field: objects[].timestamp (seconds), name, category, confidence
- **Landmark identification**:
  - Field: landmarks[].timestamp (seconds), name, location
- **Face detection**:
  - Field: faces[].timestamp (seconds), description, bbox, age_estimate, gender
- **OCR**:
  - Field: text_ocr[].timestamp (seconds), text, language
- **Sensitive content**:
  - Field: sensitive_content[].timestamp (seconds), type, severity
- **Era estimate**:
  - Field: era_estimate.decade, confidence, visual_cues

**Section sources**
- [visual_analysis.py:15-41](file://backend/pipeline/visual_analysis.py#L15-L41)

### Relationship to Subsequent Pipeline Stages
- **Face recognition** consumes detected faces to enrich identities.
- **Metadata structuring** aggregates visual, audio, and face results into broadcast-ready metadata.
- **Search index** builds searchable segments combining scenes and transcripts.

**Section sources**
- [orchestrator.py:131-166](file://backend/pipeline/orchestrator.py#L131-L166)
- [README.md:171-179](file://README.md#L171-L179)
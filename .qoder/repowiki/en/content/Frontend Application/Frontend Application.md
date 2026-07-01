# Frontend Application

<cite>
**Referenced Files in This Document**
- [layout.tsx](file://frontend/src/app/layout.tsx)
- [page.tsx](file://frontend/src/app/page.tsx)
- [archive/page.tsx](file://frontend/src/app/archive/page.tsx)
- [rfp-creator/page.tsx](file://frontend/src/app/rfp-creator/page.tsx)
- [rfp-evaluator/page.tsx](file://frontend/src/app/rfp-evaluator/page.tsx)
- [api.ts](file://frontend/src/lib/api.ts)
- [useVideoProcessing.ts](file://frontend/src/lib/useVideoProcessing.ts)
- [Sidebar.tsx](file://frontend/src/components/Sidebar.tsx)
- [Button.tsx](file://frontend/src/components/Button.tsx)
- [Card.tsx](file://frontend/src/components/Card.tsx)
- [VideoUpload.tsx](file://frontend/src/components/archive/VideoUpload.tsx)
- [RFPForm.tsx](file://frontend/src/components/rfp/RFPForm.tsx)
- [EvaluationSetup.tsx](file://frontend/src/components/evaluator/EvaluationSetup.tsx)
- [MetadataPanel.tsx](file://frontend/src/components/archive/MetadataPanel.tsx)
- [VideoTimeline.tsx](file://frontend/src/components/archive/VideoTimeline.tsx)
- [TranscriptPanel.tsx](file://frontend/src/components/archive/TranscriptPanel.tsx)
- [SearchDemo.tsx](file://frontend/src/components/archive/SearchDemo.tsx)
- [APITransparencyPanel.tsx](file://frontend/src/components/archive/APITransparencyPanel.tsx)
- [PipelineVisualizer.tsx](file://frontend/src/components/archive/PipelineVisualizer.tsx)
- [package.json](file://frontend/package.json)
- [next.config.ts](file://frontend/next.config.ts)
</cite>

## Update Summary
**Changes Made**
- Enhanced API integration with XMLHttpRequest-based upload progress tracking
- Implemented robust polling fallback mechanism for video processing status monitoring
- Improved WebSocket error handling with automatic fallback to REST polling
- Enhanced resource management with proper cleanup of WebSocket connections and polling intervals
- Added improved error handling and user feedback mechanisms for upload failures
- Enhanced timestamp formatting utilities across multiple components
- Improved sensitive content display with better flag handling
- Intelligent thumbnail URL resolution with automatic path normalization
- Added URL parameter support for loading existing videos via ?video=<video_id>
- Enhanced component error boundaries and graceful degradation

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
This document explains the Next.js frontend application architecture for the Dubai Media × Alibaba Cloud AI project. It covers the page-based routing structure, component library organization, reusable UI components, state management patterns, API integration layer, real-time WebSocket handling with polling fallback, sidebar navigation, layout components, responsive design, and integration patterns with backend APIs. It also provides examples of component usage, customization guidelines, performance optimization techniques, and troubleshooting guidance for common frontend issues.

## Project Structure
The frontend is organized using Next.js App Router conventions under the src/app directory. Each feature area has its own page route:
- Home page: src/app/page.tsx
- Archive Metadata Tool: src/app/archive/page.tsx
- RFP Creator: src/app/rfp-creator/page.tsx
- RFP Evaluator: src/app/rfp-evaluator/page.tsx

Global layout and fonts are configured in src/app/layout.tsx, which renders a fixed sidebar and a main content area. The sidebar navigation is implemented in src/components/Sidebar.tsx and is shared across all pages.

Reusable UI primitives live in src/components/ and include Button and Card. Feature-specific components are grouped under:
- Archive: src/components/archive/*
- RFP: src/components/rfp/*
- Evaluator: src/components/evaluator/*

The API integration layer is centralized in src/lib/api.ts, while real-time pipeline updates are handled by src/lib/useVideoProcessing.ts with robust fallback mechanisms.

```mermaid
graph TB
A["App Router Pages<br/>src/app/*"] --> L["Root Layout<br/>src/app/layout.tsx"]
L --> S["Sidebar<br/>src/components/Sidebar.tsx"]
L --> M["Main Content<br/>pages rendered inside <main>"]
subgraph "Pages"
H["Home<br/>src/app/page.tsx"]
AR["Archive<br/>src/app/archive/page.tsx"]
RC["RFP Creator<br/>src/app/rfp-creator/page.tsx"]
RE["RFP Evaluator<br/>src/app/rfp-evaluator/page.tsx"]
end
subgraph "Components"
B["Button<br/>src/components/Button.tsx"]
C["Card<br/>src/components/Card.tsx"]
SU["Sidebar<br/>src/components/Sidebar.tsx"]
VU["VideoUpload<br/>src/components/archive/VideoUpload.tsx"]
RFPF["RFPForm<br/>src/components/rfp/RFPForm.tsx"]
ES["EvaluationSetup<br/>src/components/evaluator/EvaluationSetup.tsx"]
MP["MetadataPanel<br/>src/components/archive/MetadataPanel.tsx"]
VT["VideoTimeline<br/>src/components/archive/VideoTimeline.tsx"]
TP["TranscriptPanel<br/>src/components/archive/TranscriptPanel.tsx"]
SD["SearchDemo<br/>src/components/archive/SearchDemo.tsx"]
ATP["APITransparencyPanel<br/>src/components/archive/APITransparencyPanel.tsx"]
PV["PipelineVisualizer<br/>src/components/archive/PipelineVisualizer.tsx"]
end
subgraph "Lib"
API["api.ts<br/>src/lib/api.ts"]
UVP["useVideoProcessing.ts<br/>src/lib/useVideoProcessing.ts"]
end
H --> B
H --> C
AR --> VU
AR --> MP
AR --> VT
AR --> TP
AR --> SD
AR --> ATP
AR --> PV
RC --> RFPF
RE --> ES
AR --> UVP
AR --> API
RC --> API
RE --> API
UVP --> API
```

**Diagram sources**
- [layout.tsx:22-40](file://frontend/src/app/layout.tsx#L22-L40)
- [Sidebar.tsx:17-66](file://frontend/src/components/Sidebar.tsx#L17-L66)
- [archive/page.tsx:12-167](file://frontend/src/app/archive/page.tsx#L12-L167)
- [rfp-creator/page.tsx:8-158](file://frontend/src/app/rfp-creator/page.tsx#L8-L158)
- [rfp-evaluator/page.tsx:18-177](file://frontend/src/app/rfp-evaluator/page.tsx#L18-L177)
- [api.ts:164-244](file://frontend/src/lib/api.ts#L164-L244)
- [useVideoProcessing.ts:122-420](file://frontend/src/lib/useVideoProcessing.ts#L122-L420)

**Section sources**
- [layout.tsx:1-41](file://frontend/src/app/layout.tsx#L1-L41)
- [Sidebar.tsx:1-67](file://frontend/src/components/Sidebar.tsx#L1-L67)
- [archive/page.tsx:1-167](file://frontend/src/app/archive/page.tsx#L1-L167)
- [rfp-creator/page.tsx:1-159](file://frontend/src/app/rfp-creator/page.tsx#L1-L159)
- [rfp-evaluator/page.tsx:1-178](file://frontend/src/app/rfp-evaluator/page.tsx#L1-L178)

## Core Components
This section documents the reusable UI primitives and their roles in the application.

- Button: Provides primary and secondary variants with consistent sizing and focus styles. Used across forms and action buttons.
- Card: A lightweight container with rounded borders and padding, used to group related form sections and results panels.

These components are designed for consistency and minimal props, enabling easy reuse across pages.

**Section sources**
- [Button.tsx:1-30](file://frontend/src/components/Button.tsx#L1-L30)
- [Card.tsx:1-17](file://frontend/src/components/Card.tsx#L1-L17)

## Architecture Overview
The application follows a layered architecture:
- Presentation Layer: Next.js App Router pages render feature-specific views and orchestrate component composition.
- Component Layer: Reusable UI primitives and feature-specific components encapsulate UI logic and interactions.
- State Management: React hooks manage local UI state; a dedicated hook centralizes video processing state, WebSocket handling, and polling fallback mechanisms.
- Integration Layer: A typed API client abstracts HTTP requests and WebSocket connections, exposing convenience methods per domain (video, RFP).
- Backend Integration: Pages call the API client to perform uploads, fetch results, and poll evaluation status with robust fallback mechanisms.

```mermaid
graph TB
subgraph "Presentation"
P1["Home Page<br/>src/app/page.tsx"]
P2["Archive Page<br/>src/app/archive/page.tsx"]
P3["RFP Creator Page<br/>src/app/rfp-creator/page.tsx"]
P4["RFP Evaluator Page<br/>src/app/rfp-evaluator/page.tsx"]
end
subgraph "Components"
C1["Button<br/>src/components/Button.tsx"]
C2["Card<br/>src/components/Card.tsx"]
C3["VideoUpload<br/>src/components/archive/VideoUpload.tsx"]
C4["RFPForm<br/>src/components/rfp/RFPForm.tsx"]
C5["EvaluationSetup<br/>src/components/evaluator/EvaluationSetup.tsx"]
C6["MetadataPanel<br/>src/components/archive/MetadataPanel.tsx"]
C7["VideoTimeline<br/>src/components/archive/VideoTimeline.tsx"]
C8["TranscriptPanel<br/>src/components/archive/TranscriptPanel.tsx"]
C9["SearchDemo<br/>src/components/archive/SearchDemo.tsx"]
C10["APITransparencyPanel<br/>src/components/archive/APITransparencyPanel.tsx"]
C11["PipelineVisualizer<br/>src/components/archive/PipelineVisualizer.tsx"]
end
subgraph "State"
H1["useVideoProcessing<br/>src/lib/useVideoProcessing.ts"]
end
subgraph "Integration"
L1["api.ts<br/>src/lib/api.ts"]
end
P1 --> C1
P2 --> C3
P2 --> C6
P2 --> C7
P2 --> C8
P2 --> C9
P2 --> C10
P2 --> C11
P3 --> C4
P4 --> C5
P2 --> H1
H1 --> L1
P3 --> L1
P4 --> L1
```

**Diagram sources**
- [page.tsx:69-198](file://frontend/src/app/page.tsx#L69-L198)
- [archive/page.tsx:12-167](file://frontend/src/app/archive/page.tsx#L12-L167)
- [rfp-creator/page.tsx:8-158](file://frontend/src/app/rfp-creator/page.tsx#L8-L158)
- [rfp-evaluator/page.tsx:18-177](file://frontend/src/app/rfp-evaluator/page.tsx#L18-L177)
- [useVideoProcessing.ts:122-420](file://frontend/src/lib/useVideoProcessing.ts#L122-L420)
- [api.ts:164-244](file://frontend/src/lib/api.ts#L164-L244)

## Detailed Component Analysis

### Page-Based Routing and Navigation
- Root layout sets up fonts, global CSS, a fixed sidebar, and a main content area. The sidebar uses Next.js navigation to highlight active routes and links to the three feature areas.
- Home page presents feature cards linking to the three tools and showcases technology highlights.
- Each feature page composes domain-specific components and integrates with the API client.

```mermaid
sequenceDiagram
participant U as "User"
participant Nav as "Sidebar<br/>Sidebar.tsx"
participant Router as "Next.js Router"
participant Page as "Feature Page"
U->>Nav : Click navigation item
Nav->>Router : navigate(href)
Router-->>Page : render page component
Page-->>U : display page content
```

**Diagram sources**
- [layout.tsx:22-40](file://frontend/src/app/layout.tsx#L22-L40)
- [Sidebar.tsx:17-66](file://frontend/src/components/Sidebar.tsx#L17-L66)
- [page.tsx:69-198](file://frontend/src/app/page.tsx#L69-L198)

**Section sources**
- [layout.tsx:1-41](file://frontend/src/app/layout.tsx#L1-L41)
- [Sidebar.tsx:1-67](file://frontend/src/components/Sidebar.tsx#L1-L67)
- [page.tsx:1-199](file://frontend/src/app/page.tsx#L1-L199)

### Archive Metadata Tool
The Archive page coordinates video upload, pipeline visualization, and results presentation. It relies on a custom hook to manage upload state, WebSocket updates, polling fallback, and result retrieval.

Key responsibilities:
- Orchestrate VideoUpload component and pass upload callbacks.
- Render PipelineVisualizer during processing with real-time status updates.
- Display VideoTimeline, TranscriptPanel, MetadataPanel, and APITransparencyPanel upon completion.
- Provide a persistent SearchDemo for semantic search across the archive.
- Support loading existing videos via URL parameters (?video=<video_id>).
- Implement robust error handling with graceful fallback mechanisms.

```mermaid
sequenceDiagram
participant U as "User"
participant AU as "Archive Page<br/>archive/page.tsx"
participant VP as "useVideoProcessing<br/>useVideoProcessing.ts"
participant API as "api.ts"
participant WS as "WebSocket"
U->>AU : Select video file
AU->>VP : uploadVideo(file)
VP->>API : POST /api/video/upload (with XMLHttpRequest progress tracking)
API-->>VP : {video_id,status}
VP->>WS : connect /ws/pipeline/{video_id}
alt WebSocket connection established
WS-->>VP : stage status updates
VP->>VP : update stages and view
alt all stages complete
VP->>API : GET /api/video/{video_id}/metadata
API-->>VP : metadata
VP->>API : GET /api/video/{video_id}/transcript
API-->>VP : transcript
end
else WebSocket error/closed
VP->>VP : startPollingFallback(video_id)
loop every 3 seconds
VP->>API : GET /api/video/{video_id}/status
API-->>VP : {stages}
VP->>VP : update stages and view
alt all stages complete
VP->>API : GET /api/video/{video_id}/metadata
API-->>VP : metadata
VP->>API : GET /api/video/{video_id}/transcript
API-->>VP : transcript
end
end
end
VP-->>AU : updated state (results)
AU-->>U : render results panels
Note over AU,VP : URL parameter support : ?video=<video_id>
```

**Diagram sources**
- [archive/page.tsx:12-167](file://frontend/src/app/archive/page.tsx#L12-L167)
- [useVideoProcessing.ts:122-420](file://frontend/src/lib/useVideoProcessing.ts#L122-L420)
- [api.ts:164-244](file://frontend/src/lib/api.ts#L164-L244)

**Section sources**
- [archive/page.tsx:1-167](file://frontend/src/app/archive/page.tsx#L1-L167)
- [useVideoProcessing.ts:1-543](file://frontend/src/lib/useVideoProcessing.ts#L1-L543)
- [api.ts:164-244](file://frontend/src/lib/api.ts#L164-L244)

### Enhanced API Integration Layer
The api.ts module has been enhanced with XMLHttpRequest-based upload progress tracking and improved error handling:

- **XMLHttpRequest-Based Upload Progress Tracking**: Uses XMLHttpRequest instead of fetch for multipart/form-data uploads, enabling precise progress callbacks during file transfer with automatic timeout handling.
- **Enhanced Error Handling**: Improved error responses with detailed error messages and proper JSON parsing for both upload and API calls.
- **WebSocket Integration**: Maintains WebSocket connection helper with typed message shapes for pipeline updates and proper error handling.
- **Domain-Specific Methods**: Video and RFP operations with proper typing and parameter handling.
- **Status Endpoint**: Dedicated status endpoint for polling fallback mechanism.

**Updated** Enhanced with XMLHttpRequest-based upload progress tracking for better user feedback during large file transfers and improved error handling mechanisms.

```mermaid
sequenceDiagram
participant Client as "Client Code"
participant API as "api.ts"
participant Server as "Backend Server"
Client->>API : uploadFile(file, onProgress)
API->>API : Create XMLHttpRequest
API->>Server : POST /api/video/upload (multipart/form-data)
Server-->>API : Upload progress events
API-->>Client : onProgress(percent)
Server-->>API : Upload completion response
API-->>Client : Resolve with {video_id,status}
Note over API,Server : Automatic timeout handling set to 0 for large files
```

**Diagram sources**
- [api.ts:43-95](file://frontend/src/lib/api.ts#L43-L95)

**Section sources**
- [api.ts:1-277](file://frontend/src/lib/api.ts#L1-L277)

### Enhanced Video Processing Hook with Polling Fallback
The useVideoProcessing hook has been significantly enhanced with improved timestamp handling, better state management, and robust fallback mechanisms:

- **Improved Timestamp Formatting**: Enhanced parsing and formatting functions for various timestamp formats (seconds, MM:SS, HH:MM:SS).
- **Better State Management**: More robust state updates with proper cleanup and resource management.
- **Enhanced Error Handling**: Improved error recovery and fallback mechanisms with automatic WebSocket-to-polling transition.
- **Resource Cleanup**: Proper cleanup of WebSockets, polling intervals, and object URLs on component unmount.
- **Polling Fallback Mechanism**: Automatic fallback to REST polling when WebSocket connections fail or close.
- **Enhanced Resource Management**: Proper cleanup of WebSocket connections and polling intervals on component unmount.

**Updated** Enhanced with improved timestamp parsing utilities, better state management for video processing workflows, and robust polling fallback mechanism for video processing status monitoring.

**Section sources**
- [useVideoProcessing.ts:1-543](file://frontend/src/lib/useVideoProcessing.ts#L1-L543)

### Enhanced Component Features

#### VideoUpload Component
- **Real Progress Tracking**: Displays upload progress with percentage and file size formatting using XMLHttpRequest callbacks.
- **Enhanced File Validation**: Improved file type checking and size validation.
- **Better User Feedback**: Clear error states and loading indicators with improved error messaging.

#### MetadataPanel Component
- **Enhanced Sensitive Content Display**: Improved handling and display of sensitive content flags with better formatting.
- **Better Tab Management**: Enhanced tab switching with better state persistence.
- **Improved Data Visualization**: Better display of detected persons, landmarks, and scenes.

#### SearchDemo Component
- **Intelligent Thumbnail URL Resolution**: Automatic conversion of raw thumbnail paths to accessible URLs.
- **Enhanced Timestamp Formatting**: Support for various timestamp formats in search results.
- **Better Result Handling**: Improved result display with person detection information.

#### PipelineVisualizer Component
- **Enhanced Status Display**: Improved visual representation of pipeline stages with real-time status updates.
- **Better Progress Tracking**: Enhanced progress indicators and stage completion visualization.
- **Improved Error Handling**: Better display of failed stages and error states.

**Updated** Enhanced with improved timestamp formatting, better sensitive content display, intelligent thumbnail URL resolution, and enhanced pipeline status visualization.

**Section sources**
- [VideoUpload.tsx:1-221](file://frontend/src/components/archive/VideoUpload.tsx#L1-L221)
- [MetadataPanel.tsx:1-380](file://frontend/src/components/archive/MetadataPanel.tsx#L1-L380)
- [SearchDemo.tsx:1-230](file://frontend/src/components/archive/SearchDemo.tsx#L1-L230)
- [PipelineVisualizer.tsx:1-181](file://frontend/src/components/archive/PipelineVisualizer.tsx#L1-L181)

### RFP Creator
The RFP Creator page manages form submission, skeleton previews, and section regeneration. It uses the API client to create RFPs, regenerate sections, and export documents.

Key responsibilities:
- Capture project details and evaluation criteria.
- Call api.rfp.create to generate sections.
- Render RFPPreview with bilingual support and export actions.
- Handle errors and loading states.

```mermaid
sequenceDiagram
participant U as "User"
participant RC as "RFP Creator Page<br/>rfp-creator/page.tsx"
participant API as "api.ts"
U->>RC : Submit RFPForm
RC->>API : POST /api/rfp/create
API-->>RC : {rfp_id,sections,language}
RC-->>U : Render RFPPreview with sections
U->>RC : Regenerate section
RC->>API : POST /api/rfp/regenerate-section
API-->>RC : {content}
RC-->>U : Update preview content
```

**Diagram sources**
- [rfp-creator/page.tsx:8-158](file://frontend/src/app/rfp-creator/page.tsx#L8-L158)
- [api.ts:186-200](file://frontend/src/lib/api.ts#L186-L200)

**Section sources**
- [rfp-creator/page.tsx:1-159](file://frontend/src/app/rfp-creator/page.tsx#L1-L159)
- [RFPForm.tsx:1-411](file://frontend/src/components/rfp/RFPForm.tsx#L1-L411)
- [api.ts:186-200](file://frontend/src/lib/api.ts#L186-L200)

### RFP Evaluator
The RFP Evaluator page handles vendor proposal evaluation via a multi-phase workflow: setup, evaluating, and results. It polls evaluation status and displays structured results.

Key responsibilities:
- Collect RFP and vendor files, criteria, and weights.
- Start evaluation and poll status until completion.
- Render ComparisonMatrix, VendorScorecard, and RecommendationPanel.
- Provide export actions for evaluation reports.

```mermaid
sequenceDiagram
participant U as "User"
participant RE as "RFP Evaluator Page<br/>rfp-evaluator/page.tsx"
participant API as "api.ts"
U->>RE : Configure evaluation (RFP + vendors + criteria)
RE->>API : POST /api/rfp/evaluate
API-->>RE : {eval_id,status}
loop Polling
RE->>API : GET /api/rfp/evaluation/{eval_id}/status
API-->>RE : {status,message,error}
end
RE->>API : GET /api/rfp/evaluation/{eval_id}/results
API-->>RE : {results}
RE-->>U : Render results panels
```

**Diagram sources**
- [rfp-evaluator/page.tsx:18-177](file://frontend/src/app/rfp-evaluator/page.tsx#L18-L177)
- [api.ts:209-239](file://frontend/src/lib/api.ts#L209-L239)

**Section sources**
- [rfp-evaluator/page.tsx:1-178](file://frontend/src/app/rfp-evaluator/page.tsx#L1-L178)
- [EvaluationSetup.tsx:1-429](file://frontend/src/components/evaluator/EvaluationSetup.tsx#L1-L429)
- [api.ts:209-239](file://frontend/src/lib/api.ts#L209-L239)

### Component Library Organization
- Reusable primitives: Button and Card provide consistent styling and behavior across pages.
- Feature-specific components:
  - Archive: VideoUpload, PipelineVisualizer, VideoTimeline, TranscriptPanel, MetadataPanel, SearchDemo, APITransparencyPanel.
  - RFP: RFPForm, RFPPreview, CriteriaEditor, TimelineEditor.
  - Evaluator: EvaluationSetup, ComparisonMatrix, VendorScorecard, RecommendationPanel.

These components are designed to be self-contained, accept typed props, and minimize coupling to external state.

**Section sources**
- [Button.tsx:1-30](file://frontend/src/components/Button.tsx#L1-L30)
- [Card.tsx:1-17](file://frontend/src/components/Card.tsx#L1-L17)
- [VideoUpload.tsx:1-221](file://frontend/src/components/archive/VideoUpload.tsx#L1-L221)
- [RFPForm.tsx:1-411](file://frontend/src/components/rfp/RFPForm.tsx#L1-L411)
- [EvaluationSetup.tsx:1-429](file://frontend/src/components/evaluator/EvaluationSetup.tsx#L1-L429)

### State Management Patterns
- Local UI state: Pages maintain transient UI state (loading, errors, form inputs).
- Centralized video processing state: The useVideoProcessing hook encapsulates upload progress, pipeline stages, metadata, transcript, search results, WebSocket lifecycle, and polling fallback mechanisms.
- Controlled components: Inputs and interactive elements are controlled, updating state via callbacks.
- Resource cleanup: Proper cleanup of WebSocket connections and polling intervals on component unmount.

```mermaid
flowchart TD
Start(["Hook Initialization"]) --> Init["Initialize state:<br/>view, uploadState, stages, metadata, transcript"]
Init --> Upload["User selects file"]
Upload --> CallUpload["Call uploadVideo(file)"]
CallUpload --> SetIdle["Set uploadState='uploading'"]
SetIdle --> PostUpload["POST /api/video/upload (XHR with progress)"]
PostUpload --> GotId{"Got video_id?"}
GotId --> |Yes| StartPolling["Start polling fallback mechanism"]
GotId --> |No| HandleErr["Set uploadState='error'"]
StartPolling --> PollLoop["Poll every 3 seconds:<br/>GET /api/video/{video_id}/status"]
PollLoop --> WSConn["Attempt WebSocket connection:<br/>/ws/pipeline/{video_id}"]
WSConn --> WSMsg["Receive stage status"]
WSMsg --> UpdateStages["Update stages and view"]
WSConn --> WSError["WebSocket error/closed"]
WSError --> PollLoop
UpdateStages --> Done{"All stages complete?"}
Done --> |Yes| FetchData["Fetch metadata/transcript"]
Done --> |No| Wait["Continue polling/waiting"]
FetchData --> Render["Render results panels"]
HandleErr --> End(["End"])
Render --> End
Wait --> WSConn
```

**Diagram sources**
- [useVideoProcessing.ts:122-420](file://frontend/src/lib/useVideoProcessing.ts#L122-L420)

**Section sources**
- [useVideoProcessing.ts:1-543](file://frontend/src/lib/useVideoProcessing.ts#L1-L543)

### Real-Time WebSocket Handling with Polling Fallback
The useVideoProcessing hook connects to a WebSocket endpoint to receive pipeline stage updates with robust fallback mechanisms:

- Establishes the WebSocket connection on successful upload.
- Parses incoming messages and updates stage statuses and timing.
- Falls back to REST polling if WebSocket fails or closes.
- Triggers result retrieval when the final stage completes.
- Implements automatic cleanup of WebSocket connections and polling intervals.
- Provides graceful degradation when network connectivity is poor.

```mermaid
sequenceDiagram
participant VP as "useVideoProcessing"
participant WS as "WebSocket"
participant API as "Backend"
VP->>WS : connect(/ws/pipeline/{videoId})
alt WebSocket connection successful
WS-->>VP : {"stage","status","message","progress"}
VP->>VP : update stages and view
alt status=complete
VP->>API : GET /api/video/{video_id}/metadata
API-->>VP : metadata
VP->>API : GET /api/video/{video_id}/transcript
API-->>VP : transcript
else error/closed
VP->>VP : startPollingFallback(videoId)
loop every 3 seconds
VP->>API : GET /api/video/{video_id}/status
API-->>VP : {stages}
VP->>VP : update stages and view
alt all stages complete
VP->>API : GET /api/video/{video_id}/metadata
API-->>VP : metadata
VP->>API : GET /api/video/{video_id}/transcript
API-->>VP : transcript
end
end
end
else WebSocket connection fails
VP->>VP : startPollingFallback(videoId)
loop every 3 seconds
VP->>API : GET /api/video/{video_id}/status
API-->>VP : {stages}
VP->>VP : update stages and view
alt all stages complete
VP->>API : GET /api/video/{video_id}/metadata
API-->>VP : metadata
VP->>API : GET /api/video/{video_id}/transcript
API-->>VP : transcript
end
end
end
```

**Diagram sources**
- [useVideoProcessing.ts:215-276](file://frontend/src/lib/useVideoProcessing.ts#L215-L276)
- [api.ts:179-183](file://frontend/src/lib/api.ts#L179-L183)

**Section sources**
- [useVideoProcessing.ts:213-348](file://frontend/src/lib/useVideoProcessing.ts#L213-L348)
- [api.ts:179-183](file://frontend/src/lib/api.ts#L179-L183)

### Sidebar Navigation and Layout
The layout.tsx defines the global HTML structure with fonts and a fixed sidebar. The Sidebar component:
- Renders navigation items for Archive Metadata, RFP Creator, and RFP Evaluator.
- Uses Next.js usePathname to compute active state and apply active styles.
- Displays a small connectivity indicator.

Responsive design:
- The layout uses Tailwind utilities to ensure a minimum height and flexible main content area.
- Grid layouts adapt to larger screens for results panels.

**Section sources**
- [layout.tsx:1-41](file://frontend/src/app/layout.tsx#L1-L41)
- [Sidebar.tsx:1-67](file://frontend/src/components/Sidebar.tsx#L1-L67)

### Component Usage and Customization Guidelines
- Button
  - Props: children, variant ("primary" | "secondary"), className, and standard button attributes.
  - Usage: Prefer variant="primary" for main actions; use variant="secondary" for secondary actions.
- Card
  - Props: children, className.
  - Usage: Wrap form sections and result panels for consistent spacing and borders.
- VideoUpload
  - Props: uploadState, uploadProgress, fileName, fileSize, error, onUpload.
  - Usage: Pass callbacks from useVideoProcessing to handle file selection and upload.
- RFPForm
  - Props: onSubmit, isLoading.
  - Usage: Validate required fields and construct RFPCreatePayload before calling onSubmit.
- EvaluationSetup
  - Props: onEvaluate, isEvaluating, progressMessage.
  - Usage: Ensure total criteria weights equal 100% before submitting.

Customization tips:
- Extend Button and Card with additional variants or sizes by adding new style mappings.
- For components with complex forms, keep validation close to submission to surface errors early.
- Use controlled components to avoid unexpected re-renders and simplify debugging.
- Implement proper error boundaries for components that rely on external resources.

**Section sources**
- [Button.tsx:1-30](file://frontend/src/components/Button.tsx#L1-L30)
- [Card.tsx:1-17](file://frontend/src/components/Card.tsx#L1-L17)
- [VideoUpload.tsx:1-221](file://frontend/src/components/archive/VideoUpload.tsx#L1-L221)
- [RFPForm.tsx:1-411](file://frontend/src/components/rfp/RFPForm.tsx#L1-L411)
- [EvaluationSetup.tsx:1-429](file://frontend/src/components/evaluator/EvaluationSetup.tsx#L1-L429)

## Dependency Analysis
External dependencies include Next.js, React, Heroicons, Tailwind CSS, TypeScript, and Recharts. The project uses a minimal configuration with Tailwind PostCSS support.

```mermaid
graph LR
P["package.json"] --> N["next"]
P --> R["react / react-dom"]
P --> H["@heroicons/react"]
P --> T["tailwindcss"]
P --> TS["typescript"]
P --> RC["recharts"]
```

**Diagram sources**
- [package.json:11-28](file://frontend/package.json#L11-L28)

**Section sources**
- [package.json:1-29](file://frontend/package.json#L1-L29)
- [next.config.ts:1-8](file://frontend/next.config.ts#L1-L8)

## Performance Considerations
- Lazy loading: Defer heavy chart rendering until results are available.
- Memoization: Use React.memo for static panels and useCallback for event handlers to reduce re-renders.
- Virtualization: For large lists (e.g., search results), consider virtualizing rows.
- Image optimization: Use Next.js Image component for thumbnails and visual assets.
- Network efficiency: Batch API calls where possible; cancel ongoing requests on route changes.
- Web Workers: Offload heavy computations (e.g., transcript processing) to workers if needed.
- Bundle size: Keep icons and charts scoped to pages to avoid unnecessary imports.
- **Enhanced Upload Performance**: XMLHttpRequest-based uploads provide better progress tracking and user feedback for large files.
- **Robust Fallback Mechanisms**: Automatic polling fallback ensures reliable status monitoring even with intermittent network connectivity.
- **Resource Management**: Proper cleanup of WebSocket connections and polling intervals prevents memory leaks and improves application stability.

## Troubleshooting Guide
Common issues and resolutions:
- Upload failures
  - Symptom: Error displayed in VideoUpload with red banner.
  - Actions: Verify backend connectivity, supported file types (.mp4, .mov, .avi), and file size limits.
  - **Updated**: Check upload progress tracking for XMLHttpRequest errors and network timeouts.
- WebSocket disconnects
  - Symptom: Pipeline stalls; fallback polling occurs automatically.
  - Actions: Check network stability; confirm backend WebSocket endpoint availability.
  - **New**: Monitor console for WebSocket error messages and verify automatic fallback to polling mechanism.
- Evaluation timeout
  - Symptom: Polling continues indefinitely.
  - Actions: Inspect backend logs; ensure evaluation job starts and progresses.
- Export downloads blocked
  - Symptom: Blank tab or blocked popup.
  - Actions: Allow popups; verify CORS and backend export endpoints.
- Navigation highlighting incorrect
  - Symptom: Sidebar active state mismatch.
  - Actions: Confirm route paths match navigation entries; ensure usePathname is used consistently.
- **New**: Thumbnail URL resolution issues
  - Symptom: Missing or broken thumbnails in search results.
  - Actions: Verify thumbnail path resolution logic handles various formats correctly.
- **New**: Timestamp formatting problems
  - Symptom: Incorrect time display in timeline or transcript panels.
  - Actions: Check timestamp parsing utilities for various input formats.
- **New**: Polling fallback not triggering
  - Symptom: Pipeline appears stuck without progress updates.
  - Actions: Verify WebSocket connection establishment and check for console errors indicating fallback mechanism activation.
- **New**: Memory leaks during video processing
  - Symptom: Application becomes slower over time with multiple video uploads.
  - Actions: Ensure proper cleanup of WebSocket connections and polling intervals on component unmount.

**Section sources**
- [VideoUpload.tsx:200-217](file://frontend/src/components/archive/VideoUpload.tsx#L200-L217)
- [useVideoProcessing.ts:263-270](file://frontend/src/lib/useVideoProcessing.ts#L263-L270)
- [api.ts:31-36](file://frontend/src/lib/api.ts#L31-L36)

## Conclusion
The frontend employs a clean separation of concerns with Next.js App Router, reusable UI primitives, a centralized API client, and a dedicated hook for complex state and real-time updates with robust fallback mechanisms. The architecture supports scalable feature development, robust error handling, responsive user experience across devices, and reliable video processing status monitoring through automatic WebSocket-to-polling fallback transitions. Recent enhancements include improved upload progress tracking, better timestamp formatting, enhanced sensitive content display, intelligent thumbnail URL resolution, and comprehensive resource management for optimal application performance.

## Appendices
- Environment variables: NEXT_PUBLIC_API_URL is used to configure the API base URL at runtime.
- Fonts: Google Fonts via Next.js font providers are applied globally for sans-serif and mono fonts.
- Styling: Tailwind utility classes are used extensively for responsive layouts and component styling.

**Section sources**
- [api.ts:1-3](file://frontend/src/lib/api.ts#L1-L3)
- [layout.tsx:6-14](file://frontend/src/app/layout.tsx#L6-L14)
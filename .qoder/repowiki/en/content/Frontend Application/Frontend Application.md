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
- [package.json](file://frontend/package.json)
- [next.config.ts](file://frontend/next.config.ts)
</cite>

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
This document explains the Next.js frontend application architecture for the Dubai Media × Alibaba Cloud AI project. It covers the page-based routing structure, component library organization, reusable UI components, state management patterns, API integration layer, real-time WebSocket handling, sidebar navigation, layout components, responsive design, and integration patterns with backend APIs. It also provides examples of component usage, customization guidelines, performance optimization techniques, and troubleshooting guidance for common frontend issues.

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

The API integration layer is centralized in src/lib/api.ts, while real-time pipeline updates are handled by src/lib/useVideoProcessing.ts.

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
end
subgraph "Lib"
API["api.ts<br/>src/lib/api.ts"]
UVP["useVideoProcessing.ts<br/>src/lib/useVideoProcessing.ts"]
end
H --> B
H --> C
AR --> VU
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
- [archive/page.tsx:12-128](file://frontend/src/app/archive/page.tsx#L12-L128)
- [rfp-creator/page.tsx:8-158](file://frontend/src/app/rfp-creator/page.tsx#L8-L158)
- [rfp-evaluator/page.tsx:18-177](file://frontend/src/app/rfp-evaluator/page.tsx#L18-L177)
- [api.ts:164-244](file://frontend/src/lib/api.ts#L164-L244)
- [useVideoProcessing.ts:122-420](file://frontend/src/lib/useVideoProcessing.ts#L122-L420)

**Section sources**
- [layout.tsx:1-41](file://frontend/src/app/layout.tsx#L1-L41)
- [Sidebar.tsx:1-67](file://frontend/src/components/Sidebar.tsx#L1-L67)
- [archive/page.tsx:1-129](file://frontend/src/app/archive/page.tsx#L1-L129)
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
- State Management: React hooks manage local UI state; a dedicated hook centralizes video processing state and WebSocket handling.
- Integration Layer: A typed API client abstracts HTTP requests and WebSocket connections, exposing convenience methods per domain (video, RFP).
- Backend Integration: Pages call the API client to perform uploads, fetch results, and poll evaluation status.

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
end
subgraph "State"
H1["useVideoProcessing<br/>src/lib/useVideoProcessing.ts"]
end
subgraph "Integration"
L1["api.ts<br/>src/lib/api.ts"]
end
P1 --> C1
P2 --> C3
P3 --> C4
P4 --> C5
P2 --> H1
H1 --> L1
P3 --> L1
P4 --> L1
```

**Diagram sources**
- [page.tsx:69-198](file://frontend/src/app/page.tsx#L69-L198)
- [archive/page.tsx:12-128](file://frontend/src/app/archive/page.tsx#L12-L128)
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
The Archive page coordinates video upload, pipeline visualization, and results presentation. It relies on a custom hook to manage upload state, WebSocket updates, and result retrieval.

Key responsibilities:
- Orchestrate VideoUpload component and pass upload callbacks.
- Render PipelineVisualizer during processing.
- Display VideoTimeline, TranscriptPanel, MetadataPanel, and APITransparencyPanel upon completion.
- Provide a persistent SearchDemo for semantic search across the archive.

```mermaid
sequenceDiagram
participant U as "User"
participant AU as "Archive Page<br/>archive/page.tsx"
participant VP as "useVideoProcessing<br/>useVideoProcessing.ts"
participant API as "api.ts"
participant WS as "WebSocket"
U->>AU : Select video file
AU->>VP : uploadVideo(file)
VP->>API : POST /api/video/upload
API-->>VP : {video_id,status}
VP->>WS : connect /ws/pipeline/{video_id}
WS-->>VP : stage status updates
VP->>API : GET /api/video/{video_id}/metadata
API-->>VP : metadata
VP->>API : GET /api/video/{video_id}/transcript
API-->>VP : transcript
VP-->>AU : updated state (results)
AU-->>U : render results panels
```

**Diagram sources**
- [archive/page.tsx:12-128](file://frontend/src/app/archive/page.tsx#L12-L128)
- [useVideoProcessing.ts:122-420](file://frontend/src/lib/useVideoProcessing.ts#L122-L420)
- [api.ts:164-244](file://frontend/src/lib/api.ts#L164-L244)

**Section sources**
- [archive/page.tsx:1-129](file://frontend/src/app/archive/page.tsx#L1-L129)
- [useVideoProcessing.ts:1-421](file://frontend/src/lib/useVideoProcessing.ts#L1-L421)
- [api.ts:164-244](file://frontend/src/lib/api.ts#L164-L244)

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
- Centralized video processing state: The useVideoProcessing hook encapsulates upload progress, pipeline stages, metadata, transcript, search results, and WebSocket lifecycle.
- Controlled components: Inputs and interactive elements are controlled, updating state via callbacks.

```mermaid
flowchart TD
Start(["Hook Initialization"]) --> Init["Initialize state:<br/>view, uploadState, stages, metadata, transcript"]
Init --> Upload["User selects file"]
Upload --> CallUpload["Call uploadVideo(file)"]
CallUpload --> SetIdle["Set uploadState='uploading'"]
SetIdle --> PostUpload["POST /api/video/upload"]
PostUpload --> GotId{"Got video_id?"}
GotId --> |Yes| ConnectWS["Connect WebSocket /ws/pipeline/{id}"]
GotId --> |No| HandleErr["Set uploadState='error'"]
ConnectWS --> WSMsg["Receive stage status"]
WSMsg --> UpdateStages["Update stages and view"]
UpdateStages --> Done{"All stages complete?"}
Done --> |Yes| FetchData["Fetch metadata/transcript"]
Done --> |No| Wait["Continue waiting"]
FetchData --> Render["Render results panels"]
HandleErr --> End(["End"])
Render --> End
Wait --> WSMsg
```

**Diagram sources**
- [useVideoProcessing.ts:122-420](file://frontend/src/lib/useVideoProcessing.ts#L122-L420)

**Section sources**
- [useVideoProcessing.ts:1-421](file://frontend/src/lib/useVideoProcessing.ts#L1-L421)

### API Integration Layer
The api.ts module provides:
- A typed fetch wrapper supporting query parameters and JSON parsing.
- File upload helpers for multipart/form-data.
- WebSocket connection helper with typed message shape.
- Domain-specific convenience methods for video and RFP operations.
- Strongly typed interfaces for request/response payloads.

Integration patterns:
- Pages import api and call domain methods (e.g., api.video.upload, api.rfp.create).
- Error handling is centralized in the fetch wrapper and surfaced to pages.
- Export endpoints open new browser tabs for downloadable artifacts.

**Section sources**
- [api.ts:1-245](file://frontend/src/lib/api.ts#L1-L245)

### Real-Time WebSocket Handling
The useVideoProcessing hook connects to a WebSocket endpoint to receive pipeline stage updates. It:
- Establishes the connection on successful upload.
- Parses incoming messages and updates stage statuses and timing.
- Falls back to REST polling if WebSocket fails or closes.
- Triggers result retrieval when the final stage completes.

```mermaid
sequenceDiagram
participant VP as "useVideoProcessing"
participant WS as "WebSocket"
participant API as "Backend"
VP->>WS : connect(/ws/pipeline/{videoId})
WS-->>VP : {"stage","status","message","progress"}
VP->>VP : update stages and view
alt status=complete
VP->>API : GET /api/video/{video_id}/metadata
API-->>VP : metadata
VP->>API : GET /api/video/{video_id}/transcript
API-->>VP : transcript
else error/closed
VP->>API : GET /api/video/{video_id}/status (poll)
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

## Troubleshooting Guide
Common issues and resolutions:
- Upload failures
  - Symptom: Error displayed in VideoUpload with red banner.
  - Actions: Verify backend connectivity, supported file types (.mp4, .mov, .avi), and file size limits.
- WebSocket disconnects
  - Symptom: Pipeline stalls; fallback polling occurs.
  - Actions: Check network stability; confirm backend WebSocket endpoint availability.
- Evaluation timeout
  - Symptom: Polling continues indefinitely.
  - Actions: Inspect backend logs; ensure evaluation job starts and progresses.
- Export downloads blocked
  - Symptom: Blank tab or blocked popup.
  - Actions: Allow popups; verify CORS and backend export endpoints.
- Navigation highlighting incorrect
  - Symptom: Sidebar active state mismatch.
  - Actions: Confirm route paths match navigation entries; ensure usePathname is used consistently.

**Section sources**
- [VideoUpload.tsx:200-217](file://frontend/src/components/archive/VideoUpload.tsx#L200-L217)
- [useVideoProcessing.ts:263-270](file://frontend/src/lib/useVideoProcessing.ts#L263-L270)
- [api.ts:31-36](file://frontend/src/lib/api.ts#L31-L36)

## Conclusion
The frontend employs a clean separation of concerns with Next.js App Router, reusable UI primitives, a centralized API client, and a dedicated hook for complex state and real-time updates. The architecture supports scalable feature development, robust error handling, and a responsive user experience across devices.

## Appendices
- Environment variables: NEXT_PUBLIC_API_URL is used to configure the API base URL at runtime.
- Fonts: Google Fonts via Next.js font providers are applied globally for sans-serif and mono fonts.
- Styling: Tailwind utility classes are used extensively for responsive layouts and component styling.

**Section sources**
- [api.ts:1-3](file://frontend/src/lib/api.ts#L1-L3)
- [layout.tsx:6-14](file://frontend/src/app/layout.tsx#L6-L14)
# Component Library

<cite>
**Referenced Files in This Document**
- [globals.css](file://frontend/src/app/globals.css)
- [Button.tsx](file://frontend/src/components/Button.tsx)
- [Card.tsx](file://frontend/src/components/Card.tsx)
- [VideoUpload.tsx](file://frontend/src/components/archive/VideoUpload.tsx)
- [VideoTimeline.tsx](file://frontend/src/components/archive/VideoTimeline.tsx)
- [TranscriptPanel.tsx](file://frontend/src/components/archive/TranscriptPanel.tsx)
- [MetadataPanel.tsx](file://frontend/src/components/archive/MetadataPanel.tsx)
- [SearchDemo.tsx](file://frontend/src/components/archive/SearchDemo.tsx)
- [PipelineVisualizer.tsx](file://frontend/src/components/archive/PipelineVisualizer.tsx)
- [SceneDetection.tsx](file://frontend/src/components/archive/SceneDetection.tsx)
- [RFPForm.tsx](file://frontend/src/components/rfp/RFPForm.tsx)
- [RFPPreview.tsx](file://frontend/src/components/rfp/RFPPreview.tsx)
- [TimelineEditor.tsx](file://frontend/src/components/rfp/TimelineEditor.tsx)
- [EvaluationSetup.tsx](file://frontend/src/components/evaluator/EvaluationSetup.tsx)
- [VendorScorecard.tsx](file://frontend/src/components/evaluator/VendorScorecard.tsx)
- [ComparisonMatrix.tsx](file://frontend/src/components/evaluator/ComparisonMatrix.tsx)
- [Sidebar.tsx](file://frontend/src/components/Sidebar.tsx)
- [api.ts](file://frontend/src/lib/api.ts)
- [useVideoProcessing.ts](file://frontend/src/lib/useVideoProcessing.ts)
- [archive/page.tsx](file://frontend/src/app/archive/page.tsx)
</cite>

## Update Summary
**Changes Made**
- Added comprehensive documentation for the new SceneDetection component
- Integrated SceneDetection into the Archive Components section with detailed analysis
- Updated component architecture diagrams to include SceneDetection
- Enhanced defensive programming practices section with SceneDetection examples
- Updated troubleshooting guide with SceneDetection-specific guidance

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Accessibility Improvements](#accessibility-improvements)
7. [Defensive Programming and Error Handling](#defensive-programming-and-error-handling)
8. [Dependency Analysis](#dependency-analysis)
9. [Performance Considerations](#performance-considerations)
10. [Troubleshooting Guide](#troubleshooting-guide)
11. [Conclusion](#conclusion)

## Introduction
This document describes the reusable UI component library used across the Dubai Media application. It covers foundational components (Button, Card) and specialized components grouped by feature areas: Archive, RFP Creator, and RFP Evaluator. For each component, we document props, events, styling patterns, composition guidelines, state management integration, accessibility, responsiveness, and performance characteristics. The goal is to enable consistent development and easy reuse across pages such as Archive Metadata, RFP Creator, and RFP Evaluator.

## Project Structure
The component library is organized by feature folders under frontend/src/components:
- Base primitives: Button, Card
- Archive feature: VideoUpload, VideoTimeline, TranscriptPanel, MetadataPanel, SearchDemo, PipelineVisualizer, SceneDetection
- RFP feature: RFPForm, RFPPreview, TimelineEditor
- Evaluator feature: EvaluationSetup, VendorScorecard, ComparisonMatrix
- Shared layout: Sidebar
- Shared libraries: api.ts (typed API helpers), useVideoProcessing.ts (video pipeline state hook)

```mermaid
graph TB
subgraph "Base"
B["Button.tsx"]
C["Card.tsx"]
end
subgraph "Archive"
VU["VideoUpload.tsx"]
VT["VideoTimeline.tsx"]
TP["TranscriptPanel.tsx"]
MP["MetadataPanel.tsx"]
SD["SearchDemo.tsx"]
PV["PipelineVisualizer.tsx"]
SC["SceneDetection.tsx"]
end
subgraph "RFP"
RF["RFPForm.tsx"]
RP["RFPPreview.tsx"]
TE["TimelineEditor.tsx"]
end
subgraph "Evaluator"
ES["EvaluationSetup.tsx"]
VS["VendorScorecard.tsx"]
CM["ComparisonMatrix.tsx"]
end
SB["Sidebar.tsx"]
B --> VU
C --> ES
VU --> VT
VT --> TP
VT --> MP
VT --> SC
MP --> SD
PV --> SC
SC --> SD
RF --> RP
TE --> RF
ES --> VS
ES --> CM
SB --> VU
SB --> RF
SB --> ES
```

**Diagram sources**
- [Button.tsx:1-30](file://frontend/src/components/Button.tsx#L1-L30)
- [Card.tsx:1-17](file://frontend/src/components/Card.tsx#L1-L17)
- [VideoUpload.tsx:1-221](file://frontend/src/components/archive/VideoUpload.tsx#L1-L221)
- [VideoTimeline.tsx:1-245](file://frontend/src/components/archive/VideoTimeline.tsx#L1-L245)
- [TranscriptPanel.tsx:1-169](file://frontend/src/components/archive/TranscriptPanel.tsx#L1-L169)
- [MetadataPanel.tsx:1-380](file://frontend/src/components/archive/MetadataPanel.tsx#L1-L380)
- [SearchDemo.tsx:1-230](file://frontend/src/components/archive/SearchDemo.tsx#L1-L230)
- [PipelineVisualizer.tsx:1-181](file://frontend/src/components/archive/PipelineVisualizer.tsx#L1-L181)
- [SceneDetection.tsx:1-181](file://frontend/src/components/archive/SceneDetection.tsx#L1-L181)
- [RFPForm.tsx:1-411](file://frontend/src/components/rfp/RFPForm.tsx#L1-L411)
- [RFPPreview.tsx:1-200](file://frontend/src/components/rfp/RFPPreview.tsx#L1-L200)
- [TimelineEditor.tsx:1-111](file://frontend/src/components/rfp/TimelineEditor.tsx#L1-L111)
- [EvaluationSetup.tsx:1-429](file://frontend/src/components/evaluator/EvaluationSetup.tsx#L1-L429)
- [VendorScorecard.tsx:1-241](file://frontend/src/components/evaluator/VendorScorecard.tsx#L1-L241)
- [ComparisonMatrix.tsx:1-318](file://frontend/src/components/evaluator/ComparisonMatrix.tsx#L1-L318)
- [Sidebar.tsx:1-67](file://frontend/src/components/Sidebar.tsx#L1-L67)

**Section sources**
- [Button.tsx:1-30](file://frontend/src/components/Button.tsx#L1-L30)
- [Card.tsx:1-17](file://frontend/src/components/Card.tsx#L1-L17)
- [VideoUpload.tsx:1-221](file://frontend/src/components/archive/VideoUpload.tsx#L1-L221)
- [VideoTimeline.tsx:1-245](file://frontend/src/components/archive/VideoTimeline.tsx#L1-L245)
- [TranscriptPanel.tsx:1-169](file://frontend/src/components/archive/TranscriptPanel.tsx#L1-L169)
- [MetadataPanel.tsx:1-380](file://frontend/src/components/archive/MetadataPanel.tsx#L1-L380)
- [SearchDemo.tsx:1-230](file://frontend/src/components/archive/SearchDemo.tsx#L1-L230)
- [PipelineVisualizer.tsx:1-181](file://frontend/src/components/archive/PipelineVisualizer.tsx#L1-L181)
- [SceneDetection.tsx:1-181](file://frontend/src/components/archive/SceneDetection.tsx#L1-L181)
- [RFPForm.tsx:1-411](file://frontend/src/components/rfp/RFPForm.tsx#L1-L411)
- [RFPPreview.tsx:1-200](file://frontend/src/components/rfp/RFPPreview.tsx#L1-L200)
- [TimelineEditor.tsx:1-111](file://frontend/src/components/rfp/TimelineEditor.tsx#L1-L111)
- [EvaluationSetup.tsx:1-429](file://frontend/src/components/evaluator/EvaluationSetup.tsx#L1-L429)
- [VendorScorecard.tsx:1-241](file://frontend/src/components/evaluator/VendorScorecard.tsx#L1-L241)
- [ComparisonMatrix.tsx:1-318](file://frontend/src/components/evaluator/ComparisonMatrix.tsx#L1-L318)
- [Sidebar.tsx:1-67](file://frontend/src/components/Sidebar.tsx#L1-L67)

## Core Components
These are the foundational building blocks reused across the application.

- Button
  - Purpose: Standardized button with primary/secondary variants and consistent focus/ring behavior.
  - Props:
    - children: ReactNode
    - variant?: "primary" | "secondary"
    - className?: string
    - Additional native button attributes (e.g., onClick, disabled)
  - Events: Inherits standard button events.
  - Styling: Uses Tailwind utility classes for spacing, colors, borders, transitions, and focus rings.
  - Accessibility: Focus-visible ring and keyboard operable.
  - Composition: Wrap with Card or layout containers for grouping.

- Card
  - Purpose: lightweight container with rounded corners, border, and padding.
  - Props:
    - children: ReactNode
    - className?: string
    - Additional native div attributes
  - Styling: Consistent white background, rounded-xl, gray-200 border, and p-6 padding.
  - Composition: Ideal for sectioning content in forms and dashboards.

**Section sources**
- [Button.tsx:3-29](file://frontend/src/components/Button.tsx#L3-L29)
- [Card.tsx:3-16](file://frontend/src/components/Card.tsx#L3-L16)

## Architecture Overview
The component library integrates with shared state and APIs:
- useVideoProcessing.ts manages upload, pipeline stages, metadata, transcript, search, and playback synchronization.
- api.ts provides typed wrappers for REST and WebSocket interactions.
- Components are designed to be stateless consumers of props and callbacks, enabling composability.

```mermaid
sequenceDiagram
participant U as "User"
participant VU as "VideoUpload"
participant UV as "useVideoProcessing"
participant API as "api.video.upload"
participant WS as "WebSocket /ws/pipeline/{id}"
U->>VU : Select video file
VU->>UV : uploadVideo(file)
UV->>API : POST /api/video/upload
API-->>UV : {video_id, status}
UV->>WS : connectWebSocket(/ws/pipeline/{video_id})
WS-->>UV : stage status updates
UV-->>VU : stages[], view=processing/results
UV-->>VU : metadata, transcript when ready
```

**Diagram sources**
- [VideoUpload.tsx:63-67](file://frontend/src/components/archive/VideoUpload.tsx#L63-L67)
- [useVideoProcessing.ts:162-211](file://frontend/src/lib/useVideoProcessing.ts#L162-L211)
- [api.ts:167-182](file://frontend/src/lib/api.ts#L167-L182)

## Detailed Component Analysis

### Archive Components

#### VideoUpload
- Purpose: Accepts video uploads with drag-and-drop, validates file types/extensions, displays progress, and surfaces errors.
- Props:
  - uploadState: UploadState ("idle" | "uploading" | "uploaded" | "error")
  - uploadProgress: number (0–100)
  - fileName: string | null
  - fileSize: number | null
  - error: string | null
  - onUpload: (file: File) => void
- Events:
  - Clicking the drop zone triggers hidden file input.
  - Drag-and-drop handlers manage dragOver state and file selection.
- Styling: Rounded card container, centered film/camera icon, hover states, disabled pointer-events during upload.
- Accessibility: Hidden input focusable via click; drag-and-drop uses aria-friendly markup.
- State integration: Integrates with useVideoProcessing for upload lifecycle and progress.
- Performance: Uses object URL for immediate playback; limits DOM updates to essential fields.

**Section sources**
- [VideoUpload.tsx:7-67](file://frontend/src/components/archive/VideoUpload.tsx#L7-L67)
- [useVideoProcessing.ts:162-211](file://frontend/src/lib/useVideoProcessing.ts#L162-L211)

#### VideoTimeline
- Purpose: Renders a video player with a scrubber timeline, scene markers, detected objects, and per-face appearance bars.
- Props:
  - videoRef: RefObject<HTMLVideoElement | null>
  - videoUrl: string | null
  - metadata: VideoMetadata | null
  - currentTime: number
  - onTimeUpdate: (time: number) => void
  - onSeek: (time: number) => void
- Interactions:
  - Timeline click seeks to computed timestamp.
  - Hover shows tooltip for nearby scene.
  - Clicking markers or face bars seeks to target time.
- Styling: Dark video container, progress overlay, blue scene markers, yellow object dots, primary-position indicator.
- Accessibility: Keyboard-accessible scrubber; tooltips provide context.
- State integration: Subscribes to video timeupdate and loadedmetadata; syncs with current time prop.
- **Enhanced Face Appearance Handling**: Implements null-safe face appearances mapping with fallback to empty array to prevent crashes when metadata is incomplete. Each face appearance now includes individual click handlers that seek to the start time of the appearance range, providing granular control over face detection navigation.

**Updated** Enhanced defensive programming improvements have been implemented to enhance the reliability and interactivity of face appearance rendering. The component now includes:

- **Null-safe face appearances mapping**: Uses `(face.appearances || []).map()` to safely handle cases where face appearances data might be missing or undefined
- **Individual appearance click handlers**: Each face appearance bar now has its own click handler that seeks to the specific start time of the appearance range
- **Improved tooltip information**: Tooltips now display face names along with formatted time ranges (e.g., "John Doe: 2:15 - 3:45")

**Section sources**
- [VideoTimeline.tsx:11-58](file://frontend/src/components/archive/VideoTimeline.tsx#L11-L58)
- [VideoTimeline.tsx:200-201](file://frontend/src/components/archive/VideoTimeline.tsx#L200-L201)
- [VideoTimeline.tsx:216-219](file://frontend/src/components/archive/VideoTimeline.tsx#L216-L219)
- [useVideoProcessing.ts:370-381](file://frontend/src/lib/useVideoProcessing.ts#L370-L381)

#### TranscriptPanel
- Purpose: Displays speech transcript segments with speaker identity, timestamps, and language indicators; auto-scrolls to active segment.
- Props:
  - segments: TranscriptSegment[]
  - currentTime: number
  - onSeek: (time: number) => void
- Interactions:
  - Clicking a timestamp seeks video to start of segment.
  - Auto-scroll keeps active segment visible.
- Styling: Scrollable panel, speaker badges with distinct colors, active segment highlighting.
- Accessibility: Smooth scroll behavior; clickable buttons for seeking; readable monospace timestamps.
- **Enhanced Timestamp Formatting**: Implements robust timestamp formatting using formatTimestamp function that handles multiple input types including strings (e.g., "00:15", "1:30"), numeric seconds, and malformed data with graceful fallback to "0:00".

**Updated** Enhanced timestamp formatting capabilities have been implemented to provide robust handling of various timestamp formats:

- **Multi-format support**: Handles string timestamps in "mm:ss" or "hh:mm:ss" format, numeric seconds, and malformed input
- **Graceful fallback**: Automatically falls back to "0:00" for invalid or undefined timestamps
- **Consistent output**: Always returns formatted timestamps in "m:ss" format with zero-padded seconds

**Section sources**
- [TranscriptPanel.tsx:6-59](file://frontend/src/components/archive/TranscriptPanel.tsx#L6-L59)
- [TranscriptPanel.tsx:30-48](file://frontend/src/components/archive/TranscriptPanel.tsx#L30-L48)

#### MetadataPanel
- Purpose: Presents processed metadata in tabs: Summary, EBUCore XML, IPTC JSON, Raw JSON.
- Props:
  - metadata: VideoMetadata | null
- Features:
  - Summary: Topic, sentiment, era, duration, detected persons, landmarks, sensitive content flags.
  - EBUCore: Copy XML and download as .xml.
  - IPTC/Raw: Expandable JSON tree with copy-to-clipboard.
- Styling: Tabbed interface with active-state underline; dark theme JSON viewer; badge chips for tags.
- Accessibility: Keyboard navigation among tabs; focusable copy/download buttons.

**Updated** Enhanced multilingual support and structured flag objects have been implemented to improve metadata display capabilities:

- **Bilingual person display**: When Arabic names are available, they are shown alongside English names in parentheses with proper RTL directionality
- **Structured flag objects**: Enhanced sensitive_content field now supports both string flags and structured objects with type, severity, and timestamp properties
- **Improved fallback handling**: Graceful handling of missing Arabic names with conditional rendering
- **RTL text support**: Proper right-to-left text direction for Arabic content within the badge display

**Section sources**
- [MetadataPanel.tsx:6-376](file://frontend/src/components/archive/MetadataPanel.tsx#L6-L376)
- [useVideoProcessing.ts:36-41](file://frontend/src/lib/useVideoProcessing.ts#L36-L41)

#### SearchDemo
- Purpose: Demonstrates semantic search over the archive with query input, results list, and result click handler.
- Props:
  - searchResults: SearchResult[]
  - isSearching: boolean
  - searchQuery: string
  - onSearch: (query: string) => void
  - onResultClick?: (result: SearchResult) => void
- Interactions:
  - Enter-key submission; disabled when empty or searching.
  - Clicking a result invokes onResultClick.
- Styling: Search icon, prominent input, result cards with thumbnails and score badges.

**Updated** Enhanced thumbnail URL resolution has been implemented to provide robust handling of various thumbnail path formats:

- **Universal URL resolution**: The resolveThumbnailUrl function handles multiple thumbnail path formats including "./uploads/...", "uploads/...", "/uploads/...", and full URLs
- **Environment-aware URLs**: Automatically prepends API_BASE_URL for relative paths to ensure browser accessibility
- **Null-safe handling**: Gracefully handles undefined or null thumbnail values without crashing
- **Cross-platform compatibility**: Works with different deployment environments and CDN configurations

**Section sources**
- [SearchDemo.tsx:7-43](file://frontend/src/components/archive/SearchDemo.tsx#L7-L43)
- [SearchDemo.tsx:13-21](file://frontend/src/components/archive/SearchDemo.tsx#L13-L21)

#### PipelineVisualizer
- Purpose: Visualizes pipeline stage statuses, progress, elapsed time, and messages.
- Props:
  - stages: PipelineStage[]
- Features:
  - Overall completion percentage bar.
  - Grid of stages with icons, status badges, elapsed time, and optional messages.
  - Animated processing state with spinner.
- Styling: Responsive grid (2–6 columns), connector lines between stages, color-coded backgrounds per status.

**Section sources**
- [PipelineVisualizer.tsx:6-91](file://frontend/src/components/archive/PipelineVisualizer.tsx#L6-L91)

#### SceneDetection
- Purpose: Provides sophisticated video scene analysis with timeline visualization, scene type categorization, and interactive navigation features.
- Props:
  - scenes: SceneBoundary[] - Array of scene boundary objects containing timestamp, description, and optional scene_type
  - duration: number - Total video duration in seconds
  - currentTime: number - Current playback position in seconds
  - onSeek: (time: number) => void - Callback function to seek to a specific timestamp
- Features:
  - Timeline visualization with color-coded scene segments based on scene_type
  - Active scene highlighting with orange ring indicator
  - Scene type legend with color mapping
  - Interactive scene list with expandable descriptions
  - Timestamp navigation from both timeline and list views
  - Responsive design with hover effects and smooth transitions
- Interactions:
  - Click timeline segments to navigate to scene start time
  - Click scene list items to seek to specific timestamps
  - Expand/collapse scene descriptions for detailed information
  - Hover over timeline segments for scene type and timestamp tooltips
- Styling: White card container with rounded corners, shadow, and responsive layout; color-coded scene segments with hover effects; active scene highlighting; scrollable scene list with expandable descriptions.
- Accessibility: Keyboard navigable timeline segments; clear visual hierarchy; color-coded legend; descriptive tooltips; expand/collapse controls with proper ARIA attributes.
- **Enhanced Scene Type Categorization**: Implements comprehensive color mapping for 8 different scene types including interview, b-roll, aerial, ceremony, documentary, news-anchor, sport, and other. Each scene type has associated background, text, border, and bar colors for consistent visual representation.
- **Interactive Timeline Visualization**: Provides precise timeline segmentation with calculated width percentages based on scene durations, creating an intuitive visual representation of scene distribution throughout the video.
- **Responsive Scene List**: Features expandable scene descriptions with show more/show less functionality, preventing clutter while providing detailed information access.
- **Integration with VideoTimeline**: Seamlessly complements VideoTimeline by providing an alternative visualization method and additional scene analysis capabilities. Both components share the same SceneBoundary interface from useVideoProcessing, ensuring consistency across the video analysis ecosystem.

**New** Comprehensive documentation for the SceneDetection component, including:
- Scene type color mapping system with 8 predefined categories
- Timeline visualization with interactive segments and playback indicator
- Detailed scene list with expandable descriptions and timestamp navigation
- Integration with useVideoProcessing SceneBoundary interface
- Responsive design patterns and accessibility features

**Section sources**
- [SceneDetection.tsx:6-40](file://frontend/src/components/archive/SceneDetection.tsx#L6-L40)
- [SceneDetection.tsx:14-27](file://frontend/src/components/archive/SceneDetection.tsx#L14-L27)
- [SceneDetection.tsx:74-101](file://frontend/src/components/archive/SceneDetection.tsx#L74-L101)
- [SceneDetection.tsx:119-176](file://frontend/src/components/archive/SceneDetection.tsx#L119-L176)
- [useVideoProcessing.ts:30-35](file://frontend/src/lib/useVideoProcessing.ts#L30-L35)

### RFP Components

#### RFPForm
- Purpose: Creates an RFP by collecting project details, technical requirements, evaluation criteria, timeline/milestones, budget range, compliance requirements, industry, language, and tone.
- Props:
  - onSubmit: (payload: RFPCreatePayload) => void
  - isLoading: boolean
- Interactions:
  - Dynamic lists for technical requirements and evaluation criteria.
  - Toggle for budget visibility; currency selector.
  - Compliance checkboxes with custom addition.
  - Language/tone radio groups.
  - Reset form to defaults.
- Validation:
  - Required fields: project title and overview.
  - Disabled submit until required fields are filled.
- Styling: Form sections with labels, inputs, toggles, and chips for custom compliance.

**Section sources**
- [RFPForm.tsx:10-123](file://frontend/src/components/rfp/RFPForm.tsx#L10-L123)

#### RFPPreview
- Purpose: Renders a bilingual preview of generated RFP sections with export options and optional regeneration.
- Props:
  - rfpId: string
  - title: string
  - sections: RFPSection[]
  - language: string
  - onRegenerateSection: (sectionName: string, instructions: string) => Promise<void>
  - onExportDocx: () => void
  - onExportPdf: () => void
  - regeneratingSection: string | null
- Interactions:
  - Switch between EN/AR views when bilingual.
  - Per-section regenerate prompt with instructions.
  - Export to DOCX/PDF via API endpoints.
- Styling: Document-like header/footer, sectioned content with RTL support when Arabic is active.

**Section sources**
- [RFPPreview.tsx:7-46](file://frontend/src/components/rfp/RFPPreview.tsx#L7-L46)

#### TimelineEditor
- Purpose: Manages project start/end dates and milestone entries with add/remove actions.
- Props:
  - startDate: string
  - endDate: string
  - milestones: Milestone[]
  - onStartDateChange: (date: string) => void
  - onEndDateChange: (date: string) => void
  - onMilestonesChange: (milestones: Milestone[]) => void
- Interactions:
  - Add milestone row; remove individual milestones.
  - Edit milestone name/date inline.

**Section sources**
- [TimelineEditor.tsx:11-43](file://frontend/src/components/rfp/TimelineEditor.tsx#L11-L43)

### Evaluator Components

#### EvaluationSetup
- Purpose: Configures evaluation by uploading the original RFP, vendor responses, and evaluation criteria weights; validates totals and runs evaluation.
- Props:
  - onEvaluate: (data) => Promise<void>
  - isEvaluating: boolean
  - progressMessage: string
- Interactions:
  - Upload RFP (PDF/DOCX); preview first 200 chars.
  - Add/remove vendor rows with name and file.
  - Manage criteria: add/remove, edit name/description, adjust weight, mark mandatory.
  - Apply preset templates.
  - Submit with validation: RFP present, minimum 2 vendors, all vendors complete, weights sum to 100%.
- Styling: Three-column layout with Cards; template chips; total weight indicator.

**Section sources**
- [EvaluationSetup.tsx:26-189](file://frontend/src/components/evaluator/EvaluationSetup.tsx#L26-L189)

#### VendorScorecard
- Purpose: Displays a vendor's overall score and detailed criterion breakdown with expandable justifications and evidence.
- Props:
  - vendors: VendorResult[]
- Features:
  - Tabbed vendor switching.
  - Radial progress for overall score.
  - Strengths/Gaps/Risks summary cards.
  - Expandable criterion rows with justification and evidence.
- Styling: Color-coded score badges; SVG radial progress; responsive grid for summary cards.

**Section sources**
- [VendorScorecard.tsx:70-239](file://frontend/src/components/evaluator/VendorScorecard.tsx#L70-L239)

#### ComparisonMatrix
- Purpose: Compares vendors across criteria with a matrix table, radar chart, and mandatory compliance checks; exports to XLSX/PDF.
- Props:
  - results: EvaluationResults
  - criteriaWeights: Record<string, number>
  - onExportXlsx: () => void
  - onExportPdf: () => void
- Features:
  - Top-score summary cards.
  - Matrix table with criterion weights and scores.
  - Radar chart visualization of vendor profiles.
  - Mandatory compliance matrix with pass/fail icons.
- Styling: Responsive tables, legend for radar chart, color-coded score badges.

**Section sources**
- [ComparisonMatrix.tsx:42-317](file://frontend/src/components/evaluator/ComparisonMatrix.tsx#L42-L317)

### Sidebar
- Purpose: Navigation sidebar linking to Archive Metadata, RFP Creator, and RFP Evaluator with active state indication and API connection status.
- Props: None (client-side navigation).
- Styling: Fixed position, brand header, navigation items with icons, active highlight.

**Section sources**
- [Sidebar.tsx:17-66](file://frontend/src/components/Sidebar.tsx#L17-L66)

## Accessibility Improvements

**Updated** Comprehensive CSS improvements have been implemented to address text visibility issues on dark backgrounds and improve overall accessibility across form components.

### Text Color Standards
The global stylesheet now enforces consistent text colors for optimal readability:

- **Primary text color**: `#1f2937` for all input elements (inputs, textareas, selects)
- **Placeholder text color**: `#6b7280` with full opacity for better contrast
- **Dark mode compatibility**: Automatic color adaptation through CSS variables

### CSS Structure Enhancements
The global stylesheet has been optimized to eliminate conflicts:

- **Removed duplicate imports**: Consolidated multiple `@import "tailwindcss"` statements
- **Eliminated conflicting dark mode queries**: Streamlined media query handling
- **Added systematic form styling**: Universal text color rules applied to all form controls

### Form Component Accessibility Improvements
All form components now benefit from improved text visibility:

- **Input fields**: Consistent dark gray text (`#1f2937`) ensures readability regardless of background
- **Placeholders**: Medium gray text (`#6b7280`) with opacity 1 prevents fading issues
- **Focus states**: Maintained high contrast for keyboard navigation
- **Error states**: Red text colors maintain sufficient contrast against light backgrounds

### Implementation Details
The accessibility improvements are implemented through:

```css
/* Ensure form inputs always have readable text and placeholder colors */
input,
textarea,
select {
  color: #1f2937;
}

input::placeholder,
textarea::placeholder {
  color: #6b7280;
  opacity: 1;
}
```

These changes ensure consistent text visibility across:
- Light and dark themes
- All form input types (text, textarea, select, checkbox, radio)
- Interactive states (hover, focus, disabled)
- High contrast scenarios

**Section sources**
- [globals.css:31-42](file://frontend/src/app/globals.css#L31-L42)
- [globals.css:86-91](file://frontend/src/app/globals.css#L86-L91)

## Defensive Programming and Error Handling

**Updated** The component library now includes comprehensive defensive programming practices to ensure robust operation even when data is incomplete or unexpected.

### Null-Safe Data Access Patterns
Components consistently implement null-safe data access patterns to prevent runtime errors:

- **Optional chaining operators (?.)**: Used for accessing nested properties that may be undefined
- **Logical OR fallbacks (|| [])**: Ensures arrays always have a valid fallback
- **Conditional rendering**: Components check for data existence before attempting to render

### Specific Defensive Programming Improvements

#### VideoTimeline Component
The VideoTimeline component demonstrates key defensive programming practices:

- **Face appearances safety**: Uses `(face.appearances || []).map()` to safely handle null/undefined appearances arrays
- **Duration validation**: Checks `duration > 0` before calculating percentages to prevent division by zero
- **Metadata fallbacks**: Provides default empty arrays for scenes, faces, and objects when metadata is unavailable
- **Individual appearance click handlers**: Each face appearance now has its own click handler that seeks to the specific start time of the appearance range

#### SceneDetection Component
The SceneDetection component implements comprehensive defensive programming patterns:

- **Empty scenes handling**: Returns null when scenes array is empty or undefined to prevent rendering issues
- **Scene boundary calculation**: Safely computes scene segments with fallback duration for the final scene
- **Active scene detection**: Uses findIndex with proper boundary checking to determine current scene
- **Scene type color mapping**: Provides fallback color mapping for unknown scene types
- **Expandable description handling**: Uses conditional rendering for truncated descriptions with proper state management

#### SearchDemo Component
The SearchDemo component includes enhanced defensive programming for thumbnail handling:

- **Thumbnail URL resolution safety**: The resolveThumbnailUrl function handles multiple input formats and edge cases
- **Environment configuration**: Uses NEXT_PUBLIC_API_URL with fallback to localhost for development
- **Null-safe rendering**: Thumbnail images are only rendered when valid URLs are available

#### TranscriptPanel Component
The TranscriptPanel component implements robust timestamp formatting:

- **Multi-type timestamp handling**: formatTimestamp function processes strings, numbers, and invalid inputs gracefully
- **Regex validation**: String timestamps are validated against expected patterns before processing
- **Zero-padded output**: Seconds are always zero-padded for consistent formatting

#### MetadataPanel Component
The MetadataPanel component includes enhanced multilingual support with defensive programming:

- **Conditional Arabic name rendering**: Uses `face.name_ar &&` to conditionally render Arabic names only when available
- **RTL direction handling**: Applies `dir="rtl"` attribute for proper right-to-left text display
- **Fallback to English names**: Gracefully falls back to English names when Arabic names are not available
- **Structured flag objects**: Enhanced sensitive_content field supports both string and object formats

#### General Error Handling Patterns
- **Early returns**: Functions return early when required data is missing
- **Safe calculations**: Percentage calculations include bounds checking
- **Graceful degradation**: Components render partial content when data is incomplete

### Benefits of Defensive Programming
- **Improved reliability**: Components continue functioning even with incomplete data
- **Better user experience**: Users see meaningful content rather than blank screens
- **Easier debugging**: Clear error boundaries help identify data source issues
- **Future-proofing**: Components can handle API changes gracefully

**Section sources**
- [VideoTimeline.tsx:84-86](file://frontend/src/components/archive/VideoTimeline.tsx#L84-L86)
- [VideoTimeline.tsx:200-201](file://frontend/src/components/archive/VideoTimeline.tsx#L200-L201)
- [VideoTimeline.tsx:216-219](file://frontend/src/components/archive/VideoTimeline.tsx#L216-L219)
- [VideoTimeline.tsx:229-239](file://frontend/src/components/archive/VideoTimeline.tsx#L229-L239)
- [SceneDetection.tsx:43](file://frontend/src/components/archive/SceneDetection.tsx#L43)
- [SceneDetection.tsx:52-55](file://frontend/src/components/archive/SceneDetection.tsx#L52-L55)
- [SceneDetection.tsx:25-27](file://frontend/src/components/archive/SceneDetection.tsx#L25-L27)
- [SearchDemo.tsx:13-21](file://frontend/src/components/archive/SearchDemo.tsx#L13-L21)
- [TranscriptPanel.tsx:30-48](file://frontend/src/components/archive/TranscriptPanel.tsx#L30-L48)
- [MetadataPanel.tsx:193-198](file://frontend/src/components/archive/MetadataPanel.tsx#L193-L198)

## Dependency Analysis
- Component coupling:
  - Archive components depend on useVideoProcessing for state and on api for REST/WebSocket calls.
  - RFP components depend on api for creation, regeneration, and evaluation workflows.
  - Evaluator components depend on api for evaluation status/results and exports.
- External dependencies:
  - Recharts for radar visualization in ComparisonMatrix.
  - Heroicons for UI icons across components.
- Potential circular dependencies:
  - None observed; components are leaf nodes consuming hooks and APIs.

```mermaid
graph LR
UV["useVideoProcessing.ts"] --> VU["VideoUpload.tsx"]
UV --> VT["VideoTimeline.tsx"]
UV --> TP["TranscriptPanel.tsx"]
UV --> MP["MetadataPanel.tsx"]
UV --> SD["SearchDemo.tsx"]
UV --> PV["PipelineVisualizer.tsx"]
UV --> SC["SceneDetection.tsx"]
API["api.ts"] --> VU
API --> VT
API --> MP
API --> SD
API --> RF["RFPForm.tsx"]
API --> RP["RFPPreview.tsx"]
API --> ES["EvaluationSetup.tsx"]
API --> VS["VendorScorecard.tsx"]
API --> CM["ComparisonMatrix.tsx"]
```

**Diagram sources**
- [useVideoProcessing.ts:122-420](file://frontend/src/lib/useVideoProcessing.ts#L122-L420)
- [api.ts:164-244](file://frontend/src/lib/api.ts#L164-L244)
- [VideoUpload.tsx:1-221](file://frontend/src/components/archive/VideoUpload.tsx#L1-L221)
- [VideoTimeline.tsx:1-245](file://frontend/src/components/archive/VideoTimeline.tsx#L1-L245)
- [TranscriptPanel.tsx:1-169](file://frontend/src/components/archive/TranscriptPanel.tsx#L1-L169)
- [MetadataPanel.tsx:1-380](file://frontend/src/components/archive/MetadataPanel.tsx#L1-L380)
- [SearchDemo.tsx:1-230](file://frontend/src/components/archive/SearchDemo.tsx#L1-L230)
- [PipelineVisualizer.tsx:1-181](file://frontend/src/components/archive/PipelineVisualizer.tsx#L1-L181)
- [SceneDetection.tsx:1-181](file://frontend/src/components/archive/SceneDetection.tsx#L1-L181)
- [RFPForm.tsx:1-411](file://frontend/src/components/rfp/RFPForm.tsx#L1-L411)
- [RFPPreview.tsx:1-200](file://frontend/src/components/rfp/RFPPreview.tsx#L1-L200)
- [EvaluationSetup.tsx:1-429](file://frontend/src/components/evaluator/EvaluationSetup.tsx#L1-L429)
- [VendorScorecard.tsx:1-241](file://frontend/src/components/evaluator/VendorScorecard.tsx#L1-L241)
- [ComparisonMatrix.tsx:1-318](file://frontend/src/components/evaluator/ComparisonMatrix.tsx#L1-L318)

**Section sources**
- [useVideoProcessing.ts:122-420](file://frontend/src/lib/useVideoProcessing.ts#L122-L420)
- [api.ts:164-244](file://frontend/src/lib/api.ts#L164-L244)

## Performance Considerations
- Virtualization: Not implemented; transcripts and metadata panels render lists. Consider virtualizing long lists if performance becomes an issue.
- Rendering frequency:
  - VideoTimeline updates on timeupdate; throttle if needed.
  - SceneDetection renders scene lists with expandable descriptions; consider virtualization for videos with many scenes.
  - MetadataPanel JSON tree renders deeply nested structures; keep expansion defaults minimal.
- Network:
  - useVideoProcessing simulates upload progress; real progress requires XHR with onprogress. Consider upgrading upload flow for accurate progress.
- Memory:
  - VideoUpload creates object URLs; revoke on reset to prevent leaks.
  - PipelineVisualizer and ComparisonMatrix render charts; unmount components to dispose resources.
  - SceneDetection maintains expanded state for individual scenes; consider limiting expanded scenes to improve performance.

## Troubleshooting Guide
- Upload fails:
  - Check error prop in VideoUpload and inspect network requests.
  - Verify accepted file types and sizes.
- Pipeline stalls:
  - Confirm WebSocket connection; fallback polling is used but may delay results.
  - Inspect stage statuses and elapsed times.
- Transcript not appearing:
  - Ensure pipeline reached completion and metadata/transcript fetched.
- RFP generation stuck:
  - Validate required fields and weights; ensure submit conditions are met.
- Evaluation errors:
  - Review validation messages and ensure RFP and vendor documents are present.
- **VideoTimeline rendering issues**:
  - Check if face appearances data is available in metadata.
  - Verify that duration is properly calculated before rendering appearance bars.
  - Ensure metadata is fully loaded before attempting to render timeline components.
  - **Updated**: Individual face appearance click handlers should now work correctly even when some faces lack appearance data.
- **SceneDetection rendering issues**:
  - **New**: Verify that scenes array contains valid SceneBoundary objects with timestamp and description properties.
  - Check that scene_type values match the predefined color mapping keys (interview, b-roll, aerial, ceremony, documentary, news-anchor, sport, other).
  - Ensure duration is greater than 0 to prevent timeline calculation errors.
  - Verify that onSeek callback properly handles timestamp values.
  - **Updated**: Scene detection now includes comprehensive defensive programming to handle missing or incomplete scene data gracefully.
- **MetadataPanel display issues**:
  - **Updated**: Arabic names should now display properly alongside English names with proper RTL directionality.
  - Check if face.name_ar property exists in the metadata structure.
  - Verify that the conditional rendering logic handles missing Arabic names gracefully.
  - **Updated**: Sensitive content flags now support both string and structured object formats.
- **SearchDemo thumbnail issues**:
  - **Updated**: Thumbnail URLs are now resolved using the enhanced resolveThumbnailUrl function.
  - Verify that thumbnail paths are properly formatted and accessible.
  - Check API_BASE_URL environment variable configuration.
- **TranscriptPanel timestamp problems**:
  - **Updated**: Timestamp formatting now handles multiple input formats and edge cases.
  - Verify that transcript segments contain valid start/end time values.
  - Check for malformed timestamp data in the backend response.

**Section sources**
- [VideoUpload.tsx:199-217](file://frontend/src/components/archive/VideoUpload.tsx#L199-L217)
- [useVideoProcessing.ts:215-276](file://frontend/src/lib/useVideoProcessing.ts#L215-L276)
- [EvaluationSetup.tsx:156-189](file://frontend/src/components/evaluator/EvaluationSetup.tsx#L156-L189)
- [VideoTimeline.tsx:200-201](file://frontend/src/components/archive/VideoTimeline.tsx#L200-L201)
- [SceneDetection.tsx:43](file://frontend/src/components/archive/SceneDetection.tsx#L43)
- [SceneDetection.tsx:52-55](file://frontend/src/components/archive/SceneDetection.tsx#L52-L55)
- [MetadataPanel.tsx:193-198](file://frontend/src/components/archive/MetadataPanel.tsx#L193-L198)
- [SearchDemo.tsx:13-21](file://frontend/src/components/archive/SearchDemo.tsx#L13-L21)
- [TranscriptPanel.tsx:30-48](file://frontend/src/components/archive/TranscriptPanel.tsx#L30-L48)

## Conclusion
The component library provides a cohesive, accessible, and extensible foundation for the Dubai Media application. Base components (Button, Card) standardize UI patterns; feature-specific components encapsulate complex workflows while integrating with shared state and APIs. The recent defensive programming improvements ensure reliable operation even with incomplete data, while the accessibility enhancements guarantee consistent text visibility across all form components. 

The new SceneDetection component significantly enhances the Archive feature by providing sophisticated video scene analysis capabilities. It offers both timeline visualization and detailed scene listing with interactive navigation, making video content exploration more intuitive and efficient. The component integrates seamlessly with the existing VideoTimeline component and shares the same SceneBoundary interface from useVideoProcessing, ensuring consistency across the video analysis ecosystem.

Key improvements include:
- **Comprehensive Scene Type Categorization**: Eight predefined scene types with consistent color mapping for visual differentiation
- **Interactive Timeline Visualization**: Precise scene segmentation with hover effects and active scene highlighting
- **Responsive Design**: Expandable scene descriptions with show more/show less functionality
- **Robust Error Handling**: Defensive programming patterns to handle incomplete or missing scene data gracefully
- **Accessibility Features**: Keyboard navigation, descriptive tooltips, and clear visual hierarchy

The enhanced VideoTimeline component now provides granular face detection navigation with improved tooltip information, and the MetadataPanel component offers comprehensive multilingual support with proper RTL handling. The SearchDemo component now features robust thumbnail URL resolution that handles various path formats, and the TranscriptPanel provides reliable timestamp formatting across multiple input types. By adhering to the documented props, composition patterns, defensive programming practices, and accessibility guidelines, teams can build consistent experiences across Archive, RFP, and Evaluator features.
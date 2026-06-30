"use client";

import { useVideoProcessing } from "@/lib/useVideoProcessing";
import VideoUpload from "@/components/archive/VideoUpload";
import PipelineVisualizer from "@/components/archive/PipelineVisualizer";
import VideoTimeline from "@/components/archive/VideoTimeline";
import TranscriptPanel from "@/components/archive/TranscriptPanel";
import MetadataPanel from "@/components/archive/MetadataPanel";
import SearchDemo from "@/components/archive/SearchDemo";
import APITransparencyPanel from "@/components/archive/APITransparencyPanel";

/** Convert a timestamp (number of seconds, or "MM:SS" / "HH:MM:SS" string) to seconds */
function parseTimestamp(value: unknown): number {
  if (typeof value === "number" && !isNaN(value)) return value;
  if (typeof value === "string") {
    // Try "HH:MM:SS" or "MM:SS"
    const parts = value.split(":").map(Number);
    if (parts.length === 3 && parts.every((p) => !isNaN(p))) {
      return parts[0] * 3600 + parts[1] * 60 + parts[2];
    }
    if (parts.length === 2 && parts.every((p) => !isNaN(p))) {
      return parts[0] * 60 + parts[1];
    }
    const parsed = parseFloat(value);
    if (!isNaN(parsed)) return parsed;
  }
  return 0;
}

export default function ArchivePage() {
  const {
    state,
    videoRef,
    uploadVideo,
    search,
    setCurrentTime,
    seekTo,
    reset,
  } = useVideoProcessing();

  return (
    <div className="max-w-[1400px] mx-auto">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Archive Metadata Tool
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Upload videos to extract metadata, transcripts, and scene
            descriptions using AI
          </p>
        </div>
        {state.view !== "upload" && (
          <button
            onClick={reset}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99"
              />
            </svg>
            New Video
          </button>
        )}
      </div>

      {/* Upload Section - shown when idle or uploading */}
      {(state.view === "upload" ||
        state.uploadState === "uploading") && (
        <div className="mb-6">
          <VideoUpload
            uploadState={state.uploadState}
            uploadProgress={state.uploadProgress}
            fileName={state.fileName}
            fileSize={state.fileSize}
            error={state.error}
            onUpload={uploadVideo}
          />
        </div>
      )}

      {/* Pipeline Visualizer - shown during processing */}
      {(state.view === "processing" || state.view === "results") && (
        <div className="mb-6">
          <PipelineVisualizer stages={state.stages} />
        </div>
      )}

      {/* Results Section - shown when processing is done */}
      {state.view === "results" && (
        <div className="mb-6">
          {/* Main content grid: Timeline+Transcript on left, Metadata on right */}
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
            {/* Left: Video Timeline + Transcript */}
            <div className="lg:col-span-3 space-y-6">
              <VideoTimeline
                videoRef={videoRef}
                videoUrl={state.videoUrl}
                metadata={state.metadata}
                currentTime={state.currentTime}
                onTimeUpdate={setCurrentTime}
                onSeek={seekTo}
              />
              <TranscriptPanel
                segments={state.transcript}
                currentTime={state.currentTime}
                onSeek={seekTo}
              />
            </div>

            {/* Right: Metadata + API Transparency */}
            <div className="lg:col-span-2 space-y-6">
              <MetadataPanel metadata={state.metadata} />
              <APITransparencyPanel
                apiCalls={state.metadata?.api_calls || []}
              />
            </div>
          </div>
        </div>
      )}

      {/* Search Demo - always visible at bottom */}
      <div className="mt-6">
        <SearchDemo
          searchResults={state.searchResults}
          isSearching={state.isSearching}
          searchQuery={state.searchQuery}
          onSearch={search}
          onResultClick={(result) => {
            seekTo(parseTimestamp(result.timestamp));
          }}
        />
      </div>
    </div>
  );
}

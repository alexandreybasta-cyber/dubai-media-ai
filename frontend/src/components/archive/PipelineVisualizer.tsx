"use client";

import { ReactNode } from "react";
import { PipelineStage, StageStatus } from "@/lib/useVideoProcessing";

interface PipelineVisualizerProps {
  stages: PipelineStage[];
}

function formatElapsed(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.floor(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`;
}

const STAGE_ICONS: Record<string, ReactNode> = {
  ingestion: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" />
    </svg>
  ),
  visual_analysis: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
    </svg>
  ),
  audio_speech: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z" />
    </svg>
  ),
  face_recognition: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
    </svg>
  ),
  metadata_structuring: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
    </svg>
  ),
  search_indexing: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
    </svg>
  ),
};

function StatusBadge({ status }: { status: StageStatus }) {
  const styles: Record<StageStatus, string> = {
    pending: "bg-gray-100 text-gray-500",
    processing: "bg-primary-100 text-primary-700",
    complete: "bg-green-100 text-green-700",
    failed: "bg-red-100 text-red-700",
  };

  const labels: Record<StageStatus, string> = {
    pending: "Pending",
    processing: "Processing",
    complete: "Complete",
    failed: "Failed",
  };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${styles[status]}`}>
      {status === "processing" && (
        <svg className="w-3 h-3 mr-1 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )}
      {status === "complete" && (
        <svg className="w-3 h-3 mr-1" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
        </svg>
      )}
      {status === "failed" && (
        <svg className="w-3 h-3 mr-1" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
        </svg>
      )}
      {labels[status]}
    </span>
  );
}

export default function PipelineVisualizer({ stages }: PipelineVisualizerProps) {
  const completedCount = stages.filter((s) => s.status === "complete").length;
  const totalCount = stages.length;
  const progressPercent = (completedCount / totalCount) * 100;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">
          Pipeline Progress
        </h2>
        <span className="text-sm text-gray-500">
          {completedCount}/{totalCount} stages complete
        </span>
      </div>

      {/* Overall progress bar */}
      <div className="w-full bg-gray-100 rounded-full h-2 mb-6">
        <div
          className="bg-primary-500 h-2 rounded-full transition-all duration-500"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Stages */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {stages.map((stage, index) => (
          <div key={stage.id} className="relative">
            {/* Connector line */}
            {index < stages.length - 1 && (
              <div className="hidden lg:block absolute top-6 left-[calc(50%+24px)] right-[-50%] h-0.5 bg-gray-200">
                {stage.status === "complete" && (
                  <div className="absolute inset-0 bg-green-400" />
                )}
              </div>
            )}

            <div
              className={`flex flex-col items-center p-3 rounded-lg transition-all ${
                stage.status === "processing"
                  ? "bg-primary-50 ring-2 ring-primary-200"
                  : stage.status === "complete"
                  ? "bg-green-50"
                  : stage.status === "failed"
                  ? "bg-red-50"
                  : "bg-gray-50"
              }`}
            >
              {/* Icon */}
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center mb-2 ${
                  stage.status === "processing"
                    ? "bg-primary-100 text-primary-600"
                    : stage.status === "complete"
                    ? "bg-green-100 text-green-600"
                    : stage.status === "failed"
                    ? "bg-red-100 text-red-600"
                    : "bg-gray-200 text-gray-400"
                }`}
              >
                {STAGE_ICONS[stage.id] || (
                  <span className="text-sm font-bold">{index + 1}</span>
                )}
              </div>

              {/* Name */}
              <p className="text-xs font-medium text-gray-700 text-center mb-1">
                {stage.name}
              </p>

              {/* Status badge */}
              <StatusBadge status={stage.status} />

              {/* Elapsed time */}
              {stage.elapsed && (
                <p className="text-[10px] text-gray-400 mt-1">
                  {formatElapsed(stage.elapsed)}
                </p>
              )}

              {/* Message */}
              {stage.message && stage.status === "processing" && (
                <p className="text-[10px] text-primary-600 mt-1 text-center truncate max-w-full">
                  {stage.message}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

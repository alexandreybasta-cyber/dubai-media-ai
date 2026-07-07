"use client";

import { useEffect, useRef } from "react";
import { TranscriptSegment } from "@/lib/useVideoProcessing";

interface TranscriptPanelProps {
  segments: TranscriptSegment[];
  currentTime: number;
  onSeek: (time: number) => void;
}

const SPEAKER_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  "Speaker 1": { bg: "bg-blue-100", text: "text-blue-700", border: "border-blue-200" },
  "Speaker 2": { bg: "bg-green-100", text: "text-green-700", border: "border-green-200" },
  "Speaker 3": { bg: "bg-purple-100", text: "text-purple-700", border: "border-purple-200" },
  "Speaker 4": { bg: "bg-amber-100", text: "text-amber-700", border: "border-amber-200" },
  "Speaker 5": { bg: "bg-pink-100", text: "text-pink-700", border: "border-pink-200" },
};

function getSpeakerStyle(speaker: string) {
  return (
    SPEAKER_COLORS[speaker] || {
      bg: "bg-gray-100",
      text: "text-gray-700",
      border: "border-gray-200",
    }
  );
}

function formatTimestamp(value: unknown): string {
  // Handle string timestamps (e.g., "00:15", "1:30")
  if (typeof value === "string") {
    if (/^\d{1,2}(:\d{2}){1,2}$/.test(value)) return value;
    const parsed = parseFloat(value);
    if (!isNaN(parsed)) {
      const m = Math.floor(parsed / 60);
      const s = Math.floor(parsed % 60);
      return `${m}:${s.toString().padStart(2, "0")}`;
    }
    return "0:00";
  }
  if (typeof value === "number" && !isNaN(value)) {
    const m = Math.floor(value / 60);
    const s = Math.floor(value % 60);
    return `${m}:${s.toString().padStart(2, "0")}`;
  }
  return "0:00";
}

export default function TranscriptPanel({
  segments,
  currentTime,
  onSeek,
}: TranscriptPanelProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const activeRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to active segment
  useEffect(() => {
    if (activeRef.current && containerRef.current) {
      const container = containerRef.current;
      const active = activeRef.current;
      const containerRect = container.getBoundingClientRect();
      const activeRect = active.getBoundingClientRect();

      if (
        activeRect.top < containerRect.top ||
        activeRect.bottom > containerRect.bottom
      ) {
        active.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  }, [currentTime]);

  if (segments.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm min-h-[200px] flex items-center justify-center">
        <div className="text-center">
          <svg
            className="w-10 h-10 text-gray-300 mx-auto mb-2"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 0 1 .865-.501 48.172 48.172 0 0 0 3.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018Z"
            />
          </svg>
          <p className="text-sm text-gray-500">Transcript will appear here</p>
          <p className="text-xs text-gray-400 mt-1">
            After audio/speech processing completes
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm flex flex-col">
      <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900">Transcript</h3>
        <span className="text-xs text-gray-400">
          {segments.length} segments
        </span>
      </div>

      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto p-4 space-y-3 max-h-[500px]"
      >
        {segments.map((segment, index) => {
          const isActive =
            currentTime >= segment.start && currentTime < segment.end;
          const style = getSpeakerStyle(segment.speaker);

          return (
            <div
              key={index}
              ref={isActive ? activeRef : null}
              className={`rounded-lg p-3 transition-colors ${
                isActive
                  ? "bg-primary-50 ring-1 ring-primary-200"
                  : "hover:bg-gray-50"
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                {/* Speaker badge */}
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${style.bg} ${style.text}`}
                >
                  {segment.speaker}
                </span>

                {/* Language indicator */}
                {segment.language && (
                  <span className="text-[10px] text-gray-400 uppercase">
                    {segment.language}
                  </span>
                )}

                {/* Timestamp */}
                <button
                  onClick={() => onSeek(segment.start)}
                  className="ml-auto text-xs text-gray-400 hover:text-primary-500 font-mono transition-colors"
                >
                  {formatTimestamp(segment.start)}
                </button>
              </div>

              {/* Text content */}
              <p
                dir="auto"
                className={`text-sm leading-relaxed ${
                  isActive ? "text-gray-900" : "text-gray-700"
                }`}
              >
                {segment.text}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

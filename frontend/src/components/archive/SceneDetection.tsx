"use client";

import { useState } from "react";
import { SceneBoundary } from "@/lib/useVideoProcessing";

interface SceneDetectionProps {
  scenes: SceneBoundary[];
  duration: number;
  currentTime: number;
  onSeek: (time: number) => void;
}

/** Color map for scene types */
const SCENE_TYPE_COLORS: Record<string, { bg: string; text: string; border: string; bar: string }> = {
  interview: { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-400", bar: "#3B82F6" },
  "b-roll": { bg: "bg-orange-50", text: "text-orange-700", border: "border-orange-400", bar: "#F97316" },
  aerial: { bg: "bg-teal-50", text: "text-teal-700", border: "border-teal-400", bar: "#14B8A6" },
  ceremony: { bg: "bg-purple-50", text: "text-purple-700", border: "border-purple-400", bar: "#8B5CF6" },
  documentary: { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-400", bar: "#F59E0B" },
  "news-anchor": { bg: "bg-red-50", text: "text-red-700", border: "border-red-400", bar: "#EF4444" },
  sport: { bg: "bg-green-50", text: "text-green-700", border: "border-green-400", bar: "#22C55E" },
  other: { bg: "bg-gray-50", text: "text-gray-600", border: "border-gray-400", bar: "#9CA3AF" },
};

function getSceneColor(sceneType?: string) {
  return SCENE_TYPE_COLORS[sceneType || "other"] || SCENE_TYPE_COLORS["other"];
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function SceneDetection({
  scenes,
  duration,
  currentTime,
  onSeek,
}: SceneDetectionProps) {
  const [expandedScene, setExpandedScene] = useState<number | null>(null);

  if (!scenes || scenes.length === 0) return null;

  // Compute scene segments with start/end times for timeline bar
  const segments = scenes.map((scene, i) => {
    const start = scene.timestamp;
    const end = i < scenes.length - 1 ? scenes[i + 1].timestamp : duration;
    return { ...scene, start, end, index: i };
  });

  // Find active scene based on current time
  const activeSceneIndex = segments.findIndex(
    (seg) => currentTime >= seg.start && currentTime < seg.end
  );

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-orange-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 0 1-1.125-1.125M3.375 19.5h1.5C5.496 19.5 6 18.996 6 18.375m-2.625 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-1.5A1.125 1.125 0 0 1 18 18.375M20.625 4.5H3.375m17.25 0c.621 0 1.125.504 1.125 1.125M20.625 4.5h-1.5C18.504 4.5 18 5.004 18 5.625m3.75 0v1.5c0 .621-.504 1.125-1.125 1.125M3.375 4.5c-.621 0-1.125.504-1.125 1.125M3.375 4.5h1.5C5.496 4.5 6 5.004 6 5.625m-3.75 0v1.5c0 .621.504 1.125 1.125 1.125m0 0h1.5m-1.5 0c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m1.5-3.75C5.496 8.25 6 7.746 6 7.125v-1.5M4.875 8.25C5.496 8.25 6 8.754 6 9.375v1.5m0-5.25v5.25m0-5.25C6 5.004 6.504 4.5 7.125 4.5h9.75c.621 0 1.125.504 1.125 1.125m1.125 2.625h1.5m-1.5 0A1.125 1.125 0 0 1 18 7.125v-1.5m1.125 2.625c-.621 0-1.125.504-1.125 1.125v1.5m2.625-2.625c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125M18 5.625v5.25M7.125 12h9.75m-9.75 0A1.125 1.125 0 0 1 6 10.875M7.125 12C6.504 12 6 12.504 6 13.125m0-2.25C6 11.496 5.496 12 4.875 12M18 10.875c0 .621-.504 1.125-1.125 1.125M18 10.875c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125m-12 5.25v-5.25m0 5.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125m-12 0v-1.5c0-.621-.504-1.125-1.125-1.125M18 18.375v-5.25m0 5.25v-1.5c0-.621.504-1.125 1.125-1.125M18 13.125v1.5c0 .621.504 1.125 1.125 1.125M18 13.125c0-.621.504-1.125 1.125-1.125M6 13.125v1.5c0 .621-.504 1.125-1.125 1.125M6 13.125C6 12.504 5.496 12 4.875 12m-1.5 0h1.5m-1.5 0c-.621 0-1.125-.504-1.125-1.125v-1.5c0-.621.504-1.125 1.125-1.125m1.5 2.625c0-.621-.504-1.125-1.125-1.125M19.125 12h1.5m0 0c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 2.625h-1.5" />
          </svg>
          <h3 className="text-sm font-semibold text-gray-900">Scene Detection</h3>
          <span className="ml-auto text-xs text-gray-500">{scenes.length} scenes detected</span>
        </div>
      </div>

      <div className="p-5">
        {/* Scene Timeline Bar */}
        <div className="mb-4">
          <div className="relative h-8 rounded-lg overflow-hidden flex cursor-pointer border border-gray-200">
            {segments.map((seg, i) => {
              const widthPercent = duration > 0 ? ((seg.end - seg.start) / duration) * 100 : 0;
              const color = getSceneColor(seg.scene_type);
              const isActive = i === activeSceneIndex;
              return (
                <div
                  key={i}
                  className={`relative h-full transition-all duration-150 ${isActive ? "ring-2 ring-orange-400 ring-inset z-10" : "hover:brightness-110"}`}
                  style={{
                    width: `${widthPercent}%`,
                    backgroundColor: color.bar,
                    opacity: isActive ? 1 : 0.7,
                  }}
                  onClick={() => onSeek(seg.start)}
                  title={`${seg.scene_type || "other"} — ${formatTime(seg.start)}`}
                />
              );
            })}
            {/* Playback indicator */}
            {duration > 0 && (
              <div
                className="absolute top-0 bottom-0 w-0.5 bg-gray-900 z-20 pointer-events-none"
                style={{ left: `${(currentTime / duration) * 100}%` }}
              >
                <div className="absolute -top-0.5 left-1/2 -translate-x-1/2 w-2 h-2 rounded-full bg-gray-900" />
              </div>
            )}
          </div>

          {/* Legend */}
          <div className="flex flex-wrap gap-3 mt-3">
            {Array.from(new Set(scenes.map((s) => s.scene_type || "other"))).map((type) => {
              const color = getSceneColor(type);
              return (
                <div key={type} className="flex items-center gap-1.5">
                  <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: color.bar }} />
                  <span className="text-xs text-gray-600 capitalize">{type}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Scene List */}
        <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
          {scenes.map((scene, i) => {
            const color = getSceneColor(scene.scene_type);
            const isActive = i === activeSceneIndex;
            const isExpanded = expandedScene === i;
            const descTruncated = scene.description.length > 120;

            return (
              <div
                key={i}
                className={`border-l-4 rounded-lg p-3 cursor-pointer transition-all duration-150 ${
                  isActive
                    ? "bg-orange-50 border-orange-400 shadow-sm"
                    : "bg-white hover:bg-gray-50 border-transparent hover:border-gray-300"
                } ${color.border}`}
                style={{ borderLeftColor: color.bar }}
                onClick={() => onSeek(scene.timestamp)}
              >
                <div className="flex items-start gap-3">
                  {/* Timestamp */}
                  <button
                    className="flex-shrink-0 text-xs font-mono font-medium text-orange-600 bg-orange-50 px-2 py-1 rounded hover:bg-orange-100 transition-colors"
                    onClick={(e) => {
                      e.stopPropagation();
                      onSeek(scene.timestamp);
                    }}
                  >
                    {formatTime(scene.timestamp)}
                  </button>

                  {/* Scene type badge */}
                  <span
                    className={`flex-shrink-0 text-xs font-medium px-2 py-0.5 rounded-full capitalize ${color.bg} ${color.text}`}
                  >
                    {scene.scene_type || "other"}
                  </span>

                  {/* Description */}
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm text-gray-700 leading-relaxed ${!isExpanded && descTruncated ? "line-clamp-2" : ""}`}>
                      {scene.description}
                    </p>
                    {descTruncated && (
                      <button
                        className="text-xs text-orange-600 hover:text-orange-700 mt-1 font-medium"
                        onClick={(e) => {
                          e.stopPropagation();
                          setExpandedScene(isExpanded ? null : i);
                        }}
                      >
                        {isExpanded ? "Show less" : "Show more"}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

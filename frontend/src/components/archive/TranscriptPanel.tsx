"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { TranscriptSegment } from "@/lib/useVideoProcessing";
import { api } from "@/lib/api";

interface TranscriptPanelProps {
  videoId: string | null;
  segments: TranscriptSegment[];
  currentTime: number;
  onSeek: (time: number) => void;
}

const TRANSLATE_OPTIONS: { value: string; label: string }[] = [
  { value: "ar", label: "العربية" },
  { value: "fr", label: "Français" },
  { value: "ru", label: "Русский" },
];

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
  videoId,
  segments,
  currentTime,
  onSeek,
}: TranscriptPanelProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const activeRef = useRef<HTMLDivElement>(null);

  // Translation state
  const [translatedSegments, setTranslatedSegments] = useState<Map<number, string>>(
    new Map()
  );
  const [translating, setTranslating] = useState(false);
  const [activeLanguage, setActiveLanguage] = useState<string | null>(null);
  const [translateError, setTranslateError] = useState<string | null>(null);

  // Reset any translation when the underlying transcript/video changes
  useEffect(() => {
    setTranslatedSegments(new Map());
    setActiveLanguage(null);
    setTranslateError(null);
  }, [videoId]);

  const handleTranslate = useCallback(
    async (language: string) => {
      setTranslateError(null);

      // "Original" clears the translation
      if (!language) {
        setActiveLanguage(null);
        setTranslatedSegments(new Map());
        return;
      }

      if (!videoId || segments.length === 0) return;

      setTranslating(true);
      setActiveLanguage(language);
      try {
        const payload = segments.map((s) => ({
          text: s.text,
          start_time: s.start,
          end_time: s.end,
        }));
        const res = await api.video.translateTranscript(videoId, language, payload);
        const map = new Map<number, string>();
        (res.translations || []).forEach((t, i) => {
          if (t?.text) map.set(i, t.text);
        });
        setTranslatedSegments(map);
      } catch (err) {
        console.error("Translation failed:", err);
        setTranslateError(
          err instanceof Error ? err.message : "Translation failed. Please try again."
        );
        setActiveLanguage(null);
        setTranslatedSegments(new Map());
      } finally {
        setTranslating(false);
      }
    },
    [videoId, segments]
  );

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
      <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-gray-900">Transcript</h3>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">
            {segments.length} segments
          </span>

          {/* Translate dropdown */}
          <div className="relative flex items-center">
            <svg
              className="w-3.5 h-3.5 text-primary-500 absolute left-2 pointer-events-none"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.8}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Zm0 0c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m-9 9h18"
              />
            </svg>
            <select
              value={activeLanguage ?? ""}
              disabled={translating || segments.length === 0}
              onChange={(e) => handleTranslate(e.target.value)}
              className="appearance-none pl-7 pr-6 py-1 text-xs font-medium rounded-md bg-primary-500 text-white border border-primary-500 hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-300 cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
              aria-label="Translate transcript"
            >
              <option value="">Original</option>
              {TRANSLATE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value} className="text-gray-900">
                  {opt.label}
                </option>
              ))}
            </select>
            <svg
              className="w-3 h-3 text-white absolute right-1.5 pointer-events-none"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2.5}
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
            </svg>
          </div>

          {translating && (
            <span className="flex items-center gap-1 text-xs text-primary-600">
              <svg className="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8V0C5.373 0 0 5.373 0 12h4Z" />
              </svg>
              Translating…
            </span>
          )}
        </div>
      </div>

      {translateError && (
        <div className="px-4 py-2 text-xs text-red-600 bg-red-50 border-b border-red-100">
          {translateError}
        </div>
      )}

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

              {/* Translated text (shown under the original) */}
              {translatedSegments.has(index) && (
                <>
                  <div className="my-2 border-t border-primary-200/60" />
                  <p
                    dir={activeLanguage === "ar" ? "rtl" : "auto"}
                    className="text-sm leading-relaxed italic text-primary-700/90"
                  >
                    {translatedSegments.get(index)}
                  </p>
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

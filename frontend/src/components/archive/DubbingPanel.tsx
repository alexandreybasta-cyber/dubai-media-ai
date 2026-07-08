"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, API_BASE_URL } from "@/lib/api";

interface DubbingPanelProps {
  videoId: string | null;
}

const LANGUAGE_LABELS: Record<string, string> = {
  ar: "Arabic (العربية)",
  en: "English",
  fr: "French (Français)",
  es: "Spanish (Español)",
  de: "German (Deutsch)",
  ru: "Russian (Русский)",
  hi: "Hindi (हिन्दी)",
  zh: "Chinese (中文)",
};

const SUPPORTED_LANGUAGES = ["ar", "en", "fr", "es", "de", "ru", "hi", "zh"];

function dubbedVideoUrl(videoId: string, language: string): string {
  return `${API_BASE_URL}/api/video/${videoId}/dubbed/${language}`;
}

export default function DubbingPanel({ videoId }: DubbingPanelProps) {
  const [targetLanguage, setTargetLanguage] = useState<string>("ar");
  const [dubbedLanguages, setDubbedLanguages] = useState<string[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingLanguage, setProcessingLanguage] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [playingLanguage, setPlayingLanguage] = useState<string | null>(null);

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const progressRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearTimers = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    if (progressRef.current) {
      clearInterval(progressRef.current);
      progressRef.current = null;
    }
  }, []);

  // Load already-dubbed languages when the video changes
  const loadLanguages = useCallback(async () => {
    if (!videoId) return;
    try {
      const res = await api.video.getDubbingLanguages(videoId);
      setDubbedLanguages(res.dubbed_languages || []);
    } catch {
      // A video with no dubbing yet may 404 / error — treat as empty
      setDubbedLanguages([]);
    }
  }, [videoId]);

  useEffect(() => {
    // Reset state whenever the video changes
    clearTimers();
    setIsProcessing(false);
    setProcessingLanguage(null);
    setProgress(0);
    setError(null);
    setPlayingLanguage(null);
    setDubbedLanguages([]);
    loadLanguages();
    return clearTimers;
  }, [videoId, loadLanguages, clearTimers]);

  const startPolling = useCallback(
    (language: string) => {
      if (!videoId) return;

      // Simulated progress bar (backend status is boolean-ish, so animate up to 90%)
      setProgress(5);
      progressRef.current = setInterval(() => {
        setProgress((p) => (p < 90 ? p + Math.max(1, Math.round((90 - p) / 12)) : p));
      }, 800);

      pollRef.current = setInterval(async () => {
        try {
          const status = await api.video.getDubbingStatus(videoId);
          const langs = status.languages || {};
          const entry = langs[language] as
            | { status?: string; ready?: boolean; completed?: boolean }
            | undefined;

          const done =
            entry?.status === "completed" ||
            entry?.ready === true ||
            entry?.completed === true ||
            // Fallback: language now appears in the languages map with truthy value
            (entry !== undefined && entry !== null && typeof entry !== "object");

          if (done) {
            clearTimers();
            setProgress(100);
            setIsProcessing(false);
            setProcessingLanguage(null);
            await loadLanguages();
          }
        } catch (err) {
          // Keep polling on transient errors, but surface persistent ones
          console.error("Dubbing status poll failed:", err);
        }
      }, 3000);
    },
    [videoId, clearTimers, loadLanguages]
  );

  const handleDub = useCallback(async () => {
    if (!videoId || isProcessing) return;
    setError(null);

    // Already dubbed — no need to re-run
    if (dubbedLanguages.includes(targetLanguage)) {
      return;
    }

    setIsProcessing(true);
    setProcessingLanguage(targetLanguage);
    setProgress(0);
    try {
      await api.video.requestDubbing(videoId, targetLanguage);
      startPolling(targetLanguage);
    } catch (err) {
      clearTimers();
      setIsProcessing(false);
      setProcessingLanguage(null);
      setProgress(0);
      setError(
        err instanceof Error ? err.message : "Failed to start dubbing. Please try again."
      );
    }
  }, [videoId, isProcessing, dubbedLanguages, targetLanguage, startPolling, clearTimers]);

  if (!videoId) {
    return null;
  }

  const alreadyDubbed = dubbedLanguages.includes(targetLanguage);

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-100 flex items-center gap-2">
        <svg
          className="w-4 h-4 text-primary-500"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.8}
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z"
          />
        </svg>
        <h3 className="text-sm font-semibold text-gray-900">Video Dubbing</h3>
      </div>

      <div className="p-4 space-y-4">
        {/* Language selector + Dub button */}
        <div className="space-y-3">
          <label className="block text-xs font-medium text-gray-600">
            Target Language
          </label>
          <div className="relative flex items-center">
            <select
              value={targetLanguage}
              disabled={isProcessing}
              onChange={(e) => setTargetLanguage(e.target.value)}
              className="appearance-none w-full pl-3 pr-8 py-2 text-sm font-medium text-gray-900 rounded-md bg-white border border-gray-300 hover:border-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-300 cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
              aria-label="Target dubbing language"
            >
              {SUPPORTED_LANGUAGES.map((code) => (
                <option key={code} value={code} className="text-gray-900">
                  {LANGUAGE_LABELS[code] || code}
                </option>
              ))}
            </select>
            <svg
              className="w-3.5 h-3.5 text-gray-400 absolute right-2.5 pointer-events-none"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2.5}
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
            </svg>
          </div>

          <button
            onClick={handleDub}
            disabled={isProcessing || alreadyDubbed}
            className="inline-flex items-center justify-center gap-2 w-full px-4 py-2 text-sm font-semibold rounded-md bg-primary-500 text-white hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-300 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {isProcessing ? (
              <>
                <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8V0C5.373 0 0 5.373 0 12h4Z" />
                </svg>
                Dubbing…
              </>
            ) : alreadyDubbed ? (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                </svg>
                Already Dubbed
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.8} stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M19.114 5.636a9 9 0 0 1 0 12.728M16.463 8.288a5.25 5.25 0 0 1 0 7.424M6.75 8.25l4.72-4.72a.75.75 0 0 1 1.28.53v15.88a.75.75 0 0 1-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.009 9.009 0 0 1 2.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75Z"
                  />
                </svg>
                Dub Video
              </>
            )}
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="px-3 py-2 text-xs text-red-600 bg-red-50 border border-red-100 rounded-md">
            {error}
          </div>
        )}

        {/* Progress indicator */}
        {isProcessing && (
          <div className="rounded-lg bg-primary-50 border border-primary-100 p-3 space-y-2">
            <div className="flex items-center gap-2 text-xs font-medium text-primary-700">
              <svg className="w-3.5 h-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8V0C5.373 0 0 5.373 0 12h4Z" />
              </svg>
              Dubbing in progress — Generating{" "}
              {LANGUAGE_LABELS[processingLanguage || ""] || processingLanguage}…
            </div>
            <div className="w-full h-2 rounded-full bg-primary-100 overflow-hidden">
              <div
                className="h-full bg-primary-500 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Available dubs */}
        <div className="pt-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Available Dubs
            </span>
            <span className="text-xs text-gray-400">({dubbedLanguages.length})</span>
          </div>

          {dubbedLanguages.length === 0 ? (
            <p className="text-xs text-gray-400">
              No dubbed versions yet. Select a language and click “Dub Video”.
            </p>
          ) : (
            <ul className="space-y-2">
              {dubbedLanguages.map((code) => (
                <li
                  key={code}
                  className="flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2"
                >
                  <svg
                    className="w-4 h-4 text-green-500 flex-shrink-0"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={2}
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                  </svg>
                  <span className="text-sm text-gray-800 flex-1 truncate">
                    {LANGUAGE_LABELS[code] || code}
                  </span>
                  <button
                    onClick={() =>
                      setPlayingLanguage((cur) => (cur === code ? null : code))
                    }
                    className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-md bg-primary-500 text-white hover:bg-primary-600 transition-colors"
                  >
                    <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M4.5 5.653c0-1.426 1.529-2.33 2.779-1.643l11.54 6.348c1.295.712 1.295 2.573 0 3.285L7.28 19.99c-1.25.687-2.779-.217-2.779-1.643V5.653Z" />
                    </svg>
                    {playingLanguage === code ? "Hide" : "Play"}
                  </button>
                  <a
                    href={dubbedVideoUrl(videoId, code)}
                    download={`dubbed_${videoId}_${code}.mp4`}
                    className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-md border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3"
                      />
                    </svg>
                    Download
                  </a>
                </li>
              ))}
            </ul>
          )}

          {/* Inline player for selected dubbed language */}
          {playingLanguage && (
            <div className="mt-3 rounded-lg overflow-hidden border border-gray-200 bg-black">
              <video
                key={playingLanguage}
                src={dubbedVideoUrl(videoId, playingLanguage)}
                controls
                autoPlay
                className="w-full max-h-[320px]"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

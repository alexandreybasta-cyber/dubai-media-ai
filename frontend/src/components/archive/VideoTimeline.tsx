"use client";

import { RefObject, useEffect, useRef, useState } from "react";
import { API_BASE_URL } from "@/lib/api";
import {
  SceneBoundary,
  DetectedFace,
  DetectedObject,
  VideoMetadata,
} from "@/lib/useVideoProcessing";

interface VideoTimelineProps {
  videoRef: RefObject<HTMLVideoElement | null>;
  /** Seek requested before the media was ready; applied on loadedmetadata */
  pendingSeekRef?: RefObject<number | null>;
  videoId: string | null;
  videoUrl: string | null;
  metadata: VideoMetadata | null;
  currentTime: number;
  onTimeUpdate: (time: number) => void;
  onSeek: (time: number) => void;
}

interface SubtitleLanguage {
  code: string;
  label: string;
  rtl: boolean;
}

const SUBTITLE_LANGUAGES: SubtitleLanguage[] = [
  { code: "en", label: "English", rtl: false },
  { code: "ar", label: "العربية", rtl: true },
  { code: "fr", label: "Français", rtl: false },
  { code: "ru", label: "Русский", rtl: false },
];

// Per-speaker caption colors (light shades for readability on dark backdrop).
const SPEAKER_COLORS: Record<string, string> = {
  "Speaker 1": "#93c5fd", // blue
  "Speaker 2": "#6ee7b7", // green
  "Speaker 3": "#c4b5fd", // purple
  "Speaker 4": "#fcd34d", // amber
  "Speaker 5": "#f9a8d4", // pink
};

/**
 * Parse a WebVTT cue's raw text, extracting an optional `<v Speaker N>` voice
 * tag to determine the speaker color. Returns the clean display text and color.
 */
function parseCueText(raw: string): { text: string; color: string } {
  let speaker: string | null = null;
  let text = raw;
  const voice = raw.match(/<v\s+([^>]+)>([\s\S]*?)<\/v>/);
  if (voice) {
    speaker = voice[1].trim();
    text = voice[2];
  } else {
    // Handle a self-closing / unterminated voice tag: `<v Speaker 1>text`
    const open = raw.match(/<v\s+([^>]+)>([\s\S]*)$/);
    if (open) {
      speaker = open[1].trim();
      text = open[2];
    }
  }
  // Strip any residual tags and normalise whitespace.
  text = text.replace(/<\/?[^>]+>/g, "").trim();
  const color = (speaker && SPEAKER_COLORS[speaker]) || "#ffffff";
  return { text, color };
}

interface ActiveCue {
  text: string;
  color: string;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function VideoTimeline({
  videoRef,
  pendingSeekRef,
  videoId,
  videoUrl,
  metadata,
  currentTime,
  onTimeUpdate,
  onSeek,
}: VideoTimelineProps) {
  const timelineRef = useRef<HTMLDivElement>(null);
  const [duration, setDuration] = useState(metadata?.duration || 0);
  const [hoveredScene, setHoveredScene] = useState<SceneBoundary | null>(null);
  const [hoverPos, setHoverPos] = useState(0);

  // ─── Closed-caption / subtitle state ──────────────────────────────────
  const [ccEnabled, setCcEnabled] = useState(false);
  const [activeLang, setActiveLang] = useState("en");
  const [showLangMenu, setShowLangMenu] = useState(false);
  const [showDownloadMenu, setShowDownloadMenu] = useState(false);
  // Current caption rendered as a custom overlay (JS-driven, not native).
  const [activeCue, setActiveCue] = useState<ActiveCue | null>(null);

  const subtitleSrc = (lang: string) =>
    videoId
      ? `${API_BASE_URL}/api/video/${videoId}/subtitles?language=${lang}`
      : "";

  // Drive captions ourselves: keep every native track in "hidden" mode (so the
  // browser parses cues but never renders them), then read the active track's
  // cues on `cuechange` and paint them into a custom overlay. This gives full
  // control over per-speaker colors, which `::cue(v[voice=...])` can't provide
  // reliably across browsers.
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    let activeTrack: TextTrack | null = null;

    const handleCueChange = () => {
      if (!ccEnabled || !activeTrack) {
        setActiveCue(null);
        return;
      }
      const cues = activeTrack.activeCues;
      if (!cues || cues.length === 0) {
        setActiveCue(null);
        return;
      }
      // Combine any simultaneously-active cues; color from the first speaker.
      const parsed = Array.from(cues).map((c) =>
        parseCueText((c as VTTCue).text)
      );
      const text = parsed
        .map((p) => p.text)
        .filter(Boolean)
        .join("\n");
      const color = parsed.find((p) => p.text)?.color || "#ffffff";
      setActiveCue(text ? { text, color } : null);
    };

    const applyTracks = () => {
      if (activeTrack) {
        activeTrack.removeEventListener("cuechange", handleCueChange);
        activeTrack = null;
      }
      const tracks = video.textTracks;
      for (let i = 0; i < tracks.length; i++) {
        const track = tracks[i];
        if (track.kind !== "subtitles" && track.kind !== "captions") continue;
        if (ccEnabled && track.language === activeLang) {
          // "hidden" => cues are parsed and `cuechange` fires, but the browser
          // does not draw them (we render our own overlay instead).
          track.mode = "hidden";
          activeTrack = track;
        } else {
          track.mode = "disabled";
        }
      }
      if (activeTrack) {
        activeTrack.addEventListener("cuechange", handleCueChange);
        handleCueChange();
      } else {
        setActiveCue(null);
      }
    };

    applyTracks();
    // Track list may populate slightly after mount / src change.
    video.textTracks.addEventListener?.("addtrack", applyTracks);
    return () => {
      video.textTracks.removeEventListener?.("addtrack", applyTracks);
      if (activeTrack) {
        activeTrack.removeEventListener("cuechange", handleCueChange);
      }
    };
  }, [videoRef, ccEnabled, activeLang, videoUrl, videoId]);

  const toggleCc = () => {
    setCcEnabled((prev) => {
      const next = !prev;
      if (next) setShowLangMenu(true);
      else setShowLangMenu(false);
      return next;
    });
    setShowDownloadMenu(false);
  };

  const selectLanguage = (code: string) => {
    setActiveLang(code);
    setCcEnabled(true);
    setShowLangMenu(false);
  };

  const downloadSrt = (lang: string) => {
    if (!videoId) return;
    const url = `${API_BASE_URL}/api/video/${videoId}/subtitles/download?language=${lang}&format=srt`;
    window.open(url, "_blank");
    setShowDownloadMenu(false);
  };

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => {
      onTimeUpdate(video.currentTime);
    };

    const handleLoadedMetadata = () => {
      setDuration(video.duration);
      // Honor a seek requested before the media was ready (e.g. deep links
      // like ?video=…&t=…, or search-result clicks on a freshly loaded video)
      const target = pendingSeekRef?.current;
      if (target != null && pendingSeekRef) {
        pendingSeekRef.current = null;
        video.currentTime = target;
      }
    };

    video.addEventListener("timeupdate", handleTimeUpdate);
    video.addEventListener("loadedmetadata", handleLoadedMetadata);

    // The element may mount with metadata already available (or this effect
    // may re-run after the src arrived) — handle that case directly.
    if (video.readyState >= 1) {
      handleLoadedMetadata();
    }

    return () => {
      video.removeEventListener("timeupdate", handleTimeUpdate);
      video.removeEventListener("loadedmetadata", handleLoadedMetadata);
    };
    // videoUrl is a dep so listeners attach once the <video> element mounts
    // (it renders conditionally on videoUrl)
  }, [videoRef, pendingSeekRef, onTimeUpdate, videoUrl]);

  const handleTimelineClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!timelineRef.current || !duration) return;
    const rect = timelineRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = x / rect.width;
    const seekTime = percentage * duration;
    onSeek(seekTime);
  };

  const handleTimelineHover = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!timelineRef.current || !duration) return;
    const rect = timelineRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = x / rect.width;
    const hoverTime = percentage * duration;
    setHoverPos(x);

    // Find scene near hover point
    const scene = metadata?.scenes?.find(
      (s) => Math.abs(s.timestamp - hoverTime) < duration * 0.02
    );
    setHoveredScene(scene || null);
  };

  const scenes = metadata?.scenes || [];
  const faces = metadata?.faces || [];
  const objects = metadata?.objects || [];
  const progressPercent = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Video Player */}
      <div className="relative bg-black aspect-video">
        {videoUrl ? (
          <video
            ref={videoRef}
            src={videoUrl}
            className="w-full h-full object-contain"
            crossOrigin="anonymous"
            controls
            playsInline
          >
            {videoId &&
              SUBTITLE_LANGUAGES.map((lang) => (
                <track
                  key={lang.code}
                  kind="subtitles"
                  src={subtitleSrc(lang.code)}
                  srcLang={lang.code}
                  label={lang.label}
                />
              ))}
          </video>
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <p className="text-gray-400 text-sm">No video loaded</p>
          </div>
        )}

        {/* Custom JS-driven caption overlay (per-speaker colored). Sits above
            the native video controls. */}
        {ccEnabled && activeCue && activeCue.text && (
          <div className="pointer-events-none absolute inset-x-0 bottom-16 flex justify-center px-4">
            <span
              dir={activeLang === "ar" ? "rtl" : "ltr"}
              className="max-w-[92%] whitespace-pre-line rounded px-2 py-1 text-center text-base font-medium leading-snug"
              style={{
                color: activeCue.color,
                backgroundColor: "rgba(0, 0, 0, 0.72)",
                textShadow: "0 1px 2px rgba(0,0,0,0.9)",
              }}
            >
              {activeCue.text}
            </span>
          </div>
        )}
      </div>

      {/* Caption controls */}
      {videoUrl && videoId && (
        <div className="flex items-center gap-2 px-4 pt-3 border-b border-gray-100 pb-3">
          {/* CC toggle */}
          <div className="relative">
            <button
              type="button"
              onClick={toggleCc}
              aria-pressed={ccEnabled}
              title="Toggle captions"
              className={`flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-xs font-semibold transition-colors ${
                ccEnabled
                  ? "border-primary-500 bg-primary-500 text-white"
                  : "border-gray-200 bg-white text-gray-600 hover:bg-gray-50"
              }`}
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <rect x="2" y="5" width="20" height="14" rx="2" />
                <path d="M9.5 10a2 2 0 0 0-2 2 2 2 0 0 0 2 2" />
                <path d="M16.5 10a2 2 0 0 0-2 2 2 2 0 0 0 2 2" />
              </svg>
              CC
            </button>

            {ccEnabled && showLangMenu && (
              <div className="absolute z-40 mt-1 w-40 rounded-md border border-gray-200 bg-white py-1 shadow-lg">
                {SUBTITLE_LANGUAGES.map((lang) => (
                  <button
                    key={lang.code}
                    type="button"
                    dir={lang.rtl ? "rtl" : "ltr"}
                    onClick={() => selectLanguage(lang.code)}
                    className={`flex w-full items-center justify-between px-3 py-1.5 text-xs hover:bg-primary-50 ${
                      activeLang === lang.code
                        ? "font-semibold text-primary-600"
                        : "text-gray-700"
                    }`}
                  >
                    <span>{lang.label}</span>
                    {activeLang === lang.code && (
                      <span className="text-primary-500">✓</span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Active language pill + change trigger */}
          {ccEnabled && (
            <button
              type="button"
              onClick={() => {
                setShowLangMenu((v) => !v);
                setShowDownloadMenu(false);
              }}
              className="rounded-md border border-gray-200 bg-white px-2.5 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50"
            >
              {SUBTITLE_LANGUAGES.find((l) => l.code === activeLang)?.label ??
                "English"}
            </button>
          )}

          {/* SRT download */}
          <div className="relative ml-auto">
            <button
              type="button"
              onClick={() => {
                setShowDownloadMenu((v) => !v);
                setShowLangMenu(false);
              }}
              title="Download subtitles (.srt)"
              className="flex items-center gap-1.5 rounded-md border border-gray-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-gray-600 transition-colors hover:bg-gray-50"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
              SRT
            </button>

            {showDownloadMenu && (
              <div className="absolute right-0 z-40 mt-1 w-40 rounded-md border border-gray-200 bg-white py-1 shadow-lg">
                {SUBTITLE_LANGUAGES.map((lang) => (
                  <button
                    key={lang.code}
                    type="button"
                    dir={lang.rtl ? "rtl" : "ltr"}
                    onClick={() => downloadSrt(lang.code)}
                    className="block w-full px-3 py-1.5 text-left text-xs text-gray-700 hover:bg-primary-50"
                  >
                    {lang.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Timeline Section */}
      <div className="p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-500 font-mono">
            {formatTime(currentTime)}
          </span>
          <span className="text-xs text-gray-500 font-mono">
            {formatTime(duration)}
          </span>
        </div>

        {/* Main timeline bar */}
        <div
          ref={timelineRef}
          className="relative h-8 bg-gray-100 rounded cursor-pointer group"
          onClick={handleTimelineClick}
          onMouseMove={handleTimelineHover}
          onMouseLeave={() => setHoveredScene(null)}
        >
          {/* Progress */}
          <div
            className="absolute top-0 left-0 h-full bg-primary-100 rounded-l"
            style={{ width: `${progressPercent}%` }}
          />

          {/* Scene markers */}
          {scenes.map((scene, i) => {
            const pos = duration > 0 ? (scene.timestamp / duration) * 100 : 0;
            return (
              <div
                key={i}
                className="absolute top-0 bottom-0 w-0.5 bg-blue-400 hover:bg-blue-600 z-10"
                style={{ left: `${pos}%` }}
                onClick={(e) => {
                  e.stopPropagation();
                  onSeek(scene.timestamp);
                }}
                title={scene.description}
              />
            );
          })}

          {/* Object/landmark markers */}
          {objects.map((obj, i) => {
            const pos = duration > 0 ? (obj.timestamp / duration) * 100 : 0;
            return (
              <div
                key={`obj-${i}`}
                className="absolute bottom-0 w-3 h-3 -translate-x-1/2 rounded-full bg-yellow-400 border border-yellow-600 z-10 cursor-pointer hover:scale-125 transition-transform"
                style={{ left: `${pos}%` }}
                onClick={(e) => {
                  e.stopPropagation();
                  onSeek(obj.timestamp);
                }}
                title={obj.name}
              />
            );
          })}

          {/* Playback position indicator */}
          <div
            className="absolute top-0 bottom-0 w-0.5 bg-primary-500 z-20"
            style={{ left: `${progressPercent}%` }}
          >
            <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-primary-500 border-2 border-white shadow" />
          </div>

          {/* Hover tooltip */}
          {hoveredScene && (
            <div
              className="absolute bottom-full mb-2 -translate-x-1/2 bg-gray-900 text-white text-xs rounded px-2 py-1 whitespace-nowrap z-30 pointer-events-none"
              style={{ left: `${hoverPos}px` }}
            >
              {hoveredScene.description}
            </div>
          )}
        </div>

        {/* Face appearance bars */}
        {faces.length > 0 && (
          <div className="mt-3 space-y-1.5">
            <p className="text-xs font-medium text-gray-600 mb-1">
              Detected Persons
            </p>
            {faces.map((face, i) => (
              <div key={i} className="flex items-center gap-2">
                <span
                  className="text-xs font-medium min-w-[80px] truncate"
                  style={{ color: face.color }}
                >
                  {face.name || "Unknown"}
                </span>
                <div className="flex-1 relative h-3 bg-gray-50 rounded">
                  {(face.appearances || []).map((app, j) => {
                    const left =
                      duration > 0 ? (app.start / duration) * 100 : 0;
                    const width =
                      duration > 0
                        ? ((app.end - app.start) / duration) * 100
                        : 0;
                    return (
                      <div
                        key={j}
                        className="absolute top-0 bottom-0 rounded opacity-70 hover:opacity-100 cursor-pointer transition-opacity"
                        style={{
                          left: `${left}%`,
                          width: `${width}%`,
                          backgroundColor: face.color,
                        }}
                        onClick={() => onSeek(app.start)}
                        title={`${face.name || "Unknown"}: ${formatTime(app.start)} - ${formatTime(app.end)}`}
                      />
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Time labels */}
        {duration > 0 && (
          <div className="flex justify-between mt-2">
            {Array.from({ length: 5 }, (_, i) => {
              const t = (duration / 4) * i;
              return (
                <span key={i} className="text-[10px] text-gray-400 font-mono">
                  {formatTime(t)}
                </span>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

"use client";

import { RefObject, useEffect, useRef, useState } from "react";
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
  videoUrl: string | null;
  metadata: VideoMetadata | null;
  currentTime: number;
  onTimeUpdate: (time: number) => void;
  onSeek: (time: number) => void;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function VideoTimeline({
  videoRef,
  pendingSeekRef,
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
            controls
            playsInline
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <p className="text-gray-400 text-sm">No video loaded</p>
          </div>
        )}
      </div>

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

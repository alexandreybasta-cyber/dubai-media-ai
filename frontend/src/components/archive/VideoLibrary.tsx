"use client";

import { useEffect, useState } from "react";
import { api, API_BASE_URL, LibraryVideo } from "@/lib/api";

interface VideoLibraryProps {
  onSelect: (videoId: string) => void;
}

function formatDuration(seconds: number): string {
  if (!seconds || seconds <= 0) return "";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function formatDate(iso: string): string {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  } catch {
    return "";
  }
}

export default function VideoLibrary({ onSelect }: VideoLibraryProps) {
  const [videos, setVideos] = useState<LibraryVideo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    api.video
      .list()
      .then((res) => {
        if (!cancelled) {
          setVideos((res.videos || []).filter((v) => v.status.startsWith("completed")));
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="animate-pulse">
            <div className="aspect-video bg-gray-200 rounded-lg" />
            <div className="h-3 bg-gray-200 rounded mt-2 w-3/4" />
            <div className="h-2.5 bg-gray-100 rounded mt-1.5 w-1/2" />
          </div>
        ))}
      </div>
    );
  }

  if (videos.length === 0) return null;

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <svg className="w-5 h-5 text-primary-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 0 1 4.5 9.75h15A2.25 2.25 0 0 1 21.75 12v.75m-8.69-6.44-2.12-2.12a1.5 1.5 0 0 0-1.061-.44H4.5A2.25 2.25 0 0 0 2.25 6v12a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9a2.25 2.25 0 0 0-2.25-2.25h-5.379a1.5 1.5 0 0 1-1.06-.44Z" />
        </svg>
        <h2 className="text-lg font-semibold text-gray-900">Archive Library</h2>
        <span className="text-xs text-gray-500 ml-1">
          {videos.length} processed video{videos.length !== 1 ? "s" : ""}
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
        {videos.map((video) => (
          <button
            key={video.video_id}
            onClick={() => onSelect(video.video_id)}
            className="group text-left rounded-xl border border-gray-200 bg-white overflow-hidden hover:border-primary-300 hover:shadow-md transition-all"
          >
            <div className="relative aspect-video bg-gray-900">
              {video.thumbnail ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={`${API_BASE_URL}${video.thumbnail}`}
                  alt=""
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <svg className="w-8 h-8 text-gray-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" />
                  </svg>
                </div>
              )}
              {video.duration > 0 && (
                <span className="absolute bottom-1.5 right-1.5 px-1.5 py-0.5 rounded bg-black/70 text-white text-[10px] font-mono">
                  {formatDuration(video.duration)}
                </span>
              )}
            </div>
            <div className="p-3">
              <p className="text-sm font-medium text-gray-900 line-clamp-2 leading-snug">
                {video.title || video.filename || "Untitled"}
              </p>
              <div className="flex items-center gap-2 mt-1.5 text-[11px] text-gray-500">
                {formatDate(video.created_at) && <span>{formatDate(video.created_at)}</span>}
                {video.scene_count > 0 && <span>· {video.scene_count} scenes</span>}
              </div>
              {video.persons.length > 0 && (
                <p className="mt-1 text-[11px] text-primary-600 line-clamp-1">
                  {video.persons.join(", ")}
                </p>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

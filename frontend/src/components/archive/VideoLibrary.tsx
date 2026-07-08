"use client";

import { useEffect, useState } from "react";
import { api, API_BASE_URL, LibraryVideo } from "@/lib/api";

interface VideoLibraryProps {
  onSelect: (videoId: string) => void;
  onRefresh?: () => void;
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

export default function VideoLibrary({ onSelect, onRefresh }: VideoLibraryProps) {
  const [videos, setVideos] = useState<LibraryVideo[]>([]);
  const [loading, setLoading] = useState(true);
  const [isSelectMode, setIsSelectMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [isDeleting, setIsDeleting] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);

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

  const exitSelectMode = () => {
    setIsSelectMode(false);
    setSelectedIds(new Set());
  };

  const toggleSelectMode = () => {
    if (isSelectMode) {
      exitSelectMode();
    } else {
      setIsSelectMode(true);
    }
  };

  const toggleSelected = (videoId: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(videoId)) {
        next.delete(videoId);
      } else {
        next.add(videoId);
      }
      return next;
    });
  };

  const allSelected = videos.length > 0 && selectedIds.size === videos.length;

  const toggleSelectAll = () => {
    if (allSelected) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(videos.map((v) => v.video_id)));
    }
  };

  const handleCardClick = (videoId: string) => {
    if (isSelectMode) {
      toggleSelected(videoId);
    } else {
      onSelect(videoId);
    }
  };

  const handleConfirmDelete = async () => {
    if (selectedIds.size === 0) return;
    setIsDeleting(true);
    try {
      const ids = Array.from(selectedIds);
      const res = await api.video.delete(ids);
      const deleted = new Set(res.deleted || []);
      setVideos((prev) => prev.filter((v) => !deleted.has(v.video_id)));
      setShowConfirmModal(false);
      exitSelectMode();
      onRefresh?.();
    } catch (err) {
      console.error("Failed to delete videos:", err);
    } finally {
      setIsDeleting(false);
    }
  };

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

        <div className="ml-auto flex items-center gap-2">
          {isSelectMode && (
            <>
              <button
                onClick={toggleSelectAll}
                className="text-xs font-medium text-gray-600 hover:text-primary-600 transition-colors"
              >
                {allSelected ? "Deselect All" : "Select All"}
              </button>

              {selectedIds.size > 0 && (
                <span className="inline-flex items-center justify-center min-w-[1.25rem] px-1.5 h-5 rounded-full bg-primary-100 text-primary-700 text-[11px] font-semibold">
                  {selectedIds.size}
                </span>
              )}

              <button
                onClick={() => setShowConfirmModal(true)}
                disabled={selectedIds.size === 0}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-500 hover:bg-red-600 text-white text-xs font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={1.8} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
                </svg>
                Delete
              </button>
            </>
          )}

          <button
            onClick={toggleSelectMode}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors ${
              isSelectMode
                ? "border-primary-500 text-primary-600 bg-primary-50"
                : "border-gray-300 text-gray-600 hover:border-primary-400 hover:text-primary-600"
            }`}
          >
            {isSelectMode ? "Cancel" : "Select"}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
        {videos.map((video) => {
          const isChecked = selectedIds.has(video.video_id);
          return (
            <button
              key={video.video_id}
              onClick={() => handleCardClick(video.video_id)}
              className={`group relative text-left rounded-xl border bg-white overflow-hidden transition-all ${
                isSelectMode && isChecked
                  ? "border-primary-500 ring-2 ring-primary-200 shadow-md"
                  : "border-gray-200 hover:border-primary-300 hover:shadow-md"
              }`}
            >
              {isSelectMode && (
                <span
                  className={`absolute top-2 left-2 z-10 flex items-center justify-center w-6 h-6 rounded-full border-2 transition-all duration-200 ${
                    isChecked
                      ? "bg-primary-500 border-primary-500"
                      : "bg-white/80 border-white shadow-sm"
                  }`}
                >
                  {isChecked && (
                    <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" strokeWidth={3} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                    </svg>
                  )}
                </span>
              )}
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
          );
        })}
      </div>

      {showConfirmModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="w-full max-w-sm rounded-2xl bg-white shadow-xl p-6">
            <div className="flex items-center gap-3 mb-3">
              <span className="flex items-center justify-center w-10 h-10 rounded-full bg-red-100">
                <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.8} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                </svg>
              </span>
              <h3 className="text-base font-semibold text-gray-900">Delete videos</h3>
            </div>
            <p className="text-sm text-gray-600 mb-6">
              Delete {selectedIds.size} video{selectedIds.size !== 1 ? "s" : ""}? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowConfirmModal(false)}
                disabled={isDeleting}
                className="px-4 py-2 rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmDelete}
                disabled={isDeleting}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-red-500 hover:bg-red-600 text-white text-sm font-medium transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {isDeleting && (
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v4a4 4 0 0 0-4 4H4Z" />
                  </svg>
                )}
                {isDeleting ? "Deleting..." : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

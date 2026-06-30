"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { api, connectWebSocket, WSMessage } from "./api";

// ─── Types ──────────────────────────────────────────────────────────────

export type UploadState = "idle" | "uploading" | "uploaded" | "error";

export type StageStatus = "pending" | "running" | "completed" | "failed";

export interface PipelineStage {
  id: string;
  name: string;
  status: StageStatus;
  startTime?: number;
  endTime?: number;
  elapsed?: number;
  message?: string;
}

export interface TranscriptSegment {
  speaker: string;
  start: number;
  end: number;
  text: string;
  language?: string;
}

export interface SceneBoundary {
  timestamp: number;
  description: string;
  thumbnail?: string;
}

export interface DetectedFace {
  name: string;
  name_ar?: string;
  appearances: { start: number; end: number }[];
  color: string;
}

export interface DetectedObject {
  name: string;
  timestamp: number;
  confidence: number;
}

export interface APICallLog {
  stage: string;
  model: string;
  endpoint: string;
  inputTokens: number;
  outputTokens: number;
  latencyMs: number;
  estimatedCost: number;
}

export interface VideoMetadata {
  video_id: string;
  duration: number;
  title?: string;
  topic?: string;
  sentiment?: string;
  era?: string;
  scenes: SceneBoundary[];
  faces: DetectedFace[];
  objects: DetectedObject[];
  landmarks: { name: string; timestamp: number }[];
  sensitive_content: string[];
  ebucore_xml?: string;
  iptc_json?: Record<string, unknown>;
  raw?: Record<string, unknown>;
  api_calls?: APICallLog[];
}

export interface SearchResult {
  video_id: string;
  title: string;
  timestamp: number;
  description: string;
  score: number;
  thumbnail?: string;
}

export type PageView = "upload" | "processing" | "results";

export interface VideoProcessingState {
  view: PageView;
  uploadState: UploadState;
  uploadProgress: number;
  videoId: string | null;
  videoUrl: string | null;
  fileName: string | null;
  fileSize: number | null;
  stages: PipelineStage[];
  metadata: VideoMetadata | null;
  transcript: TranscriptSegment[];
  searchResults: SearchResult[];
  searchQuery: string;
  isSearching: boolean;
  currentTime: number;
  error: string | null;
}

const INITIAL_STAGES: PipelineStage[] = [
  { id: "ingestion", name: "Ingestion", status: "pending" },
  { id: "visual_analysis", name: "Visual Analysis", status: "pending" },
  { id: "audio_analysis", name: "Audio/Speech", status: "pending" },
  { id: "face_recognition", name: "Face Recognition", status: "pending" },
  { id: "metadata_structuring", name: "Metadata Structuring", status: "pending" },
  { id: "search_index", name: "Search Indexing", status: "pending" },
];

const FACE_COLORS = [
  "#3B82F6", "#10B981", "#8B5CF6", "#F59E0B",
  "#EF4444", "#06B6D4", "#EC4899", "#14B8A6",
];

// ─── Hook ───────────────────────────────────────────────────────────────

export function useVideoProcessing() {
  const [state, setState] = useState<VideoProcessingState>({
    view: "upload",
    uploadState: "idle",
    uploadProgress: 0,
    videoId: null,
    videoUrl: null,
    fileName: null,
    fileSize: null,
    stages: INITIAL_STAGES,
    metadata: null,
    transcript: [],
    searchResults: [],
    searchQuery: "",
    isSearching: false,
    currentTime: 0,
    error: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  // Clean up WebSocket and polling on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  const updateState = useCallback(
    (updates: Partial<VideoProcessingState>) => {
      setState((prev) => ({ ...prev, ...updates }));
    },
    []
  );

  // ─── Upload ─────────────────────────────────────────────────────────

  const uploadVideo = useCallback(
    async (file: File) => {
      updateState({
        uploadState: "uploading",
        uploadProgress: 0,
        fileName: file.name,
        fileSize: file.size,
        error: null,
      });

      // Create object URL for video player
      const videoUrl = URL.createObjectURL(file);

      try {
        // Simulate progress (real progress would need XMLHttpRequest)
        const progressInterval = setInterval(() => {
          setState((prev) => ({
            ...prev,
            uploadProgress: Math.min(prev.uploadProgress + 10, 90),
          }));
        }, 300);

        const result = (await api.video.upload(file)) as {
          video_id: string;
          status: string;
        };

        clearInterval(progressInterval);

        updateState({
          uploadState: "uploaded",
          uploadProgress: 100,
          videoId: result.video_id,
          videoUrl,
          view: "processing",
          stages: INITIAL_STAGES,
        });

        // Connect WebSocket for pipeline updates
        connectToPipeline(result.video_id);
      } catch (err) {
        updateState({
          uploadState: "error",
          uploadProgress: 0,
          error: err instanceof Error ? err.message : "Upload failed",
        });
      }
    },
    [updateState]
  );

  // ─── WebSocket Pipeline Connection ─────────────────────────────────

  const connectToPipeline = useCallback(
    (videoId: string) => {
      if (wsRef.current) {
        wsRef.current.close();
      }

      const ws = connectWebSocket(
        `/api/ws/pipeline/${videoId}`,
        (data: WSMessage) => {
          setState((prev) => {
            const newStages = prev.stages.map((stage) => {
              if (stage.id === data.stage) {
                const now = Date.now();
                const updates: Partial<PipelineStage> = {
                  status: data.status as StageStatus,
                  message: data.message,
                };
                if (data.status === "running" && !stage.startTime) {
                  updates.startTime = now;
                }
                if (data.status === "completed" || data.status === "failed") {
                  updates.endTime = now;
                  if (stage.startTime) {
                    updates.elapsed = now - stage.startTime;
                  }
                }
                return { ...stage, ...updates };
              }
              return stage;
            });

            // Check if all stages are complete
            const allComplete = newStages.every(
              (s) => s.status === "completed" || s.status === "failed"
            );

            return {
              ...prev,
              stages: newStages,
              view: allComplete ? "results" : "processing",
            };
          });

          // If pipeline is complete, fetch metadata and transcript
          if (data.status === "completed" && data.stage === "search_index") {
            fetchResults(videoId);
          }
        },
        () => {
          // On error, start polling fallback
          startPollingFallback(videoId);
        },
        () => {
          // On close, start polling fallback
          startPollingFallback(videoId);
        }
      );

      wsRef.current = ws;
    },
    []
  );

  // ─── Fetch Results ──────────────────────────────────────────────────

  const fetchResults = useCallback(async (videoId: string) => {
    try {
      const [metadataRes, transcriptRes] = await Promise.all([
        api.video.getMetadata(videoId) as Promise<Record<string, unknown>>,
        api.video.getTranscript(videoId) as Promise<Record<string, unknown>>,
      ]);

      // Map the backend response structure to the frontend VideoMetadata interface
      // Backend returns: { video_id, ingestion, visual_analysis, metadata, faces }
      // Frontend expects: { video_id, duration, scenes, faces, objects, landmarks, ... }
      const raw = metadataRes as Record<string, unknown>;
      const ingestion = (raw.ingestion || {}) as Record<string, unknown>;
      const visualAnalysis = (raw.visual_analysis || {}) as Record<string, unknown>;
      const metaBlock = (raw.metadata || {}) as Record<string, unknown>;
      const topLevelFaces = (raw.faces || []) as DetectedFace[];
      const visualFaces = (visualAnalysis.faces || []) as DetectedFace[];

      const metadata: VideoMetadata = {
        video_id: videoId,
        duration: (ingestion.duration as number) || 0,
        title: (metaBlock.title as string) || undefined,
        topic: (metaBlock.topic as string) || undefined,
        sentiment: ((metaBlock.sentiment_tags as string[]) || []).join(", ") || undefined,
        era: ((visualAnalysis.era_estimate as Record<string, unknown>)?.decade as string) || undefined,
        scenes: (visualAnalysis.scenes || []) as SceneBoundary[],
        faces: topLevelFaces.length > 0 ? topLevelFaces : visualFaces,
        objects: (visualAnalysis.objects || []) as DetectedObject[],
        landmarks: (visualAnalysis.landmarks || []) as { name: string; timestamp: number }[],
        sensitive_content: (visualAnalysis.sensitive_content || []) as string[],
        ebucore_xml: (metaBlock.ebucore_xml as string) || undefined,
        iptc_json: (metaBlock.iptc_video_metadata as Record<string, unknown>) || undefined,
        raw: raw,
      };

      // Assign colors to faces
      if (metadata.faces) {
        metadata.faces = metadata.faces.map((face, i) => ({
          ...face,
          appearances: face.appearances || [],
          color: face.color || FACE_COLORS[i % FACE_COLORS.length],
        }));
      }

      const transcript = (
        (transcriptRes as { segments?: TranscriptSegment[] }).segments || []
      ) as TranscriptSegment[];

      setState((prev) => ({
        ...prev,
        metadata,
        transcript,
        view: "results",
      }));
    } catch (err) {
      console.error("Failed to fetch results:", err);
    }
  }, []);

  // ─── Polling Fallback ─────────────────────────────────────────────

  const startPollingFallback = useCallback(
    (videoId: string) => {
      // Don't start another interval if one is already running
      if (pollIntervalRef.current) return;

      pollIntervalRef.current = setInterval(async () => {
        try {
          const statusRes = (await api.video.getStatus(videoId)) as {
            stages: Record<string, string>;
          };
          if (statusRes.stages) {
            setState((prev) => {
              const newStages = prev.stages.map((stage) => ({
                ...stage,
                status: (statusRes.stages[stage.id] || stage.status) as StageStatus,
              }));
              const allComplete = newStages.every(
                (s) => s.status === "completed" || s.status === "failed"
              );
              return {
                ...prev,
                stages: newStages,
                view: allComplete ? "results" : prev.view,
              };
            });

            const allDone = Object.values(statusRes.stages).every(
              (s) => s === "completed" || s === "failed"
            );
            if (allDone) {
              // Stop polling once done
              if (pollIntervalRef.current) {
                clearInterval(pollIntervalRef.current);
                pollIntervalRef.current = null;
              }
              fetchResults(videoId);
            }
          }
        } catch {
          // Silently fail, will retry on next interval
        }
      }, 3000);
    },
    [fetchResults]
  );

  // ─── Search ─────────────────────────────────────────────────────────

  const search = useCallback(async (query: string) => {
    if (!query.trim()) return;
    setState((prev) => ({ ...prev, searchQuery: query, isSearching: true }));

    try {
      const results = (await api.video.search(query, 5)) as {
        results: SearchResult[];
      };
      setState((prev) => ({
        ...prev,
        searchResults: results.results || [],
        isSearching: false,
      }));
    } catch {
      setState((prev) => ({ ...prev, isSearching: false, searchResults: [] }));
    }
  }, []);

  // ─── Video Time Sync ────────────────────────────────────────────────

  const setCurrentTime = useCallback((time: number) => {
    updateState({ currentTime: time });
  }, [updateState]);

  const seekTo = useCallback((time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
    }
    updateState({ currentTime: time });
  }, [updateState]);

  // ─── Reset ──────────────────────────────────────────────────────────

  const reset = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    if (state.videoUrl) {
      URL.revokeObjectURL(state.videoUrl);
    }
    setState({
      view: "upload",
      uploadState: "idle",
      uploadProgress: 0,
      videoId: null,
      videoUrl: null,
      fileName: null,
      fileSize: null,
      stages: INITIAL_STAGES,
      metadata: null,
      transcript: [],
      searchResults: [],
      searchQuery: "",
      isSearching: false,
      currentTime: 0,
      error: null,
    });
  }, [state.videoUrl]);

  return {
    state,
    videoRef,
    uploadVideo,
    search,
    setCurrentTime,
    seekTo,
    reset,
  };
}

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "";
const WS_BASE_URL = API_BASE_URL
  ? API_BASE_URL.replace(/^http/, "ws")
  : `ws://${typeof window !== "undefined" ? window.location.host : "localhost:8800"}`;

// ─── Typed Fetch Wrapper ────────────────────────────────────────────────

interface FetchOptions extends RequestInit {
  params?: Record<string, string>;
}

export async function apiFetch<T>(
  endpoint: string,
  options: FetchOptions = {}
): Promise<T> {
  const { params, ...fetchOptions } = options;

  let url = `${API_BASE_URL}${endpoint}`;
  if (params) {
    const searchParams = new URLSearchParams(params);
    url += `?${searchParams.toString()}`;
  }

  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...fetchOptions.headers,
    },
    ...fetchOptions,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      error.detail || `API Error: ${response.status} ${response.statusText}`
    );
  }

  return response.json();
}

// ─── File Upload Helper ─────────────────────────────────────────────────

export async function uploadFile<T>(
  endpoint: string,
  file: File,
  fieldName: string = "file",
  onProgress?: (progress: number) => void
): Promise<T> {
  const formData = new FormData();
  formData.append(fieldName, file);

  // Use XMLHttpRequest for real upload progress tracking
  return new Promise<T>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE_URL}${endpoint}`);

    // Track real upload progress
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        const percent = Math.round((event.loaded / event.total) * 100);
        onProgress(percent);
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch {
          reject(new Error("Failed to parse upload response"));
        }
      } else {
        try {
          const error = JSON.parse(xhr.responseText);
          reject(new Error(error.detail || `Upload Error: ${xhr.status} ${xhr.statusText}`));
        } catch {
          reject(new Error(`Upload Error: ${xhr.status} ${xhr.statusText}`));
        }
      }
    };

    xhr.onerror = () => {
      reject(new Error("Network error during upload"));
    };

    xhr.ontimeout = () => {
      reject(new Error("Upload timed out"));
    };

    // No timeout for large file uploads
    xhr.timeout = 0;

    xhr.send(formData);
  });
}

// ─── WebSocket Connection Helper ────────────────────────────────────────

export interface WSMessage {
  video_id: string;
  stage: string;
  message: string;
  progress: number;
  status: string;
}

export function connectWebSocket(
  endpoint: string,
  onMessage: (data: WSMessage) => void,
  onError?: (error: Event) => void,
  onClose?: (event: CloseEvent) => void
): WebSocket {
  const ws = new WebSocket(`${WS_BASE_URL}${endpoint}`);

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };

  ws.onerror = (error) => {
    console.error("WebSocket error:", error);
    onError?.(error);
  };

  ws.onclose = (event) => {
    onClose?.(event);
  };

  return ws;
}

// ─── Video Library Types ────────────────────────────────────────────────

export interface LibraryVideo {
  video_id: string;
  filename: string;
  title: string;
  status: string;
  progress: number;
  created_at: string;
  duration: number;
  thumbnail: string;
  scene_count: number;
  persons: string[];
  summary: string;
}

// ─── Convenience API Methods ────────────────────────────────────────────

export const api = {
  // Video endpoints
  video: {
    upload: (file: File, onProgress?: (progress: number) => void) =>
      uploadFile("/api/video/upload", file, "file", onProgress),
    getStatus: (videoId: string) =>
      apiFetch(`/api/video/${videoId}/status`),
    getMetadata: (videoId: string) =>
      apiFetch(`/api/video/${videoId}/metadata`),
    getTranscript: (videoId: string) =>
      apiFetch(`/api/video/${videoId}/transcript`),
    translateTranscript: (
      videoId: string,
      language: string,
      segments: Array<{ text: string; start_time: number; end_time: number }>
    ) =>
      apiFetch<{
        translations: Array<{ start_time: number; end_time: number; text: string }>;
        language: string;
      }>(`/api/video/${videoId}/translate-transcript`, {
        method: "POST",
        body: JSON.stringify({ language, segments }),
      }),
    search: (query: string, topK: number = 5, typeFilter?: string) =>
      apiFetch("/api/search", {
        method: "POST",
        body: JSON.stringify({
          query,
          top_k: topK,
          type_filter: typeFilter || null,
        }),
      }),
    list: () =>
      apiFetch<{ videos: LibraryVideo[]; total: number }>("/api/videos"),
    delete: (videoIds: string[]) =>
      apiFetch<{ deleted: string[]; failed: { video_id: string; error: string }[] }>(
        "/api/videos",
        { method: "DELETE", body: JSON.stringify({ video_ids: videoIds }) }
      ),
    nameFace: (
      videoId: string,
      data: {
        face_index: number;
        name_en: string;
        name_ar?: string;
        role?: string;
        add_to_reference?: boolean;
      }
    ) =>
      apiFetch<{ status: string; face: Record<string, unknown>; added_to_reference: boolean }>(
        `/api/video/${videoId}/faces/name`,
        { method: "POST", body: JSON.stringify(data) }
      ),
    connectPipeline: (
      videoId: string,
      onMessage: (data: WSMessage) => void
    ) => connectWebSocket(`/api/ws/pipeline/${videoId}`, onMessage),
    requestDubbing: (videoId: string, targetLanguage: string) =>
      apiFetch<{ status: string; video_id: string; target_language: string; message: string }>(
        `/api/video/${videoId}/dub`,
        { method: "POST", body: JSON.stringify({ target_language: targetLanguage }) }
      ),
    getDubbingStatus: (videoId: string, language?: string) =>
      apiFetch<{ status: string; target_language: string; stage: string; video_id: string }>(
        `/api/video/${videoId}/dub/status`,
        language ? { params: { language } } : undefined
      ),
    getDubbingLanguages: (videoId: string) =>
      apiFetch<{ video_id: string; dubbed_languages: string[]; supported_languages: string[] }>(
        `/api/video/${videoId}/dub/languages`
      ),
  },

  // Health check
  health: () => apiFetch("/api/health"),
};

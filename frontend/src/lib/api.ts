const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_BASE_URL = API_BASE_URL.replace(/^http/, "ws");

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
  fieldName: string = "file"
): Promise<T> {
  const formData = new FormData();
  formData.append(fieldName, file);

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      error.detail || `Upload Error: ${response.status} ${response.statusText}`
    );
  }

  return response.json();
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

// ─── Convenience API Methods ────────────────────────────────────────────

export const api = {
  // Video endpoints
  video: {
    upload: (file: File) => uploadFile("/api/video/upload", file),
    getStatus: (videoId: string) =>
      apiFetch(`/api/video/${videoId}/status`),
    getMetadata: (videoId: string) =>
      apiFetch(`/api/video/${videoId}/metadata`),
    getTranscript: (videoId: string) =>
      apiFetch(`/api/video/${videoId}/transcript`),
    search: (query: string, topK: number = 5) =>
      apiFetch("/api/search", {
        method: "POST",
        body: JSON.stringify({ query, top_k: topK }),
      }),
    connectPipeline: (
      videoId: string,
      onMessage: (data: WSMessage) => void
    ) => connectWebSocket(`/ws/pipeline/${videoId}`, onMessage),
  },

  // RFP endpoints
  rfp: {
    create: (data: {
      title: string;
      project_description: string;
      tone?: string;
      language?: string;
    }) =>
      apiFetch("/api/rfp/create", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    regenerateSection: (data: {
      rfp_id: string;
      section_name: string;
      instructions?: string;
    }) =>
      apiFetch("/api/rfp/regenerate-section", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    exportDocx: (rfpId: string) =>
      apiFetch(`/api/rfp/${rfpId}/export/docx`),
    exportPdf: (rfpId: string) =>
      apiFetch(`/api/rfp/${rfpId}/export/pdf`),
    evaluate: (data: { proposals: string[]; criteria?: string[] }) =>
      apiFetch("/api/rfp/evaluate", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    getEvaluationStatus: (evalId: string) =>
      apiFetch(`/api/rfp/evaluation/${evalId}/status`),
    getEvaluationResults: (evalId: string) =>
      apiFetch(`/api/rfp/evaluation/${evalId}/results`),
    exportEvaluationXlsx: (evalId: string) =>
      apiFetch(`/api/rfp/evaluation/${evalId}/export/xlsx`),
    exportEvaluationPdf: (evalId: string) =>
      apiFetch(`/api/rfp/evaluation/${evalId}/export/pdf`),
  },

  // Health check
  health: () => apiFetch("/api/health"),
};

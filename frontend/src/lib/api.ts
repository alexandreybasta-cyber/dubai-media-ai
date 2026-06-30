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

// ─── RFP Types ──────────────────────────────────────────────────────────

export interface RFPSection {
  name: string;
  content_en?: string;
  content_ar?: string;
}

// ─── Evaluation Types ───────────────────────────────────────────────────

export interface ScoreItem {
  criterion: string;
  score: number;
  justification: string;
  evidence: string;
}

export interface MandatoryCompliance {
  requirement: string;
  status: string;
  note: string;
}

export interface VendorResult {
  vendor_name: string;
  scores: ScoreItem[];
  weighted_total: number;
  strengths: string[];
  gaps: string[];
  risks: string[];
  mandatory_compliance: MandatoryCompliance[];
}

export interface EvaluationResults {
  vendors: VendorResult[];
  recommendation: string;
  follow_up_questions: Record<string, string[]>;
}

export interface RFPCreatePayload {
  project_title: string;
  project_overview: string;
  scope_of_work?: string;
  technical_requirements?: string[];
  evaluation_criteria?: { name: string; weight: number; description: string }[];
  timeline?: { start_date: string; end_date: string; milestones: { name: string; date: string }[] };
  budget_range?: { min: number; max: number; currency: string } | null;
  compliance_requirements?: string[];
  industry?: string;
  language?: string;
  tone?: string;
}

export interface RFPCreateResponse {
  rfp_id: string;
  title: string;
  status: string;
  sections: RFPSection[];
  language: string;
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
    search: (query: string, topK: number = 5) =>
      apiFetch("/api/search", {
        method: "POST",
        body: JSON.stringify({ query, top_k: topK }),
      }),
    connectPipeline: (
      videoId: string,
      onMessage: (data: WSMessage) => void
    ) => connectWebSocket(`/api/ws/pipeline/${videoId}`, onMessage),
  },

  // RFP endpoints
  rfp: {
    create: (data: RFPCreatePayload) =>
      apiFetch<RFPCreateResponse>("/api/rfp/create", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    regenerateSection: (data: {
      rfp_id: string;
      section_name: string;
      instructions?: string;
    }) =>
      apiFetch<{ rfp_id: string; section_name: string; content: string; status: string }>("/api/rfp/regenerate-section", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    exportDocx: (rfpId: string) => {
      const url = `${API_BASE_URL}/api/rfp/${rfpId}/export/docx`;
      window.open(url, "_blank");
    },
    exportPdf: (rfpId: string) => {
      const url = `${API_BASE_URL}/api/rfp/${rfpId}/export/pdf`;
      window.open(url, "_blank");
    },
    evaluate: (formData: FormData) => {
      return fetch(`${API_BASE_URL}/api/rfp/evaluate`, {
        method: "POST",
        body: formData,
      }).then(async (res) => {
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Evaluate Error: ${res.status}`);
        }
        return res.json();
      });
    },
    getEvaluationStatus: (evalId: string) =>
      apiFetch<{
        eval_id: string;
        status: string;
        progress: number;
        proposals_evaluated: number;
        error: string | null;
        message: string;
      }>(`/api/rfp/evaluation/${evalId}/status`),
    getEvaluationResults: (evalId: string) =>
      apiFetch<{ eval_id: string; status: string; results: EvaluationResults }>(
        `/api/rfp/evaluation/${evalId}/results`
      ),
    exportEvaluationXlsx: (evalId: string) => {
      window.open(`${API_BASE_URL}/api/rfp/evaluation/${evalId}/export/xlsx`, "_blank");
    },
    exportEvaluationPdf: (evalId: string) => {
      window.open(`${API_BASE_URL}/api/rfp/evaluation/${evalId}/export/pdf`, "_blank");
    },
  },

  // Health check
  health: () => apiFetch("/api/health"),
};

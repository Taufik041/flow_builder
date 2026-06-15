import { getTokenCookie, clearTokenCookie } from "@/lib/cookies";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface Session {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  aisensy_flow_id?: string | null;
  endpoint_uri?: string | null;
  flow_status?: string | null;
  flow_category?: string | null;
}

export interface Message {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface SessionDetail {
  session: Session;
  messages: Message[];
}

export interface GeneratedFile {
  id: string;
  message_id: string;
  file_type: "flow_json" | "handler_py";
  version: string;
  created_at: string;
  download_url: string;
}

export interface UploadResult {
  id: string;
  file_name: string;
  file_type: string;
  extracted_text: string | null;
}

export interface ValidationError {
  error: string;
  message: string;
  pointers: Array<{ path: string; line_start?: number; [key: string]: unknown }>;
}

export interface FlowState {
  aisensy_flow_id: string | null;
  endpoint_uri: string | null;
  flow_status: string | null;
  flow_category: string | null;
}

export interface Attempt {
  num: number;
  status: string;
  code: string;
  errors: ValidationError[];
  validated: boolean;
}

export interface ChatRequest {
  session_id: string;
  user_message: string;
  extracted_text?: string | null;
  version?: string;
  top_k?: number;
  model?: string;
}

interface AuthResponse {
  access_token: string;
  token_type: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function authHeaders(): Record<string, string> {
  const token = getTokenCookie();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(init.headers as Record<string, string>),
    },
  });

  if (res.status === 401) {
    clearTokenCookie();
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || "Request failed");
  }

  return res.json() as Promise<T>;
}

// ── API ───────────────────────────────────────────────────────────────────────

export const api = {
  // Auth
  register(email: string, password: string): Promise<AuthResponse> {
    return apiFetch("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  login(email: string, password: string): Promise<AuthResponse> {
    return apiFetch("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  // Sessions
  getSessions(): Promise<Session[]> {
    return apiFetch("/sessions/");
  },

  createSession(title?: string): Promise<Session> {
    return apiFetch("/sessions/", {
      method: "POST",
      body: JSON.stringify({ title }),
    });
  },

  getSession(id: string): Promise<SessionDetail> {
    return apiFetch(`/sessions/${id}`);
  },

  renameSession(id: string, title: string): Promise<Session> {
    return apiFetch(`/sessions/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ title }),
    });
  },

  deleteSession(id: string): Promise<{ deleted: string }> {
    return apiFetch(`/sessions/${id}`, { method: "DELETE" });
  },

  // Files
  async uploadFile(sessionId: string, file: File): Promise<UploadResult> {
    const form = new FormData();
    form.append("session_id", sessionId);
    form.append("file", file);

    const res = await fetch(`${API_URL}/files/upload`, {
      method: "POST",
      headers: authHeaders(),
      body: form,
    });

    if (res.status === 401) {
      clearTokenCookie();
      window.location.href = "/login";
      throw new Error("Unauthorized");
    }
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(body.detail || "Upload failed");
    }
    return res.json() as Promise<UploadResult>;
  },

  getGeneratedFiles(sessionId: string): Promise<GeneratedFile[]> {
    return apiFetch(`/files/generated/${sessionId}`);
  },

  async downloadFile(downloadUrl: string): Promise<Blob> {
    const res = await fetch(`${API_URL}${downloadUrl}`, {
      headers: authHeaders(),
    });
    if (!res.ok) throw new Error("Download failed");
    return res.blob();
  },

  // Flows
  getFlowState(sessionId: string): Promise<FlowState> {
    return apiFetch(`/flows/${sessionId}`);
  },

  setEndpoint(sessionId: string, endpointUri: string): Promise<unknown> {
    return apiFetch(`/flows/${sessionId}/endpoint`, {
      method: "POST",
      body: JSON.stringify({ endpoint_uri: endpointUri }),
    });
  },

  publishFlow(sessionId: string): Promise<unknown> {
    return apiFetch(`/flows/${sessionId}/publish`, { method: "POST" });
  },
};

// ── Streaming chat ─────────────────────────────────────────────────────────────

export interface StreamChatCallbacks {
  onStatus: (status: string, attempt: number) => void;
  onToken: (token: string) => void;
  onFlowId: (flowId: string, flowName: string) => void;
  onValidationErrors: (errors: ValidationError[], attempt: number) => void;
  onPreviewUrl: (url: string) => void;
  onEndpointDefault: (uri: string) => void;
  onError: (error: string) => void;
  onDone: () => void;
}

export async function streamChat(
  body: ChatRequest,
  callbacks: StreamChatCallbacks
): Promise<void> {
  const token = getTokenCookie();

  let res: Response;
  try {
    res = await fetch(`${API_URL}/chat/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body),
    });
  } catch {
    callbacks.onError("Network error — is the backend running?");
    callbacks.onDone();
    return;
  }

  if (!res.ok) {
    const errBody = await res.json().catch(() => ({ detail: res.statusText }));
    callbacks.onError(errBody.detail || "Chat request failed");
    callbacks.onDone();
    return;
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const raw = line.slice(6).trim();
        if (raw === "[DONE]") {
          callbacks.onDone();
          return;
        }
        try {
          const p = JSON.parse(raw) as Record<string, unknown>;
          if ("status" in p) {
            callbacks.onStatus(String(p.status), Number(p.attempt ?? 1));
          } else if ("token" in p) {
            callbacks.onToken(String(p.token));
          } else if ("flow_id" in p) {
            callbacks.onFlowId(String(p.flow_id), String(p.flow_name ?? ""));
          } else if ("validation_errors" in p) {
            callbacks.onValidationErrors(
              p.validation_errors as ValidationError[],
              Number(p.attempt ?? 1)
            );
          } else if ("preview_url" in p) {
            callbacks.onPreviewUrl(String(p.preview_url));
          } else if ("endpoint_uri_default" in p) {
            callbacks.onEndpointDefault(String(p.endpoint_uri_default));
          } else if ("error" in p) {
            callbacks.onError(String(p.error));
          }
        } catch {
          // skip malformed lines
        }
      }
    }
  } finally {
    reader.releaseLock();
  }

  callbacks.onDone();
}

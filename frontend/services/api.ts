const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function handle401() {
  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
}

async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    credentials: "include",
  });
  if (res.status === 401) {
    handle401();
    throw new Error("Unauthorized");
  }
  return res;
}

// ── Types ────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
}

export interface Session {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  aisensy_flow_id?: string;
  endpoint_uri?: string;
  flow_status?: string;
  flow_category?: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  // optional client-side only: blob URLs for images sent with this message.
  // session-lifetime (not persisted); gone on reload.
  images?: string[];
}

export interface GeneratedFile {
  id: string;
  message_id: string;
  file_type: "flow_json" | "handler_py";
  version: number;
  created_at: string;
  download_url: string;
}

export interface ValidationError {
  error: string;
  message: string;
  pointers: { path: string }[];
}

export interface FlowState {
  aisensy_flow_id?: string;
  endpoint_uri?: string;
  flow_status?: string;
  flow_category?: string;
}

// ── Auth ─────────────────────────────────────────────────────────────────────

export async function login(email: string, password: string): Promise<void> {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? "Login failed");
  }
}

export async function register(email: string, password: string): Promise<void> {
  const res = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? "Registration failed");
  }
}

export async function logout(): Promise<void> {
  await fetch(`${API_URL}/auth/logout`, {
    method: "POST",
    credentials: "include",
  });
}

export async function getMe(): Promise<User> {
  const res = await fetch(`${API_URL}/auth/me`, { credentials: "include" });
  if (res.status === 401) throw new Error("Unauthorized");
  if (!res.ok) throw new Error("Failed to get user");
  return res.json();
}

// ── Sessions ──────────────────────────────────────────────────────────────────

export async function getSessions(): Promise<Session[]> {
  const res = await apiFetch("/sessions/");
  if (!res.ok) throw new Error("Failed to get sessions");
  return res.json();
}

export async function createSession(title?: string): Promise<Session> {
  const res = await apiFetch("/sessions/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(title ? { title } : {}),
  });
  if (!res.ok) throw new Error("Failed to create session");
  return res.json();
}

export async function getSession(id: string): Promise<{ session: Session; messages: Message[] }> {
  const res = await apiFetch(`/sessions/${id}`);
  if (!res.ok) throw new Error("Failed to get session");
  return res.json();
}

export async function renameSession(id: string, title: string): Promise<Session> {
  const res = await apiFetch(`/sessions/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error("Failed to rename session");
  return res.json();
}

export async function deleteSession(id: string): Promise<void> {
  const res = await apiFetch(`/sessions/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete session");
}

// ── Chat (SSE streaming) ──────────────────────────────────────────────────────

export interface StreamHandlers {
  onStatus: (status: string, attempt?: number) => void;
  onToken: (token: string) => void;
  onFlowId: (flowId: string, flowName: string) => void;
  onValidationErrors: (errors: ValidationError[], attempt: number) => void;
  onPreviewUrl: (url: string) => void;
  onEndpointDefault: (uri: string) => void;
  onError: (msg: string) => void;
  onDone: () => void;
}

export async function streamChat(
  body: {
    session_id: string;
    user_message: string;
    extracted_text?: string;
    model?: string;
  },
  handlers: StreamHandlers,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${API_URL}/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
    signal,
  });

  if (res.status === 401) {
    handle401();
    return;
  }
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    handlers.onError(text || `HTTP ${res.status}`);
    return;
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop()!;

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const raw = line.slice(6).trim();
      if (raw === "[DONE]") {
        handlers.onDone();
        return;
      }
      try {
        const evt = JSON.parse(raw);
        if (evt.status !== undefined) handlers.onStatus(evt.status, evt.attempt);
        else if (evt.token !== undefined) handlers.onToken(evt.token);
        else if (evt.flow_id !== undefined) handlers.onFlowId(evt.flow_id, evt.flow_name ?? "");
        else if (evt.validation_errors !== undefined) handlers.onValidationErrors(evt.validation_errors, evt.attempt ?? 1);
        else if (evt.preview_url !== undefined) handlers.onPreviewUrl(evt.preview_url);
        else if (evt.endpoint_uri_default !== undefined) handlers.onEndpointDefault(evt.endpoint_uri_default);
        else if (evt.error !== undefined) handlers.onError(evt.error);
      } catch {
        // ignore malformed lines
      }
    }
  }
}

// ── Files ────────────────────────────────────────────────────────────────────

export async function uploadFile(
  sessionId: string,
  file: File
): Promise<{ id: string; file_name: string; file_type: string; extracted_text: string }> {
  const form = new FormData();
  form.append("session_id", sessionId);
  form.append("file", file);
  const res = await apiFetch("/files/upload", { method: "POST", body: form });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? "Upload failed");
  }
  return res.json();
}

export async function getGeneratedFiles(sessionId: string): Promise<GeneratedFile[]> {
  const res = await apiFetch(`/files/generated/${sessionId}`);
  if (!res.ok) return [];
  return res.json();
}

// ── Flows ────────────────────────────────────────────────────────────────────

export async function getFlowState(sessionId: string): Promise<FlowState> {
  const res = await apiFetch(`/flows/${sessionId}`);
  if (!res.ok) return {};
  return res.json();
}

export async function saveEndpoint(sessionId: string, endpointUri: string): Promise<void> {
  const res = await apiFetch(`/flows/${sessionId}/endpoint`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ endpoint_uri: endpointUri }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? "Failed to save endpoint");
  }
}

export async function publishFlow(sessionId: string): Promise<void> {
  const res = await apiFetch(`/flows/${sessionId}/publish`, { method: "POST" });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? "Failed to publish");
  }
}
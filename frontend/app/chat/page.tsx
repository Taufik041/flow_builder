"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { getTokenCookie, clearTokenCookie } from "@/lib/cookies";
import { api, streamChat } from "@/services/api";
import type { Session, Message, GeneratedFile, FlowState, Attempt, ValidationError } from "@/services/api";
import { SessionSidebar } from "@/components/SessionSidebar";
import { ChatPanel } from "@/components/ChatPanel";
import type { ChatSettings, PendingFile } from "@/components/ChatPanel";
import { OutputPanel } from "@/components/OutputPanel";

interface Toast {
  id: number;
  message: string;
  type: "error" | "info";
}

let toastSeq = 0;

export default function ChatPage() {
  const router = useRouter();

  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [generatedFiles, setGeneratedFiles] = useState<GeneratedFile[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [attempts, setAttempts] = useState<Attempt[]>([]);
  const [pendingFile, setPendingFile] = useState<PendingFile | null>(null);
  const [flowState, setFlowState] = useState<FlowState | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [endpointDefault, setEndpointDefault] = useState<string | null>(null);
  const [settings, setSettings] = useState<ChatSettings>({
    version: "7.3",
    model: "gpt-4o",
    topK: 8,
  });
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [loading, setLoading] = useState(true);

  const activeSession = sessions.find((s) => s.id === activeSessionId) ?? null;

  function showToast(message: string, type: "error" | "info" = "error") {
    const id = ++toastSeq;
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 5000);
  }

  // ── Init ─────────────────────────────────────────────────────────────────────

  useEffect(() => {
    const token = getTokenCookie();
    if (!token) {
      router.push("/login");
      return;
    }
    api
      .getSessions()
      .then(setSessions)
      .catch(() => showToast("Failed to load sessions."))
      .finally(() => setLoading(false));
  }, [router]);

  // ── Session actions ───────────────────────────────────────────────────────────

  const selectSession = useCallback(async (id: string) => {
    setActiveSessionId(id);
    setMessages([]);
    setGeneratedFiles([]);
    setPendingFile(null);
    setAttempts([]);
    setPreviewUrl(null);
    setEndpointDefault(null);
    setFlowState(null);
    try {
      const [detail, files] = await Promise.all([
        api.getSession(id),
        api.getGeneratedFiles(id),
      ]);
      setMessages(detail.messages);
      setGeneratedFiles(files);
      const flow = await api.getFlowState(id).catch(() => null);
      if (flow) setFlowState(flow);
    } catch {
      showToast("Failed to load session.");
    }
  }, []);

  async function createSession() {
    try {
      const session = await api.createSession();
      setSessions((prev) => [session, ...prev]);
      await selectSession(session.id);
    } catch {
      showToast("Failed to create session.");
    }
  }

  async function renameSession(id: string, title: string) {
    try {
      const updated = await api.renameSession(id, title);
      setSessions((prev) => prev.map((s) => (s.id === id ? { ...s, title: updated.title } : s)));
    } catch {
      showToast("Failed to rename session.");
    }
  }

  async function deleteSession(id: string) {
    try {
      await api.deleteSession(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
      if (activeSessionId === id) {
        setActiveSessionId(null);
        setMessages([]);
        setGeneratedFiles([]);
        setPendingFile(null);
        setAttempts([]);
        setFlowState(null);
        setPreviewUrl(null);
        setEndpointDefault(null);
      }
    } catch {
      showToast("Failed to delete session.");
    }
  }

  function logout() {
    clearTokenCookie();
    router.push("/login");
  }

  // ── File upload ───────────────────────────────────────────────────────────────

  async function handleUpload(file: File) {
    if (!activeSessionId) return;
    try {
      const result = await api.uploadFile(activeSessionId, file);
      setPendingFile({ name: result.file_name, extractedText: result.extracted_text });
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Upload failed.");
    }
  }

  // ── Send message ──────────────────────────────────────────────────────────────

  async function handleSend(userMessage: string) {
    if (!activeSessionId || isStreaming) return;

    const sid = activeSessionId; // capture before any async state changes
    const tempUserId = `tmp-u-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      {
        id: tempUserId,
        session_id: sid,
        role: "user" as const,
        content: userMessage,
        created_at: new Date().toISOString(),
      },
    ]);

    const extractedText = pendingFile?.extractedText ?? null;
    setPendingFile(null);
    setIsStreaming(true);
    setAttempts([]);
    setPreviewUrl(null);

    await streamChat(
      {
        session_id: sid,
        user_message: userMessage,
        extracted_text: extractedText,
        version: settings.version,
        top_k: settings.topK,
        model: settings.model,
      },
      {
        onStatus(status: string, attemptNum: number) {
          setAttempts((prev) => {
            const exists = prev.find((a) => a.num === attemptNum);
            if (!exists) {
              return [
                ...prev,
                { num: attemptNum, status, code: "", errors: [], validated: false },
              ];
            }
            return prev.map((a) => (a.num === attemptNum ? { ...a, status } : a));
          });
        },
        onToken(token: string) {
          setAttempts((prev) => {
            if (prev.length === 0) return prev;
            return prev.map((a, i) =>
              i === prev.length - 1 ? { ...a, code: a.code + token } : a
            );
          });
        },
        onFlowId(flowId: string) {
          setSessions((prev) =>
            prev.map((s) =>
              s.id === sid ? { ...s, aisensy_flow_id: flowId } : s
            )
          );
        },
        onValidationErrors(errors: ValidationError[], attemptNum: number) {
          setAttempts((prev) =>
            prev.map((a) =>
              a.num === attemptNum ? { ...a, errors, validated: true } : a
            )
          );
        },
        onPreviewUrl(url: string) {
          setPreviewUrl(url);
        },
        onEndpointDefault(uri: string) {
          setEndpointDefault(uri);
        },
        onError(error: string) {
          showToast(error);
        },
        async onDone() {
          setIsStreaming(false);
          try {
            const [detail, files] = await Promise.all([
              api.getSession(sid),
              api.getGeneratedFiles(sid),
            ]);
            setMessages(detail.messages);
            setGeneratedFiles(files);
            setAttempts([]);
            const [updatedSessions, flow] = await Promise.all([
              api.getSessions(),
              api.getFlowState(sid).catch(() => null),
            ]);
            setSessions(updatedSessions);
            if (flow) setFlowState(flow);
          } catch {
            setAttempts([]);
          }
        },
      }
    );
  }

  // ── Publish callback ──────────────────────────────────────────────────────────

  async function handleSessionPublished() {
    if (!activeSessionId) return;
    try {
      const [updatedSessions, flow] = await Promise.all([
        api.getSessions(),
        api.getFlowState(activeSessionId).catch(() => null),
      ]);
      setSessions(updatedSessions);
      if (flow) setFlowState(flow);
    } catch {
      // silently ignore — publish already succeeded
    }
  }

  // ── Render ────────────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-zinc-950">
        <div className="w-5 h-5 border-2 border-[#25D366] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-100 overflow-hidden">
      <SessionSidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelect={selectSession}
        onCreate={createSession}
        onRename={renameSession}
        onDelete={deleteSession}
        onLogout={logout}
      />

      <ChatPanel
        session={activeSession}
        messages={messages}
        attempts={attempts}
        isStreaming={isStreaming}
        settings={settings}
        pendingFile={pendingFile}
        onSettingsChange={(patch) => setSettings((prev) => ({ ...prev, ...patch }))}
        onFileClear={() => setPendingFile(null)}
        onSend={handleSend}
        onUpload={handleUpload}
      />

      <OutputPanel
        messages={messages}
        generatedFiles={generatedFiles}
        attempts={attempts}
        sessionId={activeSessionId}
        flowState={flowState}
        previewUrl={previewUrl}
        endpointDefault={endpointDefault}
        onToast={showToast}
        onSessionPublished={handleSessionPublished}
      />

      {/* Toast stack */}
      <div className="fixed bottom-4 right-4 space-y-2 z-50 max-w-sm">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`px-4 py-2.5 rounded-lg text-sm shadow-lg border ${
              t.type === "error"
                ? "bg-red-950 border-red-800 text-red-200"
                : "bg-zinc-800 border-zinc-700 text-zinc-200"
            }`}
          >
            {t.message}
          </div>
        ))}
      </div>
    </div>
  );
}

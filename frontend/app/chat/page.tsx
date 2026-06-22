"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Group as PanelGroup, Panel, Separator as PanelResizeHandle } from "react-resizable-panels";
import {
  getMe, getSessions, createSession, getSession, renameSession, deleteSession,
  uploadFile, getGeneratedFiles, getFlowState, streamChat, logout,
  Session, Message, GeneratedFile, FlowState, ValidationError,
} from "@/services/api";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { Sidebar } from "@/components/Sidebar";
import { Composer, Attachment } from "@/components/Composer";
import {
  StreamingMessage, StreamingState, StreamPhase, AttemptRecord, createInitialStreamingState,
} from "@/components/StreamingMessage";
import { CodePane } from "@/components/CodePane";
import { PreviewPane } from "@/components/PreviewPane";
import { AssistantMarkdown } from "@/components/AssistantMarkdown";
import { Toast } from "@/components/Toast";

interface ToastItem { id: number; message: string; kind: "ok" | "err"; }

// Returns the content of the last complete ```lang ... ``` block in text, or "".
function extractFenced(text: string, lang: string): string {
  const marker = "```" + lang;
  let last = "";
  let pos = 0;
  while (true) {
    const start = text.indexOf(marker, pos);
    if (start === -1) break;
    const newline = text.indexOf("\n", start + marker.length);
    if (newline === -1) break;
    const end = text.indexOf("```", newline + 1);
    if (end === -1) break;
    last = text.slice(newline + 1, end);
    pos = end + 3;
  }
  return last;
}

function formatRelativeTime(dateStr: string): string {
  const d = new Date(dateStr);
  const now = Date.now();
  const diff = now - d.getTime();
  if (diff < 60_000) return "just now";
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  return d.toLocaleDateString();
}

function ChatPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ id: string; email: string } | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [generatedFiles, setGeneratedFiles] = useState<GeneratedFile[]>([]);
  const [flowState, setFlowState] = useState<FlowState>({});
  // BUG 1: per-session streaming state so switching sessions never kills a running stream
  const [streamingBySession, setStreamingBySession] = useState<Record<string, StreamingState>>({});
  // PREVIEW FIX: preview_url / endpoint_default live only in the streaming entry, which
  // onDone deletes — so the preview vanished the instant generation finished. Persist them
  // per-session here so they survive onDone and session switches (page-session lifetime).
  const [previewBySession, setPreviewBySession] = useState<
    Record<string, { previewUrl?: string; endpointDefault?: string }>
  >({});
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  const rightPanelRef = useRef<{
    collapse: () => void;
    expand: () => void;
    isCollapsed: () => boolean;
  } | null>(null);
  const [rightMode, setRightMode] = useState<"code" | "preview">("code");
  const [codeTab, setCodeTab] = useState<"json" | "python">("json");
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const [loadingSession, setLoadingSession] = useState(false);
  const [userScrolledUp, setUserScrolledUp] = useState(false);
  const [copied, setCopied] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  // BUG 1: per-session abort controllers
  const abortBySession = useRef<Record<string, AbortController>>({});
  // BUG 5b: monotonic ref avoids stale-closure duplicate ids
  const toastSeq = useRef(0);
  // BUG 1: stable ref so async onDone callbacks know the current session
  const currentSessionIdRef = useRef<string | null>(null);

  const currentSession = sessions.find((s) => s.id === currentSessionId);
  const currentStreamingState = currentSessionId ? streamingBySession[currentSessionId] : undefined;
  // BUG 2: isStreaming is derived from the CURRENT session only
  const isStreaming = !!(currentStreamingState && currentStreamingState.phase !== "idle" && currentStreamingState.phase !== "done");

  // keep ref in sync so async callbacks always see the latest session
  useEffect(() => { currentSessionIdRef.current = currentSessionId; }, [currentSessionId]);

  // check auth on mount
  useEffect(() => {
    getMe().then(setUser).catch(() => router.push("/login"));
  }, [router]);

  // load sessions on mount
  useEffect(() => {
    if (!user) return;
    getSessions().then((list) => {
      setSessions(list);
      if (list.length > 0 && !currentSessionId) {
        setCurrentSessionId(list[0].id);
      }
    }).catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  // load session messages when session changes
  // BUG 1: removed setStreaming(null) — active streams for this session are left running
  useEffect(() => {
    if (!currentSessionId) return;
    setLoadingSession(true);
    setGeneratedFiles([]);
    setFlowState({});
    // BUG (empty code panel): blank the panel ONLY here, on a real session switch,
    // so old content never bleeds across sessions. The content effects below never
    // blank to "" anymore (that wiped the panel mid-handoff in onDone).
    setJsonContent("");
    setPyContent("");
    Promise.all([
      getSession(currentSessionId),
      getGeneratedFiles(currentSessionId),
      getFlowState(currentSessionId),
    ]).then(([{ messages: msgs }, files, flow]) => {
      setMessages(msgs);
      setGeneratedFiles(files);
      setFlowState(flow);
    }).catch(() => {}).finally(() => setLoadingSession(false));
  }, [currentSessionId]);

  // auto-scroll
  useEffect(() => {
    if (userScrolledUp) return;
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, currentStreamingState, userScrolledUp]);

  function handleScroll() {
    const el = scrollRef.current;
    if (!el) return;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 60;
    setUserScrolledUp(!atBottom);
  }

  // BUG 5b: monotonic ref ensures unique toast ids even with rapid calls
  function showToast(message: string, kind: "ok" | "err" = "ok") {
    const id = ++toastSeq.current;
    setToasts((prev) => [...prev, { id, message, kind }]);
  }

  function dismissToast(id: number) {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }

  async function handleNewSession() {
    try {
      const s = await createSession();
      setSessions((prev) => [s, ...prev]);
      setCurrentSessionId(s.id);
      setMessages([]);
      setGeneratedFiles([]);
      setFlowState({});
    } catch {
      showToast("Failed to create session", "err");
    }
  }

  // BUG 1: just switch the view; do NOT abort the running stream
  async function handleSelectSession(id: string) {
    setCurrentSessionId(id);
  }

  async function handleRenameSession(id: string, title: string) {
    try {
      const updated = await renameSession(id, title);
      setSessions((prev) => prev.map((s) => s.id === id ? updated : s));
    } catch {
      showToast("Failed to rename session", "err");
    }
  }

  async function handleDeleteSession(id: string) {
    try {
      await deleteSession(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
      if (currentSessionId === id) {
        const remaining = sessions.filter((s) => s.id !== id);
        setCurrentSessionId(remaining[0]?.id ?? null);
      }
    } catch {
      showToast("Failed to delete session", "err");
    }
  }

  async function handleLogout() {
    await logout().catch(() => {});
    router.push("/login");
  }

  async function handleAttach(file: File): Promise<Attachment> {
    if (!currentSessionId) throw new Error("No active session");
    const result = await uploadFile(currentSessionId, file);
    const isImage = file.type.startsWith("image/");
    const previewUrl = isImage ? URL.createObjectURL(file) : undefined;
    return {
      file, extractedText: result.extracted_text,
      name: result.file_name,
      type: isImage ? "image" : "pdf",
      previewUrl,
    };
  }

  const handleSend = useCallback(async (text: string, attachments: Attachment[], model: string) => {
    if (!currentSessionId) {
      try {
        const s = await createSession();
        setSessions((prev) => [s, ...prev]);
        setCurrentSessionId(s.id);
        await doStream(s.id, text, attachments, model);
      } catch {
        showToast("Failed to create session", "err");
      }
      return;
    }
    await doStream(currentSessionId, text, attachments, model);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentSessionId]);

  async function doStream(sessionId: string, text: string, attachments: Attachment[], model: string) {
    const tempMsg: Message = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
      // carry sent images into the bubble (blob URLs, session-lifetime only)
      images: attachments
        .filter((a) => a.type === "image" && a.previewUrl)
        .map((a) => a.previewUrl as string),
    };
    setMessages((prev) => [...prev, tempMsg]);
    setUserScrolledUp(false);

    const initState: StreamingState = createInitialStreamingState();
    // BUG 1: write into the session-keyed map, not a single streaming slot
    setStreamingBySession((prev) => ({ ...prev, [sessionId]: initState }));
    // PREVIEW FIX: clear any prior persisted preview for this session so a stale URL
    // doesn't linger while the new generation runs.
    setPreviewBySession((prev) => {
      const next = { ...prev };
      delete next[sessionId];
      return next;
    });

    const abort = new AbortController();
    abortBySession.current[sessionId] = abort;

    const extractedText = attachments.map((a) => a.extractedText).filter(Boolean).join("\n\n");

    let state = { ...initState };
    function update(patch: Partial<StreamingState>) {
      state = { ...state, ...patch };
      setStreamingBySession((prev) => ({ ...prev, [sessionId]: { ...state } }));
    }

    try {
      await streamChat(
        {
          session_id: sessionId,
          user_message: text,
          extracted_text: extractedText || undefined,
          model,
        },
        {
          onStatus(status, attempt = 1) {
            const phase = status as StreamPhase;
            if (phase === "generating_json") {
              update({ phase, attemptNumber: attempt });
            } else if (phase === "repairing") {
              const record: AttemptRecord = {
                snippet: state.currentJsonSnippet,
                errors: state.currentErrors,
                attemptNumber: state.attemptNumber,
              };
              update({
                phase,
                attemptNumber: attempt,
                pastAttempts: [...state.pastAttempts, record],
                currentJsonSnippet: "",
                currentErrors: [],
              });
            } else if (phase === "validating") {
              update({ phase });
            } else if (phase === "generating_backend") {
              update({ phase });
            } else if (
              phase === "max_attempts_reached" ||
              phase === "no_flow_json" ||
              phase === "validator_unavailable" ||
              phase === "preview_unavailable"
            ) {
              update({ phase });
              if (phase === "validator_unavailable" || phase === "preview_unavailable") {
                showToast(phase === "validator_unavailable" ? "Validator unavailable" : "Preview unavailable", "err");
              }
            } else {
              update({ phase });
            }
          },
          onToken(token) {
            if (state.phase === "generating_json" || state.phase === "repairing") {
              update({ currentJsonSnippet: state.currentJsonSnippet + token });
            } else if (state.phase === "generating_backend") {
              update({ pythonSnippet: state.pythonSnippet + token });
            }
          },
          onFlowId(flowId, flowName) {
            update({ flowId, flowName });
          },
          onValidationErrors(errors: ValidationError[]) {
            update({ currentErrors: errors });
          },
          onPreviewUrl(previewUrl) {
            update({ previewUrl });
            setPreviewBySession((prev) => ({
              ...prev,
              [sessionId]: { ...prev[sessionId], previewUrl },
            }));
            setFlowState((prev) => ({ ...prev, aisensy_flow_id: state.flowId }));
          },
          onEndpointDefault(endpointDefault) {
            update({ endpointDefault });
            setPreviewBySession((prev) => ({
              ...prev,
              [sessionId]: { ...prev[sessionId], endpointDefault },
            }));
          },
          onError(msg) {
            showToast(msg || "Stream error", "err");
          },
          onDone() {
            update({ phase: "done" });
            Promise.all([
              getSession(sessionId),
              getGeneratedFiles(sessionId),
              getFlowState(sessionId),
            ]).then(([{ session, messages: msgs }, files, flow]) => {
              setSessions((prev) => prev.map((s) => s.id === sessionId ? { ...s, ...session } : s));
              // BUG 1: only update visible state when user is still on this session;
              // if they switched away, the session-load effect will fetch on return.
              if (currentSessionIdRef.current === sessionId) {
                // DB rows have no images; preserve the blob URLs from the optimistic
                // user messages so sent images don't vanish when onDone refetches.
                // (session-lifetime only — gone on full reload, as designed.)
                setMessages((prev) => {
                  const imagesByContent = new Map<string, string[]>();
                  for (const m of prev) {
                    if (m.role === "user" && m.images && m.images.length) {
                      imagesByContent.set(m.content, m.images);
                    }
                  }
                  return msgs.map((m) =>
                    m.role === "user" && imagesByContent.has(m.content)
                      ? { ...m, images: imagesByContent.get(m.content) }
                      : m
                  );
                });
                setGeneratedFiles(files);
                setFlowState(flow);
              }
              setStreamingBySession((prev) => {
                const next = { ...prev };
                delete next[sessionId];
                return next;
              });
            }).catch(() => {});
          },
        },
        abort.signal
      );
    } catch (e: unknown) {
      if ((e as Error)?.name !== "AbortError") {
        showToast("Stream failed", "err");
        update({ phase: "idle" });
      }
    } finally {
      // BUG 2: guarantee the phase is reset on success, error, AND abort
      delete abortBySession.current[sessionId];
      setStreamingBySession((prev) => {
        const entry = prev[sessionId];
        if (!entry || entry.phase === "done" || entry.phase === "idle") return prev;
        return { ...prev, [sessionId]: { ...entry, phase: "idle" as StreamPhase } };
      });
    }
  }

  // derive code content from generated files
  const jsonFile = generatedFiles.filter((f) => f.file_type === "flow_json").slice(-1)[0];
  const pyFile = generatedFiles.filter((f) => f.file_type === "handler_py").slice(-1)[0];
  const [jsonContent, setJsonContent] = useState("");
  const [pyContent, setPyContent] = useState("");

  // BUG 4 + BUG 5a: use API base for file fetches; extract only fenced code from stream.
  // FIX (empty code panel): never blank to "" here. When onDone deletes the streaming
  // entry, the snippet vanishes; if generatedFiles hasn't reflected the saved file yet
  // (or the onDone guard skipped it), the old else-branch ran extractFenced("") => ""
  // and wiped the panel even though the file exists on the server. Only set from the
  // snippet when there actually is one; the file fetch is the source of truth once saved.
  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    if (jsonFile) {
      fetch(`${base}${jsonFile.download_url}`, { credentials: "include" })
        .then((r) => r.text()).then(setJsonContent).catch(() => {});
    } else {
      const fenced = extractFenced(currentStreamingState?.currentJsonSnippet ?? "", "json");
      if (fenced) setJsonContent(fenced);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jsonFile?.id, currentStreamingState?.currentJsonSnippet]);

  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    if (pyFile) {
      fetch(`${base}${pyFile.download_url}`, { credentials: "include" })
        .then((r) => r.text()).then(setPyContent).catch(() => {});
    } else {
      const fenced = extractFenced(currentStreamingState?.pythonSnippet ?? "", "python");
      if (fenced) setPyContent(fenced);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pyFile?.id, currentStreamingState?.pythonSnippet]);

  function handleFileClick(file: GeneratedFile) {
    setCodeTab(file.file_type === "flow_json" ? "json" : "python");
    setRightMode("code");
  }

  // BUG 5a: fetch blob through the API gateway (credentials + correct origin)
  async function handleDownload(file: GeneratedFile) {
    const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const res = await fetch(`${base}${file.download_url}`, { credentials: "include" });
      if (!res.ok) { showToast("Download failed", "err"); return; }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = file.file_type === "flow_json" ? "flow.json" : "main.py";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      showToast("Download failed", "err");
    }
  }

  function handleCopy() {
    setCopied(true);
    showToast("Copied to clipboard", "ok");
    setTimeout(() => setCopied(false), 2000);
  }

  if (!user) {
    return (
      <div style={{ height: "100%", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--bg)" }}>
        <span className="spin" style={{ width: 20, height: 20 }} />
      </div>
    );
  }

  return (
    <div style={{ display: "flex", height: "100%", width: "100%", background: "var(--bg)", color: "var(--text)", fontSize: 14, WebkitFontSmoothing: "antialiased", overflow: "hidden" }}>

      {/* Sidebar — outside PanelGroup so collapse works cleanly */}
      <div style={{ width: sidebarCollapsed ? 56 : 264, flex: "0 0 auto", transition: "width .18s ease", height: "100%", overflow: "hidden" }}>
        <Sidebar
          sessions={sessions}
          currentSessionId={currentSessionId}
          userEmail={user.email}
          onNewSession={handleNewSession}
          onSelectSession={handleSelectSession}
          onRenameSession={handleRenameSession}
          onDeleteSession={handleDeleteSession}
          onLogout={handleLogout}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed((c) => !c)}
        />
      </div>

      {/* Resizable chat + right panel */}
      <PanelGroup orientation="horizontal" style={{ flex: "1 1 0", minWidth: 0 }}>

        {/* Chat */}
        <Panel defaultSize={60} minSize={30}>
          <main style={{ flex: "1 1 0", minWidth: 0, display: "flex", flexDirection: "column", background: "var(--bg)", height: "100%" }}>

            {/* header */}
            <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 24px", height: 54, flex: "0 0 auto", borderBottom: "0.5px solid var(--border)" }}>
              {currentSession ? (
                <>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span style={{ fontSize: 14, fontWeight: 600, letterSpacing: "-0.01em" }}>{currentSession.title}</span>
                    <span style={{ fontSize: 11, fontWeight: 500, color: currentSession.flow_status === "published" ? "var(--green)" : "var(--text4)", border: "0.5px solid var(--border)", borderRadius: 20, padding: "2px 8px" }}>
                      {currentSession.flow_status === "published" ? "published" : "draft"}
                    </span>
                  </div>
                  <span style={{ fontSize: 12, color: "var(--text4)" }}>
                    {formatRelativeTime(currentSession.updated_at)}
                  </span>
                </>
              ) : (
                <span style={{ fontSize: 14, fontWeight: 600, color: "var(--text3)" }}>Flow generator</span>
              )}
            </header>

            {/* messages */}
            <div
              ref={scrollRef}
              className="scroll-soft"
              onScroll={handleScroll}
              style={{ flex: "1 1 0", overflowY: "auto" }}
            >
              <div style={{ maxWidth: 720, margin: "0 auto", padding: "32px 24px 24px", display: "flex", flexDirection: "column", gap: 26 }}>

                {!currentSessionId && !loadingSession && (
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 16, paddingTop: 80, color: "var(--text3)", textAlign: "center" }}>
                    <div style={{ width: 48, height: 48, borderRadius: 12, background: "var(--accentSoft)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="6" cy="6" r="2.4" /><circle cx="18" cy="18" r="2.4" />
                        <path d="M8 6h7a3 3 0 0 1 3 3v6.5" />
                      </svg>
                    </div>
                    <div>
                      <div style={{ fontSize: 16, fontWeight: 600, color: "var(--text)", marginBottom: 6 }}>Create a new flow</div>
                      <div style={{ fontSize: 14, color: "var(--text3)" }}>Describe what you want to build and the AI will generate a WhatsApp flow.</div>
                    </div>
                    <button
                      onClick={handleNewSession}
                      style={{ padding: "10px 20px", border: "none", background: "var(--accent)", color: "#fff", borderRadius: 10, cursor: "pointer", fontSize: 14, fontWeight: 600, fontFamily: "inherit" }}
                    >
                      New flow
                    </button>
                  </div>
                )}

                {loadingSession && (
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "center", paddingTop: 60 }}>
                    <span className="spin" style={{ width: 18, height: 18 }} />
                  </div>
                )}

                {messages.map((msg) => (
                  <div key={msg.id}>
                    {msg.role === "user" ? (
                      <div style={{ display: "flex", justifyContent: "flex-end" }}>
                        <div style={{ maxWidth: "82%", background: "var(--bubble)", border: "0.5px solid rgba(61,58,52,0.05)", borderRadius: "18px 18px 5px 18px", padding: "12px 16px", fontSize: 14.5, lineHeight: 1.55, color: "var(--text)" }}>
                          {msg.images && msg.images.length > 0 && (
                            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: msg.content ? 8 : 0 }}>
                              {msg.images.map((src, i) => (
                                // eslint-disable-next-line @next/next/no-img-element
                                <img
                                  key={i}
                                  src={src}
                                  alt=""
                                  style={{ maxWidth: 180, maxHeight: 180, borderRadius: 10, objectFit: "cover", display: "block" }}
                                />
                              ))}
                            </div>
                          )}
                          {msg.content}
                        </div>
                      </div>
                    ) : (
                      <div style={{ display: "flex", gap: 13, alignItems: "flex-start" }}>
                        <div style={{ width: 25, height: 25, borderRadius: 7, background: "var(--accent)", flex: "0 0 auto", marginTop: 2, display: "flex", alignItems: "center", justifyContent: "center" }}>
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <circle cx="6" cy="6" r="2.4" /><circle cx="18" cy="18" r="2.4" />
                            <path d="M8 6h7a3 3 0 0 1 3 3v6.5" />
                          </svg>
                        </div>
                        <div style={{ flex: "1 1 0", minWidth: 0 }}>
                          <div style={{ marginBottom: 8 }}>
                            <AssistantMarkdown content={msg.content} />
                          </div>
                          {/* show file chips for completed assistant messages */}
                          {generatedFiles.length > 0 && msg.id === messages.filter((m) => m.role === "assistant").slice(-1)[0]?.id && (
                            <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginTop: 8 }}>
                              {generatedFiles.filter((f) => f.file_type === "flow_json").slice(-1).map((f) => (
                                <button key={f.id} className="chip" onClick={() => handleFileClick(f)} style={{ display: "flex", alignItems: "center", gap: 9, padding: "8px 12px", border: "0.5px solid var(--border)", borderRadius: 10, background: "var(--surface)", cursor: "pointer", fontSize: 12.5, fontWeight: 500, color: "var(--text)", fontFamily: "inherit" }}>
                                  <span style={{ fontSize: 11.5, color: "var(--text4)" }}>flow.json</span>
                                </button>
                              ))}
                              {generatedFiles.filter((f) => f.file_type === "handler_py").slice(-1).map((f) => (
                                <button key={f.id} className="chip" onClick={() => handleFileClick(f)} style={{ display: "flex", alignItems: "center", gap: 9, padding: "8px 12px", border: "0.5px solid var(--border)", borderRadius: 10, background: "var(--surface)", cursor: "pointer", fontSize: 12.5, fontWeight: 500, color: "var(--text)", fontFamily: "inherit" }}>
                                  <span style={{ fontSize: 11.5, color: "var(--text4)" }}>main.py</span>
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                {/* streaming message — BUG 1: read from per-session map */}
                {currentStreamingState && currentStreamingState.phase !== "idle" && (
                  <div style={{ display: "flex", gap: 13, alignItems: "flex-start" }}>
                    <div style={{ width: 25, height: 25, borderRadius: 7, background: "var(--accent)", flex: "0 0 auto", marginTop: 2, display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="6" cy="6" r="2.4" /><circle cx="18" cy="18" r="2.4" />
                        <path d="M8 6h7a3 3 0 0 1 3 3v6.5" />
                      </svg>
                    </div>
                    <div style={{ flex: "1 1 0", minWidth: 0 }}>
                      <StreamingMessage
                        state={currentStreamingState}
                        generatedFiles={generatedFiles}
                        onFileClick={handleFileClick}
                        onViewCode={() => setRightMode("code")}
                      />
                    </div>
                  </div>
                )}

                <div style={{ height: 1 }} />
              </div>
            </div>

            {/* composer — BUG 3: streaming + onStop wired up */}
            <Composer
              onSend={handleSend}
              onAttach={handleAttach}
              disabled={isStreaming || !currentSessionId}
              sessionId={currentSessionId}
              streaming={isStreaming}
              onStop={() => { if (currentSessionId) abortBySession.current[currentSessionId]?.abort(); }}
            />
          </main>
        </Panel>

        <PanelResizeHandle style={{ width: 6, cursor: "col-resize", position: "relative", display: "flex", justifyContent: "center" }}>
          <div style={{ width: 1, height: "100%", background: "var(--border)", transition: "background .12s ease" }} />
        </PanelResizeHandle>

        {/* Right panel */}
        <Panel
          defaultSize={40}
          minSize={22}
          collapsible
          collapsedSize={0}
          ref={rightPanelRef}
          onCollapse={() => setRightCollapsed(true)}
          onExpand={() => setRightCollapsed(false)}
        >
          <aside style={{ width: "100%", display: "flex", flexDirection: "column", background: "var(--panel)", borderLeft: "0.5px solid var(--border)", height: "100%", minWidth: 0, overflow: "hidden" }}>

            {/* top strip */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 14px", height: 54, flex: "0 0 auto", borderBottom: "0.5px solid var(--border)" }}>
              {/* Code / Preview toggle */}
              <div style={{ display: "flex", alignItems: "center", gap: 2, background: "var(--seg)", borderRadius: 9, padding: 3 }}>
                {(["code", "preview"] as const).map((m) => {
                  const active = rightMode === m;
                  return (
                    <button
                      key={m}
                      onClick={() => setRightMode(m)}
                      style={{
                        display: "flex", alignItems: "center", gap: 6, padding: "6px 13px",
                        border: "none", borderRadius: 7, cursor: "pointer",
                        fontSize: 13, fontWeight: 500, fontFamily: "inherit",
                        background: active ? "var(--surface)" : "transparent",
                        color: active ? "var(--text)" : "var(--text3)",
                        boxShadow: active ? "0 1px 2px rgba(0,0,0,0.12)" : "none",
                        transition: "box-shadow .12s ease",
                      }}
                    >
                      {m === "code" ? (
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M16 18l6-6-6-6" /><path d="M8 6l-6 6 6 6" />
                        </svg>
                      ) : (
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z" /><circle cx="12" cy="12" r="3" />
                        </svg>
                      )}
                      {m === "code" ? "Code" : "Preview"}
                    </button>
                  );
                })}
              </div>

              {/* copy/download icons */}
              <div style={{ display: "flex", alignItems: "center", gap: 2 }}>
                <button
                  className="icon-btn"
                  onClick={() => {
                    const content = codeTab === "json" ? jsonContent : pyContent;
                    if (content) { navigator.clipboard.writeText(content).then(() => handleCopy()).catch(() => {}); }
                  }}
                  title="Copy"
                  style={{ width: 32, height: 32, display: "flex", alignItems: "center", justifyContent: "center", border: "none", background: "transparent", borderRadius: 8, cursor: "pointer", color: copied ? "var(--green)" : "var(--text3)" }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="9" y="9" width="13" height="13" rx="2" />
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                  </svg>
                </button>
                <button
                  className="icon-btn"
                  onClick={() => { const f = codeTab === "json" ? jsonFile : pyFile; if (f) handleDownload(f); }}
                  title="Download"
                  style={{ width: 32, height: 32, display: "flex", alignItems: "center", justifyContent: "center", border: "none", background: "transparent", borderRadius: 8, cursor: "pointer", color: "var(--text3)" }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <path d="M7 10l5 5 5-5" /><path d="M12 15V3" />
                  </svg>
                </button>
                <button
                  className="icon-btn"
                  onClick={() => rightPanelRef.current?.collapse()}
                  title="Collapse panel"
                  style={{ width: 32, height: 32, display: "flex", alignItems: "center", justifyContent: "center", border: "none", background: "transparent", borderRadius: 8, cursor: "pointer", color: "var(--text3)" }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M9 18l6-6-6-6" />
                  </svg>
                </button>
              </div>
            </div>

            {/* panel content */}
            {rightMode === "code" ? (
              <CodePane
                tab={codeTab}
                onTabChange={setCodeTab}
                jsonContent={jsonContent}
                pythonContent={pyContent}
                jsonFile={jsonFile}
                pythonFile={pyFile}
                onCopy={handleCopy}
                onDownload={handleDownload}
                generating={isStreaming}
              />
            ) : (
              currentSessionId ? (
                <PreviewPane
                  previewUrl={currentStreamingState?.previewUrl ?? previewBySession[currentSessionId]?.previewUrl}
                  sessionId={currentSessionId}
                  flowState={flowState}
                  endpointDefault={currentStreamingState?.endpointDefault ?? previewBySession[currentSessionId]?.endpointDefault}
                  onFlowStateChange={setFlowState}
                  onToast={showToast}
                />
              ) : (
                <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text4)", fontSize: 13 }}>
                  Select a session to preview.
                </div>
              )
            )}
          </aside>
        </Panel>
      </PanelGroup>

      {/* Expand rail — shown only when the right panel is collapsed */}
      {rightCollapsed && (
        <div style={{ width: 44, flex: "0 0 auto", height: "100%", borderLeft: "0.5px solid var(--border)", background: "var(--panel)", display: "flex", flexDirection: "column", alignItems: "center", paddingTop: 11 }}>
          <button
            className="icon-btn"
            onClick={() => rightPanelRef.current?.expand()}
            title="Open panel"
            style={{ width: 32, height: 32, display: "flex", alignItems: "center", justifyContent: "center", border: "none", background: "transparent", borderRadius: 8, cursor: "pointer", color: "var(--text3)" }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M15 18l-6-6 6-6" />
            </svg>
          </button>
        </div>
      )}

      {/* Toasts */}
      {toasts.map((t) => (
        <Toast key={t.id} message={t.message} kind={t.kind} onDismiss={() => dismissToast(t.id)} />
      ))}
    </div>
  );
}

export default function ChatPageWrapper() {
  return (
    <ThemeProvider>
      <ChatPage />
    </ThemeProvider>
  );
}
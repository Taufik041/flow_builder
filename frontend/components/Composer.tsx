"use client";
import { useRef, useState, useEffect } from "react";

const MODELS = [
  { id: "gpt-4o", label: "GPT-4o" },
  { id: "gpt-4o-mini", label: "GPT-4o mini" },
  { id: "claude-sonnet", label: "Claude Sonnet" },
  { id: "claude-haiku", label: "Claude Haiku" },
];

export interface Attachment {
  file: File;
  extractedText: string;
  name: string;
  type: "image" | "pdf";
  previewUrl?: string;
}

interface Props {
  onSend: (text: string, attachments: Attachment[], model: string) => void;
  onAttach: (file: File) => Promise<Attachment>;
  disabled: boolean;
  sessionId: string | null;
  streaming?: boolean;
  onStop?: () => void;
}

export function Composer({ onSend, onAttach, disabled, sessionId, streaming, onStop }: Props) {
  const [text, setText] = useState("");
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [model, setModel] = useState("gpt-4o");
  const [modelOpen, setModelOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 180) + "px";
  }, [text]);

  useEffect(() => {
    function handlePaste(e: ClipboardEvent) {
      const items = e.clipboardData?.items;
      if (!items) return;
      for (const item of Array.from(items)) {
        if (item.type.startsWith("image/")) {
          const file = item.getAsFile();
          if (file) handleFile(file);
        }
      }
    }
    document.addEventListener("paste", handlePaste);
    return () => document.removeEventListener("paste", handlePaste);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  async function handleFile(file: File) {
    if (!sessionId) return;
    const allowed = ["image/png", "image/jpeg", "image/jpg", "application/pdf"];
    if (!allowed.includes(file.type)) return;
    setUploading(true);
    try {
      const att = await onAttach(file);
      setAttachments((prev) => [...prev, att]);
    } finally {
      setUploading(false);
    }
  }

  function handleFileInput(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = "";
  }

  function removeAttachment(index: number) {
    setAttachments((prev) => prev.filter((_, i) => i !== index));
  }

  function handleSend() {
    if (disabled || uploading || !text.trim()) return;
    onSend(text.trim(), attachments, model);
    setText("");
    setAttachments([]);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  const canSend = !disabled && !uploading && text.trim().length > 0;
  const selectedModel = MODELS.find((m) => m.id === model) ?? MODELS[0];

  return (
    <div style={{ flex: "0 0 auto", padding: "0 0 22px" }}>
      <div style={{ maxWidth: 720, margin: "0 auto", padding: "0 24px" }}>
        <div style={{
          border: "0.5px solid var(--border2)", borderRadius: 18,
          background: "var(--surface)", padding: "6px 6px 6px 0",
          boxShadow: "0 1px 2px rgba(61,58,52,0.03)",
        }}>

          {/* attachments */}
          {attachments.length > 0 && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, padding: "10px 10px 2px 14px" }}>
              {attachments.map((a, i) => (
                <div key={i} style={{
                  display: "flex", alignItems: "center", gap: 9,
                  padding: "6px 9px 6px 6px",
                  border: "0.5px solid var(--border2)", borderRadius: 10,
                  background: "var(--surface-2)",
                }}>
                  {a.type === "image" ? (
                    <span style={{
                      width: 30, height: 30, borderRadius: 7, flex: "0 0 auto",
                      background: "linear-gradient(135deg,#D9D3C7,#C5BCAC)",
                      display: "flex", alignItems: "center", justifyContent: "center", overflow: "hidden",
                    }}>
                      {a.previewUrl ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={a.previewUrl} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                      ) : (
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#F6F4EE" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                          <rect x="3" y="3" width="18" height="18" rx="2.5" /><circle cx="8.5" cy="8.5" r="1.6" />
                          <path d="M21 15l-5-5L5 21" />
                        </svg>
                      )}
                    </span>
                  ) : (
                    <span style={{
                      width: 30, height: 30, borderRadius: 7, flex: "0 0 auto",
                      background: "var(--redSoft)",
                      display: "flex", alignItems: "center", justifyContent: "center",
                    }}>
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--red)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                        <path d="M14 2v6h6" />
                      </svg>
                    </span>
                  )}
                  <span style={{ fontSize: 12.5, fontWeight: 500, color: "var(--text)", maxWidth: 150, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {a.name}
                  </span>
                  <button
                    className="icon-btn"
                    onClick={() => removeAttachment(i)}
                    title="Remove"
                    style={{
                      width: 22, height: 22, display: "flex", alignItems: "center", justifyContent: "center",
                      border: "none", background: "transparent", borderRadius: 6, cursor: "pointer",
                      color: "var(--text3)", flex: "0 0 auto",
                    }}
                  >
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M18 6L6 18M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              ))}
              {uploading && (
                <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 12px", borderRadius: 10, border: "0.5px solid var(--border)", background: "var(--surface-2)" }}>
                  <span className="spin" />
                  <span style={{ fontSize: 12.5, color: "var(--text3)" }}>Uploading…</span>
                </div>
              )}
            </div>
          )}

          {/* textarea */}
          <textarea
            ref={textareaRef}
            rows={1}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe your flow, or paste an image…"
            disabled={disabled}
            style={{
              display: "block", width: "100%", border: "none", outline: "none",
              resize: "none", background: "transparent",
              padding: "13px 16px 9px", fontSize: 14.5, lineHeight: 1.5,
              color: "var(--text)", minHeight: 46, maxHeight: 180,
              overflowY: "auto",
            }}
          />

          {/* bottom toolbar */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "2px 8px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
              {/* attach */}
              <button
                className="icon-btn"
                onClick={() => fileInputRef.current?.click()}
                title="Attach file"
                style={{
                  width: 34, height: 34, display: "flex", alignItems: "center", justifyContent: "center",
                  border: "none", background: "transparent", borderRadius: 9, cursor: "pointer",
                  color: "var(--text3)",
                }}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21.44 11.05l-9.19 9.19a5 5 0 0 1-7.07-7.07l9.19-9.19a3 3 0 0 1 4.24 4.24l-9.2 9.19a1 1 0 0 1-1.41-1.41l8.49-8.49" />
                </svg>
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.png,.jpg,.jpeg"
                style={{ display: "none" }}
                onChange={handleFileInput}
              />

              {/* model picker */}
              <div style={{ position: "relative" }}>
                <button
                  className="icon-btn"
                  onClick={() => setModelOpen((o) => !o)}
                  style={{
                    display: "flex", alignItems: "center", gap: 6, padding: "7px 9px 7px 11px",
                    border: "none", background: "transparent", borderRadius: 9, cursor: "pointer",
                    color: "var(--text2)", fontSize: 13, fontWeight: 500, fontFamily: "inherit",
                  }}
                >
                  {selectedModel.label}
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--text4)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M6 9l6 6 6-6" />
                  </svg>
                </button>
                {modelOpen && (
                  <div style={{
                    position: "absolute", bottom: "calc(100% + 6px)", left: 0,
                    background: "var(--surface)", border: "0.5px solid var(--border2)",
                    borderRadius: 10, boxShadow: "0 4px 16px rgba(38,35,31,0.12)",
                    zIndex: 20, minWidth: 160, overflow: "hidden",
                  }}>
                    {MODELS.map((m) => (
                      <button
                        key={m.id}
                        onClick={() => { setModel(m.id); setModelOpen(false); }}
                        style={{
                          display: "block", width: "100%", textAlign: "left",
                          padding: "9px 14px", border: "none", background: m.id === model ? "var(--accentSoft)" : "transparent",
                          cursor: "pointer", fontSize: 13, color: m.id === model ? "var(--accentText)" : "var(--text)",
                          fontFamily: "inherit", fontWeight: m.id === model ? 600 : 400,
                        }}
                      >
                        {m.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* BUG 3: stop button while streaming, send button otherwise */}
            {streaming ? (
              <button
                className="send-btn"
                onClick={onStop}
                title="Stop"
                style={{
                  width: 34, height: 34, display: "flex", alignItems: "center", justifyContent: "center",
                  border: "none", background: "var(--accent)",
                  borderRadius: 10, cursor: "pointer",
                  transition: "background .12s ease",
                }}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                  <rect x="4" y="4" width="16" height="16" rx="2" fill="#fff" />
                </svg>
              </button>
            ) : (
              <button
                className="send-btn"
                onClick={handleSend}
                disabled={!canSend}
                title="Send"
                style={{
                  width: 34, height: 34, display: "flex", alignItems: "center", justifyContent: "center",
                  border: "none", background: canSend ? "var(--accent)" : "var(--border2)",
                  borderRadius: 10, cursor: canSend ? "pointer" : "not-allowed",
                  transition: "background .12s ease",
                }}
              >
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 19V5" /><path d="M5 12l7-7 7 7" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

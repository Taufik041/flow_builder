"use client";

import { useEffect, useRef, useState } from "react";
import { Send, Paperclip, X, ChevronRight, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Message, Session, ValidationError, Attempt } from "@/services/api";

export interface ChatSettings {
  version: "7.3" | "7.1";
  model: string;
  topK: number;
}

export interface PendingFile {
  name: string;
  extractedText: string | null;
}

interface Props {
  session: Session | null;
  messages: Message[];
  attempts: Attempt[];
  isStreaming: boolean;
  settings: ChatSettings;
  pendingFile: PendingFile | null;
  onSettingsChange: (patch: Partial<ChatSettings>) => void;
  onFileClear: () => void;
  onSend: (message: string) => void;
  onUpload: (file: File) => Promise<void>;
}

const MODELS = [
  { value: "gpt-4o", label: "GPT-4o" },
  { value: "gpt-4o-mini", label: "GPT-4o mini" },
  { value: "claude-sonnet", label: "Claude Sonnet" },
  { value: "claude-haiku", label: "Claude Haiku" },
];

// ── Status pill ───────────────────────────────────────────────────────────────

function statusLabel(attempt: Attempt): { text: string; cls: string } {
  if (attempt.validated) {
    if (attempt.errors.length > 0)
      return {
        text: `${attempt.errors.length} error${attempt.errors.length === 1 ? "" : "s"} found`,
        cls: "bg-red-950 text-red-300 border border-red-800",
      };
    return { text: "✓ Valid", cls: "bg-[#25D366]/15 text-[#25D366] border border-[#25D366]/30" };
  }
  switch (attempt.status) {
    case "generating":
      return { text: "Generating…", cls: "bg-zinc-700 text-zinc-300 border border-zinc-600 animate-pulse" };
    case "creating_flow":
      return { text: "Creating flow…", cls: "bg-zinc-700 text-zinc-300 border border-zinc-600 animate-pulse" };
    case "validating":
      return { text: "Validating…", cls: "bg-blue-950 text-blue-300 border border-blue-800 animate-pulse" };
    case "repairing":
      return { text: "Repairing…", cls: "bg-orange-950 text-orange-300 border border-orange-800 animate-pulse" };
    case "max_attempts_reached":
      return { text: "Max attempts reached", cls: "bg-red-950 text-red-300 border border-red-800" };
    case "no_flow_json":
      return { text: "No JSON found", cls: "bg-red-950 text-red-300 border border-red-800" };
    case "validator_unavailable":
      return { text: "Validator N/A", cls: "bg-zinc-700 text-zinc-400 border border-zinc-600" };
    case "preview_unavailable":
      return { text: "Preview N/A", cls: "bg-zinc-700 text-zinc-400 border border-zinc-600" };
    default:
      return { text: attempt.status, cls: "bg-zinc-700 text-zinc-400 border border-zinc-600" };
  }
}

// ── Attempt block ─────────────────────────────────────────────────────────────

function ErrorPanel({ errors }: { errors: ValidationError[] }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-2 border border-red-900/50 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center gap-2 px-3 py-2 text-xs text-red-400 bg-red-950/30 hover:bg-red-950/50 transition-colors text-left"
      >
        {open ? <ChevronDown className="w-3 h-3 flex-shrink-0" /> : <ChevronRight className="w-3 h-3 flex-shrink-0" />}
        {errors.length} validation error{errors.length === 1 ? "" : "s"}
      </button>
      {open && (
        <div className="px-3 py-2 space-y-2 bg-red-950/10">
          {errors.map((e, i) => (
            <div key={i} className="text-xs">
              <p className="text-red-300 font-medium">{e.message}</p>
              {e.pointers.map((p, j) => (
                <p key={j} className="text-red-500/80 font-mono mt-0.5">
                  {p.path}
                  {p.line_start != null ? ` (line ${p.line_start})` : ""}
                </p>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function AttemptBlock({
  attempt,
  isLatest,
}: {
  attempt: Attempt;
  isLatest: boolean;
}) {
  const [open, setOpen] = useState(true);

  // Auto-collapse when this attempt is no longer the latest
  useEffect(() => {
    if (!isLatest) setOpen(false);
  }, [isLatest]);

  const pill = statusLabel(attempt);

  return (
    <div className="border border-zinc-700/60 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className={cn(
          "w-full flex items-center gap-2 px-3 py-2 text-left transition-colors",
          open ? "bg-zinc-800" : "bg-zinc-800/50 hover:bg-zinc-800"
        )}
      >
        {open ? (
          <ChevronDown className="w-3.5 h-3.5 text-zinc-500 flex-shrink-0" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5 text-zinc-500 flex-shrink-0" />
        )}
        <span className="text-xs font-medium text-zinc-300">
          Attempt {attempt.num}
        </span>
        <span className={cn("text-[10px] px-2 py-0.5 rounded-full ml-auto", pill.cls)}>
          {pill.text}
        </span>
      </button>

      {open && (
        <div className="bg-zinc-950 border-t border-zinc-700/60">
          {attempt.code ? (
            <pre className="text-xs font-mono text-zinc-300 p-3 overflow-x-auto whitespace-pre max-h-80 overflow-y-auto leading-relaxed">
              {attempt.code}
              {isLatest && attempt.status === "generating" && (
                <span className="inline-block w-1.5 h-3.5 bg-zinc-400 animate-pulse ml-0.5 align-middle" />
              )}
            </pre>
          ) : (
            <div className="px-3 py-4 flex items-center gap-2 text-xs text-zinc-500">
              <div className="w-3 h-3 border border-zinc-600 border-t-transparent rounded-full animate-spin" />
              Waiting for output…
            </div>
          )}

          {attempt.errors.length > 0 && (
            <div className="px-3 pb-3">
              <ErrorPanel errors={attempt.errors} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Message content ───────────────────────────────────────────────────────────

function MessageContent({ content }: { content: string }) {
  const parts = content.split(/(```[\w]*\n[\s\S]*?```)/g);
  return (
    <div>
      {parts.map((part, i) => {
        const m = part.match(/```(\w*)\n([\s\S]*?)```/);
        if (m) {
          const [, lang, code] = m;
          return (
            <pre
              key={i}
              className="bg-zinc-950 border border-zinc-700 rounded-lg text-xs p-3 my-2 overflow-x-auto font-mono text-zinc-200 whitespace-pre"
            >
              {lang && <div className="text-zinc-500 text-xs mb-1 font-sans">{lang}</div>}
              <code>{code.trim()}</code>
            </pre>
          );
        }
        return part ? (
          <span key={i} className="whitespace-pre-wrap">
            {part}
          </span>
        ) : null;
      })}
    </div>
  );
}

// ── Chat panel ────────────────────────────────────────────────────────────────

export function ChatPanel({
  session,
  messages,
  attempts,
  isStreaming,
  settings,
  pendingFile,
  onSettingsChange,
  onFileClear,
  onSend,
  onUpload,
}: Props) {
  const [input, setInput] = useState("");
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, attempts]);

  function handleSend() {
    const msg = input.trim();
    if (!msg || isStreaming || !session) return;
    setInput("");
    onSend(msg);
  }

  async function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !session) return;
    e.target.value = "";
    setUploading(true);
    try {
      await onUpload(file);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="flex-1 flex flex-col min-w-0 h-full">
      {/* Session header */}
      <div className="px-4 py-3 border-b border-zinc-800 flex-shrink-0">
        <h2 className="text-sm font-medium text-zinc-200 truncate">
          {session?.title ?? "Select a session"}
        </h2>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {!session && (
          <div className="flex items-center justify-center h-full text-zinc-500 text-sm">
            Select or create a session to start.
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              "flex",
              msg.role === "user" ? "justify-end" : "justify-start"
            )}
          >
            <div
              className={cn(
                "max-w-[80%] rounded-xl px-4 py-2.5 text-sm",
                msg.role === "user"
                  ? "bg-[#25D366] text-black rounded-br-sm"
                  : "bg-zinc-800 text-zinc-100 rounded-bl-sm"
              )}
            >
              {msg.role === "assistant" ? (
                <MessageContent content={msg.content} />
              ) : (
                <span className="whitespace-pre-wrap">{msg.content}</span>
              )}
            </div>
          </div>
        ))}

        {/* Live attempt stack */}
        {attempts.length > 0 && (
          <div className="space-y-2">
            {attempts.map((attempt, i) => (
              <AttemptBlock
                key={attempt.num}
                attempt={attempt}
                isLatest={i === attempts.length - 1}
              />
            ))}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-zinc-800 px-4 py-3 flex-shrink-0 space-y-2">
        {/* Settings row */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex rounded-lg border border-zinc-700 overflow-hidden text-xs">
            {(["7.3", "7.1"] as const).map((v) => (
              <button
                key={v}
                onClick={() => onSettingsChange({ version: v })}
                className={cn(
                  "px-3 py-1 transition-colors",
                  settings.version === v
                    ? "bg-zinc-600 text-zinc-100"
                    : "text-zinc-400 hover:text-zinc-200"
                )}
              >
                v{v}
              </button>
            ))}
          </div>

          <select
            value={settings.model}
            onChange={(e) => onSettingsChange({ model: e.target.value })}
            className="bg-zinc-800 border border-zinc-700 rounded-lg px-2 py-1 text-xs text-zinc-200 focus:outline-none focus:border-zinc-500"
          >
            {MODELS.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>

          <div className="flex items-center gap-1.5">
            <span className="text-xs text-zinc-500">top_k</span>
            <input
              type="number"
              min={1}
              max={20}
              value={settings.topK}
              onChange={(e) =>
                onSettingsChange({ topK: parseInt(e.target.value) || 8 })
              }
              className="w-14 bg-zinc-800 border border-zinc-700 rounded-lg px-2 py-1 text-xs text-zinc-200 focus:outline-none focus:border-zinc-500"
            />
          </div>
        </div>

        {/* File chip */}
        {pendingFile && (
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 bg-zinc-800 border border-zinc-700 rounded-full px-3 py-1 text-xs text-zinc-300">
              <Paperclip className="w-3 h-3 text-zinc-400" />
              <span className="truncate max-w-[180px]">{pendingFile.name}</span>
              <button onClick={onFileClear} className="text-zinc-500 hover:text-zinc-300 ml-0.5">
                <X className="w-3 h-3" />
              </button>
            </div>
            {pendingFile.extractedText === null && (
              <span className="text-xs text-zinc-500">(no text extracted)</span>
            )}
          </div>
        )}

        {/* Textarea + buttons */}
        <div className="flex gap-2 items-end">
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            accept=".pdf,.png,.jpg,.jpeg"
            onChange={handleFileSelect}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={!session || uploading}
            title="Attach file (.pdf, .png, .jpg)"
            className="p-2 text-zinc-500 hover:text-zinc-300 disabled:opacity-40 transition-colors flex-shrink-0"
          >
            {uploading ? (
              <div className="w-4 h-4 border-2 border-zinc-500 border-t-transparent rounded-full animate-spin" />
            ) : (
              <Paperclip className="w-4 h-4" />
            )}
          </button>

          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder={
              session ? "Describe your WhatsApp flow…" : "Select a session first"
            }
            disabled={!session || isStreaming}
            rows={3}
            className="flex-1 bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:border-zinc-500 resize-none disabled:opacity-50"
          />

          <button
            onClick={handleSend}
            disabled={!session || isStreaming || !input.trim()}
            className="p-2.5 bg-[#25D366] hover:bg-[#1ea952] disabled:opacity-40 text-black rounded-xl transition-colors flex-shrink-0"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>

        <p className="text-xs text-zinc-600">
          Enter to send · Shift+Enter for newline
        </p>
      </div>
    </div>
  );
}

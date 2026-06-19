"use client";

import { useEffect, useState } from "react";
import { Copy, Download, Check, ExternalLink } from "lucide-react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { cn } from "@/lib/utils";
import { api } from "@/services/api";
import type { Message, GeneratedFile, FlowState, Attempt } from "@/services/api";

interface Props {
  messages: Message[];
  generatedFiles: GeneratedFile[];
  attempts: Attempt[];
  sessionId: string | null;
  flowState: FlowState | null;
  previewUrl: string | null;
  endpointDefault: string | null;
  onToast: (msg: string, type?: "error" | "info") => void;
  onSessionPublished: () => void;
}

type Tab = "json" | "python";

function parseCodeBlocks(content: string): { json: string | null; python: string | null } {
  const jsonMatch = content.match(/```json\s*([\s\S]*?)```/);
  const pyMatch = content.match(/```python\s*([\s\S]*?)```/);
  return {
    json: jsonMatch ? jsonMatch[1].trim() : null,
    python: pyMatch ? pyMatch[1].trim() : null,
  };
}

function parseLatestOutput(
  messages: Message[],
  attempts: Attempt[]
): { json: string | null; python: string | null; messageId: string | null } {
  // During streaming: use last attempt's code
  if (attempts.length > 0) {
    const last = attempts[attempts.length - 1];
    const blocks = parseCodeBlocks(last.code);
    return { ...blocks, messageId: null };
  }
  // History: scan assistant messages from newest
  const assistants = [...messages].reverse().filter((m) => m.role === "assistant");
  for (const msg of assistants) {
    const blocks = parseCodeBlocks(msg.content);
    if (blocks.json || blocks.python) return { ...blocks, messageId: msg.id };
  }
  return { json: null, python: null, messageId: null };
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// ── Preview section ───────────────────────────────────────────────────────────

function PreviewSection({ url }: { url: string }) {
  const [iframeError, setIframeError] = useState(false);

  return (
    <div className="border-t border-zinc-800 px-4 py-3 flex-shrink-0">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
          Preview
        </span>
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 text-xs text-zinc-500 hover:text-[#25D366] transition-colors"
        >
          <ExternalLink className="w-3 h-3" />
          Open ↗
        </a>
      </div>
      {!iframeError ? (
        <iframe
          src={url}
          className="w-full h-48 rounded-lg border border-zinc-700 bg-zinc-800"
          onError={() => setIframeError(true)}
          sandbox="allow-scripts allow-same-origin allow-forms"
          title="Flow preview"
        />
      ) : (
        <div className="w-full h-16 rounded-lg border border-zinc-700 bg-zinc-800/50 flex items-center justify-center">
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-xs text-[#25D366] hover:underline"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            Open live preview ↗
          </a>
        </div>
      )}
    </div>
  );
}

// ── Deploy section ────────────────────────────────────────────────────────────

function DeploySection({
  sessionId,
  flowState,
  endpointDefault,
  onToast,
  onSessionPublished,
}: {
  sessionId: string;
  flowState: FlowState | null;
  endpointDefault: string | null;
  onToast: (msg: string, type?: "error" | "info") => void;
  onSessionPublished: () => void;
}) {
  const [endpointInput, setEndpointInput] = useState("");
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  // Prefill endpoint from flowState or stream default
  useEffect(() => {
    if (flowState?.endpoint_uri) {
      setEndpointInput(flowState.endpoint_uri);
    } else if (endpointDefault) {
      setEndpointInput((prev) => prev || endpointDefault);
    }
  }, [flowState?.endpoint_uri, endpointDefault]);

  async function handleSaveEndpoint() {
    if (!endpointInput.trim()) return;
    setSaving(true);
    try {
      await api.setEndpoint(sessionId, endpointInput.trim());
      onToast("Endpoint saved.", "info");
    } catch (err) {
      onToast(err instanceof Error ? err.message : "Failed to save endpoint.");
    } finally {
      setSaving(false);
    }
  }

  async function handlePublish() {
    setPublishing(true);
    setShowConfirm(false);
    try {
      await api.publishFlow(sessionId);
      onToast("Flow published!", "info");
      onSessionPublished();
    } catch (err) {
      onToast(err instanceof Error ? err.message : "Publish failed.");
    } finally {
      setPublishing(false);
    }
  }

  return (
    <div className="border-t border-zinc-800 px-4 py-3 flex-shrink-0 space-y-3">
      <span className="text-xs font-medium text-zinc-400 uppercase tracking-wider block">
        Deploy
      </span>

      {/* Endpoint input */}
      <div className="space-y-1.5">
        <label className="text-xs text-zinc-500">Data-exchange endpoint</label>
        <div className="flex gap-2">
          <input
            type="url"
            value={endpointInput}
            onChange={(e) => setEndpointInput(e.target.value)}
            placeholder="https://your-server.com/webhook"
            className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-2.5 py-1.5 text-xs text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:border-zinc-500 min-w-0"
          />
          <button
            onClick={handleSaveEndpoint}
            disabled={saving || !endpointInput.trim()}
            className="text-xs px-3 py-1.5 bg-zinc-700 hover:bg-zinc-600 disabled:opacity-40 text-zinc-200 rounded-lg transition-colors flex-shrink-0"
          >
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      </div>

      {/* Publish */}
      {showConfirm ? (
        <div className="rounded-lg border border-zinc-700 bg-zinc-800/50 p-3 space-y-2">
          <p className="text-xs text-zinc-300">
            Publish this flow to WhatsApp? This action cannot be undone.
          </p>
          <div className="flex gap-2">
            <button
              onClick={handlePublish}
              disabled={publishing}
              className="flex-1 text-xs py-1.5 bg-[#25D366] hover:bg-[#1ea952] disabled:opacity-50 text-black rounded-lg font-medium transition-colors"
            >
              {publishing ? "Publishing…" : "Yes, publish"}
            </button>
            <button
              onClick={() => setShowConfirm(false)}
              className="flex-1 text-xs py-1.5 bg-zinc-700 hover:bg-zinc-600 text-zinc-300 rounded-lg transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setShowConfirm(true)}
          disabled={publishing || !flowState?.aisensy_flow_id}
          className="w-full text-xs py-2 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 disabled:opacity-40 text-zinc-200 rounded-lg transition-colors"
          title={!flowState?.aisensy_flow_id ? "Generate a flow first" : undefined}
        >
          {publishing ? "Publishing…" : "Publish flow"}
        </button>
      )}

      {flowState?.flow_status === "published" && (
        <p className="text-xs text-[#25D366]">Flow is published.</p>
      )}
    </div>
  );
}

// ── Output panel ──────────────────────────────────────────────────────────────

export function OutputPanel({
  messages,
  generatedFiles,
  attempts,
  sessionId,
  flowState,
  previewUrl,
  endpointDefault,
  onToast,
  onSessionPublished,
}: Props) {
  const [activeTab, setActiveTab] = useState<Tab>("json");
  const [copied, setCopied] = useState(false);
  const [downloading, setDownloading] = useState(false);

  const { json, python, messageId } = parseLatestOutput(messages, attempts);
  const content = activeTab === "json" ? json : python;
  const language = activeTab === "json" ? "json" : "python";
  const isEmpty = !content;

  async function handleCopy() {
    if (!content) return;
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  async function handleDownload() {
    if (!content) return;
    setDownloading(true);
    try {
      const fileType = activeTab === "json" ? "flow_json" : "handler_py";
      const ext = activeTab === "json" ? "flow.json" : "handler.py";
      const genFile = generatedFiles
        .filter((f) => f.message_id === messageId && f.file_type === fileType)
        .at(-1);

      if (genFile) {
        try {
          const blob = await api.downloadFile(genFile.download_url);
          triggerDownload(blob, ext);
          return;
        } catch {
          // fall through to blob
        }
      }
      const mime = activeTab === "json" ? "application/json" : "text/x-python";
      triggerDownload(new Blob([content], { type: mime }), ext);
    } finally {
      setDownloading(false);
    }
  }

  return (
    <aside className="w-96 flex-shrink-0 border-l border-zinc-800 flex flex-col bg-zinc-900 h-full overflow-hidden">
      {/* Header + tabs */}
      <div className="px-4 py-3 border-b border-zinc-800 flex-shrink-0">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
            Output
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={handleCopy}
              disabled={isEmpty}
              title="Copy"
              className="p-1.5 text-zinc-500 hover:text-zinc-300 disabled:opacity-30 transition-colors"
            >
              {copied ? (
                <Check className="w-3.5 h-3.5 text-[#25D366]" />
              ) : (
                <Copy className="w-3.5 h-3.5" />
              )}
            </button>
            <button
              onClick={handleDownload}
              disabled={isEmpty || downloading}
              title="Download"
              className="p-1.5 text-zinc-500 hover:text-zinc-300 disabled:opacity-30 transition-colors"
            >
              {downloading ? (
                <div className="w-3.5 h-3.5 border-2 border-zinc-500 border-t-transparent rounded-full animate-spin" />
              ) : (
                <Download className="w-3.5 h-3.5" />
              )}
            </button>
          </div>
        </div>

        <div className="flex gap-1 bg-zinc-800 rounded-lg p-0.5">
          {(["json", "python"] as Tab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                "flex-1 text-xs py-1 rounded-md transition-colors",
                activeTab === tab
                  ? "bg-zinc-600 text-zinc-100"
                  : "text-zinc-400 hover:text-zinc-200"
              )}
            >
              {tab === "json" ? "Flow JSON" : "Backend Code"}
            </button>
          ))}
        </div>
      </div>

      {/* Code */}
      <div className="flex-1 overflow-auto min-h-0">
        {isEmpty ? (
          <div className="flex items-center justify-center h-full text-center px-6">
            <p className="text-xs text-zinc-500">
              {messages.length === 0 && attempts.length === 0
                ? "Send a message to generate a flow."
                : `No ${activeTab === "json" ? "JSON" : "Python"} block yet.`}
            </p>
          </div>
        ) : (
          <div className="text-xs">
            <SyntaxHighlighter
              language={language}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              style={vscDarkPlus as any}
              customStyle={{
                margin: 0,
                background: "transparent",
                fontSize: "0.72rem",
                lineHeight: "1.5",
              }}
              wrapLongLines={false}
            >
              {content}
            </SyntaxHighlighter>
          </div>
        )}
      </div>

      {/* Generated files history */}
      {generatedFiles.length > 0 && (
        <div className="border-t border-zinc-800 px-4 py-3 flex-shrink-0">
          <p className="text-xs text-zinc-500 mb-1.5">
            {generatedFiles.length} saved file{generatedFiles.length !== 1 ? "s" : ""}
          </p>
          <div className="space-y-1 max-h-20 overflow-y-auto">
            {[...generatedFiles].reverse().map((f) => (
              <div key={f.id} className="flex items-center justify-between text-xs text-zinc-400">
                <span className="truncate">
                  {f.file_type === "flow_json" ? "flow.json" : "handler.py"} · v{f.version}
                </span>
                <button
                  onClick={async () => {
                    try {
                      const blob = await api.downloadFile(f.download_url);
                      const ext = f.file_type === "flow_json" ? "flow.json" : "handler.py";
                      triggerDownload(blob, ext);
                    } catch {
                      // silent
                    }
                  }}
                  className="text-zinc-600 hover:text-[#25D366] transition-colors ml-2 flex-shrink-0"
                >
                  <Download className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Preview */}
      {previewUrl && <PreviewSection url={previewUrl} />}

      {/* Deploy */}
      {sessionId && (
        <DeploySection
          sessionId={sessionId}
          flowState={flowState}
          endpointDefault={endpointDefault}
          onToast={onToast}
          onSessionPublished={onSessionPublished}
        />
      )}
    </aside>
  );
}

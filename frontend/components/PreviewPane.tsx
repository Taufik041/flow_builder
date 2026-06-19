"use client";
import { useState, useRef } from "react";
import { FlowState, saveEndpoint, publishFlow } from "@/services/api";
import { PublishModal } from "./PublishModal";

const SCALE = parseFloat(process.env.NEXT_PUBLIC_PREVIEW_SCALE ?? "0.67");
const WIDTH = parseInt(process.env.NEXT_PUBLIC_PREVIEW_WIDTH ?? "320", 10);
const HEIGHT = parseInt(process.env.NEXT_PUBLIC_PREVIEW_HEIGHT ?? "580", 10);
const OFFSET_X = parseInt(process.env.NEXT_PUBLIC_PREVIEW_OFFSET_X ?? "-400", 10);
const OFFSET_Y = parseInt(process.env.NEXT_PUBLIC_PREVIEW_OFFSET_Y ?? "-40", 10);
const IFRAME_W = parseInt(process.env.NEXT_PUBLIC_PREVIEW_IFRAME_WIDTH ?? "1200", 10);
const IFRAME_H = parseInt(process.env.NEXT_PUBLIC_PREVIEW_IFRAME_HEIGHT ?? "900", 10);

interface Props {
  previewUrl?: string;
  sessionId: string;
  flowState: FlowState;
  endpointDefault?: string;
  onFlowStateChange: (s: FlowState) => void;
  onToast: (msg: string, kind?: "ok" | "err") => void;
}

export function PreviewPane({
  previewUrl, sessionId, flowState, endpointDefault, onFlowStateChange, onToast,
}: Props) {
  const [iframeOk, setIframeOk] = useState(true);
  const [endpointInput, setEndpointInput] = useState(
    flowState.endpoint_uri ?? endpointDefault ?? ""
  );
  const [savingEndpoint, setSavingEndpoint] = useState(false);
  const [publishOpen, setPublishOpen] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // sync endpoint from props
  const displayEndpoint = endpointInput || flowState.endpoint_uri || endpointDefault || "";

  async function handleSaveEndpoint() {
    if (!displayEndpoint) return;
    setSavingEndpoint(true);
    try {
      await saveEndpoint(sessionId, displayEndpoint);
      onFlowStateChange({ ...flowState, endpoint_uri: displayEndpoint });
      onToast("Endpoint saved", "ok");
    } catch (e: unknown) {
      onToast(e instanceof Error ? e.message : "Failed to save endpoint", "err");
    } finally {
      setSavingEndpoint(false);
    }
  }

  async function handlePublish() {
    setPublishing(true);
    try {
      await publishFlow(sessionId);
      onFlowStateChange({ ...flowState, flow_status: "published" });
      onToast("Flow published!", "ok");
      setPublishOpen(false);
    } catch (e: unknown) {
      onToast(e instanceof Error ? e.message : "Failed to publish", "err");
    } finally {
      setPublishing(false);
    }
  }

  return (
    <div className="scroll-soft" style={{ flex: "1 1 0", minHeight: 0, overflowY: "auto", display: "flex", flexDirection: "column" }}>
      <div style={{ flex: "1 1 0", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 22, padding: "30px 24px" }}>

        {previewUrl ? (
          <>
            {iframeOk ? (
              <div style={{
                width: WIDTH, height: HEIGHT, overflow: "hidden",
                borderRadius: 16, boxShadow: "0 4px 24px rgba(38,35,31,0.13)",
                position: "relative", flex: "0 0 auto",
                border: "0.5px solid var(--border)",
              }}>
                <iframe
                  ref={iframeRef}
                  src={previewUrl}
                  style={{
                    position: "absolute",
                    width: IFRAME_W, height: IFRAME_H,
                    border: "none",
                    transformOrigin: "top left",
                    transform: `scale(${SCALE}) translate(${OFFSET_X}px, ${OFFSET_Y}px)`,
                  }}
                  onError={() => setIframeOk(false)}
                />
              </div>
            ) : (
              <div style={{
                padding: "24px 32px", border: "0.5px solid var(--border)",
                borderRadius: 16, background: "var(--surface)",
                display: "flex", flexDirection: "column", alignItems: "center", gap: 12,
                textAlign: "center",
              }}>
                <div style={{
                  width: 44, height: 44, borderRadius: "50%", background: "var(--accentSoft)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                </div>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text)", marginBottom: 4 }}>Preview ready</div>
                  <div style={{ fontSize: 13, color: "var(--text3)" }}>Open the preview in a new tab to see it.</div>
                </div>
              </div>
            )}

            <a
              href={previewUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: "inline-flex", alignItems: "center", gap: 8,
                padding: "11px 20px", border: "none",
                background: "var(--accent)", borderRadius: 11, cursor: "pointer",
                color: "#fff", fontSize: 13.5, fontWeight: 600,
                textDecoration: "none",
                boxShadow: "0 1px 2px rgba(61,58,52,0.04)",
              }}
            >
              Open live preview ↗
            </a>
          </>
        ) : (
          <div style={{
            display: "flex", flexDirection: "column", alignItems: "center", gap: 12,
            color: "var(--text4)", textAlign: "center",
          }}>
            <div style={{
              width: 44, height: 44, borderRadius: "50%", background: "var(--surface-3)",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--text4)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            </div>
            <div style={{ fontSize: 13 }}>Preview will appear here after generation.</div>
          </div>
        )}
      </div>

      {/* deploy section */}
      <div style={{
        flex: "0 0 auto", borderTop: "0.5px solid var(--border)",
        background: "var(--panel)", padding: "18px 18px 20px",
      }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: "var(--text4)", marginBottom: 10 }}>Deploy</div>

        <div style={{ display: "flex", flexDirection: "column", gap: 5, marginBottom: 12 }}>
          <span style={{ fontSize: 11.5, color: "var(--text3)" }}>Endpoint URL</span>
          <input
            type="text"
            value={displayEndpoint}
            onChange={(e) => setEndpointInput(e.target.value)}
            placeholder="https://your-server.com/api/v1/flow/…"
            style={{
              width: "100%", border: "0.5px solid var(--border2)", borderRadius: 9,
              padding: "10px 12px", fontSize: 12.5, color: "var(--text)",
              background: "var(--surface)", outline: "none",
              fontFamily: "ui-monospace,'SF Mono',Menlo,monospace",
            }}
          />
        </div>

        <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 8 }}>
          <button
            className="icon-btn"
            onClick={handleSaveEndpoint}
            disabled={savingEndpoint || !displayEndpoint}
            style={{
              padding: "9px 14px", border: "0.5px solid var(--border2)",
              background: "var(--surface-2)", borderRadius: 9, cursor: "pointer",
              color: "var(--text)", fontSize: 13, fontWeight: 500, fontFamily: "inherit",
            }}
          >
            {savingEndpoint ? "Saving…" : "Save endpoint"}
          </button>
          <button
            className="send-btn"
            onClick={() => setPublishOpen(true)}
            style={{
              padding: "9px 18px", border: "none", background: "var(--accent)",
              borderRadius: 9, cursor: "pointer", color: "#FFFFFF",
              fontSize: 13, fontWeight: 600, fontFamily: "inherit",
            }}
          >
            Publish
          </button>
        </div>

        {flowState.flow_status === "published" && (
          <div style={{ marginTop: 10, display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{
              width: 16, height: 16, borderRadius: "50%", background: "var(--greenSoft)",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="var(--green)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 6L9 17l-5-5" />
              </svg>
            </span>
            <span style={{ fontSize: 12, color: "var(--green)", fontWeight: 500 }}>Published</span>
          </div>
        )}
      </div>

      {publishOpen && (
        <PublishModal
          onConfirm={handlePublish}
          onCancel={() => setPublishOpen(false)}
          loading={publishing}
        />
      )}
    </div>
  );
}

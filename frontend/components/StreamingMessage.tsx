"use client";
import { useState } from "react";
import { GeneratedFile, ValidationError } from "@/services/api";

export type StreamPhase =
  | "idle"
  | "generating_json"
  | "creating_flow"
  | "validating"
  | "repairing"
  | "generating_backend"
  | "max_attempts_reached"
  | "no_flow_json"
  | "validator_unavailable"
  | "preview_unavailable"
  | "done";

export interface AttemptRecord {
  snippet: string;
  errors: ValidationError[];
  attemptNumber: number;
}

export interface StreamingState {
  phase: StreamPhase;
  attemptNumber: number;
  pastAttempts: AttemptRecord[];
  currentJsonSnippet: string;
  currentErrors: ValidationError[];
  pythonSnippet: string;
  flowId?: string;
  flowName?: string;
  previewUrl?: string;
  endpointDefault?: string;
}

interface Props {
  state: StreamingState;
  generatedFiles: GeneratedFile[];
  onFileClick: (file: GeneratedFile) => void;
  onViewCode: () => void;
}

function CollapseIcon({ expanded }: { expanded: boolean }) {
  return (
    <svg
      width="13" height="13" viewBox="0 0 24 24" fill="none"
      stroke="var(--text4)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"
      style={{ transform: expanded ? "rotate(90deg)" : "rotate(0deg)", transition: "transform .15s ease", flex: "0 0 auto" }}
    >
      <path d="M9 18l6-6-6-6" />
    </svg>
  );
}

function CollapsedAttempt({ record, index }: { record: AttemptRecord; index: number }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div
      onClick={() => setExpanded((x) => !x)}
      style={{
        border: "0.5px solid var(--border)", borderRadius: 11,
        background: "var(--surface-3)", overflow: "hidden", cursor: "pointer",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 9, padding: "10px 13px" }}>
        <CollapseIcon expanded={expanded} />
        <span style={{ fontSize: 13, fontWeight: 500, color: "var(--text2)" }}>Attempt {record.attemptNumber}</span>
        <span style={{ width: 3, height: 3, borderRadius: "50%", background: "var(--dotPast)" }} />
        <span style={{ fontSize: 12.5, color: "var(--text4)" }}>
          {record.errors.length} error{record.errors.length !== 1 ? "s" : ""} fixed
        </span>
      </div>
      {expanded && record.errors.length > 0 && (
        <div style={{ padding: "0 13px 12px 32px", display: "flex", flexDirection: "column", gap: 9 }}>
          {record.errors.map((e, i) => (
            <div key={i} style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
              <span style={{ width: 4, height: 4, borderRadius: "50%", background: "var(--dotPast)", marginTop: 7, flex: "0 0 auto" }} />
              <div style={{ flex: "1 1 0", minWidth: 0 }}>
                <div style={{ fontSize: 12.5, lineHeight: 1.45, color: "var(--text4)" }}>{e.message}</div>
                <div style={{ fontSize: 11, fontFamily: "ui-monospace,'SF Mono',Menlo,monospace", color: "#B6B1A5", marginTop: 1 }}>
                  {e.pointers?.[0]?.path ?? ""}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ValidationErrorsPanel({ errors }: { errors: ValidationError[] }) {
  if (!errors.length) return null;
  return (
    <div style={{
      border: "0.5px solid var(--errBorder)", background: "var(--errBg)",
      borderRadius: 11, padding: "12px 14px",
      display: "flex", flexDirection: "column", gap: 11, alignSelf: "stretch",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--clay)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" />
        </svg>
        <span style={{ fontSize: 12.5, fontWeight: 600, color: "var(--errTitle)" }}>
          {errors.length} validation error{errors.length !== 1 ? "s" : ""}
        </span>
      </div>
      {errors.map((e, i) => (
        <div key={i} style={{ display: "flex", gap: 9, alignItems: "flex-start" }}>
          <span style={{ width: 5, height: 5, borderRadius: "50%", background: "var(--clay)", marginTop: 7, flex: "0 0 auto" }} />
          <div style={{ flex: "1 1 0", minWidth: 0 }}>
            <div style={{ fontSize: 13, lineHeight: 1.45, color: "var(--errMsg)" }}>{e.message}</div>
            <div style={{ fontSize: 11.5, fontFamily: "ui-monospace,'SF Mono',Menlo,monospace", color: "var(--errPath)", marginTop: 2 }}>
              {e.pointers?.[0]?.path ?? ""}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function StatusPill({ text, type }: { text: string; type: "spin" | "pulse" }) {
  return (
    <div style={{
      display: "inline-flex", alignItems: "center", gap: 9,
      padding: "7px 14px 7px 11px",
      border: "0.5px solid var(--border)", borderRadius: 999,
      background: "var(--surface)", fontSize: 13, fontWeight: 500,
      color: "var(--text2)", alignSelf: "flex-start",
    }}>
      <span className={type} />
      {text}
    </div>
  );
}

function FileChip({ file, onClick }: { file: GeneratedFile; onClick: () => void }) {
  const isJson = file.file_type === "flow_json";
  return (
    <div
      className="chip"
      onClick={onClick}
      style={{
        display: "flex", alignItems: "center", gap: 11,
        padding: "10px 13px", border: "0.5px solid var(--border)",
        borderRadius: 11, background: "var(--surface)", cursor: "pointer", minWidth: 208,
      }}
    >
      <span style={{
        width: 32, height: 32, borderRadius: 8,
        background: isJson ? "var(--claySoft)" : "var(--greenSoft)",
        display: "flex", alignItems: "center", justifyContent: "center", flex: "0 0 auto",
      }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
          stroke={isJson ? "var(--clay)" : "var(--green)"}
          strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <path d="M14 2v6h6" />
        </svg>
      </span>
      <div style={{ flex: "1 1 0", minWidth: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 500, color: "var(--text)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
          {isJson ? "flow.json" : "main.py"}
        </div>
        <div style={{ fontSize: 11.5, color: "var(--text4)" }}>
          {isJson ? "Flow JSON" : "Backend"} · v{file.version}
        </div>
      </div>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#B0ABA0" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <path d="M7 10l5 5 5-5" /><path d="M12 15V3" />
      </svg>
    </div>
  );
}

export function StreamingMessage({ state, generatedFiles, onFileClick, onViewCode }: Props) {
  const {
    phase, pastAttempts, currentJsonSnippet, currentErrors,
    pythonSnippet, attemptNumber,
  } = state;

  const isGeneratingJson = phase === "generating_json";
  const isValidating = phase === "validating";
  const isRepairing = phase === "repairing";
  const isGeneratingBackend = phase === "generating_backend";
  const isDone = phase === "done";

  const showJsonSnippet = currentJsonSnippet.length > 0 && phase !== "idle";
  const showPythonSnippet = pythonSnippet.length > 0 && (isGeneratingBackend || isDone);
  const showGenPill = isGeneratingJson || isRepairing;
  const showValidatingPill = isValidating;
  const showBackendProgressPill = isGeneratingBackend;

  const genPillText = isRepairing
    ? `Repairing · attempt ${attemptNumber}`
    : "Generating flow…";

  const jsonFiles = generatedFiles.filter((f) => f.file_type === "flow_json");
  const pyFiles = generatedFiles.filter((f) => f.file_type === "handler_py");
  const latestJson = jsonFiles[jsonFiles.length - 1];
  const latestPy = pyFiles[pyFiles.length - 1];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>

      {/* collapsed past attempts */}
      {pastAttempts.map((rec, i) => (
        <CollapsedAttempt key={i} record={rec} index={i} />
      ))}

      {/* current JSON snippet */}
      {showJsonSnippet && (
        <div style={{
          border: "0.5px solid var(--border)", borderRadius: 11,
          background: "var(--surface-3)", padding: "13px 15px", overflow: "hidden",
        }}>
          <pre style={{
            margin: 0, fontFamily: "ui-monospace,'SF Mono',Menlo,monospace",
            fontSize: 11.5, lineHeight: 1.7, color: "var(--text3)",
            whiteSpace: "pre-wrap", wordBreak: "break-word",
            opacity: isGeneratingJson || isRepairing ? 1 : 0.6,
          }}>
            {currentJsonSnippet}
            {(isGeneratingJson || isRepairing) && <span className="blink" />}
          </pre>
        </div>
      )}

      {/* generating pill */}
      {showGenPill && <StatusPill text={genPillText} type="spin" />}

      {/* validating pill */}
      {showValidatingPill && <StatusPill text="Validating against Meta…" type="pulse" />}

      {/* validation errors */}
      {currentErrors.length > 0 && phase !== "done" && (
        <ValidationErrorsPanel errors={currentErrors} />
      )}

      {/* "Flow JSON validated" + backend pill */}
      {(isGeneratingBackend || isDone) && (
        <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
          <span style={{
            width: 18, height: 18, borderRadius: "50%", background: "var(--greenSoft)",
            display: "flex", alignItems: "center", justifyContent: "center", flex: "0 0 auto",
          }}>
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="var(--green)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 6L9 17l-5-5" />
            </svg>
          </span>
          <span style={{ fontSize: 13, color: "var(--text2)" }}>Flow JSON validated</span>
        </div>
      )}

      {showBackendProgressPill && <StatusPill text="Writing backend…" type="spin" />}

      {/* python snippet */}
      {showPythonSnippet && (
        <div style={{
          border: "0.5px solid var(--border)", borderRadius: 11,
          background: "var(--surface-3)", padding: "13px 15px", overflow: "hidden",
        }}>
          <pre style={{
            margin: 0, fontFamily: "ui-monospace,'SF Mono',Menlo,monospace",
            fontSize: 11.5, lineHeight: 1.7, color: "var(--text3)",
            whiteSpace: "pre-wrap", wordBreak: "break-word",
            opacity: isGeneratingBackend ? 1 : 0.6,
          }}>
            {pythonSnippet}
            {isGeneratingBackend && <span className="blink" />}
          </pre>
        </div>
      )}

      {/* done state */}
      {isDone && (
        <>
          <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
            <span style={{
              width: 18, height: 18, borderRadius: "50%", background: "var(--greenSoft)",
              display: "flex", alignItems: "center", justifyContent: "center", flex: "0 0 auto",
            }}>
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="var(--green)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 6L9 17l-5-5" />
              </svg>
            </span>
            <span style={{ fontSize: 13.5, fontWeight: 500, color: "var(--green)" }}>Flow validated</span>
            {state.flowName && (
              <span style={{ fontSize: 13, color: "var(--text4)" }}>· {state.flowName}</span>
            )}
          </div>

          {/* file chips */}
          {(latestJson || latestPy) && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
              {latestJson && (
                <FileChip
                  file={latestJson}
                  onClick={() => { onFileClick(latestJson); onViewCode(); }}
                />
              )}
              {latestPy && (
                <FileChip
                  file={latestPy}
                  onClick={() => { onFileClick(latestPy); onViewCode(); }}
                />
              )}
            </div>
          )}
        </>
      )}

      {/* terminal error states */}
      {(phase === "max_attempts_reached" || phase === "no_flow_json") && (
        <div style={{
          display: "flex", alignItems: "center", gap: 9,
          padding: "9px 12px", background: "var(--redBg)",
          border: "0.5px solid var(--redBorder)", borderRadius: 10,
        }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--red)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flex: "0 0 auto" }}>
            <circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" />
          </svg>
          <span style={{ fontSize: 13, color: "var(--redText)" }}>
            {phase === "max_attempts_reached"
              ? "Could not produce a valid flow after max attempts."
              : "No valid flow JSON was generated."}
          </span>
        </div>
      )}
    </div>
  );
}

export function createInitialStreamingState(): StreamingState {
  return {
    phase: "idle",
    attemptNumber: 1,
    pastAttempts: [],
    currentJsonSnippet: "",
    currentErrors: [],
    pythonSnippet: "",
  };
}

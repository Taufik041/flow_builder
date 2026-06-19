"use client";
import SyntaxHighlighter from "react-syntax-highlighter";
import { GeneratedFile } from "@/services/api";

interface Props {
  tab: "json" | "python";
  onTabChange: (t: "json" | "python") => void;
  jsonContent: string;
  pythonContent: string;
  jsonFile?: GeneratedFile;
  pythonFile?: GeneratedFile;
  onCopy: () => void;
  onDownload: (file: GeneratedFile) => void;
  generating?: boolean;
}

const jsonTheme: { [key: string]: React.CSSProperties } = {
  "hljs": { background: "transparent", color: "var(--codeBase)", padding: 0 },
  "hljs-attr": { color: "var(--codeKey)" },
  "hljs-string": { color: "var(--codeStr)" },
  "hljs-number": { color: "var(--clay)" },
  "hljs-literal": { color: "var(--clay)" },
  "hljs-keyword": { color: "var(--clay)" },
  "hljs-built_in": { color: "var(--codeFn)" },
  "hljs-comment": { color: "var(--text4)" },
};

const pyTheme: { [key: string]: React.CSSProperties } = {
  "hljs": { background: "transparent", color: "var(--text2)", padding: 0 },
  "hljs-keyword": { color: "var(--clay)" },
  "hljs-string": { color: "var(--codeStr)" },
  "hljs-built_in": { color: "var(--codeFn)" },
  "hljs-decorator": { color: "var(--codeDec)" },
  "hljs-function": { color: "var(--codeFn)" },
  "hljs-title": { color: "var(--codeFn)" },
  "hljs-params": { color: "var(--text2)" },
  "hljs-comment": { color: "var(--text4)" },
  "hljs-number": { color: "var(--clay)" },
};

function SubTabBtn({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: "5px 12px", border: "none", borderRadius: 7, cursor: "pointer",
        fontSize: 12.5, fontWeight: 500,
        fontFamily: "ui-monospace,'SF Mono',Menlo,monospace",
        background: active ? "var(--seg)" : "transparent",
        color: active ? "var(--text)" : "var(--text4)",
      }}
    >
      {label}
    </button>
  );
}

export function CodePane({ tab, onTabChange, jsonContent, pythonContent, jsonFile, pythonFile, onCopy, onDownload, generating }: Props) {
  const isJson = tab === "json";
  const content = isJson ? jsonContent : pythonContent;
  const activeFile = isJson ? jsonFile : pythonFile;

  function handleCopy() {
    navigator.clipboard.writeText(content).catch(() => {});
    onCopy();
  }

  return (
    <div style={{ flex: "1 1 0", minHeight: 0, display: "flex", flexDirection: "column" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 2, padding: "10px 14px 6px" }}>
        <SubTabBtn label="flow.json" active={isJson} onClick={() => onTabChange("json")} />
        <SubTabBtn label="main.py" active={!isJson} onClick={() => onTabChange("python")} />
      </div>

      {content ? (
        <pre
          className="codepane"
          style={{
            margin: 0, flex: "1 1 0", minHeight: 0, overflow: "auto",
            padding: "14px 18px 22px",
            fontFamily: "ui-monospace,'SF Mono',Menlo,monospace",
            fontSize: 12.5, lineHeight: 1.78,
            color: "var(--codeBase)", whiteSpace: "pre",
          }}
        >
          <SyntaxHighlighter
            language={isJson ? "json" : "python"}
            style={isJson ? jsonTheme : pyTheme}
            customStyle={{ margin: 0, padding: 0, background: "transparent", fontSize: "inherit", lineHeight: "inherit" }}
            useInlineStyles
          >
            {content}
          </SyntaxHighlighter>
        </pre>
      ) : (
        <div style={{
          flex: "1 1 0", display: "flex", alignItems: "center", justifyContent: "center",
          color: "var(--text4)", fontSize: 13,
        }}>
          {generating ? "Generating…" : (tab === "json" ? "Generate a flow to see the JSON here." : "The backend handler will appear here.")}
        </div>
      )}

      {/* copy/download overlay row (only when file exists) */}
      {activeFile && (
        <div style={{
          position: "sticky", bottom: 0,
          display: "flex", justifyContent: "flex-end", gap: 6,
          padding: "8px 14px", background: "var(--panel)",
          borderTop: "0.5px solid var(--border)",
        }}>
          <button
            className="icon-btn"
            onClick={handleCopy}
            title="Copy"
            style={{
              display: "flex", alignItems: "center", gap: 6, padding: "6px 12px",
              border: "0.5px solid var(--border)", background: "var(--surface)",
              borderRadius: 8, cursor: "pointer", color: "var(--text2)",
              fontSize: 12.5, fontWeight: 500, fontFamily: "inherit",
            }}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="9" y="9" width="13" height="13" rx="2" />
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
            </svg>
            Copy
          </button>
          <button
            className="icon-btn"
            onClick={() => onDownload(activeFile)}
            title="Download"
            style={{
              display: "flex", alignItems: "center", gap: 6, padding: "6px 12px",
              border: "0.5px solid var(--border)", background: "var(--surface)",
              borderRadius: 8, cursor: "pointer", color: "var(--text2)",
              fontSize: 12.5, fontWeight: 500, fontFamily: "inherit",
            }}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <path d="M7 10l5 5 5-5" /><path d="M12 15V3" />
            </svg>
            Download
          </button>
        </div>
      )}
    </div>
  );
}

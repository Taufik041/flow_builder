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

export function CodePane({ tab, onTabChange, jsonContent, pythonContent, generating }: Props) {
  const isJson = tab === "json";
  const content = isJson ? jsonContent : pythonContent;

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
    </div>
  );
}
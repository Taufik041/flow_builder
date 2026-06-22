"use client";
import ReactMarkdown from "react-markdown";

// Flip to false later if you want the json/python blocks shown (collapsed/inline)
// in the chat bubble instead of hidden. The code already lives in the code panel
// + file chips, so hiding avoids duplication.
const HIDE_CODE_BLOCKS = true;

// Languages whose fenced blocks we strip from the chat bubble.
const HIDDEN_LANGS = new Set(["json", "python", "py"]);

interface Props {
  content: string;
}

/**
 * Renders assistant message markdown (headings, bold, lists, inline code) with
 * a warm, compact style. Fenced ```json / ```python blocks are removed before
 * rendering so the bubble shows only the prose/explanation.
 */
export function AssistantMarkdown({ content }: Props) {
  const text = HIDE_CODE_BLOCKS ? stripFencedCode(content) : content;

  return (
    <div className="assistant-md" style={{ fontSize: 14.5, lineHeight: 1.62, color: "var(--text)" }}>
      <ReactMarkdown
        components={{
          p: ({ children }) => (
            <p style={{ margin: "0 0 8px" }}>{children}</p>
          ),
          h1: ({ children }) => (
            <h1 style={{ fontSize: 16.5, fontWeight: 600, margin: "12px 0 6px" }}>{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 style={{ fontSize: 15.5, fontWeight: 600, margin: "12px 0 6px" }}>{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 style={{ fontSize: 14.5, fontWeight: 600, margin: "10px 0 5px" }}>{children}</h3>
          ),
          ul: ({ children }) => (
            <ul style={{ margin: "0 0 8px", paddingLeft: 20 }}>{children}</ul>
          ),
          ol: ({ children }) => (
            <ol style={{ margin: "0 0 8px", paddingLeft: 20 }}>{children}</ol>
          ),
          li: ({ children }) => (
            <li style={{ margin: "2px 0" }}>{children}</li>
          ),
          strong: ({ children }) => (
            <strong style={{ fontWeight: 600 }}>{children}</strong>
          ),
          a: ({ children, href }) => (
            <a href={href} target="_blank" rel="noopener noreferrer" style={{ color: "var(--accent)", textDecoration: "underline" }}>
              {children}
            </a>
          ),
          code: ({ children }) => (
            <code style={{
              fontFamily: "ui-monospace,'SF Mono',Menlo,monospace",
              fontSize: 12.5, background: "var(--surface-3)",
              padding: "1px 5px", borderRadius: 5,
            }}>
              {children}
            </code>
          ),
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}

/** Remove fenced code blocks whose language is in HIDDEN_LANGS. */
function stripFencedCode(src: string): string {
  // matches ```lang ... ``` (lang optional); drops the whole block if lang is hidden
  return src
    .replace(/```([a-zA-Z0-9]*)\n[\s\S]*?```/g, (full, lang) =>
      HIDDEN_LANGS.has((lang || "").toLowerCase()) ? "" : full
    )
    .replace(/\n{3,}/g, "\n\n") // collapse the gap left behind
    .trim();
}
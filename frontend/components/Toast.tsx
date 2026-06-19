"use client";
import { useEffect } from "react";

interface Props {
  message: string;
  kind?: "ok" | "err";
  onDismiss: () => void;
}

export function Toast({ message, kind = "ok", onDismiss }: Props) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 3500);
    return () => clearTimeout(t);
  }, [onDismiss]);

  const isErr = kind === "err";

  return (
    <div
      onClick={onDismiss}
      style={{
        position: "fixed", bottom: 24, left: "50%", transform: "translateX(-50%)",
        zIndex: 100, display: "flex", alignItems: "center", gap: 10,
        padding: "10px 16px",
        background: isErr ? "var(--redBg)" : "var(--surface)",
        border: `0.5px solid ${isErr ? "var(--redBorder)" : "var(--border2)"}`,
        borderRadius: 12,
        boxShadow: "0 4px 16px rgba(38,35,31,0.14)",
        cursor: "pointer", animation: "fade-in .2s ease",
        maxWidth: 400,
      }}
    >
      {isErr ? (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--red)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flex: "0 0 auto" }}>
          <circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" />
        </svg>
      ) : (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--green)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flex: "0 0 auto" }}>
          <path d="M20 6L9 17l-5-5" />
        </svg>
      )}
      <span style={{ fontSize: 13.5, color: isErr ? "var(--redText)" : "var(--text)", fontWeight: 500 }}>{message}</span>
    </div>
  );
}

"use client";

interface Props {
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

export function PublishModal({ onConfirm, onCancel, loading }: Props) {
  return (
    <div
      onClick={onCancel}
      style={{
        position: "fixed", inset: 0, zIndex: 50, background: "var(--overlay)",
        display: "flex", alignItems: "center", justifyContent: "center", padding: 24,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: "100%", maxWidth: 380, background: "var(--surface)",
          border: "0.5px solid var(--border)", borderRadius: 16,
          boxShadow: "0 12px 40px rgba(38,35,31,0.18)", padding: 24,
        }}
      >
        <h2 style={{ margin: "0 0 8px", fontSize: 17, fontWeight: 600, letterSpacing: "-0.01em", color: "var(--text)" }}>
          Publish this flow?
        </h2>
        <p style={{ margin: "0 0 20px", fontSize: 13.5, lineHeight: 1.55, color: "var(--text3)" }}>
          This will make the flow live at your endpoint. Are you sure?
        </p>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 8 }}>
          <button
            className="icon-btn"
            onClick={onCancel}
            disabled={loading}
            style={{
              padding: "9px 16px", border: "0.5px solid var(--border2)",
              background: "var(--surface-2)", borderRadius: 9, cursor: "pointer",
              color: "var(--text)", fontSize: 13.5, fontWeight: 500, fontFamily: "inherit",
            }}
          >
            Cancel
          </button>
          <button
            className="send-btn"
            onClick={onConfirm}
            disabled={loading}
            style={{
              padding: "9px 18px", border: "none", background: "var(--accent)",
              borderRadius: 9, cursor: loading ? "not-allowed" : "pointer",
              color: "#FFFFFF", fontSize: 13.5, fontWeight: 600, fontFamily: "inherit",
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? "Publishing…" : "Publish"}
          </button>
        </div>
      </div>
    </div>
  );
}

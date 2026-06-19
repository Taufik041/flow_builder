"use client";
import { useState } from "react";
import { Session } from "@/services/api";
import { useTheme } from "@/contexts/ThemeContext";

interface Props {
  sessions: Session[];
  currentSessionId: string | null;
  userEmail: string;
  onNewSession: () => void;
  onSelectSession: (id: string) => void;
  onRenameSession: (id: string, title: string) => void;
  onDeleteSession: (id: string) => void;
  onLogout: () => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

function FlowIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="6" cy="6" r="2.4" /><circle cx="18" cy="18" r="2.4" />
      <path d="M8 6h7a3 3 0 0 1 3 3v6.5" />
    </svg>
  );
}

function LogoutIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <path d="M16 17l5-5-5-5" /><path d="M21 12H9" />
    </svg>
  );
}

function ThemeToggleIcon({ theme }: { theme: string }) {
  return theme === "dark" ? (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </svg>
  ) : (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  );
}

function RenameModal({ session, onDone, onCancel }: { session: Session; onDone: (title: string) => void; onCancel: () => void }) {
  const [value, setValue] = useState(session.title);
  return (
    <div onClick={onCancel} style={{ position: "fixed", inset: 0, zIndex: 60, background: "var(--overlay)", display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
      <div onClick={(e) => e.stopPropagation()} style={{ width: "100%", maxWidth: 360, background: "var(--surface)", border: "0.5px solid var(--border)", borderRadius: 14, boxShadow: "0 8px 28px rgba(38,35,31,0.14)", padding: 24, display: "flex", flexDirection: "column", gap: 16 }}>
        <h2 style={{ margin: 0, fontSize: 16, fontWeight: 600, color: "var(--text)" }}>Rename session</h2>
        <input
          autoFocus
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && value.trim()) onDone(value.trim()); if (e.key === "Escape") onCancel(); }}
          style={{ border: "0.5px solid var(--border2)", borderRadius: 9, padding: "9px 12px", fontSize: 14, color: "var(--text)", background: "var(--surface)", outline: "none", width: "100%" }}
        />
        <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
          <button onClick={onCancel} style={{ padding: "8px 14px", border: "0.5px solid var(--border2)", background: "var(--surface-2)", borderRadius: 8, cursor: "pointer", color: "var(--text)", fontSize: 13, fontWeight: 500, fontFamily: "inherit" }}>Cancel</button>
          <button onClick={() => value.trim() && onDone(value.trim())} style={{ padding: "8px 16px", border: "none", background: "var(--accent)", borderRadius: 8, cursor: "pointer", color: "#fff", fontSize: 13, fontWeight: 600, fontFamily: "inherit" }}>Save</button>
        </div>
      </div>
    </div>
  );
}

export function Sidebar({
  sessions, currentSessionId, userEmail, onNewSession, onSelectSession,
  onRenameSession, onDeleteSession, onLogout, collapsed, onToggleCollapse,
}: Props) {
  const { theme, toggleTheme } = useTheme();
  const [renamingSession, setRenamingSession] = useState<Session | null>(null);
  const initial = userEmail.charAt(0).toUpperCase();

  if (collapsed) {
    return (
      <aside style={{
        width: "100%", height: "100%", flex: "1 1 0", display: "flex", flexDirection: "column",
        alignItems: "center", background: "var(--sidebar)",
        borderRight: "0.5px solid var(--border)", padding: "14px 0",
        overflow: "hidden",
      }}>
        <div style={{ width: 26, height: 26, borderRadius: 7, background: "var(--accent)", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 14 }}>
          <FlowIcon />
        </div>
        <button className="icon-btn" onClick={onToggleCollapse} title="Expand sidebar" style={{ width: 34, height: 34, display: "flex", alignItems: "center", justifyContent: "center", border: "none", background: "transparent", borderRadius: 8, cursor: "pointer", color: "var(--text3)", marginBottom: 6 }}>
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 18l6-6-6-6" /></svg>
        </button>
        <button className="icon-btn" onClick={onNewSession} title="New flow" style={{ width: 34, height: 34, display: "flex", alignItems: "center", justifyContent: "center", border: "0.5px solid var(--border)", background: "var(--surface-2)", borderRadius: 9, cursor: "pointer", color: "var(--accent)", marginBottom: 14 }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5v14M5 12h14" /></svg>
        </button>
        <div style={{ flex: "1 1 0", display: "flex", flexDirection: "column", gap: 4, alignItems: "center" }}>
          {sessions.slice(0, 8).map((s) => {
            const sel = s.id === currentSessionId;
            return (
              <div key={s.id} onClick={() => onSelectSession(s.id)} title={s.title} style={{ width: 34, height: 34, borderRadius: 9, display: "flex", alignItems: "center", justifyContent: "center", background: sel ? "var(--accentSoft)" : "transparent", color: sel ? "var(--accentText)" : "var(--text3)", fontSize: 12, fontWeight: 600, cursor: "pointer" }}>
                {s.title.charAt(0).toUpperCase()}
              </div>
            );
          })}
        </div>
        <button className="icon-btn" onClick={toggleTheme} title="Toggle theme" style={{ width: 34, height: 34, display: "flex", alignItems: "center", justifyContent: "center", border: "none", background: "transparent", borderRadius: 8, cursor: "pointer", color: "var(--text3)", marginBottom: 4 }}>
          <ThemeToggleIcon theme={theme} />
        </button>
        <button className="icon-btn" onClick={onLogout} title="Log out" style={{ width: 34, height: 34, display: "flex", alignItems: "center", justifyContent: "center", border: "none", background: "transparent", borderRadius: 8, cursor: "pointer", color: "var(--text3)" }}>
          <LogoutIcon />
        </button>
      </aside>
    );
  }

  return (
    <>
      <aside style={{
        width: "100%", height: "100%", flex: "1 1 0", display: "flex", flexDirection: "column",
        background: "var(--sidebar)", borderRight: "0.5px solid var(--border)",
      }}>
        {/* header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px 14px 6px 16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
            <div style={{ width: 26, height: 26, borderRadius: 7, background: "var(--accent)", display: "flex", alignItems: "center", justifyContent: "center", flex: "0 0 auto" }}>
              <FlowIcon />
            </div>
            <span style={{ fontSize: 14, fontWeight: 600, letterSpacing: "-0.01em" }}>Flow generator</span>
          </div>
          <button className="icon-btn" onClick={onToggleCollapse} title="Collapse sidebar" style={{ width: 28, height: 28, display: "flex", alignItems: "center", justifyContent: "center", border: "none", background: "transparent", borderRadius: 7, cursor: "pointer", color: "var(--text3)" }}>
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 18l-6-6 6-6" /></svg>
          </button>
        </div>

        {/* new flow button */}
        <div style={{ padding: "8px 12px 12px" }}>
          <button className="icon-btn" onClick={onNewSession} style={{ width: "100%", display: "flex", alignItems: "center", gap: 9, padding: "9px 12px", border: "0.5px solid var(--border)", background: "var(--surface-2)", borderRadius: 10, cursor: "pointer", color: "var(--text)", fontSize: 13.5, fontWeight: 500, fontFamily: "inherit" }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5v14M5 12h14" /></svg>
            New flow
          </button>
        </div>

        <div style={{ padding: "6px 20px 6px", fontSize: 11.5, fontWeight: 600, letterSpacing: "0.02em", color: "var(--text4)" }}>Recents</div>

        {/* session list */}
        <div className="scroll-soft" style={{ flex: "1 1 0", overflowY: "auto", padding: "2px 0 8px" }}>
          {sessions.length === 0 && (
            <div style={{ padding: "20px 20px", fontSize: 13, color: "var(--text4)" }}>No sessions yet.</div>
          )}
          {sessions.map((s) => {
            const sel = s.id === currentSessionId;
            const isPublished = s.flow_status === "published";
            return (
              <div
                key={s.id}
                className={`session-row${sel ? " selected" : ""}`}
                onClick={() => onSelectSession(s.id)}
                style={{
                  position: "relative", display: "flex", alignItems: "center", gap: 9,
                  margin: "1px 8px", padding: "8px 11px", borderRadius: 9, cursor: "pointer",
                  background: sel ? "var(--accentSoft)" : "transparent",
                }}
              >
                <div style={{ flex: "1 1 0", minWidth: 0, overflow: "hidden" }}>
                  <div style={{ fontSize: 13.5, fontWeight: 500, color: sel ? "var(--accentText)" : "var(--text)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", letterSpacing: "-0.005em" }}>
                    {s.title}
                  </div>
                </div>
                <span style={{ flex: "0 0 auto", fontSize: 11, fontWeight: 500, color: isPublished ? "var(--green)" : "var(--text4)" }}>
                  {isPublished ? "published" : "draft"}
                </span>
                <div
                  className="row-actions"
                  style={{
                    position: "absolute", right: 8, top: "50%", transform: "translateY(-50%)",
                    display: "flex", alignItems: "center", gap: 2,
                    background: sel ? "var(--accentSoft)" : "var(--sidebar)", paddingLeft: 8,
                  }}
                >
                  <button
                    className="icon-btn"
                    title="Rename"
                    onClick={(e) => { e.stopPropagation(); setRenamingSession(s); }}
                    style={{ width: 26, height: 26, display: "flex", alignItems: "center", justifyContent: "center", border: "none", background: "transparent", borderRadius: 6, cursor: "pointer", color: "var(--text3)" }}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 20h9" /><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4z" />
                    </svg>
                  </button>
                  <button
                    className="icon-btn"
                    title="Delete"
                    onClick={(e) => { e.stopPropagation(); onDeleteSession(s.id); }}
                    style={{ width: 26, height: 26, display: "flex", alignItems: "center", justifyContent: "center", border: "none", background: "transparent", borderRadius: 6, cursor: "pointer", color: "var(--text3)" }}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M3 6h18" /><path d="M8 6V4h8v2" /><path d="M6 6l1 14h10l1-14" />
                    </svg>
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* footer */}
        <div style={{ borderTop: "0.5px solid var(--border)", padding: "10px 12px", display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 28, height: 28, borderRadius: "50%", background: "var(--avatar)", display: "flex", alignItems: "center", justifyContent: "center", flex: "0 0 auto", fontSize: 12, fontWeight: 600, color: "var(--text2)" }}>
            {initial}
          </div>
          <div style={{ flex: "1 1 0", minWidth: 0 }}>
            <div style={{ fontSize: 12.5, fontWeight: 500, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{userEmail}</div>
          </div>
          <button className="icon-btn" onClick={toggleTheme} title="Toggle theme" style={{ width: 30, height: 30, display: "flex", alignItems: "center", justifyContent: "center", border: "none", background: "transparent", borderRadius: 7, cursor: "pointer", color: "var(--text3)" }}>
            <ThemeToggleIcon theme={theme} />
          </button>
          <button className="icon-btn" onClick={onLogout} title="Log out" style={{ width: 30, height: 30, display: "flex", alignItems: "center", justifyContent: "center", border: "none", background: "transparent", borderRadius: 7, cursor: "pointer", color: "var(--text3)" }}>
            <LogoutIcon />
          </button>
        </div>
      </aside>

      {renamingSession && (
        <RenameModal
          session={renamingSession}
          onDone={(title) => { onRenameSession(renamingSession.id, title); setRenamingSession(null); }}
          onCancel={() => setRenamingSession(null)}
        />
      )}
    </>
  );
}

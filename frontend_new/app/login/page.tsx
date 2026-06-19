"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { login, register } from "@/services/api";
import { ThemeProvider, useTheme } from "@/contexts/ThemeContext";

function LoginInner() {
  const router = useRouter();
  const { theme, toggleTheme } = useTheme();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit() {
    if (!email || !password) { setError("Please fill in all fields."); return; }
    setLoading(true);
    setError("");
    try {
      if (mode === "login") await login(email, password);
      else await register(email, password);
      router.push("/chat");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === "Enter") handleSubmit();
  }

  return (
    <div
      style={{
        minHeight: "100vh", width: "100%",
        background: "var(--bg)", color: "var(--text)",
        fontFamily: "inherit",
        WebkitFontSmoothing: "antialiased",
        display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center",
        padding: "40px 24px", position: "relative",
      }}
    >
      {/* theme toggle */}
      <button
        className="icon-btn"
        onClick={toggleTheme}
        title="Toggle theme"
        style={{
          position: "fixed", top: 18, right: 18,
          width: 38, height: 38,
          display: "flex", alignItems: "center", justifyContent: "center",
          border: "0.5px solid var(--border2)", background: "var(--surface)",
          borderRadius: 10, cursor: "pointer", color: "var(--text3)",
        }}
      >
        {theme === "dark" ? (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
          </svg>
        ) : (
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
          </svg>
        )}
      </button>

      {/* brand */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 26 }}>
        <div style={{
          width: 30, height: 30, borderRadius: 8, background: "var(--accent)",
          display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="6" cy="6" r="2.4" /><circle cx="18" cy="18" r="2.4" />
            <path d="M8 6h7a3 3 0 0 1 3 3v6.5" />
          </svg>
        </div>
        <span style={{ fontSize: 16, fontWeight: 600, letterSpacing: "-0.01em" }}>Flow generator</span>
      </div>

      {/* card */}
      <div style={{
        width: "100%", maxWidth: 380,
        background: "var(--surface)", border: "0.5px solid var(--border)",
        borderRadius: 16, boxShadow: "0 1px 3px rgba(61,58,52,0.05)",
        padding: "32px 32px 28px",
        display: "flex", flexDirection: "column", gap: 20,
      }}>
        {/* heading */}
        <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
          <h1 style={{ margin: 0, fontSize: 22, fontWeight: 600, letterSpacing: "-0.015em", color: "var(--text)" }}>
            {mode === "login" ? "Log in" : "Create account"}
          </h1>
          <p style={{ margin: 0, fontSize: 14, lineHeight: 1.5, color: "var(--text3)" }}>
            {mode === "login" ? "Welcome back — sign in to continue." : "Set up your account to get started."}
          </p>
        </div>

        {/* error */}
        {error && (
          <div style={{
            display: "flex", alignItems: "center", gap: 9,
            padding: "9px 12px",
            background: "var(--redBg)", border: "0.5px solid var(--redBorder)", borderRadius: 10,
          }}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--red)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flex: "0 0 auto" }}>
              <circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" />
            </svg>
            <span style={{ fontSize: 13, lineHeight: 1.4, color: "var(--redText)" }}>{error}</span>
          </div>
        )}

        {/* fields */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span style={{ fontSize: 12.5, fontWeight: 500, color: "var(--text2)" }}>Email</span>
            <input
              className="auth-input"
              type="email"
              placeholder="you@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyDown={handleKey}
              style={{
                width: "100%", border: "0.5px solid var(--border2)", borderRadius: 10,
                padding: "11px 13px", fontSize: 14, color: "var(--text)",
                background: "var(--surface)", outline: "none",
                transition: "border-color .12s ease, box-shadow .12s ease",
              }}
            />
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span style={{ fontSize: 12.5, fontWeight: 500, color: "var(--text2)" }}>Password</span>
            <input
              className="auth-input"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={handleKey}
              style={{
                width: "100%", border: "0.5px solid var(--border2)", borderRadius: 10,
                padding: "11px 13px", fontSize: 14, color: "var(--text)",
                background: "var(--surface)", outline: "none",
                transition: "border-color .12s ease, box-shadow .12s ease",
              }}
            />
          </label>
        </div>

        {/* submit */}
        <button
          className="auth-submit"
          onClick={handleSubmit}
          disabled={loading}
          style={{
            width: "100%", border: "none", background: "var(--accent)",
            color: "#FFFFFF", borderRadius: 10, padding: 12,
            fontSize: 14.5, fontWeight: 600, cursor: loading ? "not-allowed" : "pointer",
            fontFamily: "inherit", transition: "background .12s ease",
            opacity: loading ? 0.7 : 1,
          }}
        >
          {loading ? "Please wait…" : mode === "login" ? "Log in" : "Create account"}
        </button>

        {/* switch */}
        <div style={{ textAlign: "center", fontSize: 13.5, color: "var(--text3)" }}>
          {mode === "login" ? (
            <>
              Don&apos;t have an account?{" "}
              <button
                className="auth-link"
                onClick={() => { setMode("register"); setError(""); }}
                style={{
                  border: "none", background: "none", padding: "0 0 0 3px",
                  fontSize: 13.5, fontWeight: 600, color: "var(--accent)",
                  cursor: "pointer", fontFamily: "inherit", transition: "color .12s ease",
                }}
              >
                Register
              </button>
            </>
          ) : (
            <>
              Already have an account?{" "}
              <button
                className="auth-link"
                onClick={() => { setMode("login"); setError(""); }}
                style={{
                  border: "none", background: "none", padding: "0 0 0 3px",
                  fontSize: 13.5, fontWeight: 600, color: "var(--accent)",
                  cursor: "pointer", fontFamily: "inherit", transition: "color .12s ease",
                }}
              >
                Log in
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <ThemeProvider>
      <LoginInner />
    </ThemeProvider>
  );
}

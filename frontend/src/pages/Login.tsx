import { useState } from "react";
import { api } from "../api";
import type { User } from "../types";

export function Login({ onLogin }: { onLogin: (user: User) => void }) {
  const [name, setName] = useState("");
  const [role, setRole] = useState<"student" | "instructor">("student");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const user = await api.createUser(name.trim(), role);
      onLogin(user);
    } catch {
      setError("Could not reach the backend. Is it running on port 8000?");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh" }}>
      <form
        onSubmit={handleSubmit}
        style={{
          background: "var(--bg-panel)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-lg)",
          padding: "32px",
          width: 340,
          display: "flex",
          flexDirection: "column",
          gap: 14,
        }}
      >
        <div style={{ fontFamily: "var(--font-voice)", fontSize: 22 }}>Misconception feedback</div>
        <div style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 6 }}>
          Enter a name to continue. No password &mdash; this is a research prototype.
        </div>
        <input
          placeholder="Your name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          autoFocus
        />
        <div style={{ display: "flex", gap: 8 }}>
          <button
            type="button"
            className={role === "student" ? "primary" : ""}
            style={{ flex: 1 }}
            onClick={() => setRole("student")}
          >
            Student
          </button>
          <button
            type="button"
            className={role === "instructor" ? "primary" : ""}
            style={{ flex: 1 }}
            onClick={() => setRole("instructor")}
          >
            Instructor
          </button>
        </div>
        {error && <div style={{ fontSize: 12, color: "var(--amber)" }}>{error}</div>}
        <button type="submit" className="primary" disabled={busy || !name.trim()}>
          {busy ? "Continuing\u2026" : "Continue"}
        </button>
      </form>
    </div>
  );
}

import type { StudentProgress } from "../types";
import { misconceptionColor, misconceptionSoft } from "../misconceptions";

export function ProgressPanel({ progress }: { progress: StudentProgress }) {
  const coveragePct = progress.tasks_total > 0 ? Math.round((progress.tasks_attempted / progress.tasks_total) * 100) : 0;
  const masteredPct = progress.tasks_total > 0 ? Math.round((progress.tasks_mastered / progress.tasks_total) * 100) : 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        <StatCard label="Exercises attempted" value={`${progress.tasks_attempted}/${progress.tasks_total}`} pct={coveragePct} color="var(--accent-2)" />
        <StatCard label="Fully clean" value={`${progress.tasks_mastered}/${progress.tasks_total}`} pct={masteredPct} color="var(--green)" />
        <StatCard label="Submissions" value={String(progress.total_submissions)} color="var(--amber)" />
      </div>

      {progress.badges.length > 0 && (
        <div>
          <SectionLabel>Badges</SectionLabel>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {progress.badges.map((b) => (
              <span key={b.id} className="badge-pill" title={b.description}>
                {b.label}
              </span>
            ))}
          </div>
        </div>
      )}

      <div>
        <SectionLabel>Summary</SectionLabel>
        <div
          style={{
            background: "var(--bg-sunken)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-md)",
            padding: "14px 16px",
            fontSize: 13.5,
            lineHeight: 1.6,
            color: "var(--text-primary)",
          }}
        >
          {progress.ai_summary}
        </div>
      </div>

      {progress.misconceptions.length > 0 && (
        <div>
          <SectionLabel>By misconception</SectionLabel>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {progress.misconceptions.map((m) => {
              const color = misconceptionColor(m.misconception_id);
              return (
                <div
                  key={m.misconception_id}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "10px 14px",
                    borderRadius: "var(--radius-md)",
                    background: misconceptionSoft(m.misconception_id),
                    border: `1px solid ${color}33`,
                  }}
                >
                  <div>
                    <div style={{ fontSize: 13.5, fontWeight: 600, color }}>{m.misconception_name}</div>
                    <div style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 2 }}>
                      Seen {m.times_seen} time{m.times_seen === 1 ? "" : "s"}
                      {m.decay_events > 0 && (
                        <> &middot; reappeared after looking resolved ({m.decay_events})</>
                      )}
                    </div>
                  </div>
                  <span
                    style={{
                      fontSize: 11.5,
                      fontWeight: 600,
                      padding: "4px 10px",
                      borderRadius: 20,
                      background: m.resolved ? "var(--green-soft)" : "#ffffff",
                      color: m.resolved ? "var(--green)" : color,
                      border: `1px solid ${m.resolved ? "var(--green)" : color}`,
                      whiteSpace: "nowrap",
                    }}
                  >
                    {m.resolved ? "Not seen recently" : `${m.current_clean_streak} clean since`}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        fontSize: 12,
        fontWeight: 600,
        color: "var(--text-secondary)",
        marginBottom: 8,
        textTransform: "uppercase",
        letterSpacing: 0.4,
      }}
    >
      {children}
    </div>
  );
}

function StatCard({ label, value, pct, color }: { label: string; value: string; pct?: number; color: string }) {
  return (
    <div
      style={{
        flex: "1 1 140px",
        background: "var(--bg-panel)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-md)",
        padding: "14px 16px",
      }}
    >
      <div style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 600, color: "var(--text-primary)", marginBottom: pct != null ? 8 : 0 }}>
        {value}
      </div>
      {pct != null && (
        <div style={{ height: 6, borderRadius: 4, background: "var(--bg-sunken)", overflow: "hidden" }}>
          <div style={{ height: "100%", width: `${pct}%`, background: color, borderRadius: 4 }} />
        </div>
      )}
    </div>
  );
}

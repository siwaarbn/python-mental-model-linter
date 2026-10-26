import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { api } from "../api";
import type { ClassAnalytics, User, StudentSummary, StudentProgress, HinweisItem } from "../types";
import { ProgressPanel } from "../components/ProgressPanel";

type View = "analytics" | "students";

export function InstructorDashboard({ user }: { user: User }) {
  const [view, setView] = useState<View>("analytics");
  const [data, setData] = useState<ClassAnalytics | null>(null);
  const [selectedTask, setSelectedTask] = useState<string | "all">("all");

  const [students, setStudents] = useState<StudentSummary[]>([]);
  const [selectedStudentId, setSelectedStudentId] = useState<number | null>(null);
  const [studentProgress, setStudentProgress] = useState<StudentProgress | null>(null);

  const [hinweise, setHinweise] = useState<HinweisItem[]>([]);
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

  useEffect(() => {
    api.instructorAnalytics().then(setData);
    api.instructorStudents().then(setStudents);
    api.instructorHinweise().then(setHinweise).catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedStudentId == null) {
      setStudentProgress(null);
      return;
    }
    api.instructorStudentProgress(selectedStudentId).then(setStudentProgress).catch(() => {});
  }, [selectedStudentId]);

  const visibleHinweise = hinweise.filter((h) => !dismissed.has(h.id));

  if (!data) {
    return <div style={{ padding: 28 }}>Loading analytics&hellip;</div>;
  }

  const chartData =
    selectedTask === "all"
      ? data.misconceptions
      : data.by_task.find((t) => t.task_id === selectedTask)?.misconceptions ?? [];

  return (
    <div style={{ padding: "24px 32px", display: "flex", flexDirection: "column", gap: 20, maxWidth: 980, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <span style={{ fontFamily: "var(--font-voice)", fontSize: 22 }}>Instructor dashboard</span>
        <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>{user.display_name}</span>
      </div>

      {visibleHinweise.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {visibleHinweise.map((h) => (
            <HinweisCard key={h.id} item={h} onDismiss={() => setDismissed((prev) => new Set(prev).add(h.id))} />
          ))}
        </div>
      )}

      <div style={{ display: "flex", gap: 8 }}>
        <button className={view === "analytics" ? "primary" : ""} onClick={() => setView("analytics")}>
          Class analytics
        </button>
        <button className={view === "students" ? "primary" : ""} onClick={() => setView("students")}>
          Students
        </button>
      </div>

      {view === "analytics" && (
        <>
          <div style={{ display: "flex", gap: 12 }}>
            <MetricCard label="Students" value={data.total_students} color="var(--accent-2)" />
            <MetricCard label="Submissions" value={data.total_submissions} color="var(--amber)" />
            <MetricCard label="Distinct misconceptions seen" value={data.misconceptions.length} color="var(--pink)" />
          </div>

          <div
            style={{
              background: "var(--bg-panel)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-lg)",
              padding: "18px 20px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
              <span style={{ fontFamily: "var(--font-voice)", fontSize: 16 }}>Misconception frequency</span>
              <select value={selectedTask} onChange={(e) => setSelectedTask(e.target.value)}>
                <option value="all">All tasks</option>
                {data.by_task.map((t) => (
                  <option key={t.task_id} value={t.task_id}>
                    {t.task_id} &middot; {t.task_title}
                  </option>
                ))}
              </select>
            </div>

            {chartData.length === 0 ? (
              <div style={{ fontSize: 13, color: "var(--text-muted)" }}>No findings recorded yet.</div>
            ) : (
              <ResponsiveContainer width="100%" height={Math.max(160, chartData.length * 40)}>
                <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 24 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                  <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12, fill: "var(--text-secondary)" }} />
                  <YAxis
                    type="category"
                    dataKey="misconception_id"
                    width={40}
                    tick={{ fontSize: 12, fill: "var(--text-secondary)" }}
                  />
                  <Tooltip
                    formatter={((value: number, _name: unknown, props: { payload: { student_count: number; misconception_name: string } }) => [
                      `${value} occurrence${value === 1 ? "" : "s"} \u00b7 ${props.payload.student_count} student${
                        props.payload.student_count === 1 ? "" : "s"
                      }`,
                      props.payload.misconception_name,
                    ]) as never}
                  />
                  <Bar dataKey="count" fill="#7c3fd4" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          <div
            style={{
              background: "var(--bg-panel)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-lg)",
              padding: "18px 20px",
            }}
          >
            <div style={{ fontFamily: "var(--font-voice)", fontSize: 16, marginBottom: 12 }}>By task</div>
            <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ textAlign: "left", color: "var(--text-secondary)", borderBottom: "1px solid var(--border)" }}>
                  <th style={{ padding: "6px 4px" }}>Task</th>
                  <th style={{ padding: "6px 4px" }}>Submissions</th>
                  <th style={{ padding: "6px 4px" }}>Top misconception</th>
                </tr>
              </thead>
              <tbody>
                {data.by_task.map((t) => (
                  <tr key={t.task_id} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ padding: "8px 4px" }}>{t.task_id} &middot; {t.task_title}</td>
                    <td style={{ padding: "8px 4px" }}>{t.submission_count}</td>
                    <td style={{ padding: "8px 4px" }}>
                      {t.misconceptions[0]
                        ? `${t.misconceptions[0].misconception_name} (${t.misconceptions[0].count})`
                        : "\u2014"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {view === "students" && (
        <div style={{ display: "grid", gridTemplateColumns: "260px 1fr", gap: 16 }}>
          <div
            style={{
              background: "var(--bg-panel)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-lg)",
              padding: "12px",
              display: "flex",
              flexDirection: "column",
              gap: 6,
              maxHeight: 560,
              overflowY: "auto",
            }}
          >
            {students.length === 0 && <div style={{ fontSize: 13, color: "var(--text-muted)", padding: 8 }}>No students yet.</div>}
            {students.map((s) => (
              <button
                key={s.user_id}
                onClick={() => setSelectedStudentId(s.user_id)}
                className={selectedStudentId === s.user_id ? "primary" : ""}
                style={{ textAlign: "left", display: "flex", flexDirection: "column", gap: 3, height: "auto", padding: "10px 12px" }}
              >
                <span style={{ fontSize: 13.5, fontWeight: 500 }}>{s.display_name}</span>
                <span style={{ fontSize: 11.5, opacity: 0.85 }}>
                  {s.tasks_attempted}/{s.tasks_total} attempted &middot; {s.tasks_mastered} clean
                </span>
              </button>
            ))}
          </div>

          <div
            style={{
              background: "var(--bg-panel)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-lg)",
              padding: "20px 22px",
            }}
          >
            {selectedStudentId == null ? (
              <div style={{ fontSize: 13, color: "var(--text-muted)" }}>Select a student to see their progress.</div>
            ) : studentProgress ? (
              <ProgressPanel progress={studentProgress} />
            ) : (
              <div style={{ fontSize: 13, color: "var(--text-muted)" }}>Loading&hellip;</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function HinweisCard({ item, onDismiss }: { item: HinweisItem; onDismiss: () => void }) {
  const isReteach = item.type === "reteach";
  const accent = isReteach ? "var(--amber)" : "var(--green)";
  const soft = isReteach ? "var(--amber-soft)" : "var(--green-soft)";

  return (
    <div
      className="pop-in"
      style={{
        background: soft,
        border: `1.5px solid ${accent}`,
        borderRadius: "var(--radius-md)",
        padding: "14px 16px",
        display: "flex",
        justifyContent: "space-between",
        gap: 16,
      }}
    >
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
          <span
            style={{
              fontSize: 10.5,
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: 0.5,
              color: accent,
              background: "#ffffff",
              padding: "2px 8px",
              borderRadius: 10,
            }}
          >
            {isReteach ? "Suggestion \u00b7 Reteach" : "Suggestion \u00b7 Extend"}
          </span>
        </div>
        <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", marginBottom: 4 }}>{item.title}</div>
        <div style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 6 }}>{item.message}</div>
        <div style={{ fontSize: 13, color: "var(--text-primary)" }}>{item.suggestion}</div>
      </div>
      <button onClick={onDismiss} style={{ alignSelf: "flex-start", fontSize: 11, padding: "4px 10px", flexShrink: 0 }}>
        Dismiss
      </button>
    </div>
  );
}

function MetricCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div
      style={{
        background: "var(--bg-sunken)",
        borderRadius: "var(--radius-md)",
        padding: "14px 18px",
        minWidth: 140,
        borderTop: `3px solid ${color}`,
      }}
    >
      <div style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 500 }}>{value}</div>
    </div>
  );
}
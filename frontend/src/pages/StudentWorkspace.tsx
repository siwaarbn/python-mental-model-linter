import { useEffect, useState } from "react";
import { api } from "../api";
import type { Task, User, FeedbackCard, SubmissionHistoryItem, StudentProgress } from "../types";
import { CodeEditor } from "../components/CodeEditor";
import { FeedbackPanel } from "../components/FeedbackPanel";
import { ProgressPanel } from "../components/ProgressPanel";

type Panel = "workspace" | "history" | "progress";

export function StudentWorkspace({
  user,
  initialTask,
  onBackToOverview,
}: {
  user: User;
  initialTask: Task;
  onBackToOverview: () => void;
}) {
  const [tasks, setTasks] = useState<Task[]>([initialTask]);
  const [activeTaskId, setActiveTaskId] = useState<string>(initialTask.id);
  const [code, setCode] = useState(initialTask.starter_code);
  const [findings, setFindings] = useState<FeedbackCard[]>([]);
  const [parseError, setParseError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<SubmissionHistoryItem[]>([]);
  const [panel, setPanel] = useState<Panel>("workspace");
  const [progress, setProgress] = useState<StudentProgress | null>(null);
  const [hasRun, setHasRun] = useState(false);

  useEffect(() => {
    api.listTasks().then(setTasks);
    refreshHistory();
  }, []);

  function selectTask(task: Task) {
    setActiveTaskId(task.id);
    setCode(task.starter_code);
    setFindings([]);
    setParseError(null);
    setHasRun(false);
  }

  function refreshHistory() {
    api.history(user.id).then(setHistory).catch(() => {});
  }

  function openPanel(next: Panel) {
    setPanel(next);
    if (next === "progress") {
      api.progress(user.id).then(setProgress).catch(() => {});
    }
  }

  async function handleRun() {
    if (!activeTaskId) return;
    setLoading(true);
    try {
      const result = await api.submit(user.id, activeTaskId, code);
      setFindings(result.findings);
      setParseError(result.parse_error);
      setHasRun(true);
      refreshHistory();
    } catch (e) {
      setParseError(e instanceof Error ? e.message : "Submission failed.");
      setHasRun(true);
    } finally {
      setLoading(false);
    }
  }

  async function loadPastSubmission(id: number) {
    const detail = await api.submissionDetail(id);
    setActiveTaskId(detail.task_id);
    setCode(detail.source_code);
    setFindings(detail.findings);
    setParseError(detail.parse_error);
    setHasRun(true);
    setPanel("workspace");
  }

  const activeTask = tasks.find((t) => t.id === activeTaskId) ?? initialTask;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", padding: "20px 28px", gap: 14 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <button onClick={onBackToOverview} style={{ fontSize: 12 }}>
            &larr; All tasks
          </button>
          <select
            value={activeTaskId}
            onChange={(e) => {
              const t = tasks.find((t) => t.id === e.target.value);
              if (t) selectTask(t);
            }}
          >
            {tasks.map((t) => (
              <option key={t.id} value={t.id}>
                {t.title}
              </option>
            ))}
          </select>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>{user.display_name}</span>
          <button onClick={() => openPanel(panel === "progress" ? "workspace" : "progress")}>
            {panel === "progress" ? "Back to workspace" : "My progress"}
          </button>
          <button onClick={() => openPanel(panel === "history" ? "workspace" : "history")}>
            {panel === "history" ? "Hide history" : "Submission history"}
          </button>
        </div>
      </div>

      {panel === "workspace" && activeTask && (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <div
            style={{
              background: "var(--pink-soft)",
              border: "1.5px solid var(--pink)",
              borderRadius: "var(--radius-lg)",
              padding: "14px 18px",
            }}
          >
            <div style={{ fontSize: 11, fontWeight: 700, color: "var(--pink)", marginBottom: 4, textTransform: "uppercase", letterSpacing: 0.5 }}>
              Task
            </div>
            <div style={{ fontSize: 14, color: "var(--text-primary)", lineHeight: 1.55 }}>{activeTask.prompt}</div>
          </div>
          {activeTask.example && (
            <div
              style={{
                background: "var(--accent-2-soft)",
                border: "1px solid var(--accent-2)",
                borderRadius: "var(--radius-md)",
                padding: "10px 16px",
              }}
            >
              <div style={{ fontSize: 11, fontWeight: 600, color: "var(--accent-2)", marginBottom: 3, textTransform: "uppercase", letterSpacing: 0.4 }}>
                Example
              </div>
              <div style={{ fontSize: 13.5, color: "var(--text-primary)", lineHeight: 1.5 }}>{activeTask.example}</div>
            </div>
          )}
        </div>
      )}

      {panel === "history" && (
        <div
          style={{
            background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)",
            padding: "16px 20px", flex: 1, overflowY: "auto",
          }}
        >
          <div style={{ fontFamily: "var(--font-voice)", fontSize: 16, marginBottom: 10 }}>Your submissions</div>
          {history.length === 0 && <div style={{ fontSize: 13, color: "var(--text-muted)" }}>No submissions yet.</div>}
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {history.map((h) => (
              <button
                key={h.id}
                onClick={() => loadPastSubmission(h.id)}
                style={{ display: "flex", justifyContent: "space-between", textAlign: "left", fontSize: 13, fontWeight: 400 }}
              >
                <span>{h.task_id} &middot; {new Date(h.submitted_at).toLocaleString()}</span>
                <span style={{ color: "var(--text-muted)" }}>
                  {h.parse_error ? "parse error" : `${h.finding_count} finding${h.finding_count === 1 ? "" : "s"}`}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      {panel === "progress" && (
        <div
          style={{
            background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)",
            padding: "20px 22px", flex: 1, overflowY: "auto",
          }}
        >
          <div style={{ fontFamily: "var(--font-voice)", fontSize: 16, marginBottom: 14 }}>Your progress</div>
          {progress ? <ProgressPanel progress={progress} /> : <div style={{ fontSize: 13, color: "var(--text-muted)" }}>Loading&hellip;</div>}
        </div>
      )}

      {panel === "workspace" && (
        <div style={{ display: "grid", gridTemplateColumns: "1.15fr 0.85fr", gap: 16, flex: 1, minHeight: 0, height: 0 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 10, minHeight: 0, height: "100%" }}>
            <div style={{ flex: 1, minHeight: 0 }}>
              <CodeEditor
                value={code}
                onChange={(v) => {
                  setCode(v);
                  if (hasRun) setHasRun(false);
                }}
              />
            </div>
            <button className="primary" onClick={handleRun} disabled={loading || !activeTaskId} style={{ alignSelf: "flex-start", flexShrink: 0 }}>
              {loading ? "Running\u2026" : "Run analysis"}
            </button>
          </div>
          <div style={{ minHeight: 0, height: "100%" }}>
            <FeedbackPanel
              findings={findings}
              parseError={parseError}
              loading={loading}
              hasRun={hasRun}
              sourceCode={code}
              exampleTests={activeTask?.example_tests ?? ""}
            />
          </div>
        </div>
      )}
    </div>
  );
}

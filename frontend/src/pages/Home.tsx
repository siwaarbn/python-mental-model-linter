import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import type { Task, User } from "../types";
import { ALL_MISCONCEPTION_IDS, misconceptionColor, misconceptionLabel, misconceptionSoft } from "../misconceptions";

export function Home({ user, onSelectTask }: { user: User; onSelectTask: (task: Task) => void }) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [activeCategories, setActiveCategories] = useState<Set<string>>(new Set());

  useEffect(() => {
    api.listTasks().then(setTasks);
  }, []);

  const categoriesPresent = useMemo(
    () =>
      ALL_MISCONCEPTION_IDS.filter((id) =>
        tasks.some((t) => t.target_misconceptions.split(",").map((m) => m.trim()).includes(id))
      ),
    [tasks]
  );

  function toggleCategory(id: string) {
    setActiveCategories((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  const filteredTasks =
    activeCategories.size === 0
      ? tasks
      : tasks.filter((t) =>
          t.target_misconceptions
            .split(",")
            .map((m) => m.trim())
            .some((m) => activeCategories.has(m))
        );

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "40px 28px 60px" }}>
      <div className="hero-banner" style={{ marginBottom: 28 }}>
        <div style={{ fontFamily: "var(--font-voice)", fontSize: 30, marginBottom: 8 }}>
          Welcome, {user.display_name}
        </div>
        <div style={{ fontSize: 14.5, opacity: 0.92, maxWidth: 560, lineHeight: 1.55 }}>
          Pick a task below to start. Write your solution, run it, and you'll get feedback
          on your code &mdash; step by step, not all at once.
        </div>
      </div>

      {categoriesPresent.length > 0 && (
        <div style={{ marginBottom: 22 }}>
          <div
            style={{
              fontSize: 12.5,
              fontWeight: 600,
              color: "var(--text-secondary)",
              marginBottom: 10,
              textTransform: "uppercase",
              letterSpacing: 0.4,
            }}
          >
            Filter by topic
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {activeCategories.size > 0 && (
              <button className="chip" onClick={() => setActiveCategories(new Set())} style={{ borderStyle: "dashed" }}>
                Clear filters &times;
              </button>
            )}
            {categoriesPresent.map((id) => {
              const active = activeCategories.has(id);
              return (
                <button
                  key={id}
                  className={`chip${active ? " active" : ""}`}
                  onClick={() => toggleCategory(id)}
                  style={
                    active
                      ? { background: misconceptionColor(id) }
                      : { color: misconceptionColor(id), borderColor: misconceptionColor(id) }
                  }
                >
                  {misconceptionLabel(id)}
                </button>
              );
            })}
          </div>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {filteredTasks.map((task) => {
          const primaryMisconception = task.target_misconceptions.split(",")[0]?.trim() ?? "";
          const accent = misconceptionColor(primaryMisconception);
          return (
            <button
              key={task.id}
              className="task-card pop-in"
              onClick={() => onSelectTask(task)}
              style={{ "--card-accent": accent } as React.CSSProperties}
            >
              <div style={{ display: "flex", flexDirection: "column", gap: 6, maxWidth: 620 }}>
                <div style={{ fontFamily: "var(--font-voice)", fontSize: 17, color: "var(--text-primary)" }}>
                  {task.title}
                </div>
                <div style={{ fontSize: 13.5, color: "var(--text-secondary)", lineHeight: 1.5 }}>{task.prompt}</div>
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, justifyContent: "flex-end", marginLeft: 16 }}>
                {task.target_misconceptions.split(",").map((m) => {
                  const id = m.trim();
                  return (
                    <span
                      key={id}
                      style={{
                        fontSize: 11.5,
                        fontWeight: 600,
                        color: misconceptionColor(id),
                        background: misconceptionSoft(id),
                        padding: "4px 10px",
                        borderRadius: 20,
                        whiteSpace: "nowrap",
                      }}
                    >
                      {misconceptionLabel(id)}
                    </span>
                  );
                })}
              </div>
            </button>
          );
        })}
        {tasks.length === 0 && <div style={{ fontSize: 13, color: "var(--text-muted)" }}>Loading tasks&hellip;</div>}
        {tasks.length > 0 && filteredTasks.length === 0 && (
          <div style={{ fontSize: 13, color: "var(--text-muted)" }}>No tasks match the selected topics.</div>
        )}
      </div>
    </div>
  );
}

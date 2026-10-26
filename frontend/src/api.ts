import type {
  User,
  Task,
  SubmissionResult,
  SubmissionHistoryItem,
  SubmissionDetail,
  ClassAnalytics,
  StudentProgress,
  StudentSummary,
  SuggestionItem,
} from "./types";

const BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${detail}`);
  }
  return res.json();
}

export const api = {
  health: () => request<{ status: string }>("/api/health"),

  createUser: (display_name: string, role: "student" | "instructor" = "student") =>
    request<User>("/api/users", {
      method: "POST",
      body: JSON.stringify({ display_name, role }),
    }),

  listTasks: () => request<Task[]>("/api/tasks"),

  submit: (user_id: number, task_id: string, source_code: string) =>
    request<SubmissionResult>("/api/submissions", {
      method: "POST",
      body: JSON.stringify({ user_id, task_id, source_code }),
    }),

  history: (userId: number) =>
    request<SubmissionHistoryItem[]>(`/api/users/${userId}/submissions`),

  submissionDetail: (id: number) => request<SubmissionDetail>(`/api/submissions/${id}`),

  instructorAnalytics: () => request<ClassAnalytics>("/api/instructor/analytics"),

  progress: (userId: number) => request<StudentProgress>(`/api/users/${userId}/progress`),

  instructorStudents: () => request<StudentSummary[]>("/api/instructor/students"),

  instructorStudentProgress: (userId: number) =>
    request<StudentProgress>(`/api/instructor/students/${userId}/progress`),

  instructorSuggestions: () => request<SuggestionItem[]>("/api/instructor/suggestions"),
};

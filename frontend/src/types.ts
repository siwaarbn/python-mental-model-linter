export interface User {
  id: number;
  display_name: string;
  role: "student" | "instructor";
}

export interface Task {
  id: string;
  title: string;
  prompt: string;
  example: string;
  starter_code: string;
  target_misconceptions: string;
  example_tests: string;
}

export interface FeedbackCard {
  rule_id: string;
  misconception_id: string;
  misconception_name: string;
  severity: number;
  line: number | null;
  column: number | null;
  confidence: string | null;
  layer1_observation: string;
  layer2_conceptual_explanation: string;
  layer3_mental_model_correction: string;
  layer4_reflection_prompt: string;
}

export interface SubmissionResult {
  submission_id: number;
  parse_error: string | null;
  findings: FeedbackCard[];
}

export interface SubmissionHistoryItem {
  id: number;
  task_id: string;
  submitted_at: string;
  parse_error: string | null;
  finding_count: number;
}

export interface SubmissionDetail {
  id: number;
  task_id: string;
  submitted_at: string;
  source_code: string;
  parse_error: string | null;
  findings: FeedbackCard[];
}

export interface MisconceptionFrequency {
  misconception_id: string;
  misconception_name: string;
  count: number;
  student_count: number;
}

export interface TaskAnalytics {
  task_id: string;
  task_title: string;
  submission_count: number;
  misconceptions: MisconceptionFrequency[];
}

export interface ClassAnalytics {
  total_students: number;
  total_submissions: number;
  misconceptions: MisconceptionFrequency[];
  by_task: TaskAnalytics[];
}

// --- Progress / streaks / decay --------------------------------------------

export interface Badge {
  id: string;
  label: string;
  description: string;
}

export interface MisconceptionProgress {
  misconception_id: string;
  misconception_name: string;
  times_seen: number;
  current_clean_streak: number;
  resolved: boolean;
  decay_events: number;
}

export interface StudentProgress {
  user_id: number;
  display_name: string;
  tasks_total: number;
  tasks_attempted: number;
  tasks_mastered: number;
  total_submissions: number;
  clean_submissions: number;
  badges: Badge[];
  misconceptions: MisconceptionProgress[];
  ai_summary: string;
  ai_summary_source: "model" | "heuristic";
}

export interface StudentSummary {
  user_id: number;
  display_name: string;
  tasks_attempted: number;
  tasks_total: number;
  tasks_mastered: number;
  total_submissions: number;
  last_active: string | null;
}

export interface HinweisItem {
  id: string;
  type: "reteach" | "extend";
  misconception_id: string | null;
  misconception_name: string | null;
  title: string;
  message: string;
  suggestion: string;
  affected_count: number;
}
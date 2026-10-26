from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    display_name: str
    role: str = "student"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    display_name: str
    role: str


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    prompt: str
    example: str
    starter_code: str
    target_misconceptions: str
    example_tests: str


class FeedbackCardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    rule_id: str
    misconception_id: str
    misconception_name: str
    severity: int
    line: Optional[int] = None
    column: Optional[int] = None
    confidence: Optional[str] = None
    layer1_observation: str
    layer2_conceptual_explanation: str
    layer3_mental_model_correction: str
    layer4_reflection_prompt: str


class SubmissionCreate(BaseModel):
    user_id: int
    task_id: str
    source_code: str


class SubmissionResult(BaseModel):
    submission_id: int
    parse_error: Optional[str] = None
    findings: list[FeedbackCardOut] = []


class SubmissionHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    task_id: str
    submitted_at: datetime
    parse_error: Optional[str] = None
    finding_count: int


class SubmissionDetail(BaseModel):
    id: int
    task_id: str
    submitted_at: datetime
    source_code: str
    parse_error: Optional[str] = None
    findings: list[FeedbackCardOut] = []


class MisconceptionFrequency(BaseModel):
    misconception_id: str
    misconception_name: str
    count: int
    student_count: int


class TaskAnalytics(BaseModel):
    task_id: str
    task_title: str
    submission_count: int
    misconceptions: list[MisconceptionFrequency]


class ClassAnalytics(BaseModel):
    total_students: int
    total_submissions: int
    misconceptions: list[MisconceptionFrequency]
    by_task: list[TaskAnalytics]


# --- Progress / streaks / decay tracking -----------------------------------
# Everything here is computed on the fly from existing Submission/Finding
# rows -- no schema migration needed. See app/services/progress_service.py
# for the aggregation logic and the reasoning behind each metric.

class Badge(BaseModel):
    id: str
    label: str
    description: str


class MisconceptionProgress(BaseModel):
    misconception_id: str
    misconception_name: str
    times_seen: int
    # Submissions made since this misconception last appeared, with none of
    # them showing it again. Private, self-referenced -- never compared to
    # other students.
    current_clean_streak: int
    # True once current_clean_streak has crossed a small threshold. Used to
    # decide whether this shows up as "mastered" vs. "still emerging".
    resolved: bool
    # A "decay" event: the misconception went quiet for a while (student
    # looked like they'd corrected it) and then reappeared later. This is
    # the durable-vs-superficial-correction signal from Sorva's mental model
    # work -- it's arguably more pedagogically interesting than raw frequency.
    decay_events: int


class StudentProgress(BaseModel):
    user_id: int
    display_name: str
    tasks_total: int
    tasks_attempted: int
    tasks_mastered: int  # at least one clean (zero-finding, no parse error) submission
    total_submissions: int
    clean_submissions: int
    badges: list[Badge]
    misconceptions: list[MisconceptionProgress]
    ai_summary: str
    ai_summary_source: str  # "model" if a real LLM call produced it, "heuristic" otherwise


class StudentSummary(BaseModel):
    user_id: int
    display_name: str
    tasks_attempted: int
    tasks_total: int
    tasks_mastered: int
    total_submissions: int
    last_active: Optional[datetime] = None


class SuggestionItem(BaseModel):
    id: str
    type: str  # "reteach" (misconception is widespread) | "extend" (student(s) ready to go further)
    misconception_id: Optional[str] = None
    misconception_name: Optional[str] = None
    title: str
    message: str
    suggestion: str
    affected_count: int  # students (reteach) or the single student (extend)
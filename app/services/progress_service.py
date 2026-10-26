"""
Progress, streak, and decay-tracking engine.

Deliberately computed on the fly from Submission/Finding rows rather than
stored -- there is no new DB table here, so nothing needs migrating and the
numbers are always consistent with the raw findings. The one thing this
module intentionally does NOT do is compare students to each other: every
metric here is self-referenced (a student's own history), so streaks stay
private and there is no leaderboard.

Three ideas this module encodes:

1. Coverage/effort, not just correctness. `tasks_attempted` and the
   `attempted_all_tasks` badge reward trying every exercise, independent of
   whether any individual attempt was clean. This is the guard against
   rewarding only students who were already strong.

2. Private streaks. `current_clean_streak` per misconception counts
   consecutive submissions (most recent first) since that misconception was
   last observed. It is never shown ranked against other students.

3. Decay detection. A misconception can look "resolved" (goes quiet for a
   couple of submissions) and then reappear later. That reappearance is a
   `decay_event` -- pedagogically the more interesting signal than raw
   frequency, since it distinguishes durable correction from a mental model
   that only looked fixed (Sorva's framing, which the four-layer feedback
   design already leans on).
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app import models, schemas

# How many consecutive clean submissions (since a misconception last showed
# up) before we call it "resolved" rather than just "not seen yet again".
RESOLVED_THRESHOLD = 2

# How many submissions have to sit between two occurrences of the same
# misconception before the second occurrence counts as a "decay" event
# rather than just the tail end of the same struggle.
DECAY_GAP_THRESHOLD = 2


@dataclass
class _SubmissionRecord:
    id: int
    task_id: str
    submitted_at: datetime
    is_clean: bool  # no parse error AND zero findings
    misconception_ids: set[str]


def _load_submission_records(submissions: list[models.Submission]) -> list[_SubmissionRecord]:
    records = [
        _SubmissionRecord(
            id=s.id,
            task_id=s.task_id,
            submitted_at=s.submitted_at,
            is_clean=(s.parse_error is None and len(s.findings) == 0),
            misconception_ids={f.misconception_id for f in s.findings},
        )
        for s in submissions
    ]
    records.sort(key=lambda r: (r.submitted_at, r.id))
    return records


def _misconception_progress(records: list[_SubmissionRecord], names: dict[str, str]) -> list[schemas.MisconceptionProgress]:
    all_ids = sorted({mid for r in records for mid in r.misconception_ids})
    results = []

    for mid in all_ids:
        seen_indices = [i for i, r in enumerate(records) if mid in r.misconception_ids]
        times_seen = len(seen_indices)

        decay_events = 0
        for a, b in zip(seen_indices, seen_indices[1:]):
            gap = b - a - 1
            if gap >= DECAY_GAP_THRESHOLD:
                decay_events += 1

        last_seen = seen_indices[-1]
        clean_since = len(records) - 1 - last_seen
        results.append(
            schemas.MisconceptionProgress(
                misconception_id=mid,
                misconception_name=names.get(mid, mid),
                times_seen=times_seen,
                current_clean_streak=clean_since,
                resolved=clean_since >= RESOLVED_THRESHOLD,
                decay_events=decay_events,
            )
        )

    return sorted(results, key=lambda m: m.misconception_id)


def _best_overall_clean_streak(records: list[_SubmissionRecord]) -> int:
    best = current = 0
    for r in records:
        if r.is_clean:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def _compute_badges(
    tasks_attempted: int,
    tasks_total: int,
    tasks_mastered: int,
    best_clean_streak: int,
    misconceptions: list[schemas.MisconceptionProgress],
) -> list[schemas.Badge]:
    badges: list[schemas.Badge] = []

    if tasks_attempted > 0:
        badges.append(schemas.Badge(
            id="first_attempt",
            label="Getting started",
            description="Submitted your first solution.",
        ))

    # Effort/coverage badge -- awarded for attempting every task, regardless
    # of whether each attempt was clean. Kept deliberately separate from any
    # "mastered everything" badge below.
    if tasks_total > 0 and tasks_attempted >= tasks_total:
        badges.append(schemas.Badge(
            id="full_coverage",
            label="Full coverage",
            description=f"Attempted all {tasks_total} exercises.",
        ))

    if tasks_total > 0 and tasks_mastered >= tasks_total:
        badges.append(schemas.Badge(
            id="all_mastered",
            label="Clean sweep",
            description="Every exercise has at least one submission with no misconceptions flagged.",
        ))

    for threshold, badge_id, label in ((3, "streak_3", "On a roll"), (5, "streak_5", "In the zone")):
        if best_clean_streak >= threshold:
            badges.append(schemas.Badge(
                id=badge_id,
                label=label,
                description=f"{threshold} clean submissions in a row at some point.",
            ))

    resolved_count = sum(1 for m in misconceptions if m.resolved)
    if resolved_count >= 1:
        plural = "misconception" if resolved_count == 1 else "misconceptions"
        badges.append(schemas.Badge(
            id="resolved_misconceptions",
            label="Correcting course",
            description=f"{resolved_count} {plural} no longer showing up in recent submissions.",
        ))

    return badges


def _generate_heuristic_summary(
    display_name: str,
    misconceptions: list[schemas.MisconceptionProgress],
    tasks_attempted: int,
    tasks_total: int,
    tasks_mastered: int,
) -> str:
    """
    Deterministic fallback summary -- used whenever a real model call isn't
    configured (see generate_ai_summary below).
    """
    if tasks_attempted == 0:
        return f"{display_name} hasn't submitted anything yet."

    resolved = [m for m in misconceptions if m.resolved]
    active = [m for m in misconceptions if not m.resolved]
    decaying = [m for m in misconceptions if m.decay_events > 0]

    parts = []
    parts.append(f"Attempted {tasks_attempted} of {tasks_total} exercises, with {tasks_mastered} fully clean.")

    if resolved:
        names = ", ".join(m.misconception_name for m in resolved[:3])
        parts.append(f"Recent submissions no longer show: {names}.")

    if active:
        top = sorted(active, key=lambda m: m.times_seen, reverse=True)[0]
        parts.append(
            f"Still recurring: {top.misconception_name} (seen {top.times_seen}x) -- "
            f"worth another look at this pattern specifically."
        )

    if decaying:
        names = ", ".join(m.misconception_name for m in decaying[:2])
        parts.append(
            f"Note: {names} went quiet for a while but came back later -- "
            f"this suggests the underlying mental model may not be fully settled yet, "
            f"even though it looked resolved for a stretch."
        )

    if not active and tasks_mastered >= tasks_total and tasks_total > 0:
        parts.append("No open misconceptions and full coverage -- ready for a harder extension exercise.")

    return " ".join(parts)


def generate_ai_summary(
    display_name: str,
    misconceptions: list[schemas.MisconceptionProgress],
    tasks_attempted: int,
    tasks_total: int,
    tasks_mastered: int,
) -> tuple[str, str]:
    """
    Returns (summary_text, source) where source is "model" or "heuristic".

    Tries a real Claude API call ONLY if ANTHROPIC_API_KEY is set in the
    environment; otherwise falls back to the deterministic summary above.
    Intentionally sends only the aggregated numbers below -- never raw
    source code -- to keep the prompt small and avoid shipping student code
    to a third party unnecessarily.
    """
    import os

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _generate_heuristic_summary(display_name, misconceptions, tasks_attempted, tasks_total, tasks_mastered), "heuristic"

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        misconception_lines = "\n".join(
            f"- {m.misconception_name}: seen {m.times_seen}x, "
            f"{'resolved' if m.resolved else 'still active'}, "
            f"{m.decay_events} decay event(s)"
            for m in misconceptions
        ) or "- none recorded"

        prompt = (
            f"You are giving a short, encouraging progress note to a programming student "
            f"named {display_name}. Facts:\n"
            f"- Attempted {tasks_attempted} of {tasks_total} exercises, {tasks_mastered} fully clean.\n"
            f"- Misconceptions:\n{misconception_lines}\n\n"
            f"Write 3-4 sentences: (1) what they've mastered, (2) what to focus on next, "
            f"(3) if nothing is active and coverage is full, suggest building on it further. "
            f"Plain language, no jargon, second person, no headers or bullet points."
        )

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in response.content if block.type == "text").strip()
        if text:
            return text, "model"
    except Exception:
        # Any failure (missing package, network, bad key, etc.) falls back
        # silently to the heuristic summary -- progress data should never
        # 500 just because the AI layer is unavailable.
        pass

    return _generate_heuristic_summary(display_name, misconceptions, tasks_attempted, tasks_total, tasks_mastered), "heuristic"


def compute_student_progress(
    user: models.User,
    submissions: list[models.Submission],
    total_task_count: int,
) -> schemas.StudentProgress:
    records = _load_submission_records(submissions)
    names = {f.misconception_id: f.misconception_name for s in submissions for f in s.findings}

    tasks_attempted = len({r.task_id for r in records})
    clean_task_ids = {r.task_id for r in records if r.is_clean}
    tasks_mastered = len(clean_task_ids)
    clean_submissions = sum(1 for r in records if r.is_clean)

    misconceptions = _misconception_progress(records, names)
    best_streak = _best_overall_clean_streak(records)
    badges = _compute_badges(tasks_attempted, total_task_count, tasks_mastered, best_streak, misconceptions)

    ai_summary, ai_source = generate_ai_summary(
        user.display_name, misconceptions, tasks_attempted, total_task_count, tasks_mastered
    )

    return schemas.StudentProgress(
        user_id=user.id,
        display_name=user.display_name,
        tasks_total=total_task_count,
        tasks_attempted=tasks_attempted,
        tasks_mastered=tasks_mastered,
        total_submissions=len(records),
        clean_submissions=clean_submissions,
        badges=badges,
        misconceptions=misconceptions,
        ai_summary=ai_summary,
        ai_summary_source=ai_source,
    )


# --- Curated extension suggestions ------------------------------------------
# Static, instructor-curated mapping from a mastered misconception to a
# next-step suggestion. Deliberately NOT AI-generated: an LLM shouldn't be
# inventing exercise names or links, so this mapping is edited by hand as
# the task bank grows.
EXTENSION_SUGGESTIONS: dict[str, str] = {
    "M1": "Try a task that requires building up a running total or list across loop iterations, to reinforce the accumulator pattern that fixes this.",
    "M2": "Introduce a task involving mutable default arguments -- it builds on the same reference-vs-value distinction from a new angle.",
    "M3": "Move on to tasks comparing custom objects, where the identity-vs-equality distinction gets more subtle (e.g. overriding __eq__).",
    "M4": "Try a task with a while-loop that depends on external state (e.g. user input or a file), where termination is less obvious than a for-loop.",
    "M5": "Introduce a task with multiple return paths and early returns to build on solid return semantics.",
    "M6": "Try a task involving nested functions and closures -- a natural next step once basic scope is solid.",
    "M7": "Move to a task that accumulates into a dictionary or set instead of a list, to generalize the accumulation pattern.",
    "M8": "Try a task chaining several mutating list methods together, to reinforce when a method returns None vs. mutates in place.",
    "M9": "Introduce a task using higher-order functions (e.g. passing a method as a callback) to build on the method-reference distinction.",
    "M10": "Try a task with mixed boolean and arithmetic operators in the same expression to reinforce precedence rules further.",
    "M11": "Move to a task involving explicit None-checks vs. falsy-value checks (e.g. distinguishing 0, '', and None).",
}

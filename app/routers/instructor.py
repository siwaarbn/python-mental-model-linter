from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app import models, schemas
from app.services.progress_service import compute_student_progress, EXTENSION_SUGGESTIONS

router = APIRouter(prefix="/api/instructor", tags=["instructor"])

# A misconception counts as "widespread" (worth a reteach suggestion) once it
# has shown up for at least this many distinct students. Kept as a module
# constant rather than buried in the function so it's easy to tune from one
# place as the class size changes.
RETEACH_STUDENT_THRESHOLD = 2


def _aggregate(submissions: list[models.Submission]) -> list[schemas.MisconceptionFrequency]:
    """
    Aggregates findings across a set of submissions into per-misconception
    frequency + distinct-student counts. Kept as a standalone function
    (not inlined) so class-wide and per-task analytics reuse the exact
    same aggregation logic -- one source of truth for how "frequency"
    is defined.
    """
    counts: dict[str, int] = defaultdict(int)
    names: dict[str, str] = {}
    students_by_misconception: dict[str, set] = defaultdict(set)

    for sub in submissions:
        for f in sub.findings:
            counts[f.misconception_id] += 1
            names[f.misconception_id] = f.misconception_name
            students_by_misconception[f.misconception_id].add(sub.user_id)

    return sorted(
        [
            schemas.MisconceptionFrequency(
                misconception_id=mid,
                misconception_name=names[mid],
                count=counts[mid],
                student_count=len(students_by_misconception[mid]),
            )
            for mid in counts
        ],
        key=lambda m: m.count,
        reverse=True,
    )


@router.get("/analytics", response_model=schemas.ClassAnalytics)
def class_analytics(db: Session = Depends(get_db)):
    submissions = (
        db.query(models.Submission).options(joinedload(models.Submission.findings)).all()
    )
    tasks = {t.id: t for t in db.query(models.Task).all()}

    by_task_map: dict[str, list[models.Submission]] = defaultdict(list)
    for s in submissions:
        by_task_map[s.task_id].append(s)

    by_task = [
        schemas.TaskAnalytics(
            task_id=task_id,
            task_title=tasks[task_id].title if task_id in tasks else task_id,
            submission_count=len(subs),
            misconceptions=_aggregate(subs),
        )
        for task_id, subs in by_task_map.items()
    ]

    return schemas.ClassAnalytics(
        total_students=len({s.user_id for s in submissions}),
        total_submissions=len(submissions),
        misconceptions=_aggregate(submissions),
        by_task=sorted(by_task, key=lambda t: t.task_id),
    )


@router.get("/students", response_model=list[schemas.StudentSummary])
def list_students(db: Session = Depends(get_db)):
    """
    Roster view for the instructor to pick a student's progress page from.
    One query per student's submissions is fine for a single class; use a
    join if this needs to scale further.
    """
    students = db.query(models.User).filter(models.User.role == "student").all()
    total_task_count = db.query(models.Task).count()

    summaries = []
    for student in students:
        subs = (
            db.query(models.Submission)
            .filter(models.Submission.user_id == student.id)
            .all()
        )
        clean_task_ids = {
            s.task_id for s in subs
            if s.parse_error is None and len(s.findings) == 0
        }
        summaries.append(
            schemas.StudentSummary(
                user_id=student.id,
                display_name=student.display_name,
                tasks_attempted=len({s.task_id for s in subs}),
                tasks_total=total_task_count,
                tasks_mastered=len(clean_task_ids),
                total_submissions=len(subs),
                last_active=max((s.submitted_at for s in subs), default=None),
            )
        )
    return sorted(summaries, key=lambda s: s.display_name)


@router.get("/students/{user_id}/progress", response_model=schemas.StudentProgress)
def student_progress_for_instructor(user_id: int, db: Session = Depends(get_db)):
    """Same computation as the student-facing progress page, viewed by an instructor."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Student not found.")

    submissions = (
        db.query(models.Submission)
        .options(joinedload(models.Submission.findings))
        .filter(models.Submission.user_id == user_id)
        .all()
    )
    total_task_count = db.query(models.Task).count()
    return compute_student_progress(user, submissions, total_task_count)


@router.get("/suggestions", response_model=list[schemas.SuggestionItem])
def suggestions(db: Session = Depends(get_db)):
    """
    Instructor suggestion feed with two kinds of signal.

    - "reteach": a misconception is widespread across the class -> suggests
      revisiting that topic or handing out more material on it.
    - "extend": a specific student has full coverage and nothing currently
      active -> suggests a next-step exercise from the curated
      EXTENSION_SUGGESTIONS map, so students who are already doing well
      don't just disappear from the instructor's radar.

    Both are computed on each call rather than stored. Dismissed suggestions
    are tracked in the frontend only.
    """
    submissions = (
        db.query(models.Submission).options(joinedload(models.Submission.findings)).all()
    )
    total_task_count = db.query(models.Task).count()
    items: list[schemas.SuggestionItem] = []

    # --- Reteach signals: widespread misconceptions across the whole class ---
    for freq in _aggregate(submissions):
        if freq.student_count >= RETEACH_STUDENT_THRESHOLD:
            items.append(
                schemas.SuggestionItem(
                    id=f"reteach-{freq.misconception_id}",
                    type="reteach",
                    misconception_id=freq.misconception_id,
                    misconception_name=freq.misconception_name,
                    title=f"{freq.misconception_name} is showing up widely",
                    message=(
                        f"{freq.student_count} students have triggered this misconception "
                        f"({freq.count} occurrence{'s' if freq.count != 1 else ''} total)."
                    ),
                    suggestion=(
                        f"Consider a short recap or worked example on {freq.misconception_name.lower()} "
                        f"before the next exercise, or point students back to that section of the material."
                    ),
                    affected_count=freq.student_count,
                )
            )

    # --- Extend signals: students with full coverage and nothing active ---
    students = db.query(models.User).filter(models.User.role == "student").all()
    for student in students:
        student_subs = [s for s in submissions if s.user_id == student.id]
        if not student_subs:
            continue
        progress = compute_student_progress(student, student_subs, total_task_count)
        if progress.tasks_attempted < total_task_count or total_task_count == 0:
            continue
        active = [m for m in progress.misconceptions if not m.resolved]
        if active:
            continue

        # Pick the most recently-resolved misconception (if any) to anchor
        # the suggestion; fall back to a generic "keep going" note if the
        # student never triggered anything at all.
        resolved = sorted(progress.misconceptions, key=lambda m: m.times_seen, reverse=True)
        if resolved:
            top = resolved[0]
            suggestion = EXTENSION_SUGGESTIONS.get(
                top.misconception_id,
                "Consider a follow-up exercise that combines several concepts they've already shown mastery of.",
            )
            title = f"{student.display_name} is ready to go further"
            message = f"Full coverage, and {top.misconception_name.lower()} no longer appears in recent work."
        else:
            top = None
            suggestion = "Consider an extension exercise or an outside resource that goes beyond the current task bank."
            title = f"{student.display_name} has clean coverage across all tasks"
            message = "No misconceptions have been flagged at all."

        items.append(
            schemas.SuggestionItem(
                id=f"extend-{student.id}",
                type="extend",
                misconception_id=top.misconception_id if top else None,
                misconception_name=top.misconception_name if top else None,
                title=title,
                message=message,
                suggestion=suggestion,
                affected_count=1,
            )
        )

    return items

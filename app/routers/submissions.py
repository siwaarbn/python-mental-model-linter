from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app import models, schemas
from app.services.analysis_service import run_analysis

router = APIRouter(prefix="/api", tags=["submissions"])


@router.post("/submissions", response_model=schemas.SubmissionResult)
def create_submission(payload: schemas.SubmissionCreate, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == payload.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    result = run_analysis(payload.source_code)

    submission = models.Submission(
        user_id=payload.user_id,
        task_id=payload.task_id,
        source_code=payload.source_code,
        parse_error=result["parse_error"],
    )
    db.add(submission)
    db.flush()  # get submission.id before committing findings

    for card in result["findings"]:
        db.add(
            models.Finding(
                submission_id=submission.id,
                rule_id=card.rule_id,
                misconception_id=card.misconception_id,
                misconception_name=card.misconception_name,
                severity=card.severity,
                line=getattr(card, "line", None),
                column=getattr(card, "column", None),
                confidence=getattr(card, "confidence", None),
                layer1_observation=card.layer1_observation,
                layer2_conceptual_explanation=card.layer2_conceptual_explanation,
                layer3_mental_model_correction=card.layer3_mental_model_correction,
                layer4_reflection_prompt=card.layer4_reflection_prompt,
            )
        )

    db.commit()
    db.refresh(submission)

    return schemas.SubmissionResult(
        submission_id=submission.id,
        parse_error=submission.parse_error,
        findings=[schemas.FeedbackCardOut.model_validate(f) for f in submission.findings],
    )


@router.get("/users/{user_id}/submissions", response_model=list[schemas.SubmissionHistoryItem])
def submission_history(user_id: int, db: Session = Depends(get_db)):
    subs = (
        db.query(models.Submission)
        .options(joinedload(models.Submission.findings))
        .filter(models.Submission.user_id == user_id)
        .order_by(models.Submission.submitted_at.desc())
        .all()
    )
    return [
        schemas.SubmissionHistoryItem(
            id=s.id,
            task_id=s.task_id,
            submitted_at=s.submitted_at,
            parse_error=s.parse_error,
            finding_count=len(s.findings),
        )
        for s in subs
    ]


@router.get("/submissions/{submission_id}", response_model=schemas.SubmissionDetail)
def submission_detail(submission_id: int, db: Session = Depends(get_db)):
    s = (
        db.query(models.Submission)
        .options(joinedload(models.Submission.findings))
        .filter(models.Submission.id == submission_id)
        .first()
    )
    if not s:
        raise HTTPException(status_code=404, detail="Submission not found.")

    return schemas.SubmissionDetail(
        id=s.id,
        task_id=s.task_id,
        submitted_at=s.submitted_at,
        source_code=s.source_code,
        parse_error=s.parse_error,
        findings=[schemas.FeedbackCardOut.model_validate(f) for f in s.findings],
    )

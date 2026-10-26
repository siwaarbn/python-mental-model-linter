from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app import models, schemas
from app.services.progress_service import compute_student_progress

router = APIRouter(prefix="/api", tags=["progress"])


@router.get("/users/{user_id}/progress", response_model=schemas.StudentProgress)
def student_progress(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    submissions = (
        db.query(models.Submission)
        .options(joinedload(models.Submission.findings))
        .filter(models.Submission.user_id == user_id)
        .all()
    )
    total_task_count = db.query(models.Task).count()

    return compute_student_progress(user, submissions, total_task_count)

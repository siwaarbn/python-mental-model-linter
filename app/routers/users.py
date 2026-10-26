from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("", response_model=schemas.UserOut)
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Lightweight identity, not a real account: a student or instructor
    enters a name once and gets an id back to use for the rest of the
    session. There is no password: the prototype focuses on analysis and
    feedback, not account management.
    """
    existing = (
        db.query(models.User)
        .filter(
            models.User.display_name == payload.display_name,
            models.User.role == payload.role,
        )
        .first()
    )
    if existing:
        return existing

    user = models.User(display_name=payload.display_name, role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=schemas.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.User).filter(models.User.id == user_id).first()
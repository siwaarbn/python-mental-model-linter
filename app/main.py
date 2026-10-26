from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine, SessionLocal
from app import models
from app.seed_data import TASKS
from app.routers import users, tasks, submissions, instructor, progress
from app.services.analysis_service import ENGINE_AVAILABLE

app = FastAPI(title="Misconception Feedback API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(submissions.router)
app.include_router(instructor.router)
app.include_router(progress.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    _seed_tasks_if_empty()
    if not ENGINE_AVAILABLE:
        print(
            "\n"
            "  ! analysis_engine not found -- serving STUB feedback only.\n"
            "  Drop your Month 2 analysis_engine/ folder into backend/analysis_engine/\n"
            "  and restart. See backend/README.md.\n"
        )


def _seed_tasks_if_empty():
    db = SessionLocal()
    try:
        if db.query(models.Task).count() == 0:
            for t in TASKS:
                db.add(models.Task(**t))
            db.commit()
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {"status": "ok", "analysis_engine_connected": ENGINE_AVAILABLE}

"""
SQLite database setup via SQLAlchemy.

Why SQLite: the system is a prototype for a single class, so a single
file with zero setup is enough.
Why SQLAlchemy on top of it: it keeps the ORM code backend-agnostic. If
this ever needs to move to PostgreSQL (e.g. a multi-cohort deployment),
it is a one-line change to DATABASE_URL below, not a rewrite of models.py.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./thesis_app.db"

engine = create_engine(
    DATABASE_URL,
    # SQLite-specific: allows the connection to be used across the
    # threads FastAPI's request handling may use.
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a session, always closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

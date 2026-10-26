# Backend — Misconception Feedback API

FastAPI service wrapping the Month 2 `analysis_engine` and persisting
submissions/findings to SQLite for the student history and instructor
analytics views.

## 1. Connect your real analysis engine (do this first)

This backend was built to import your Month 2 pipeline exactly as designed:

```python
from analysis_engine.pipeline import analyze
```

**Copy your actual `analysis_engine/` folder** (the one with `parser.py`,
`context_builder.py`, `registry.py`, `pipeline.py`, `rules/`, `feedback/`)
into `backend/analysis_engine/`, replacing the placeholder file there.

Nothing else needs to change. `app/services/analysis_service.py` calls
`analyze(source_code)` and reads the result's `parse_error` / findings —
the same shape you designed in Month 2 (`FeedbackCard` with
`rule_id, misconception_id, misconception_name, severity, line, column,
confidence, layer1_observation, layer2_conceptual_explanation,
layer3_mental_model_correction, layer4_reflection_prompt`).

Until you do this, the API runs on an obviously-fake stub (`misconception_id:
"M0"`) so the frontend has something to render during setup. Check
`GET /api/health` — `analysis_engine_connected: true` confirms your real
engine is wired in.

## 2. Run it

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Server starts on `http://127.0.0.1:8000`. Interactive API docs at
`http://127.0.0.1:8000/docs`.

First run creates `thesis_app.db` (SQLite) and seeds the 11-task bank
(`app/seed_data.py`, one task per misconception M1–M11, matching your
finalized taxonomy names and severities exactly).

## 3. Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/users` | Create/fetch a lightweight student or instructor identity |
| GET | `/api/tasks` | List the task bank |
| POST | `/api/submissions` | Submit code for a task → runs `analyze()`, stores result, returns feedback cards |
| GET | `/api/users/{id}/submissions` | Submission history for a student |
| GET | `/api/submissions/{id}` | Full detail of one submission (code + feedback) |
| GET | `/api/instructor/analytics` | Class-wide and per-task misconception frequency |

## 4. Design notes (for your thesis write-up)

- **Why SQLite**: thesis-scale prototype, not production traffic. SQLAlchemy
  ORM keeps the code backend-agnostic — swapping to Postgres later is a
  one-line `DATABASE_URL` change, not a rewrite.
- **Why no real auth**: a name-only identity is intentional — this is a
  research prototype whose contribution is the detection/feedback pipeline,
  not account infrastructure. State this explicitly as a scoping decision
  in your limitations section, not an oversight.
- **Why `Finding` mirrors `FeedbackCard` field-for-field**: no translation
  layer between what the analysis engine produces and what gets persisted
  or served — one schema, defined once, in `app/schemas.py`.
- **`target_misconceptions` on `Task` is design intent, not a filter**:
  every submission is analyzed against all 22 rules regardless of task.
  This matters for your methodology section — the system never assumes
  which misconception a student will exhibit.

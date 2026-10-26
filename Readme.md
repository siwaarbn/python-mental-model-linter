# Month 3 — Frontend and API

Two pieces: `backend/` (FastAPI + SQLite, wraps your Month 2 `analysis_engine`)
and `frontend/` (React + TypeScript + Monaco).

## Quick start

**1. Connect your real analysis engine** — copy your Month 2 `analysis_engine/`
folder into `backend/analysis_engine/`, replacing the placeholder. Full
details in `backend/README.md`.

**2. Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Runs on `http://127.0.0.1:8000`. Confirm `analysis_engine_connected: true`
at `http://127.0.0.1:8000/api/health`.

**3. Frontend:**
```bash
cd frontend
npm install
npm run dev
```
Runs on `http://localhost:5173`.

**4. Open the app** — enter a name, pick "Student" or "Instructor".
Everything a student submits shows up immediately in the instructor
analytics view (same SQLite database, no separate sync step).

## What was built (Month 3 deliverables)

- **REST API** (FastAPI) — `backend/app/routers/`: users, tasks, submissions,
  instructor analytics. Endpoint list and design rationale in
  `backend/README.md`.
- **Code editor** — Monaco (`frontend/src/components/CodeEditor.tsx`), same
  editor family as VS Code.
- **Feedback display** — `frontend/src/components/FeedbackPanel.tsx`,
  built around Direction A ("diagnostic chart") agreed on before
  implementation: each finding is a numbered "case note" with the four
  layers (Observation / Conceptual Explanation / Mental Model Correction /
  Reflection Prompt) revealed progressively, one at a time, mirroring the
  same doctor/chart analogy your thesis already uses to justify
  `FeedbackCard`'s design.
- **Submission history** — students can browse and reopen any past
  submission, code and feedback exactly as it was generated.
- **Instructor analytics** — class-wide and per-task misconception
  frequency, both occurrence count and distinct-student count (so a single
  student repeatedly triggering M7 doesn't look like a class-wide gap).

## Consistency with the thesis (why this shouldn't create contradictions)

- Task bank (`backend/app/seed_data.py`) uses the exact M1-M11 names and
  severities from the finalized Month 1 taxonomy.
- `FeedbackCard` fields are never renamed or restructured anywhere in the
  stack — same names from `analysis_engine` through the DB (`app/models.py`)
  through the API (`app/schemas.py`) through the frontend (`src/types.ts`).
- No code execution anywhere (frontend or backend) — consistent with the
  system being purely AST-based static analysis, as designed in Month 1/2.
- Auth is intentionally minimal (name only, no password) — call this out
  as a scoping decision in your limitations section, not an oversight;
  see `backend/README.md` for the reasoning to reuse in your write-up.

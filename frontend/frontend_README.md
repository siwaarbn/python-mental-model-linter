# Frontend — Misconception Feedback UI

React + TypeScript + Vite. Talks to the FastAPI backend over plain `fetch`
calls (no state management library — the app is small enough that
component-local `useState` covers everything so far).

## 1. What's actually in here

```
frontend/src/
├── types.ts                     Mirrors backend/app/schemas.py field-for-field
├── api.ts                       Every backend call, in one place
├── App.tsx                      Routes to student or instructor view by role
├── main.tsx                     Entry point
├── index.css                    Design tokens (see "Design direction" below)
├── components/
│   ├── CodeEditor.tsx            Monaco wrapper
│   └── FeedbackPanel.tsx         The four-layer "case notes" panel
└── pages/
    ├── Login.tsx                 Name + role entry, no password
    ├── StudentWorkspace.tsx      Task picker, editor, feedback, history
    └── InstructorDashboard.tsx   Class-wide analytics
```

`types.ts` is worth calling out specifically: every field name in it was
copied directly from `backend/app/schemas.py`, which was itself copied
from `analysis_engine/feedback/generator.py`'s real `FeedbackCard`. There
is no renaming or reshaping anywhere in this chain — `misconception_name`
is `misconception_name` from the moment your rule fires to the moment it
renders on screen. If you ever add a field to `FeedbackCard`, this is the
first place to mirror it.

## 2. Design direction (why the feedback panel looks the way it does)

We went through three UI directions before building anything — a
"diagnostic chart" panel, a "field notebook" with inline margin
annotations, and a minimal dark IDE — and picked the diagnostic chart one
on purpose, not just because it looked nicest.

The reasoning: your own feedback-design chapter already explains
`FeedbackCard` using a doctor/X-ray analogy — a specific observation
("hairline fracture here") stapled to shared reference material that's
the same for every patient with that injury, revealed a layer at a time
depending on how much the patient wants to know. `FeedbackPanel.tsx`
takes that literally. Each finding renders as a "case note," numbered
(`01`–`04`), and a student can only open layer *N* after opening layer
*N-1* — Observation, then Conceptual Explanation, then Mental Model
Correction, then Reflection Prompt, one button press ("Reveal →") at a
time.

That progressive-disclosure mechanic isn't decoration. It's the same
principle Narciss's feedback taxonomy and Edwards' reflection-in-action
argument are already doing work for in your Month 2 write-up — dumping
all four layers on screen at once defeats the purpose of having four
layers instead of one paragraph. The UI is just the taxonomy's structure
made visible.

One deliberate absence: **the system never shows corrected code, anywhere,
on any screen.** Not in the feedback panel, not in submission history.
That's not a missing feature — the reflection prompt (layer 4) is written
as a question specifically so the student reconstructs the fix themselves
instead of being handed it. If you ever want to change that, it's a real
scope decision, not a bug — worth deciding deliberately, not by accident.

## 3. Running it

```bash
npm install
npm run dev
```

Opens on `http://localhost:5173`. Needs the backend running on
`http://127.0.0.1:8000` at the same time (see `backend/README.md`) — the
frontend has no fallback if it can't reach the API; you'll just see
requests fail silently in most places except login, which shows an error.

`VITE_API_BASE` in `.env` can override the backend URL if you ever deploy
them to different hosts.

## 4. How to actually test it, with code that will trigger something

Picking random buggy code and hoping it matches one of your 22 rules
wastes time — most "obviously wrong" code doesn't match any rule's exact
AST pattern (I hit this myself: `total = p` looks like a bug but only
`total += p` matches R-M7-01's pattern, since it specifically checks for
`AugAssign`). Below is one working example per task, each run through
your real `analyze()` and confirmed to produce a finding before being
written down here — not guessed.

**T01 — Repeated greeting (M1, Variable Persistence)**
```python
def collect_last(items):
    result = 0
    for x in items:
        result = x
    print(len(result))
    return result
```

**T02 — Swap two values (M2, Assignment Direction)**
```python
def swap(a, b):
    original = [1, 2, 3]
    copy = original
    copy.append(4)
    return original
```

**T03 — Is it the same list? (M3, Identity vs Equality)**
```python
def check(status):
    if status is "done":
        return True
    return False
```

**T04 — Count down (M4, Loop Termination)**
```python
def countdown(n):
    result = []
    i = n
    while i > 0:
        result.append(i)
    return result
```

**T05 — First even number (M5, Return Semantics)**
```python
def find_all_evens(numbers):
    for n in numbers:
        return n
```

**T07 — Total price (M7, Accumulation Pattern)**
```python
def total_price(prices):
    for p in prices:
        total += p
    return total
```

**T08 — Sort a copy (M8, Mutation vs Return Value)**
```python
def sorted_copy(items):
    items = items.sort()
    return items
```

**T09 — Shout it (M9, Method Reference vs Method Call)**
```python
def shout(sentence):
    sentence.upper
    return sentence
```

**T11 — Is the cart empty? (M11, Truthiness)**
```python
def is_cart_empty(cart):
    items = []
    if items == None:
        return True
    return False
```

**T06 and T10 don't have a confirmed example yet.** R-M6-01 needs
module-level code that reads a variable which was only ever assigned
inside a function — a slightly different shape than a single function
body, so the T06 starter code as it stands won't naturally produce it.
R-M10-01 needs a nested `and` inside an `or` with no parentheses around
it. Both are on the "to fix" list below rather than guessed at here.

**To test the instructor view**, submit a few of the snippets above under
different student names, then log in with a fresh name and pick
"Instructor" — the dashboard reads from the same database, so anything
submitted as a student shows up there immediately.

## 5. Bugs found and fixed while testing (kept here so the history isn't lost)

- **Run analysis button not rendering.** The code editor and the button
  sat in a CSS Grid + Flexbox layout that, under certain window sizes,
  let the editor's height grow unbounded and push the button off-screen
  entirely. Fixed by forcing explicit heights down the whole container
  chain (`StudentWorkspace.tsx`) instead of relying on Grid's default
  `auto`-sized rows, which don't respect a flex parent's height the way
  you'd expect.
- **Instructor login silently returning the student account.** The
  backend looked up an existing user by name only, so logging in again
  with the same name but a different role just handed back the original
  (student) account — the instructor dashboard never actually loaded,
  it just looked identical because it was the same page. Fixed in
  `backend/app/routers/users.py` by keying the lookup on
  `(display_name, role)` instead of name alone. If you tested with the
  same name before this fix, that name is now permanently tied to
  whichever role it first logged in as — use a new name to get a clean
  instructor account.

## 6. What's actually left to fix or improve

Roughly in order of how much it matters for the thesis:

- **T06 and T10 need real, verified example code**, and honestly the
  whole task bank deserves a pass where every task is checked against
  its target rule's actual AST pattern rather than just its
  misconception *name*. Right now that's only been done for 9 of 11.
- **Hint escalation is not built.** Right now a student can resubmit the
  same broken code fifty times and see the exact same four-layer card
  every time, with no scaffolding that adapts to repeated struggle. Your
  supervisor's Codio/Stepik references and the design-recommendations PDF
  both point toward this as the natural next step. Worth a deliberate
  decision, not a silent gap in the final write-up.
- **No automated frontend tests.** The backend has your real 74-test
  suite; the frontend has zero. Even a handful of component tests
  (does `FeedbackPanel` reveal layers in order, does submit actually
  disable the button while loading) would strengthen the "this was
  engineered carefully" story for your methodology chapter.
- **Submission history has no pagination.** Fine for a handful of test
  submissions; will get unwieldy fast once real students are using it
  across a whole task bank.
- **No error state for "backend unreachable"** outside of the login
  screen. If the backend crashes mid-session, the workspace just fails
  silently on the next submit instead of telling the student anything.
- **Bundle size warning on build** (~575kB, mostly Monaco). Not a
  correctness problem, but worth knowing about if this ever needs to
  load quickly on a slow connection — code-splitting Monaco behind a
  dynamic `import()` would fix it.
- **Never tested on a real mobile screen or with a screen reader.** The
  layout is desktop-first (two-column grid); on a narrow screen it will
  likely just squash rather than adapt.

# Analysis Engine — Month 2 Delivery

Backend implementation for the automated Python misconception detection system
(Master's thesis). This document describes what was built in Month 2, how it's
organized, how to run it, and what its known limitations are.

Month 1 produced the taxonomy (11 misconceptions, 22 detection rules, fully
specified as AST patterns). Month 2 turns that taxonomy into working code:
a parser, a context builder, 22 rule matchers, and a four-layer feedback
generator, wired together into one pipeline.

---

## 1. What Month 2 delivers

| Component | File(s) | Status |
|---|---|---|
| AST parser integration | `parser.py` | Done (Month 2, week 1) |
| Single-pass context builder | `context_builder.py` | Done |
| Rule Engine (22 rule matchers) | `rules/` | Done — all 22 active |
| Feedback Generator (4-layer) | `feedback/` | Done |
| Pipeline entry point | `pipeline.py` | Done |
| Test suite | `tests/` | Done — 74 tests, all passing |

Nothing in this delivery is a stub or placeholder. Every one of the 22 rules
in the finalized taxonomy has a real, tested implementation.

---

## 2. Architecture

### 2.1 Pipeline

```
source code (string)
        │
        ▼
   parser.py            parse_source() — wraps ast.parse(), never crashes,
                         returns either a tree or a clean ParseError
        │
        ▼
   context_builder.py    ONE traversal of the tree. Builds a shared
                         SubmissionContext: scopes, loops, functions,
                         light type-tracking, flat whole-file indexes.
        │
        ▼
   registry.py            Runs all 22 independent Rule objects against
                         the SAME context. Each rule only reads from
                         the context — none of them re-walk the tree.
                         Returns a sorted list of Finding objects.
        │
        ▼
   feedback/generator.py  Maps each Finding to a 4-layer FeedbackCard
                         (Observation → Conceptual Explanation →
                         Mental Model Correction → Reflection Prompt),
                         using the misconception's severity and
                         template content from feedback/templates.py.
        │
        ▼
   AnalysisResult(feedback_cards=[FeedbackCard, ...])
```

Single call: `analysis_engine.pipeline.analyze(source_code)`.

### 2.2 Why this architecture (Option C)

Four architectures were compared in the Month 2 design phase:

- **Option A** — one monolithic `ast.NodeVisitor` with all 22 rules inline.
  Rejected: unmaintainable and hard to debug once past ~15 rules
  (Foote & Yoder 1997, "Big Ball of Mud").
- **Option B** — one full tree traversal per misconception (11 separate walks).
  Rejected: wasteful, and rules needing cross-location context (e.g. "was this
  variable used after the loop?") would have to re-derive it independently
  in every walk.
- **Option C (chosen)** — one traversal builds a shared context; 22
  independent rule objects each ask questions of that context
  (Strategy pattern — Gamma et al. 1994; same approach used by PMD,
  arXiv:1208.3205).
- **Option D** — delegate to an external tool (e.g. Semgrep). Rejected:
  breaks traceability back to Python's own `ast` vocabulary, which was a
  deliberate Month 1 design choice, and generic linter rules are a poor fit
  for novice code (arXiv:2102.06098).

### 2.3 Data model

- **`SubmissionContext`** — the "notes taken during the one tree walk":
  scopes (module + each function), loops (with test-names and in-body
  assignments), functions (params/returns/prints), a light type-tracking
  pass (list/dict/set/str/int/...), and flat whole-file indexes (all
  assigns, all names, calls-by-name). The raw source text is also carried
  through, needed by R-M10-01's tokenize cross-check.
- **`Rule`** — one small, self-contained class per rule ID. `check(context)
  -> list[Finding]`. Knows nothing about tree-walking.
- **`Finding`** — one flagged instance: rule ID, misconception ID, line,
  message, confidence.
- **`FeedbackCard`** — one Finding expanded into the four pedagogical
  layers plus the misconception's severity.

Adding rule #23 in the future means writing one new `Rule` subclass and
adding one line to `registry.ALL_RULES` — nothing else changes.

---

## 3. The taxonomy (M1–M11) and severity

Severity is the taxonomy's resistance-to-correction scale, not a bug-severity
scale:

- **1 — Surface**: a missing piece of knowledge. One clear demonstration
  usually fixes it for good.
- **2 — Moderate**: a wrong belief that needs replacing. Resists a single
  correction; the same pattern tends to reappear until the model is rebuilt.
- **3 — Deep / threshold concept**: correcting it destabilizes other things
  the student thought they understood. Requires genuine reconstruction, not
  just a correction.

| ID | Name | Severity | Rules |
|---|---|---|---|
| M1 | Variable Persistence | 2 | R-M1-01, R-M1-02 |
| M2 | Assignment Direction | 2 | R-M2-01 |
| M3 | Comparison-as-Assignment / Identity-vs-Equality | 2 | R-M3-01, R-M3-02 |
| M4 | Loop Termination | 2 | R-M4-01, R-M4-02 |
| M5 | Return Semantics | 3 | R-M5-01, R-M5-02, R-M5-03 |
| M6 | Scope | 3 | R-M6-01, R-M6-02, R-M6-03 |
| M7 | Accumulation Pattern | 1 | R-M7-01, R-M7-02 |
| M8 | Mutation vs Return Value | 2 | R-M8-01, R-M8-02 |
| M9 | Method Reference vs Method Call | 1 | R-M9-01, R-M9-02 |
| M10 | Operator Precedence | 2 | R-M10-01 |
| M11 | Truthiness / Boolean-Numeric Conflation | 2 | R-M11-01, R-M11-02 |

**22 rules total**, all active.

---

## 4. Rule reference

Full AST-pattern-level detail for each rule lives in its own module's
docstrings (`rules/m1_rules.py` ... `rules/m11_rules.py`) — this table is
a quick index.

| Rule ID | Detects | Confidence |
|---|---|---|
| R-M1-01 | Loop-body overwrite without accumulation | HIGH |
| R-M1-02 | List overwritten with `=` instead of grown with `.append()` | HIGH |
| R-M2-01 | Mutable alias mutated through one name, read through the other | MEDIUM |
| R-M3-01 | `is`/`is not` used against a literal instead of `==`/`!=` | HIGH |
| R-M3-02 | `== True` / `== False` instead of a plain boolean check | MEDIUM |
| R-M4-01 | `while` condition whose variables are never updated in the body | HIGH |
| R-M4-02 | `range(N)` loop indexing out to `items[N]` (off-by-one) | MEDIUM |
| R-M5-01 | `return` inside an accumulation-style loop (exits on first match) | MEDIUM–HIGH |
| R-M5-02 | `print()`-only function whose result is used as a value elsewhere | HIGH |
| R-M5-03 | Unreachable code after a `return` | HIGH |
| R-M6-01 | Module-level read of a name that only exists inside a function | HIGH |
| R-M6-02 | Local read-before-assign that shadows a global (UnboundLocalError) | HIGH |
| R-M6-03 | Global re-passed as a parameter at every call site (overcorrection) | LOW–MEDIUM |
| R-M7-01 | `+=` used on a variable with no prior initialisation | HIGH |
| R-M7-02 | Accumulator read mid-loop as well as after it | MEDIUM |
| R-M8-01 | `x = x.sort()` — capturing the `None` a mutator returns | MEDIUM–HIGH |
| R-M8-02 | A mutator call (`.sort()`, `.append()`, ...) used as a sub-expression | HIGH |
| R-M9-01 | `obj.method` written as a statement, missing `()` | HIGH |
| R-M9-02 | A bare function name written as a statement, missing `()` | MEDIUM |
| R-M10-01 | `a and b or c` without parentheses (AST + tokenize hybrid) | MEDIUM |
| R-M11-01 | `container == None` instead of `if not container:` | MEDIUM–HIGH |
| R-M11-02 | Bare arithmetic expression used directly as a condition | MEDIUM |

---

## 5. Project structure

```
analysis_engine/
├── __init__.py              Package marker + roadmap
├── parser.py                Component 1: AST parser integration
├── context_builder.py       Component 2: single-pass context builder
├── registry.py               Component 3: Rule Engine (runs all 22 rules)
├── pipeline.py               analyze(code) — the one call that runs everything
│
├── rules/
│   ├── base.py               Rule / Finding base classes
│   ├── m1_rules.py .. m11_rules.py    One module per misconception
│
├── feedback/
│   ├── templates.py          4-layer content + severity, per misconception
│   └── generator.py          FeedbackGenerator, FeedbackCard
│
└── tests/
    ├── test_parser.py
    ├── test_context_builder.py
    ├── test_rules.py         True-positive / true-negative pair per rule
    ├── test_feedback.py
    └── test_pipeline.py      End-to-end tests
```

---

## 6. Running it

### Tests
```bash
pytest analysis_engine/tests -v
```
Expected: **74 passed**.

(If pytest isn't installed in your active interpreter: `pip install pytest`
first — see the PyCharm setup notes below if you hit environment issues.)

### The analyzer itself
```python
from analysis_engine.pipeline import analyze

result = analyze(source_code)

if not result.success:
    print("Syntax error:", result.parse_error.message, "at line", result.parse_error.line)
else:
    for card in result.feedback_cards:
        print(f"[{card.rule_id}] line {card.line} (severity {card.severity})")
        print("  Observation:", card.layer1_observation)
        print("  Reflection:", card.layer4_reflection_prompt)
```

---

## 7. Known, documented limitations

These are called out explicitly here — and in the affected rules' own
docstrings — rather than silently glossed over:

- **R-M6-03** requires cross-call-site analysis across the whole submission
  file, not just one function in isolation. It is intentionally the
  lowest-confidence rule in the taxonomy (`LOW-MEDIUM`) and its output is
  meant to be surfaced as a low-priority note, never a confident assertion.
- **R-M10-01** needs to know whether source-level parentheses were present
  around a boolean sub-expression — information the `ast` module discards
  once it resolves precedence. The rule re-tokenizes the raw source with
  `tokenize` as a cross-check; if tokenization itself fails for any reason,
  it falls back to flagging on the structural AST pattern alone, without the
  parenthesization check. This is a structural limitation of AST-only
  detection, not an engineering gap to be closed later.
- **M1 (Variable Persistence) and M7 (Accumulation Pattern)** target
  genuinely overlapping surface code patterns in the finalized taxonomy —
  the same snippet can trigger both rule families depending on preconditions.
  This is by design in the taxonomy, not a bug, but is worth a sentence in
  the thesis methodology noting that distinct mental models can share a
  detectable surface form.
- Type-tracking (used by R-M2-01, R-M8-01, R-M11-01) is a simple backward
  scan from each name's *first* assignment in its scope — it does not do
  full data-flow analysis, so confidence is deliberately downgraded
  (HIGH → MEDIUM) rather than suppressed when a variable's type can't be
  confirmed with certainty.

---

## 8. What's next (Month 3 candidates)

- Wire the pipeline into an API layer (FastAPI, per the System Architecture
  document) so submissions can be analyzed over HTTP rather than only via
  direct Python calls.
- Persist `Finding`/`FeedbackCard` output into the planned data model
  (users, tasks, submissions, findings) for longitudinal analysis.
- Build the instructor analytics view aggregating misconception frequency
  across submissions.
- Expand the technical evaluation: measure false-positive rates per rule
  against a larger corpus of real (or synthetic) student submissions,
  beyond the current true-positive/true-negative unit test pairs.
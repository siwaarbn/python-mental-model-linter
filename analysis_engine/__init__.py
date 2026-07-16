"""
analysis_engine
===============

Backend for automated detection of programming misconceptions in
Python student code (Master's thesis project).

Pipeline (Option C architecture — single-pass context builder feeding
independent pluggable rule matchers):

    source code
        -> parser.py            (AST parser integration)          [Month 2, done]
        -> context_builder.py   (single-pass context builder)      [Month 2, done]
        -> rules/                (all 22 rule matchers, Strategy pattern) [Month 2, done]
        -> registry.py          (runs all rules against the context)     [Month 2, done]
        -> feedback/             (Layer 1-4 feedback generator + templates) [Month 2, done]

All 22 rules from the finalized Month 1 taxonomy (M1-M11) are active:
R-M1-01/02, R-M2-01, R-M3-01/02, R-M4-01/02, R-M5-01/02/03,
R-M6-01/02/03, R-M7-01/02, R-M8-01/02, R-M9-01/02, R-M10-01, R-M11-01/02.

Known, documented limitations (called out explicitly in the taxonomy
itself, not implementation gaps to silently paper over):
    - R-M6-03 requires cross-call-site analysis across the whole
      submission file; it is intentionally the lowest-confidence rule
      in the taxonomy and should be surfaced as a low-priority note.
    - R-M10-01's tokenize cross-check depends on the raw source text
      being re-tokenizable; if tokenization fails, the rule falls back
      to flagging every structural match without the parenthesization
      cross-check (documented in rules/m10_rules.py).
"""

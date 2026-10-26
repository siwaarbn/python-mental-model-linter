"""
analysis_engine
===============

Static detection of beginner misconceptions in Python code, with
four-layer formative feedback for each finding.

Pipeline (one tree walk, then independent rules):

    source code
        -> parser.py            parse safely, report syntax errors
        -> context_builder.py   walk the AST once, record scopes, loops, functions
        -> rules/               22 independent rules (Strategy pattern)
        -> registry.py          run every rule against the shared context
        -> feedback/            expand each finding into four feedback layers

Rules cover misconceptions M1-M11:
R-M1-01/02, R-M2-01, R-M3-01/02, R-M4-01/02, R-M5-01/02/03,
R-M6-01/02/03, R-M7-01/02, R-M8-01/02, R-M9-01/02, R-M10-01, R-M11-01/02.

Known limitations:
    - R-M6-03 compares a function's parameters with every call site in the
      file. It is the rule with the lowest confidence.
    - R-M10-01 re-tokenizes the source to check for parentheses. If
      tokenization fails, it reports every structural match without that
      check (see rules/m10_rules.py).
"""

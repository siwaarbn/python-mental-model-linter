"""
M10 — Operator Precedence Misconception  (severity 2 — Moderate)

Faulty model: boolean/comparison operators are believed to evaluate
strictly left-to-right, rather than by Python's fixed precedence
table.
"""

import ast
import io
import tokenize

from analysis_engine.rules.base import Rule

_TRIVIAL_TOKEN_TYPES = frozenset({
    tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT,
    tokenize.COMMENT, tokenize.ENCODING,
})


class RM10_01_UnparenthesizedMixedBooleanOperators(Rule):
    """
    R-M10-01 — Unparenthesized mixed boolean operators (hybrid AST +
    tokenize).

    Precondition: A BoolOp node containing a nested BoolOp of the
    other kind.
    AST Pattern (structural part, detectable via ast):
      BoolOp(op=Or(), values=[..., BoolOp(op=And(), values=[...]), ...])
    Cross-check (requires tokenize — NOT available from ast alone):
      Re-tokenize the source spanned by the nested And-clause. Check
      whether '(' immediately precedes its first token and ')'
      immediately follows its last token. Absence of such parentheses
      elevates confidence that the grouping was accidental rather than
      deliberate.
    Confidence: MEDIUM. The ast module discards source-level
    parentheses once parsing resolves precedence — by the time the
    tree exists, there is no "missing parens" feature left in the AST
    alone. This is a structural limitation of pure AST detection, not
    a fixable engineering gap.
    False Positive Risk: HIGH for advanced students who omit optional
    parens deliberately. Pairs with a Layer 4 reflection prompt rather
    than an assertion of error.
    """
    rule_id = "R-M10-01"
    misconception_id = "M10"
    confidence = "MEDIUM"

    def check(self, context) -> list:
        findings = []
        tokens = self._tokenize_safely(context.source)

        for node in ast.walk(context.tree):
            if not (isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or)):
                continue
            for value in node.values:
                if isinstance(value, ast.BoolOp) and isinstance(value.op, ast.And):
                    parenthesized = (
                        self._is_parenthesized(tokens, value) if tokens else None
                    )
                    if parenthesized:
                        continue  # deliberately grouped — not flagged

                    findings.append(self._finding(
                        value,
                        "An 'and' expression is mixed with 'or' here without "
                        "parentheses. Python evaluates 'and' before 'or', so "
                        "this already groups as '(... and ...) or ...' — but "
                        "that grouping isn't visible in the source, which is "
                        "an easy place to misread the logic.",
                        evidence="and/or precedence",
                    ))
        return findings

    @staticmethod
    def _tokenize_safely(source: str):
        if not source:
            return None
        try:
            return list(tokenize.generate_tokens(io.StringIO(source).readline))
        except Exception:
            return None

    @staticmethod
    def _is_parenthesized(tokens, node) -> bool:
        start = (node.lineno, node.col_offset)
        end = (getattr(node, "end_lineno", node.lineno),
               getattr(node, "end_col_offset", node.col_offset))

        before = None
        after = None
        for tok in tokens:
            if tok.type in _TRIVIAL_TOKEN_TYPES:
                continue
            if tok.end <= start:
                before = tok
            elif tok.start >= end and after is None:
                after = tok
                break

        return (before is not None and before.string == "("
                and after is not None and after.string == ")")

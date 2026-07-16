"""
M3 — Comparison-as-Assignment / Identity-vs-Equality Misconception

Faulty model: `=` and `==` are believed interchangeable, or `is` is
believed to mean "equal to" rather than "the same object as".
"""

import ast

from analysis_engine.rules.base import Rule


class RM3_01_IdentityComparisonToLiteral(Rule):
    """
    Compare(left=ANY, ops=[Is|IsNot], comparators=[Constant(V)])
    where V is not None. 'is'/'is not' against a literal value almost
    always means the student wanted '=='/'!='.
    """
    rule_id = "R-M3-01"
    misconception_id = "M3"
    confidence = "HIGH"

    def check(self, context) -> list:
        findings = []
        for node in ast.walk(context.tree):
            if not isinstance(node, ast.Compare):
                continue
            for op, comparator in zip(node.ops, node.comparators):
                if not isinstance(op, (ast.Is, ast.IsNot)):
                    continue
                if not isinstance(comparator, ast.Constant):
                    continue
                if comparator.value is None:
                    continue  # 'is None' / 'is not None' is correct idiomatic Python
                op_text = "is" if isinstance(op, ast.Is) else "is not"
                findings.append(self._finding(
                    node,
                    f"'{op_text} {comparator.value!r}' checks object identity, not "
                    f"value equality. For literals this is unreliable — '=='/'!=' "
                    f"was almost certainly intended.",
                    evidence=op_text,
                ))
        return findings


class RM3_02_ExplicitBooleanComparison(Rule):
    """
    Compare(left=ANY, ops=[Eq|NotEq], comparators=[Constant(True|False)])
    e.g. `if flag == True:` instead of `if flag:`.
    """
    rule_id = "R-M3-02"
    misconception_id = "M3"
    confidence = "MEDIUM"

    def check(self, context) -> list:
        findings = []
        for node in ast.walk(context.tree):
            if not isinstance(node, ast.Compare):
                continue
            for op, comparator in zip(node.ops, node.comparators):
                if not isinstance(op, (ast.Eq, ast.NotEq)):
                    continue
                if not (isinstance(comparator, ast.Constant)
                        and isinstance(comparator.value, bool)):
                    continue
                op_text = "==" if isinstance(op, ast.Eq) else "!="
                findings.append(self._finding(
                    node,
                    f"'{op_text} {comparator.value}' explicitly compares against a "
                    f"boolean literal — the condition itself is already a boolean, "
                    f"so the comparison is redundant.",
                    evidence=f"{op_text} {comparator.value}",
                ))
        return findings

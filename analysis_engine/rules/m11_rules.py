"""
M11 — Truthiness / Boolean-Numeric Conflation Misconception  (severity 2)

Faulty model: conditions are believed to require an explicit
comparison; or a raw value is used as a condition without realising
Python's implicit truthiness conversion is occurring.
"""

import ast

from analysis_engine.rules.base import Rule


class RM11_01_ContainerComparedToNoneForEmptiness(Rule):
    """
    R-M11-01 — Container compared to None or False to check emptiness.

    Precondition: A Compare node with Eq/NotEq against None or False.
    AST Pattern:
      Compare(left=Name(id=VAR), ops=[Eq()|NotEq()],
              comparators=[Constant(value=None)|Constant(value=False)])
      where VAR was initialised earlier as List(...)/Dict(...)/Set(...)
      or via list()/dict()/set() constructor.
    Confidence: MEDIUM-HIGH, contingent on the type-tracking check.
    False Positive Risk: a container variable can legitimately be
    reassigned to None later as a sentinel. Suppressed if VAR is
    reassigned to Constant(value=None) anywhere between init and the
    comparison.
    """
    rule_id = "R-M11-01"
    misconception_id = "M11"
    confidence = "MEDIUM-HIGH"

    def check(self, context) -> list:
        findings = []
        for node in ast.walk(context.tree):
            scope = self._scope_for_node(context, node)
            finding = self._check_compare(context, scope, node)
            if finding:
                findings.append(finding)
        return findings

    @staticmethod
    def _scope_for_node(context, node):
        """Innermost function scope whose line range contains this node,
        else the module scope. Used because a single ast.walk(context.tree)
        pass doesn't otherwise tell us which scope a node lives in."""
        line = getattr(node, "lineno", None)
        if line is None:
            return context.module_scope
        best = None
        for func_info in context.functions.values():
            start = getattr(func_info.node, "lineno", None)
            end = getattr(func_info.node, "end_lineno", start)
            if start is not None and start <= line <= end:
                if best is None or (end - start) < (best[1] - best[0]):
                    best = (start, end, func_info.scope)
        return best[2] if best else context.module_scope

    def _check_compare(self, context, scope, node):
        if not isinstance(node, ast.Compare):
            return None
        if len(node.ops) != 1 or not isinstance(node.ops[0], (ast.Eq, ast.NotEq)):
            return None
        if not isinstance(node.left, ast.Name):
            return None
        comparator = node.comparators[0]
        if not (isinstance(comparator, ast.Constant)
                and (comparator.value is None or comparator.value is False)):
            return None

        var = node.left.id
        var_type = context.inferred_types.get((id(scope), var))
        if var_type not in ("list", "dict", "set"):
            return None

        if self._reassigned_to_none_before(scope, var, node):
            return None

        op_text = "==" if isinstance(node.ops[0], ast.Eq) else "!="
        return self._finding(
            node,
            f"'{var} {op_text} {comparator.value}' checks identity against "
            f"{comparator.value}, but '{var}' was created as a {var_type} — "
            f"an empty {var_type} is not the same value as {comparator.value}. "
            f"'if not {var}:' or 'if len({var}) == 0:' checks emptiness "
            f"directly.",
            evidence=var,
        )

    @staticmethod
    def _reassigned_to_none_before(scope, var, compare_node) -> bool:
        compare_line = getattr(compare_node, "lineno", 0)
        for assign in scope.assigned_names.get(var, []):
            if (getattr(assign, "lineno", 0) < compare_line
                    and isinstance(assign.value, ast.Constant)
                    and assign.value.value is None):
                return True
        return False


class RM11_02_BareArithmeticAsCondition(Rule):
    """
    R-M11-02 — Bare arithmetic expression as an if/while condition.

    Precondition: The test of an If or While node.
    AST Pattern: If/While(test=BinOp(op=Sub|Add|Mult, left=ANY, right=ANY))
    EXCLUDE: BinOp(op=Mod()) — 'x % 2' is a legitimate parity idiom.
    Confidence: MEDIUM.
    False Positive Risk: MEDIUM-HIGH. Deliberate idiomatic truthiness
    use is indistinguishable from accidental reliance at the AST
    level. Pairs with a Layer 4 reflection prompt.
    """
    rule_id = "R-M11-02"
    misconception_id = "M11"
    confidence = "MEDIUM"

    _FLAGGED_OPS = (ast.Sub, ast.Add, ast.Mult)

    def check(self, context) -> list:
        findings = []
        for node in ast.walk(context.tree):
            if not isinstance(node, (ast.If, ast.While)):
                continue
            test = node.test
            if not isinstance(test, ast.BinOp):
                continue
            if not isinstance(test.op, self._FLAGGED_OPS):
                continue
            findings.append(self._finding(
                test,
                "A bare arithmetic expression is used directly as a "
                "condition. This relies on Python's truthiness rules "
                "(any non-zero number is truthy) rather than an explicit "
                "comparison, which may not express the intended check.",
                evidence=type(test.op).__name__,
            ))
        return findings

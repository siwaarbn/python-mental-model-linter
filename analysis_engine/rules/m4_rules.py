"""
M4 — Loop Termination Misconception

Faulty model: the loop condition is believed checked only once (like an
if), or the loop bound in range() is believed inclusive of both ends.
"""

import ast

from analysis_engine.rules.base import Rule


class RM4_01_StaticWhileCondition(Rule):
    """
    While(test=T, body=B) where none of the names read in T are ever
    assigned anywhere in B — the loop condition can never change, so the
    loop either never runs or never ends.
    Suppressed if T contains a Call (state may change via a function's
    side effects, e.g. `while get_input() != "quit"`).
    """
    rule_id = "R-M4-01"
    misconception_id = "M4"
    confidence = "HIGH"

    def check(self, context) -> list:
        findings = []
        for loop in context.loops:
            if loop.kind != "while":
                continue
            test = loop.node.test
            if isinstance(test, ast.Constant) and test.value is True:
                continue  # `while True:` is a deliberate idiom
            if any(isinstance(n, ast.Call) for n in ast.walk(test)):
                continue  # state may change via a function call's side effects

            assigned_in_body = set(loop.body_assigned_names.keys())
            if loop.test_names and loop.test_names.isdisjoint(assigned_in_body):
                names = ", ".join(sorted(loop.test_names))
                findings.append(self._finding(
                    loop.node,
                    f"The while-condition depends on {{{names}}}, but nothing in "
                    f"the loop body ever changes {{{names}}} — the condition's "
                    f"truth value can never change, so the loop is checked once "
                    f"in effect, not repeatedly.",
                    evidence=names,
                ))
        return findings


class RM4_02_OffByOneInRange(Rule):
    """
    For(iter=Call(func=Name('range'), args=[N])) where N is a Constant,
    and the loop body subscripts the same sequence at index N — an
    out-of-bounds access that is the classic off-by-one signature.
    """
    rule_id = "R-M4-02"
    misconception_id = "M4"
    confidence = "MEDIUM"

    def check(self, context) -> list:
        findings = []
        for loop in context.loops:
            if loop.kind != "for":
                continue
            node = loop.node
            iter_call = node.iter
            if not (isinstance(iter_call, ast.Call)
                    and isinstance(iter_call.func, ast.Name)
                    and iter_call.func.id == "range"
                    and len(iter_call.args) == 1
                    and isinstance(iter_call.args[0], ast.Constant)
                    and isinstance(iter_call.args[0].value, int)):
                continue

            n = iter_call.args[0].value
            for sub in ast.walk(node):
                if (isinstance(sub, ast.Subscript)
                        and isinstance(sub.slice, ast.Constant)
                        and sub.slice.value == n):
                    findings.append(self._finding(
                        sub,
                        f"range({n}) produces indices 0..{n - 1}, but the loop "
                        f"body accesses index {n} — one past the last valid "
                        f"index. This is a classic off-by-one boundary error.",
                        evidence=str(n),
                    ))
        return findings

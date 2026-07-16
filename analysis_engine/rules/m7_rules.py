"""
M7 — Accumulation Pattern Misconception  (severity 1 — Surface)

Faulty model: a result is believed to build automatically from
repeating a computation, without an explicit accumulator variable.
"""

import ast

from analysis_engine.rules.base import Rule


class RM7_01_MissingAccumulatorInitialisation(Rule):
    """
    R-M7-01 — Missing accumulator initialisation.

    Precondition: For/While loop containing an AugAssign.
    AST Pattern:
      For/While(body=[..., AugAssign(target=Name(id=VAR), op=Add()/...), ...])
      where VAR does NOT appear as Name(id=VAR, ctx=Store()) anywhere
      preceding the loop at the same or an outer scope.
    Confidence: HIGH (produces NameError/UnboundLocalError).
    False Positive Risk: LOW. Excluded if VAR is a function parameter.
    """
    rule_id = "R-M7-01"
    misconception_id = "M7"
    confidence = "HIGH"

    def check(self, context) -> list:
        findings = []
        for loop in context.loops:
            for var, aug_assigns in loop.body_aug_assigned_names.items():
                if self._assigned_before_loop(context, loop, var):
                    continue
                findings.append(self._finding(
                    aug_assigns[0],
                    f"'{var} {self._op_symbol(aug_assigns[0].op)}= ...' updates "
                    f"'{var}', but '{var}' is never initialised anywhere before "
                    f"this loop — there is nothing for the loop to accumulate "
                    f"into on the first iteration.",
                    evidence=var,
                ))
        return findings

    @staticmethod
    def _assigned_before_loop(context, loop, var) -> bool:
        scope = loop.scope
        loop_line = getattr(loop.node, "lineno", 0)
        first = scope.first_assignment(var)
        if first is not None and getattr(first, "lineno", 0) < loop_line:
            return True
        for func_info in context.functions.values():
            if func_info.scope is scope and var in func_info.params:
                return True
        if scope.parent is not None:
            outer_first = scope.parent.first_assignment(var)
            if outer_first is not None and getattr(outer_first, "lineno", 0) < loop_line:
                return True
        return False

    @staticmethod
    def _op_symbol(op) -> str:
        return {
            ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
        }.get(type(op), "?")


class RM7_02_PrematureAccumulatorRead(Rule):
    """
    R-M7-02 — Premature accumulator read.

    Precondition: For/While loop.
    AST Pattern:
      For/While(body=[..., AugAssign(target=Name(id=VAR), ...), ...,
                      STMT containing Name(id=VAR, ctx=Load())])
      where the same Name(id=VAR) is ALSO read after the loop.
    Confidence: MEDIUM.
    False Positive Risk: MEDIUM. Printing intermediate values for
    debugging is legitimate — lower confidence if the inside-loop read
    feeds a print() call.
    """
    rule_id = "R-M7-02"
    misconception_id = "M7"
    confidence = "MEDIUM"

    def check(self, context) -> list:
        findings = []
        for loop in context.loops:
            for var in loop.body_aug_assigned_names:
                inside_read = self._read_inside_loop(loop, var)
                if inside_read is None:
                    continue
                loop_end_line = getattr(loop.node, "end_lineno", 0)
                if not self._read_after_loop(loop.scope, var, loop_end_line):
                    continue

                finding = self._finding(
                    inside_read,
                    f"'{var}' is read inside the loop, on the same iteration "
                    f"it was just updated — this yields an intermediate "
                    f"running value, not the final accumulated result. "
                    f"'{var}' is also read again after the loop finishes.",
                    evidence=var,
                )
                findings.append(finding)
        return findings

    @staticmethod
    def _read_inside_loop(loop, var):
        """A Load-context read of VAR inside the loop body that is not
        itself the AugAssign target being updated."""
        aug_target_ids = {
            id(a.target) for a in loop.body_aug_assigned_names[var]
        }
        for node in ast.walk(loop.node):
            if (isinstance(node, ast.Name) and node.id == var
                    and isinstance(node.ctx, ast.Load)
                    and id(node) not in aug_target_ids):
                return node
        return None

    @staticmethod
    def _read_after_loop(scope, var, after_line) -> bool:
        for name_node in scope.read_names.get(var, []):
            if getattr(name_node, "lineno", 0) > after_line:
                return True
        return False

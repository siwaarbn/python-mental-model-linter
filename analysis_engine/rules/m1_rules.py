"""
M1 — Variable Persistence Misconception  (severity 2 — Moderate)

Faulty model: a variable is believed to accumulate every value it has
ever held, rather than holding only its current value.
"""

import ast

from analysis_engine.rules.base import Rule, Finding

_COLLECTION_CONSTRUCTORS = ("list", "dict", "set")


class RM1_01_LoopBodyOverwrite(Rule):
    """
    R-M1-01 — Loop-body overwrite without accumulation.

    Precondition: A For or While loop body contains an Assign node.
    AST Pattern:
      - Outer scope: Assign(targets=[Name(id=VAR)], value=ANY)        [init]
      - Inside loop body: Assign(targets=[Name(id=VAR)], value=X)     [overwrite]
      - X does NOT contain Name(id=VAR) (not a self-update)
      - X is not a Call to list/dict/set constructor
      - After the loop: Name(id=VAR) appears in Load context
    False Positive Risk: legitimate when the variable is intentionally
    updated to the last item of a sequence. Suppressed unless VAR is
    used after the loop in a context implying a collection (passed to
    len(), iterated over, or subscripted).
    """
    rule_id = "R-M1-01"
    misconception_id = "M1"
    confidence = "HIGH"

    def check(self, context) -> list:
        findings = []
        for loop in context.loops:
            for var, assigns_in_loop in loop.body_assigned_names.items():
                if not self._initialised_before_loop(loop.scope, var, loop.node):
                    continue

                overwrites = [
                    a for a in assigns_in_loop
                    if self._is_overwrite(a.value, var)
                ]
                if not overwrites:
                    continue

                loop_end_line = getattr(loop.node, "end_lineno", None) or max(
                    getattr(a, "lineno", 0) for a in assigns_in_loop
                )
                if not self._used_as_collection_after(context, var, loop_end_line):
                    continue

                findings.append(self._finding(
                    overwrites[-1],
                    f"'{var}' is reassigned with '=' on each loop iteration, "
                    f"so only its last value survives — but it is later used "
                    f"as though it held every value the loop produced.",
                    evidence=var,
                ))
        return findings

    @staticmethod
    def _initialised_before_loop(scope, var, loop_node) -> bool:
        first = scope.first_assignment(var)
        if first is None:
            return False
        return getattr(first, "lineno", 0) < getattr(loop_node, "lineno", 0)

    @staticmethod
    def _is_overwrite(value: ast.AST, var: str) -> bool:
        # X is not a self-update: VAR must not appear anywhere inside X
        references_self = any(
            isinstance(n, ast.Name) and n.id == var for n in ast.walk(value)
        )
        if references_self:
            return False
        # X is not a fresh list/dict/set constructor (intentional reset)
        if (isinstance(value, (ast.List, ast.Dict, ast.Set))
                or (isinstance(value, ast.Call)
                    and isinstance(value.func, ast.Name)
                    and value.func.id in _COLLECTION_CONSTRUCTORS)):
            return False
        return True

    @staticmethod
    def _used_as_collection_after(context, var, after_line) -> bool:
        # len(var) anywhere after the loop
        for call in context.calls_by_name.get("len", []):
            if (getattr(call, "lineno", 0) > after_line
                    and len(call.args) == 1
                    and isinstance(call.args[0], ast.Name)
                    and call.args[0].id == var):
                return True
        # `for x in var` after the loop
        for other_loop in context.loops:
            if (other_loop.kind == "for"
                    and getattr(other_loop.node, "lineno", 0) > after_line
                    and isinstance(other_loop.node.iter, ast.Name)
                    and other_loop.node.iter.id == var):
                return True
        # var[...] subscript read after the loop
        for node in ast.walk(context.tree):
            if (isinstance(node, ast.Subscript)
                    and getattr(node, "lineno", 0) > after_line
                    and isinstance(node.value, ast.Name)
                    and node.value.id == var):
                return True
        return False


class RM1_02_ListAccumulationWithoutAppend(Rule):
    """
    A variable is initialised as an empty list, then inside a loop it is
    reassigned via plain '=' to something other than VAR.append(...) or
    VAR + [...] — i.e. the student overwrites the list itself instead of
    growing it.
    """
    rule_id = "R-M1-02"
    misconception_id = "M1"
    confidence = "HIGH"

    def check(self, context) -> list:
        findings = []
        for loop in context.loops:
            for var, assigns_in_loop in loop.body_assigned_names.items():
                if not self._initialised_as_empty_list(loop.scope, var, loop.node):
                    continue
                for assign in assigns_in_loop:
                    if self._is_legitimate_accumulation(assign.value, var):
                        continue
                    findings.append(self._finding(
                        assign,
                        f"'{var}' was created as an empty list, but inside the loop "
                        f"it is overwritten with '=' instead of grown with "
                        f"'{var}.append(...)'.",
                        evidence=var,
                    ))
        return findings

    @staticmethod
    def _initialised_as_empty_list(scope, var, loop_node) -> bool:
        first = scope.first_assignment(var)
        if first is None:
            return False
        if getattr(first, "lineno", 0) >= getattr(loop_node, "lineno", 0):
            return False  # must be initialised BEFORE the loop
        value = first.value
        return isinstance(value, ast.List) and len(value.elts) == 0

    @staticmethod
    def _is_legitimate_accumulation(value: ast.AST, var: str) -> bool:
        # VAR.append(...)
        if (isinstance(value, ast.Call)
                and isinstance(value.func, ast.Attribute)
                and isinstance(value.func.value, ast.Name)
                and value.func.value.id == var
                and value.func.attr == "append"):
            return True
        # VAR + [...]  (explicit, if unusual, correct accumulation)
        if (isinstance(value, ast.BinOp)
                and isinstance(value.op, ast.Add)
                and isinstance(value.left, ast.Name)
                and value.left.id == var):
            return True
        return False

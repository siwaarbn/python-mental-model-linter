"""
M9 — Method Reference vs Method Call Misconception  (severity 1 — Surface)

Faulty model: naming a method or function, even without parentheses,
is believed to trigger it.
"""

import ast
import builtins

from analysis_engine.rules.base import Rule

_COMMON_BUILTIN_FUNCS = frozenset({
    "print", "len", "str", "int", "float", "sorted", "sum", "max", "min",
    "input", "range", "list", "dict", "set", "type", "abs", "round",
    "open", "enumerate", "zip", "map", "filter", "reversed",
})


class RM9_01_BareAttributeAccessAsStatement(Rule):
    """
    R-M9-01 — Bare attribute access as a complete statement.

    Precondition: A statement that is just an expression (Expr node).
    AST Pattern: Expr(value=Attribute(value=ANY, attr=ANY)), where the
    Attribute is NOT wrapped in a Call.
    Confidence: HIGH.
    False Positive Risk: VERY LOW. No legitimate reason to write this
    as a standalone statement.
    """
    rule_id = "R-M9-01"
    misconception_id = "M9"
    confidence = "HIGH"

    def check(self, context) -> list:
        findings = []
        for node in ast.walk(context.tree):
            if not isinstance(node, ast.Expr):
                continue
            if isinstance(node.value, ast.Attribute):
                attr = node.value
                findings.append(self._finding(
                    node,
                    f"'{self._describe(attr)}' is written as a complete "
                    f"statement, but naming a method (even with the dot) "
                    f"does not call it — nothing happens here. Missing "
                    f"parentheses '()' at the end?",
                    evidence=attr.attr,
                ))
        return findings

    @staticmethod
    def _describe(attr: ast.Attribute) -> str:
        base = attr.value.id if isinstance(attr.value, ast.Name) else "..."
        return f"{base}.{attr.attr}"


class RM9_02_BareNameReferenceAsStatement(Rule):
    """
    R-M9-02 — Bare name reference as a complete statement (plain
    function).

    Precondition: A statement that is just an expression (Expr node).
    AST Pattern: Expr(value=Name(id=FUNC_NAME)), where FUNC_NAME
    matches a FunctionDef elsewhere in the module, or a known builtin
    function name.
    Confidence: MEDIUM.
    False Positive Risk: LOW. Suppressed if FUNC_NAME is also used as a
    plain variable anywhere in the file, which would make the case
    ambiguous.
    """
    rule_id = "R-M9-02"
    misconception_id = "M9"
    confidence = "MEDIUM"

    def check(self, context) -> list:
        findings = []
        assigned_anywhere = self._all_assigned_names(context)

        for node in ast.walk(context.tree):
            if not isinstance(node, ast.Expr):
                continue
            if not isinstance(node.value, ast.Name):
                continue
            name = node.value.id
            is_known_function = name in context.functions
            is_known_builtin = name in _COMMON_BUILTIN_FUNCS
            if not (is_known_function or is_known_builtin):
                continue
            if name in assigned_anywhere:
                continue  # ambiguous — also used as a plain variable
            findings.append(self._finding(
                node,
                f"'{name}' is written as a complete statement, but naming "
                f"a function does not call it — nothing happens here. "
                f"Missing parentheses '()' at the end?",
                evidence=name,
            ))
        return findings

    @staticmethod
    def _all_assigned_names(context) -> set:
        names = set()
        for scope in context.scopes:
            names.update(scope.assigned_names.keys())
        return names

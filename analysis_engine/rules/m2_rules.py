"""
M2 — Assignment Direction Misconception

Faulty model: assignment is believed symmetric, like mathematical
equality — the student thinks `b = a` makes an independent copy of a's
value, when for mutable objects it actually makes `b` another name for
the same object.
"""

import ast

from analysis_engine.rules.base import Rule


class RM2_01_MutableAliasWithoutCopy(Rule):
    """
    b = a, where a was previously assigned a list/dict literal, followed
    by a mutation through b (append/update/subscript-assignment) and a
    later read of a — evidence the student expected b to be independent.
    """
    rule_id = "R-M2-01"
    misconception_id = "M2"
    confidence = "MEDIUM"

    _MUTATING_ATTRS = {
        "append", "extend", "insert", "remove", "pop", "clear",
        "sort", "reverse", "update", "add", "discard",
    }

    def check(self, context) -> list:
        findings = []
        assign_scope = self._build_assign_scope_map(context)
        for assign in context.all_assigns:
            scope = assign_scope.get(id(assign), context.module_scope)
            finding = self._check_one_assign(context, scope, assign)
            if finding:
                findings.append(finding)
        return findings

    @staticmethod
    def _build_assign_scope_map(context) -> dict:
        mapping = {}
        for scope in context.scopes:
            for assigns in scope.assigned_names.values():
                for assign in assigns:
                    mapping[id(assign)] = scope
        return mapping

    def _check_one_assign(self, context, scope, assign: ast.Assign):
        if len(assign.targets) != 1 or not isinstance(assign.targets[0], ast.Name):
            return None
        if not isinstance(assign.value, ast.Name):
            return None

        b_name = assign.targets[0].id
        a_name = assign.value.id
        if a_name == b_name:
            return None

        a_type = context.inferred_types.get((id(scope), a_name))
        if a_type not in ("list", "dict", "set"):
            return None

        assign_line = getattr(assign, "lineno", 0)

        mutation = self._find_mutation_of(context.tree, b_name, assign_line)
        if mutation is None:
            return None

        a_read_after = self._find_read_after(scope, a_name, mutation)
        if a_read_after is None:
            return None

        return self._finding(
            a_read_after,
            f"'{b_name} = {a_name}' does not copy the {a_type} — both names "
            f"point to the same object. Mutating '{b_name}' also changes "
            f"'{a_name}', which is read afterward as if it were unaffected.",
            evidence=f"{a_name} -> {b_name}",
        )

    def _find_mutation_of(self, tree, name, after_line):
        for node in ast.walk(tree):
            if getattr(node, "lineno", 0) <= after_line:
                continue
            # b.append(...), b.update(...), etc.
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == name
                    and node.func.attr in self._MUTATING_ATTRS):
                return node
            # b[...] = ...
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (isinstance(target, ast.Subscript)
                            and isinstance(target.value, ast.Name)
                            and target.value.id == name):
                        return node
        return None

    @staticmethod
    def _find_read_after(scope, name, after_node):
        after_line = getattr(after_node, "lineno", 0)
        for name_node in scope.read_names.get(name, []):
            if getattr(name_node, "lineno", 0) > after_line:
                return name_node
        return None

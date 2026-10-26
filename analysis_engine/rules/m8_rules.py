"""
M8 — Mutation vs Return Value Misconception  (severity 2 — Moderate)

Faulty model: in-place mutating methods (.sort(), .append(), ...) are
believed to also hand back the changed object, like an ordinary
function.
"""

import ast

from analysis_engine.rules.base import Rule

# 'pop' is deliberately excluded — it legitimately returns a value.
_NONE_RETURNING_MUTATORS = frozenset({
    "sort", "reverse", "append", "extend", "insert",
    "remove", "clear", "update", "add", "discard",
})


def _is_none_returning_mutator_call(node) -> bool:
    return (isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in _NONE_RETURNING_MUTATORS)


class RM8_01_ReassignmentOfNoneReturningMutatorCall(Rule):
    """
    R-M8-01 — Reassignment of a None-returning mutator call.

    Precondition: An Assign node whose value is a method call.
    AST Pattern:
      Assign(targets=[Name(id=ANY)],
             value=Call(func=Attribute(value=ANY, attr=METHOD_NAME)))
      where METHOD_NAME is a known None-returning mutator.
    Confidence: HIGH when the target object's type is confirmed via the
    light type-tracking pass (list/dict/set literal or constructor);
    MEDIUM otherwise (could be a user-defined class with a same-named
    method that legitimately returns something).
    """
    rule_id = "R-M8-01"
    misconception_id = "M8"
    confidence = "MEDIUM"

    def check(self, context) -> list:
        findings = []
        assign_scope = self._build_assign_scope_map(context)
        for assign in context.all_assigns:
            scope = assign_scope.get(id(assign), context.module_scope)
            finding = self._check_one(context, scope, assign)
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

    def _check_one(self, context, scope, assign: ast.Assign):
        if not _is_none_returning_mutator_call(assign.value):
            return None
        if len(assign.targets) != 1 or not isinstance(assign.targets[0], ast.Name):
            return None

        call = assign.value
        method = call.func.attr
        receiver = call.func.value

        type_confirmed = (
            isinstance(receiver, ast.Name)
            and context.inferred_types.get((id(scope), receiver.id)) in
            ("list", "dict", "set")
        )

        finding = self._finding(
            assign,
            f"'.{method}()' mutates its target in place and returns None — "
            f"assigning its result overwrites the variable with None instead "
            f"of the mutated object.",
            evidence=method,
        )
        finding.confidence = "HIGH" if type_confirmed else "MEDIUM"
        return finding


class RM8_02_MutatorCallAsValueProducingSubExpression(Rule):
    """
    R-M8-02 — Mutator call used as a value-producing sub-expression.

    Precondition: A Call to a known None-returning mutator, not at
    statement level.
    AST Pattern:
      Call(func=Attribute(value=ANY, attr=METHOD_NAME))
      where METHOD_NAME is in the same set as R-M8-01, and the parent
      node is Call (as an argument), BinOp/Compare (as an operand),
      Return (as the returned value), or a For loop's iter.
    Confidence: HIGH (same type-inference caveats as R-M8-01).
    """
    rule_id = "R-M8-02"
    misconception_id = "M8"
    confidence = "HIGH"

    def check(self, context) -> list:
        findings = []
        assign_scope = self._build_assign_scope_map(context)
        scope_by_node = self._build_node_scope_map(context)

        for node in ast.walk(context.tree):
            for child_field, child in self._value_producing_children(node):
                if _is_none_returning_mutator_call(child):
                    method = child.func.attr
                    receiver = child.func.value

                    # As in R-M8-01: a user-defined class may have a method with
                    # the same name that returns a value (e.g. a fluent `.add()`
                    # returning `self`), so confidence is HIGH only when the
                    # receiver is confirmed to be a built-in list, dict or set.
                    scope = scope_by_node.get(id(node), context.module_scope)
                    type_confirmed = (
                        isinstance(receiver, ast.Name)
                        and context.inferred_types.get((id(scope), receiver.id)) in
                        ("list", "dict", "set")
                    )

                    finding = self._finding(
                        child,
                        f"'.{method}()' mutates in place and returns None, "
                        f"but its result is used here as though it produced "
                        f"a value — this expression will always evaluate to "
                        f"None.",
                        evidence=method,
                    )
                    finding.confidence = "HIGH" if type_confirmed else "MEDIUM"
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

    @staticmethod
    def _build_node_scope_map(context) -> dict:
        """Maps every node inside a function body to that function's scope
        (by line range), falling back to module scope -- used so the type
        lookup below checks the receiver's type in the scope it's actually
        used in, same as R-M8-01 does via its assign-specific scope map."""
        mapping = {}
        for func_info in context.functions.values():
            start = getattr(func_info.node, "lineno", None)
            end = getattr(func_info.node, "end_lineno", start)
            if start is None:
                continue
            for node in ast.walk(func_info.node):
                line = getattr(node, "lineno", None)
                if line is not None and start <= line <= end:
                    mapping[id(node)] = func_info.scope
        return mapping

    @staticmethod
    def _value_producing_children(node):
        """Yield (field_name, child) for positions where a value is
        clearly expected, excluding plain Expr-statement position."""
        if isinstance(node, ast.Call):
            for arg in node.args:
                yield "args", arg
            for kw in node.keywords:
                if kw.value is not None:
                    yield "keywords", kw.value
        elif isinstance(node, ast.BinOp):
            yield "left", node.left
            yield "right", node.right
        elif isinstance(node, ast.Compare):
            yield "left", node.left
            for comparator in node.comparators:
                yield "comparators", comparator
        elif isinstance(node, ast.Return):
            if node.value is not None:
                yield "value", node.value
        elif isinstance(node, ast.For):
            yield "iter", node.iter

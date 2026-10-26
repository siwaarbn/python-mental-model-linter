"""
M6 — Scope Misconception  (severity 3 — Deep / threshold)

Faulty model: variables are believed global by default (locals leak
out); OR, in the opposite direction, globals are believed invisible
inside a function unless explicitly passed in as a parameter.
"""

import ast
import builtins

from analysis_engine.rules.base import Rule

_BUILTIN_NAMES = frozenset(dir(builtins))


class RM6_01_OutOfScopeVariableRead(Rule):
    """
    R-M6-01 — Out-of-scope variable read.

    Precondition: Module-level code following a FunctionDef.
    AST Pattern:
      Module scope: Name(id=VAR, ctx=Load())
      where VAR appears as Name(id=VAR, ctx=Store()) ONLY inside a
      FunctionDef, VAR does NOT appear as Store() at module scope, and
      VAR is not a built-in name.
    Confidence: HIGH (causes NameError at runtime).
    False Positive Risk: LOW. Suppressed if VAR appears in any import.
    """
    rule_id = "R-M6-01"
    misconception_id = "M6"
    confidence = "HIGH"

    def check(self, context) -> list:
        findings = []
        module_scope = context.module_scope
        imported_names = self._imported_names(context.tree)

        locals_by_func = {
            name: fname
            for fname, finfo in context.functions.items()
            for name in finfo.scope.assigned_names
        }

        for var, read_nodes in module_scope.read_names.items():
            if var in module_scope.assigned_names:
                continue
            if var in imported_names or var in _BUILTIN_NAMES:
                continue
            source_func = locals_by_func.get(var)
            if source_func is None:
                continue
            for read_node in read_nodes:
                findings.append(self._finding(
                    read_node,
                    f"'{var}' is read at module level here, but it was only "
                    f"ever assigned inside the function '{source_func}'. "
                    f"A function's local variables are not visible after the "
                    f"function returns.",
                    evidence=f"{var} (local to {source_func})",
                ))
        return findings

    @staticmethod
    def _imported_names(tree) -> set:
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.add((alias.asname or alias.name).split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    names.add(alias.asname or alias.name)
        return names


class RM6_02_ShadowGlobalWithoutDeclaration(Rule):
    """
    R-M6-02 — Shadow global without declaration.

    Precondition: FunctionDef referencing a name also defined at module
    scope.
    AST Pattern:
      FunctionDef(body=[..., Assign(targets=[Name(id=VAR)], value=ANY), ...])
      where VAR is also assigned at module scope, the function does NOT
      contain Global(names=[VAR]), and Name(id=VAR, ctx=Load()) appears
      in the body BEFORE the Assign.
    Confidence: HIGH (produces UnboundLocalError).
    """
    rule_id = "R-M6-02"
    misconception_id = "M6"
    confidence = "HIGH"

    def check(self, context) -> list:
        findings = []
        module_globals = set(context.module_scope.assigned_names.keys())

        for func_info in context.functions.values():
            var_names_assigned_here = set(func_info.scope.assigned_names.keys())
            candidates = var_names_assigned_here & module_globals
            candidates -= func_info.scope.global_declarations

            for var in candidates:
                first_assign = func_info.scope.first_assignment(var)
                if first_assign is None:
                    continue
                earlier_read = self._read_before(func_info.node, var, first_assign)
                if earlier_read is not None:
                    findings.append(self._finding(
                        earlier_read,
                        f"'{var}' is read here before being assigned later in "
                        f"'{func_info.name}'. Because the function assigns "
                        f"'{var}' anywhere in its body, Python treats it as a "
                        f"local variable for the ENTIRE function — this read "
                        f"happens before that local exists, causing an "
                        f"UnboundLocalError, even though a global '{var}' "
                        f"exists.",
                        evidence=var,
                    ))
        return findings

    @staticmethod
    def _read_before(func_node, var, assign_node):
        assign_line = getattr(assign_node, "lineno", 0)
        assign_col = getattr(assign_node, "col_offset", 0)
        for node in ast.walk(func_node):
            if node is func_node:
                continue
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                continue  # nested scope, not relevant
            if isinstance(node, ast.Name) and node.id == var and isinstance(node.ctx, ast.Load):
                pos = (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))
                if pos < (assign_line, assign_col):
                    return node
        return None


class RM6_03_UnnecessaryGlobalReparameterisation(Rule):
    """
    R-M6-03 — Unnecessary global reparameterisation (inaccessibility
    variant: the opposite direction of M6).

    Precondition: FunctionDef whose parameter list includes a name that
    is also a global variable, scoped within a single submission file.
    AST Pattern:
      FunctionDef(args=arguments(args=[..., arg(arg=VAR), ...]))
      where VAR is also assigned at module scope, and every Call to
      this function anywhere in the file passes Name(id=VAR) — the
      same global — as that positional argument.

    Confidence: LOW-MEDIUM. Requires whole-file, cross-call-site
    analysis — the most expensive and least reliable rule in the
    taxonomy.
    False Positive Risk: HIGH. Passing values as parameters instead of
    reading module globals is often good practice. This rule is
    intentionally the weakest in the taxonomy: treat its output as a
    low-priority note, not confident student-facing feedback.
    """
    rule_id = "R-M6-03"
    misconception_id = "M6"
    confidence = "LOW-MEDIUM"

    def check(self, context) -> list:
        findings = []
        module_globals = set(context.module_scope.assigned_names.keys())

        for func_info in context.functions.values():
            params = func_info.params
            calls = context.calls_by_name.get(func_info.name, [])
            if not calls:
                continue

            for position, param_name in enumerate(params):
                if param_name not in module_globals:
                    continue
                if not self._every_call_passes_global(calls, position, param_name):
                    continue
                findings.append(self._finding(
                    func_info.node,
                    f"Parameter '{param_name}' shadows a module-level global "
                    f"of the same name, and every call to '{func_info.name}' "
                    f"passes that exact global as this argument. This MAY "
                    f"indicate a belief that the function couldn't otherwise "
                    f"see the global — but passing values explicitly is also "
                    f"good, deliberate practice, so treat this as a "
                    f"low-priority note rather than a confirmed error.",
                    evidence=param_name,
                ))
        return findings

    @staticmethod
    def _every_call_passes_global(calls, position: int, global_name: str) -> bool:
        for call in calls:
            if position >= len(call.args):
                return False  # passed as keyword or missing — not confirmable here
            arg = call.args[position]
            if not (isinstance(arg, ast.Name) and arg.id == global_name):
                return False
        return True

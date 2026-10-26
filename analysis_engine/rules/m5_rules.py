"""
M5 — Return Semantics Misconception

Faulty model: return inside a loop is believed to collect all values
across iterations; or print() and return are believed equivalent; or
a function is believed to keep running after it returns.
"""

import ast

from analysis_engine.rules.base import Rule

_COLLECTION_NAME_HINTS = ("all", "list", "collect", "find_all", "get_all")

# Function names that signal a deliberate "return the first match" search
# (e.g. `find_first_negative`). Its AST is identical to the misconception
# this rule targets, so the name is the only signal: the rule is skipped
# for these names, while _COLLECTION_NAME_HINTS raises confidence.
_SINGLE_MATCH_NAME_HINTS = ("find_first", "find_one", "search", "first_", "_first")


class RM5_01_ReturnInsideAccumulationLoop(Rule):
    """
    A function's only return statement(s) live inside a for/while loop,
    and the returned value is the bare loop variable itself (not wrapped
    in a conditional expression) — the classic "I thought return kept
    collecting" mistake: the function actually exits on the very first
    iteration.
    """
    rule_id = "R-M5-01"
    misconception_id = "M5"
    confidence = "MEDIUM"

    def check(self, context) -> list:
        findings = []
        for func_info in context.functions.values():
            node = func_info.node
            direct_loops = [s for s in node.body if isinstance(s, (ast.For, ast.While))]
            if not direct_loops:
                continue

            returns_outside_loop = [
                r for r in func_info.returns
                if not any(self._contains(loop, r) for loop in direct_loops)
            ]
            if returns_outside_loop:
                continue  # function also returns outside the loop — not this pattern

            for loop in direct_loops:
                loop_var = loop.target.id if isinstance(loop, ast.For) and isinstance(loop.target, ast.Name) else None
                for ret in ast.walk(loop):
                    if not isinstance(ret, ast.Return):
                        continue
                    if ret.value is None:
                        continue
                    if not isinstance(ret.value, ast.Name):
                        continue  # wrapped in an expression -> looks intentional, don't flag
                    if loop_var is not None and ret.value.id != loop_var:
                        continue

                    if any(h in func_info.name.lower() for h in _SINGLE_MATCH_NAME_HINTS):
                        continue  # deliberate search/find-first naming -- not this misconception

                    confidence = "HIGH" if any(
                        h in func_info.name.lower() for h in _COLLECTION_NAME_HINTS
                    ) else "MEDIUM"
                    finding = self._finding(
                        ret,
                        f"'{func_info.name}' returns inside the loop on the very "
                        f"first matching iteration — the function exits "
                        f"immediately rather than collecting results across all "
                        f"iterations.",
                        evidence=func_info.name,
                    )
                    finding.confidence = confidence  # per-call: name heuristic raises confidence
                    findings.append(finding)
        return findings

    @staticmethod
    def _contains(container, node) -> bool:
        return any(n is node for n in ast.walk(container))


class RM5_02_PrintUsedAsFunctionReturn(Rule):
    """
    A function's body contains a top-level print(V) and NO return
    statement anywhere, yet the function is called elsewhere in a
    position that uses its result (assignment RHS or as a call argument)
    — the student believes print() sends a value back to the caller.
    """
    rule_id = "R-M5-02"
    misconception_id = "M5"
    confidence = "HIGH"

    def check(self, context) -> list:
        findings = []
        for func_info in context.functions.values():
            if func_info.returns:
                continue
            if not func_info.top_level_prints:
                continue
            if self._used_for_its_value(context, func_info.name):
                print_call = func_info.top_level_prints[0]
                findings.append(self._finding(
                    print_call,
                    f"'{func_info.name}' has no return statement and only "
                    f"print()s its result, but it is called elsewhere as though "
                    f"it produced a value — print() displays output, it does "
                    f"not send a value back to the caller.",
                    evidence=func_info.name,
                ))
        return findings

    @staticmethod
    def _used_for_its_value(context, func_name: str) -> bool:
        # Is this call the RHS of an Assign, or an argument to another
        # call, anywhere in the tree?
        for node in ast.walk(context.tree):
            if isinstance(node, ast.Assign) and RM5_02_PrintUsedAsFunctionReturn._is_call_to(node.value, func_name):
                return True
            if isinstance(node, ast.Call):
                for arg in node.args:
                    if RM5_02_PrintUsedAsFunctionReturn._is_call_to(arg, func_name):
                        return True
        return False

    @staticmethod
    def _is_call_to(node, func_name: str) -> bool:
        return (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == func_name)


class RM5_03_UnreachableCodeAfterReturn(Rule):
    """
    Any statement block containing a Return followed by further
    statements (that are not another, differently-branched Return) —
    the student believes execution continues past a return.
    """
    rule_id = "R-M5-03"
    misconception_id = "M5"
    confidence = "HIGH"

    def check(self, context) -> list:
        findings = []
        for node in ast.walk(context.tree):
            body = getattr(node, "body", None)
            if not isinstance(body, list):
                continue
            for i, stmt in enumerate(body[:-1]):
                if isinstance(stmt, ast.Return):
                    unreachable = body[i + 1]
                    findings.append(self._finding(
                        unreachable,
                        f"This statement can never execute — the return on "
                        f"line {getattr(stmt, 'lineno', '?')} always exits the "
                        f"function first.",
                        evidence=f"line {getattr(unreachable, 'lineno', '?')}",
                    ))
                    break  # one finding per block is enough
        return findings

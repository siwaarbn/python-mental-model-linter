"""
context_builder.py
===================

Why this exists
----------------
Every rule matcher needs to answer questions like "was this variable
first assigned a list literal?", "does this while-loop's test reference
anything the body ever changes?", or "does this function have a return
statement anywhere?". If each of the 22 rules re-walked the AST to
answer these questions itself, that is one full tree traversal per
rule. Instead, this module does exactly ONE
traversal of the tree and builds a shared, read-only "context" object.
Every rule matcher (rules/*.py) only ever reads from this context; it
never touches the raw AST itself.

The rules in rules/ (run by registry.py) consume what this module
produces.

What it tracks
---------------
- Scopes (module + each function), each with its own assigned/read
  names and its `global` declarations.
- Loops (for/while), with the names referenced in a while-test and the
  names directly assigned in the loop body (not inside a nested def).
- Functions, with their parameters, return statements, and top-level
  print() calls.
- A light type-tracking pass: for every name, what kind of value it
  was FIRST assigned (list / dict / set / str / int / float / bool /
  None / unknown). Rules for M2, M8 and M11 use it to check whether a
  variable holds a built-in container.
- Flat, whole-file lists (all Assign nodes, all Name nodes, all Call
  nodes by callee name) for rules that need a global rather than a
  scoped view (e.g. R-M6-03's cross-call-site analysis).
"""

import ast
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Scope:
    """One lexical scope: either the module, or a single function body."""
    kind: str                      # "module" | "function"
    name: str                      # "<module>" or the function's name
    node: ast.AST                  # ast.Module or ast.FunctionDef
    parent: Optional["Scope"] = None
    assigned_names: dict = field(default_factory=dict)   # name -> list[ast.Assign]
    read_names: dict = field(default_factory=dict)       # name -> list[ast.Name]
    global_declarations: set = field(default_factory=set)  # names in `global x` statements

    def first_assignment(self, name: str) -> Optional[ast.Assign]:
        assigns = self.assigned_names.get(name)
        return assigns[0] if assigns else None


@dataclass
class LoopInfo:
    """One For or While loop."""
    node: ast.AST                  # ast.For | ast.While
    kind: str                      # "for" | "while"
    scope: Scope                   # the scope the loop lives in
    test_names: set                # names read in a While's test (empty for For)
    body_assigned_names: dict      # name -> list[ast.Assign] directly in the loop body
    body_aug_assigned_names: dict  # name -> list[ast.AugAssign] directly in the loop body
    body_statements: list          # the loop's direct body statements


@dataclass
class FunctionInfo:
    """One function definition."""
    node: ast.FunctionDef
    name: str
    scope: Scope                   # this function's OWN scope
    parent_scope: Scope            # the scope it is defined in
    params: list                   # list[str]
    returns: list                  # list[ast.Return] anywhere in the function
    top_level_prints: list         # list[ast.Call] to print(), direct body only


@dataclass
class SubmissionContext:
    """The complete shared context. Rule matchers only read from this."""
    tree: ast.AST
    source: str
    module_scope: Scope
    scopes: list                   # list[Scope], module first
    functions: dict                # name -> FunctionInfo (last def wins on name clash)
    loops: list                    # list[LoopInfo]
    all_assigns: list              # list[ast.Assign], whole file, in source order
    all_names: list                # list[ast.Name], whole file
    calls_by_name: dict            # callee name -> list[ast.Call]
    inferred_types: dict           # (scope_id, name) -> type label str


_TYPE_LABELS = {
    ast.List: "list",
    ast.Dict: "dict",
    ast.Set: "set",
    ast.Tuple: "tuple",
}


def _label_for_value(value: ast.AST) -> str:
    """Best-effort type label for the RHS of an assignment."""
    for node_type, label in _TYPE_LABELS.items():
        if isinstance(value, node_type):
            return label
    if isinstance(value, ast.Constant):
        if value.value is None:
            return "none"
        return type(value.value).__name__  # 'str', 'int', 'float', 'bool'
    if isinstance(value, ast.Call) and isinstance(value.func, ast.Name):
        # e.g. x = list(), x = dict(), x = set()
        if value.func.id in ("list", "dict", "set", "tuple"):
            return value.func.id
    return "unknown"


class _ShallowNameCollector(ast.NodeVisitor):
    """
    Collects names assigned/read in a set of statements WITHOUT
    descending into nested function/class definitions — those get
    their own scope and shouldn't pollute the enclosing loop/scope's
    direct name sets.
    """

    def __init__(self):
        self.assigned = {}     # name -> list[ast.Assign]
        self.aug_assigned = {}  # name -> list[ast.AugAssign]
        self.read = set()      # names

    def visit_FunctionDef(self, node):
        pass  # don't descend — nested function has its own scope

    def visit_AsyncFunctionDef(self, node):
        pass

    def visit_Lambda(self, node):
        pass

    def visit_ClassDef(self, node):
        pass

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.assigned.setdefault(target.id, []).append(node)
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        if isinstance(node.target, ast.Name):
            self.aug_assigned.setdefault(node.target.id, []).append(node)
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.read.add(node.id)


def _collect_test_names(test: ast.AST) -> set:
    names = set()
    for sub in ast.walk(test):
        if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
            names.add(sub.id)
    return names


class ContextBuilder(ast.NodeVisitor):
    """Performs the single traversal that builds a SubmissionContext."""

    def __init__(self, tree: ast.Module, source: str = ""):
        self.tree = tree
        self.source = source
        self.module_scope = Scope(kind="module", name="<module>", node=tree)
        self.scopes = [self.module_scope]
        self.scope_stack = [self.module_scope]
        self.functions = {}
        self.loops = []
        self.all_assigns = []
        self.all_names = []
        self.calls_by_name = {}
        self.inferred_types = {}

    # -- scope helpers --------------------------------------------------

    @property
    def current_scope(self) -> Scope:
        return self.scope_stack[-1]

    def _record_assign(self, node: ast.Assign):
        scope = self.current_scope
        for target in node.targets:
            if isinstance(target, ast.Name):
                scope.assigned_names.setdefault(target.id, []).append(node)
                key = (id(scope), target.id)
                if key not in self.inferred_types:
                    self.inferred_types[key] = _label_for_value(node.value)

    # -- visitors ---------------------------------------------------------

    def visit_FunctionDef(self, node: ast.FunctionDef):
        parent = self.current_scope
        scope = Scope(kind="function", name=node.name, node=node, parent=parent)
        self.scopes.append(scope)
        self.scope_stack.append(scope)

        params = [a.arg for a in node.args.args]
        returns = [n for n in ast.walk(node) if isinstance(n, ast.Return)]
        top_prints = [
            n.value for n in node.body
            if isinstance(n, ast.Expr)
            and isinstance(n.value, ast.Call)
            and isinstance(n.value.func, ast.Name)
            and n.value.func.id == "print"
        ]

        self.functions[node.name] = FunctionInfo(
            node=node, name=node.name, scope=scope, parent_scope=parent,
            params=params, returns=returns, top_level_prints=top_prints,
        )

        self.generic_visit(node)

        self.scope_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Global(self, node: ast.Global):
        self.current_scope.global_declarations.update(node.names)

    def visit_Assign(self, node: ast.Assign):
        self.all_assigns.append(node)
        self._record_assign(node)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        self.all_names.append(node)
        scope = self.current_scope
        if isinstance(node.ctx, ast.Load):
            scope.read_names.setdefault(node.id, []).append(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            self.calls_by_name.setdefault(node.func.id, []).append(node)
        self.generic_visit(node)

    def _handle_loop(self, node, kind: str):
        scope = self.current_scope
        collector = _ShallowNameCollector()
        for stmt in node.body:
            collector.visit(stmt)

        test_names = _collect_test_names(node.test) if kind == "while" else set()

        self.loops.append(LoopInfo(
            node=node, kind=kind, scope=scope,
            test_names=test_names,
            body_assigned_names=collector.assigned,
            body_aug_assigned_names=collector.aug_assigned,
            body_statements=node.body,
        ))
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        self._handle_loop(node, "for")

    def visit_While(self, node: ast.While):
        self._handle_loop(node, "while")

    def build(self) -> SubmissionContext:
        self.visit(self.tree)
        return SubmissionContext(
            tree=self.tree,
            source=self.source,
            module_scope=self.module_scope,
            scopes=self.scopes,
            functions=self.functions,
            loops=self.loops,
            all_assigns=self.all_assigns,
            all_names=self.all_names,
            calls_by_name=self.calls_by_name,
            inferred_types=self.inferred_types,
        )


def build_context(tree: ast.Module, source: str = "") -> SubmissionContext:
    """Convenience entry point: one call, one traversal, one context."""
    return ContextBuilder(tree, source).build()

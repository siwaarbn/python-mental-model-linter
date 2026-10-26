"""
parser.py
=========

The only place in the whole system allowed to call ast.parse() directly.
Every other component calls parse_source() instead, and always gets back
either (a) a usable tree, or (b) a clean description of what went wrong —
never a crash.
"""

import ast
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParseError:
    """The 'what went wrong' form — filled in only when parsing fails."""
    message: str
    line: Optional[int]
    column: Optional[int]
    bad_line_text: Optional[str]


@dataclass
class ParseResult:
    """
    The envelope every caller receives.

    success tells you whether parsing worked. Exactly one of `tree` or
    `error` is populated — never both, never neither.
    """
    success: bool
    tree: Optional[ast.AST]
    error: Optional[ParseError]


def parse_source(code: str, filename: str = "<student_submission>") -> ParseResult:
    """
    Parse student source code into an AST, never raising.

    Returns a ParseResult with success=True and a tree on success, or
    success=False and a ParseError describing the syntax problem.
    """
    try:
        tree = ast.parse(code, filename=filename)
        return ParseResult(success=True, tree=tree, error=None)
    except SyntaxError as exc:
        bad_line = None
        if exc.text is not None:
            bad_line = exc.text.rstrip("\n")
        error = ParseError(
            message=exc.msg,
            line=exc.lineno,
            column=exc.offset,
            bad_line_text=bad_line,
        )
        return ParseResult(success=False, tree=None, error=error)


def dump_tree(tree: ast.AST) -> str:
    """
    Debugging helper. Shows the exact node and field names (Assign, Name,
    ctx=Store(), ...) that the rule patterns in rules/ are written
    against.
    """
    return ast.dump(tree, indent=2)

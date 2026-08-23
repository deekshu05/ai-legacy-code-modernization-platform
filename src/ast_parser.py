"""AST-based detection of legacy code patterns.

Walks the Python Abstract Syntax Tree for a source file and flags
structural patterns that are commonly considered legacy, deprecated,
or anti-patterns worth modernizing.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Finding:
    """A single legacy-pattern match found in a source file."""

    file_path: str
    line: int
    pattern: str
    description: str
    snippet: str


class LegacyPatternVisitor(ast.NodeVisitor):
    """Visits AST nodes and records legacy-pattern findings."""

    def __init__(self, file_path: str, source_lines: list[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.findings: list[Finding] = []

    def _snippet(self, lineno: int) -> str:
        idx = lineno - 1
        return self.source_lines[idx].strip() if 0 <= idx < len(self.source_lines) else ""

    def _add(self, node: ast.AST, pattern: str, description: str) -> None:
        self.findings.append(
            Finding(
                file_path=self.file_path,
                line=getattr(node, "lineno", -1),
                pattern=pattern,
                description=description,
                snippet=self._snippet(getattr(node, "lineno", -1)),
            )
        )

    # --- pattern detectors -------------------------------------------------

    def visit_BinOp(self, node: ast.BinOp) -> None:
        if isinstance(node.op, ast.Mod) and isinstance(node.left, (ast.Str, ast.Constant)):
            self._add(
                node,
                "percent-string-formatting",
                "Legacy '%'-style string formatting; consider f-strings or .format().",
            )
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.type is None:
            self._add(
                node,
                "bare-except",
                "Bare 'except:' clause swallows all exceptions; catch specific types instead.",
            )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        for default in node.args.defaults:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self._add(
                    node,
                    "mutable-default-argument",
                    f"Function '{node.name}' uses a mutable default argument.",
                )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        deprecated_calls = {"os.popen", "os.getcwdu", "string.upper", "string.lower"}
        call_name = self._resolve_call_name(node)
        if call_name in deprecated_calls:
            self._add(
                node,
                "deprecated-api-call",
                f"Call to deprecated API '{call_name}'.",
            )
        self.generic_visit(node)

    @staticmethod
    def _resolve_call_name(node: ast.Call) -> str | None:
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            return f"{func.value.id}.{func.attr}"
        if isinstance(func, ast.Name):
            return func.id
        return None


def analyze_file(file_path: str | Path) -> list[Finding]:
    """Parse a single Python file and return all legacy-pattern findings."""
    path = Path(file_path)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    visitor = LegacyPatternVisitor(str(path), source.splitlines())
    visitor.visit(tree)
    return visitor.findings


def analyze_directory(target_path: str | Path, extensions: tuple[str, ...] = (".py",)) -> list[Finding]:
    """Recursively analyze every matching file under target_path."""
    findings: list[Finding] = []
    for path in Path(target_path).rglob("*"):
        if path.is_file() and path.suffix in extensions:
            try:
                findings.extend(analyze_file(path))
            except SyntaxError:
                # Skip files that don't parse as valid Python.
                continue
    return findings

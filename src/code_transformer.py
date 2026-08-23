"""Applies and validates LLM-proposed code transformations."""

from __future__ import annotations

import ast
from dataclasses import dataclass

from src.llm_analyzer import Suggestion


@dataclass
class TransformResult:
    suggestion: Suggestion
    applied: bool
    valid_syntax: bool
    error: str | None = None


def validate_syntax(code: str) -> tuple[bool, str | None]:
    """Return (is_valid, error_message) for a snippet of Python code."""
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as exc:
        return False, str(exc)


def apply_transformation(suggestion: Suggestion, dry_run: bool = False) -> TransformResult:
    """Validate a suggested rewrite and, if valid, write it back to disk.

    In dry_run mode the transformation is validated but never written,
    which is useful for CI checks and for reviewing a batch of proposed
    changes before committing to them.
    """
    is_valid, error = validate_syntax(suggestion.rewritten_code)

    if not is_valid:
        return TransformResult(suggestion=suggestion, applied=False, valid_syntax=False, error=error)

    if dry_run:
        return TransformResult(suggestion=suggestion, applied=False, valid_syntax=True)

    file_path = suggestion.finding.file_path
    with open(file_path, "r", encoding="utf-8") as handle:
        lines = handle.readlines()

    original_line_idx = suggestion.finding.line - 1
    if 0 <= original_line_idx < len(lines):
        lines[original_line_idx] = suggestion.rewritten_code + "\n"

    with open(file_path, "w", encoding="utf-8") as handle:
        handle.writelines(lines)

    return TransformResult(suggestion=suggestion, applied=True, valid_syntax=True)

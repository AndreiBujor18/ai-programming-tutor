"""Explain legacy or platform-specific C constructs without changing student code."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class CompatibilityWarning:
    id: str
    severity: str
    message: str


_PROTECTED_TEXT = re.compile(
    r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
)


def _mask_comments_and_literals(source: str) -> str:
    def mask(match: re.Match[str]) -> str:
        return "".join("\n" if character == "\n" else " " for character in match.group())

    return _PROTECTED_TEXT.sub(mask, source)


_RULES = (
    (
        "removed_gets",
        "danger",
        re.compile(r"\bgets\s*\("),
        "gets was removed from modern C because it cannot enforce a buffer limit; use fgets.",
    ),
    (
        "undefined_stdin_flush",
        "warning",
        re.compile(r"\bfflush\s*\(\s*stdin\s*\)"),
        "fflush(stdin) is not defined by standard C; consume pending input deliberately.",
    ),
    (
        "nonportable_console_api",
        "warning",
        re.compile(
            r"#\s*include\s*<\s*conio\.h\s*>|\b(?:getch|putch|clrscr|system)\s*\("
        ),
        "This console operation relies on non-standard APIs or platform-specific behavior.",
    ),
    (
        "nonportable_case_conversion",
        "warning",
        re.compile(r"\b(?:strlwr|strupr)\s*\("),
        "strlwr/strupr are non-standard; iterate with tolower/toupper for portable C.",
    ),
    (
        "eof_loop_condition",
        "warning",
        re.compile(r"\bwhile\s*\(\s*!\s*feof\s*\("),
        "Test the file-reading function's result instead of looping on feof before the read.",
    ),
)


def analyse_compatibility(source: str) -> tuple[dict[str, str], ...]:
    """Return deduplicated, source-free warnings for recognized legacy constructs."""
    code = _mask_comments_and_literals(source)
    return tuple(
        asdict(CompatibilityWarning(identifier, severity, message))
        for identifier, severity, expression, message in _RULES
        if expression.search(code)
    )

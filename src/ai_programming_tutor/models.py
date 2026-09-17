from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any


MAX_TEST_FILES = 8
MAX_TEST_FILE_BYTES = 32_000
MAX_TEST_CASE_FILE_BYTES = 64_000
_TEST_FILE_NAME = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,62}[A-Za-z0-9_-])?")
_RESERVED_TEST_FILE_NAMES = {"program.stderr", "program.stdout"}
_WINDOWS_RESERVED_STEMS = {
    "AUX",
    "CON",
    "NUL",
    "PRN",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


@dataclass(frozen=True)
class TestFile:
    name: str
    content: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or _TEST_FILE_NAME.fullmatch(self.name) is None:
            raise ValueError("Test file names must be portable flat filenames.")
        if self.name.lower() in _RESERVED_TEST_FILE_NAMES:
            raise ValueError("Test file name is reserved by the runner.")
        if self.name.split(".", 1)[0].upper() in _WINDOWS_RESERVED_STEMS:
            raise ValueError("Test file name is reserved on Windows.")
        if not isinstance(self.content, str):
            raise ValueError("Test file content must be text.")
        if len(self.content.encode("utf-8")) > MAX_TEST_FILE_BYTES:
            raise ValueError(f"A test file may contain at most {MAX_TEST_FILE_BYTES} bytes.")


@dataclass(frozen=True)
class TestCase:
    name: str
    input: str
    expected: str
    hidden: bool = False
    fixtures: tuple[TestFile, ...] = field(default_factory=tuple)
    expected_files: tuple[TestFile, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for label, entries in (
            ("fixture", self.fixtures),
            ("expected file", self.expected_files),
        ):
            if not isinstance(entries, tuple) or not all(
                isinstance(entry, TestFile) for entry in entries
            ):
                raise ValueError(f"Every {label} entry must be a TestFile.")
            names = [entry.name.lower() for entry in entries]
            if len(names) != len(set(names)):
                raise ValueError(f"A test may not repeat a {label} name.")
        fixture_names = {entry.name.lower(): entry.name for entry in self.fixtures}
        for expected_file in self.expected_files:
            fixture_name = fixture_names.get(expected_file.name.lower())
            if fixture_name is not None and fixture_name != expected_file.name:
                raise ValueError(
                    "A shared fixture and expected-file name must use identical spelling."
                )
        if len(self.fixtures) + len(self.expected_files) > MAX_TEST_FILES:
            raise ValueError(f"A test may define at most {MAX_TEST_FILES} file entries.")
        total_bytes = sum(
            len(entry.content.encode("utf-8"))
            for entry in self.fixtures + self.expected_files
        )
        if total_bytes > MAX_TEST_CASE_FILE_BYTES:
            raise ValueError(
                f"Test fixture and expected-file content may total at most "
                f"{MAX_TEST_CASE_FILE_BYTES} bytes."
            )


@dataclass(frozen=True)
class Exercise:
    id: str
    title: str
    statement: str
    input_format: str
    output_format: str
    tags: tuple[str, ...]
    starter_code: str
    reference_solution: str
    tests: tuple[TestCase, ...]

    def public_view(self) -> dict[str, Any]:
        public_tests = []
        for case in self.tests:
            if case.hidden:
                continue
            public_case: dict[str, Any] = {
                "name": case.name,
                "input": case.input,
                "expected": case.expected,
            }
            if case.fixtures:
                public_case["fixtures"] = [asdict(item) for item in case.fixtures]
            if case.expected_files:
                public_case["expected_files"] = [
                    asdict(item) for item in case.expected_files
                ]
            public_tests.append(public_case)
        return {
            "id": self.id,
            "title": self.title,
            "statement": self.statement,
            "input_format": self.input_format,
            "output_format": self.output_format,
            "tags": list(self.tags),
            "starter_code": self.starter_code,
            "public_tests": public_tests,
        }


@dataclass(frozen=True)
class CompilationResult:
    succeeded: bool
    return_code: int | None
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False


@dataclass(frozen=True)
class FileResult:
    name: str
    status: str
    expected: str
    actual: str


@dataclass(frozen=True)
class TestResult:
    name: str
    hidden: bool
    status: str
    expected: str
    actual: str
    stderr: str
    return_code: int | None
    duration_ms: float
    file_results: tuple[FileResult, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class EvaluationResult:
    exercise_id: str
    compilation: CompilationResult
    tests: tuple[TestResult, ...] = field(default_factory=tuple)

    @property
    def passed_count(self) -> int:
        return sum(result.status == "passed" for result in self.tests)

    @property
    def total_count(self) -> int:
        return len(self.tests)

    @property
    def all_passed(self) -> bool:
        return self.compilation.succeeded and bool(self.tests) and self.passed_count == self.total_count

    def to_dict(self, reveal_hidden: bool = False) -> dict[str, Any]:
        payload = asdict(self)
        payload["passed_count"] = self.passed_count
        payload["total_count"] = self.total_count
        payload["all_passed"] = self.all_passed
        if not reveal_hidden:
            hidden_number = 0
            for test in payload["tests"]:
                if test["hidden"]:
                    hidden_number += 1
                    test["name"] = f"hidden-test-{hidden_number}"
                    test["expected"] = ""
                    test["actual"] = ""
                    test["stderr"] = ""
                    for file_number, file_result in enumerate(test["file_results"], start=1):
                        file_result["name"] = f"hidden-file-{file_number}"
                        file_result["expected"] = ""
                        file_result["actual"] = ""
        return payload


@dataclass(frozen=True)
class DiagnosisCandidate:
    category: str
    confidence: float
    evidence: str


@dataclass(frozen=True)
class TutorResponse:
    evaluation: EvaluationResult
    candidates: tuple[DiagnosisCandidate, ...]
    hint_level: int
    hint: str | None
    dialect: str = "c17"
    language_warning: str | None = None

    def to_dict(self, reveal_hidden: bool = False) -> dict[str, Any]:
        return {
            "evaluation": self.evaluation.to_dict(reveal_hidden=reveal_hidden),
            "candidates": [asdict(candidate) for candidate in self.candidates],
            "hint_level": self.hint_level,
            "hint": self.hint,
            "dialect": self.dialect,
            "language_warning": self.language_warning,
        }

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class TestCase:
    name: str
    input: str
    expected: str
    hidden: bool = False


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
        return {
            "id": self.id,
            "title": self.title,
            "statement": self.statement,
            "input_format": self.input_format,
            "output_format": self.output_format,
            "tags": list(self.tags),
            "starter_code": self.starter_code,
            "public_tests": [
                {"name": case.name, "input": case.input, "expected": case.expected}
                for case in self.tests
                if not case.hidden
            ],
        }


@dataclass(frozen=True)
class CompilationResult:
    succeeded: bool
    return_code: int | None
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False


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

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from ai_programming_tutor.models import Exercise, TestCase, TestFile


EXERCISES_ROOT = Path(__file__).resolve().parent / "exercises"
_TEST_CASE_KEYS = {"name", "input", "expected", "hidden", "fixtures", "expected_files"}


def _test_files(value: object, field_name: str) -> tuple[TestFile, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list.")
    entries = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {"name", "content"}:
            raise ValueError(f"Every {field_name} entry requires only name and content.")
        entries.append(TestFile(name=item["name"], content=item["content"]))
    return tuple(entries)


def parse_test_case(value: object) -> TestCase:
    if not isinstance(value, dict):
        raise ValueError("Every test case must be an object.")
    unknown = set(value) - _TEST_CASE_KEYS
    if unknown:
        raise ValueError("Unknown test-case fields: " + ", ".join(sorted(unknown)))
    required = ("name", "input", "expected")
    if any(not isinstance(value.get(key), str) for key in required):
        raise ValueError("Each test requires string name, input, and expected fields.")
    hidden = value.get("hidden", False)
    if not isinstance(hidden, bool):
        raise ValueError("Test hidden must be a boolean.")
    return TestCase(
        name=value["name"],
        input=value["input"],
        expected=value["expected"],
        hidden=hidden,
        fixtures=(
            _test_files(value["fixtures"], "fixtures") if "fixtures" in value else ()
        ),
        expected_files=(
            _test_files(value["expected_files"], "expected_files")
            if "expected_files" in value
            else ()
        ),
    )


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, Exercise]:
    catalog: dict[str, Exercise] = {}
    for metadata_path in sorted(EXERCISES_ROOT.glob("*/exercise.json")):
        directory = metadata_path.parent
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        raw_tests = json.loads((directory / "tests.json").read_text(encoding="utf-8"))
        exercise = Exercise(
            id=metadata["id"],
            title=metadata["title"],
            statement=metadata["statement"],
            input_format=metadata["input_format"],
            output_format=metadata["output_format"],
            tags=tuple(metadata.get("tags", [])),
            starter_code=(directory / "starter.c").read_text(encoding="utf-8"),
            reference_solution=(directory / "solution.c").read_text(encoding="utf-8"),
            tests=tuple(parse_test_case(case) for case in raw_tests),
        )
        if exercise.id in catalog:
            raise ValueError(f"Duplicate exercise id: {exercise.id}")
        catalog[exercise.id] = exercise
    return catalog


def list_exercises() -> tuple[Exercise, ...]:
    return tuple(load_catalog().values())


def get_exercise(exercise_id: str) -> Exercise:
    try:
        return load_catalog()[exercise_id]
    except KeyError as exc:
        choices = ", ".join(load_catalog())
        raise KeyError(f"Unknown exercise '{exercise_id}'. Available: {choices}") from exc

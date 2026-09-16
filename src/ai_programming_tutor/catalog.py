from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from ai_programming_tutor.models import Exercise, TestCase


EXERCISES_ROOT = Path(__file__).resolve().parent / "exercises"


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
            tests=tuple(TestCase(**case) for case in raw_tests),
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

"""Author-owned practice exam definitions; no private course text is retained."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RubricCriterion:
    key: str
    points: float
    description: str


@dataclass(frozen=True)
class ExamTask:
    exercise_id: str
    points: float
    criteria: tuple[RubricCriterion, ...]


@dataclass(frozen=True)
class PracticeExam:
    id: str
    title: str
    duration_minutes: int
    base_points: float
    tasks: tuple[ExamTask, ...]

    @property
    def maximum_points(self) -> float:
        return self.base_points + sum(task.points for task in self.tasks)

    def public_view(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "base_points": self.base_points,
            "maximum_points": self.maximum_points,
            "tasks": [asdict(task) for task in self.tasks],
            "score_note": (
                "The browser estimates partial credit from passed tests. "
                "This is practice feedback, not an official grade."
            ),
        }


FOUNDATIONS_EXAM = PracticeExam(
    id="pclp1-foundations",
    title="PCLP1 foundations practice",
    duration_minutes=60,
    base_points=1.0,
    tasks=(
        ExamTask(
            "interval_parity",
            2.0,
            (
                RubricCriterion("interval_size", 1.0, "Compute the closed interval size."),
                RubricCriterion("parity_output", 1.0, "Test its parity and print the required word."),
            ),
        ),
        ExamTask(
            "odd_digit_count",
            2.0,
            (
                RubricCriterion("digit_traversal", 1.0, "Visit every decimal digit."),
                RubricCriterion("odd_counter", 1.0, "Count and print only odd digits."),
            ),
        ),
        ExamTask(
            "sentinel_average",
            3.0,
            (
                RubricCriterion("sentinel_stop", 1.0, "Stop at the marker without counting it."),
                RubricCriterion("average_values", 1.0, "Maintain the sum and value count."),
                RubricCriterion("empty_or_average", 1.0, "Handle empty input and real division."),
            ),
        ),
        ExamTask(
            "perfect_squares",
            2.0,
            (
                RubricCriterion("square_loop", 1.0, "Generate squares within the boundary."),
                RubricCriterion("square_output", 1.0, "Print them in order or report none."),
            ),
        ),
    ),
)


def get_practice_exam() -> PracticeExam:
    return FOUNDATIONS_EXAM

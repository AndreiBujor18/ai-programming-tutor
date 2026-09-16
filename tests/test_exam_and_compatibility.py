from __future__ import annotations

import unittest

from ai_programming_tutor.catalog import get_exercise
from ai_programming_tutor.compatibility import analyse_compatibility
from ai_programming_tutor.exam import get_practice_exam


class PracticeExamTests(unittest.TestCase):
    def test_exam_has_valid_original_tasks_and_ten_point_rubric(self) -> None:
        exam = get_practice_exam()
        self.assertEqual(exam.duration_minutes, 60)
        self.assertEqual(exam.base_points, 1.0)
        self.assertEqual(exam.maximum_points, 10.0)
        self.assertEqual(len(exam.tasks), 4)
        self.assertEqual(len({task.exercise_id for task in exam.tasks}), 4)
        for task in exam.tasks:
            with self.subTest(exercise=task.exercise_id):
                self.assertEqual(get_exercise(task.exercise_id).id, task.exercise_id)
                self.assertAlmostEqual(
                    sum(criterion.points for criterion in task.criteria), task.points
                )
                self.assertTrue(all(criterion.description for criterion in task.criteria))

    def test_public_exam_view_contains_no_solutions_or_private_source_fields(self) -> None:
        view = get_practice_exam().public_view()
        serialized = str(view).lower()
        self.assertNotIn("reference_solution", serialized)
        self.assertNotIn("source_file", serialized)
        self.assertNotIn("author", serialized)


class CompatibilityTests(unittest.TestCase):
    def test_detects_each_supported_legacy_construct_once(self) -> None:
        source = """
#include <conio.h>
int main(void) {
    char text[20];
    gets(text);
    gets(text);
    fflush(stdin);
    strupr(text);
    while (!feof(stdin)) { getch(); }
    return 0;
}
"""
        warnings = analyse_compatibility(source)
        identifiers = [warning["id"] for warning in warnings]
        self.assertEqual(
            identifiers,
            [
                "removed_gets",
                "undefined_stdin_flush",
                "nonportable_console_api",
                "nonportable_case_conversion",
                "eof_loop_condition",
            ],
        )
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertTrue(all(set(item) == {"id", "severity", "message"} for item in warnings))

    def test_ignores_comments_strings_and_portable_alternatives(self) -> None:
        source = r'''
/* gets(buffer); while (!feof(file)) {} */
// fflush(stdin); strlwr(text); getch();
printf("gets(text) and #include <conio.h>");
fgets(text, sizeof text, stdin);
while (fgets(text, sizeof text, file) != NULL) { }
'''
        self.assertEqual(analyse_compatibility(source), ())


if __name__ == "__main__":
    unittest.main()

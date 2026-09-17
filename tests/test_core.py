from __future__ import annotations

import os
import shutil
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

from ai_programming_tutor import __version__
from ai_programming_tutor.catalog import get_exercise, list_exercises
from ai_programming_tutor.dataset import iter_samples
from ai_programming_tutor.diagnosis import diagnose
from ai_programming_tutor.runner import (
    CRunner,
    _compiler_resource_limiter,
    _process_environment,
    _program_resource_limiter,
)
from ai_programming_tutor.service import TutorService


GCC_AVAILABLE = shutil.which("gcc") is not None
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class VersionTests(unittest.TestCase):
    def test_package_and_project_versions_match(self) -> None:
        with (PROJECT_ROOT / "pyproject.toml").open("rb") as stream:
            metadata = tomllib.load(stream)
        self.assertEqual(__version__, "0.7.0")
        self.assertEqual(metadata["project"]["version"], __version__)


class CatalogTests(unittest.TestCase):
    def test_catalog_contains_fourteen_exercises(self) -> None:
        exercises = list_exercises()
        self.assertEqual(len(exercises), 14)
        self.assertEqual({len(exercise.tests) for exercise in exercises}, {5})
        self.assertTrue(all(sum(test.hidden for test in exercise.tests) == 3 for exercise in exercises))

    def test_public_view_never_contains_hidden_cases(self) -> None:
        view = get_exercise("vector_average").public_view()
        self.assertEqual(len(view["public_tests"]), 2)
        self.assertNotIn("single-negative", str(view))


@unittest.skipUnless(GCC_AVAILABLE, "GCC is required for runner tests")
class RunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CRunner()

    def test_every_reference_solution_passes(self) -> None:
        for exercise in list_exercises():
            with self.subTest(exercise=exercise.id):
                result = self.runner.evaluate(exercise.reference_solution, exercise)
                self.assertTrue(result.all_passed, result.to_dict(reveal_hidden=True))

    def test_compilation_error_is_reported(self) -> None:
        exercise = get_exercise("vector_average")
        with mock.patch(
            "ai_programming_tutor.runner._compiler_resource_limiter",
            wraps=_compiler_resource_limiter,
        ) as compiler_limits:
            result = self.runner.evaluate("int main(void) { this is not C; }", exercise)
        compiler_limits.assert_called_once_with()
        self.assertFalse(result.compilation.succeeded)
        self.assertTrue(result.compilation.stderr)

    def test_integer_division_is_diagnosed(self) -> None:
        exercise = get_exercise("vector_average")
        buggy = exercise.reference_solution.replace(
            "(double) total / item_count", "(double) (total / item_count)"
        )
        result = self.runner.evaluate(buggy, exercise)
        candidates = diagnose(buggy, result)
        self.assertEqual(candidates[0].category, "integer_division")

    def test_natural_mixed_input_bug_is_diagnosed(self) -> None:
        exercise = get_exercise("line_after_number")
        buggy = (exercise.reference_solution.replace(
            "    int character;\n"
            "    while ((character = getchar()) != '\\n' && character != EOF) {\n"
            "    }\n\n",
            "",
        ))
        result = self.runner.evaluate(buggy, exercise)
        candidates = diagnose(buggy, result)
        self.assertEqual(candidates[0].category, "input_buffer_misuse")

    def test_sentinel_included_in_average_is_diagnosed(self) -> None:
        exercise = get_exercise("sentinel_average")
        buggy = exercise.reference_solution.replace(
            "if (value != 0)",
            "if (1)",
        )
        result = self.runner.evaluate(buggy, exercise)
        candidates = diagnose(buggy, result)
        self.assertEqual(candidates[0].category, "sentinel_handling")

    def test_hidden_values_are_redacted(self) -> None:
        exercise = get_exercise("vector_average")
        buggy = exercise.reference_solution.replace(
            "(double) total / item_count", "(double) (total / item_count)"
        )
        response = TutorService(self.runner).submit(exercise.id, buggy)
        payload = response.to_dict(reveal_hidden=False)
        hidden = [test for test in payload["evaluation"]["tests"] if test["hidden"]]
        self.assertTrue(hidden)
        self.assertTrue(all(test["expected"] == test["actual"] == "" for test in hidden))
        self.assertTrue(all(test["name"].startswith("hidden-test-") for test in hidden))

    def test_every_controlled_bug_compiles_fails_and_surfaces_in_top_three(self) -> None:
        for sample in iter_samples(variants=1, evaluate=False):
            with self.subTest(sample=sample["id"]):
                exercise = get_exercise(sample["exercise_id"])
                result = self.runner.evaluate(sample["source"], exercise)
                self.assertTrue(result.compilation.succeeded, result.compilation.stderr)
                self.assertFalse(result.all_passed)
                labels = [candidate.category for candidate in diagnose(sample["source"], result)]
                self.assertIn(sample["label"], labels)


class DatasetTests(unittest.TestCase):
    def test_one_variant_has_all_labels_and_unique_ids(self) -> None:
        samples = list(iter_samples(variants=1, evaluate=False))
        self.assertEqual(len(samples), 71)
        self.assertEqual(len({sample["id"] for sample in samples}), 71)
        self.assertTrue(all(sample["evidence_basis"] for sample in samples))
        self.assertEqual({sample["dataset_schema_version"] for sample in samples}, {"0.3"})
        self.assertEqual({sample["generator_version"] for sample in samples}, {"0.3.0"})
        self.assertTrue(all(len(sample["exercise_fingerprint"]) == 16 for sample in samples))
        self.assertTrue(all(len(sample["test_suite_fingerprint"]) == 16 for sample in samples))
        self.assertEqual(
            {sample["label"] for sample in samples},
            {
                "loop_boundary",
                "relational_operator",
                "wrong_initialization",
                "missing_update",
                "invalid_index",
                "logical_condition",
                "integer_division",
                "accumulator_misuse",
                "menu_dispatch",
                "input_buffer_misuse",
                "invalid_program_state",
                "wrong_identifier_or_argument",
                "sentinel_handling",
            },
        )


class RunnerEnvironmentTests(unittest.TestCase):
    @unittest.skipIf(sys.platform == "win32", "POSIX resource limits are unavailable")
    def test_compiler_limits_do_not_apply_a_user_wide_process_cap(self) -> None:
        import resource

        limiter = _compiler_resource_limiter()
        self.assertIsNotNone(limiter)
        with mock.patch("resource.setrlimit") as set_limit:
            limiter()

        limited_resources = {call.args[0] for call in set_limit.call_args_list}
        self.assertIn(resource.RLIMIT_CPU, limited_resources)
        self.assertIn(resource.RLIMIT_AS, limited_resources)
        self.assertIn(resource.RLIMIT_FSIZE, limited_resources)
        self.assertNotIn(resource.RLIMIT_NPROC, limited_resources)

    @unittest.skipIf(sys.platform == "win32", "POSIX resource limits are unavailable")
    def test_program_limits_keep_the_process_cap(self) -> None:
        import resource

        if not hasattr(resource, "RLIMIT_NPROC"):
            self.skipTest("RLIMIT_NPROC is unavailable")
        limiter = _program_resource_limiter()
        self.assertIsNotNone(limiter)
        with mock.patch("resource.setrlimit") as set_limit:
            limiter()

        set_limit.assert_any_call(resource.RLIMIT_NPROC, (16, 16))

    def test_private_temp_variables_are_always_set(self) -> None:
        workdir = Path(tempfile.gettempdir()) / "aptutor-private-test"
        environment = _process_environment(workdir)
        self.assertEqual(environment["TMP"], str(workdir))
        self.assertEqual(environment["TEMP"], str(workdir))
        self.assertEqual(environment["TMPDIR"], str(workdir))
        self.assertEqual(environment["LANG"], "C")
        self.assertEqual(environment["LC_ALL"], "C")

    def test_windows_environment_keeps_toolchain_and_system_locations_only(self) -> None:
        supplied = {
            "PATH": r"C:\\mingw64\\bin;C:\\Windows\\System32",
            "SystemRoot": r"C:\\Windows",
            "WINDIR": r"C:\\Windows",
            "COMSPEC": r"C:\\Windows\\System32\\cmd.exe",
            "PATHEXT": ".COM;.EXE;.BAT;.CMD",
            "SHOULD_NOT_LEAK": "secret",
        }
        workdir = Path(r"C:\\Users\\tester\\AppData\\Local\\Temp\\aptutor-test")
        with mock.patch.object(sys, "platform", "win32"), mock.patch.dict(
            os.environ, supplied, clear=True
        ):
            environment = _process_environment(workdir)
        self.assertEqual(environment["PATH"], supplied["PATH"])
        self.assertEqual(environment["SystemRoot"], supplied["SystemRoot"])
        self.assertEqual(environment["TMP"], str(workdir))
        self.assertNotIn("SHOULD_NOT_LEAK", environment)


if __name__ == "__main__":
    unittest.main()

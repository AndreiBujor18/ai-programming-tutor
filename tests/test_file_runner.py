from __future__ import annotations

import os
import shutil
import unittest

from ai_programming_tutor.catalog import parse_test_case
from ai_programming_tutor.dataset import test_suite_fingerprint
from ai_programming_tutor.models import (
    MAX_TEST_FILE_BYTES,
    MAX_TEST_FILES,
    CompilationResult,
    EvaluationResult,
    Exercise,
    FileResult,
    TestCase,
    TestFile,
    TestResult,
)
from ai_programming_tutor.runner import CRunner


GCC_AVAILABLE = shutil.which("gcc") is not None


def _exercise(*cases: TestCase) -> Exercise:
    return Exercise(
        id="file_contract",
        title="File contract",
        statement="Use the project-authored files.",
        input_format="No standard input.",
        output_format="Write the requested output file.",
        tags=("files",),
        starter_code="",
        reference_solution="",
        tests=cases,
    )


class FileContractTests(unittest.TestCase):
    def test_parser_accepts_bounded_file_entries(self) -> None:
        case = parse_test_case(
            {
                "name": "public-file-case",
                "input": "",
                "expected": "",
                "fixtures": [{"name": "input.txt", "content": "2\n"}],
                "expected_files": [{"name": "output.txt", "content": "4\n"}],
            }
        )
        self.assertEqual(case.fixtures, (TestFile("input.txt", "2\n"),))
        self.assertEqual(case.expected_files, (TestFile("output.txt", "4\n"),))

    def test_parser_rejects_unknown_or_malformed_fields(self) -> None:
        base = {"name": "case", "input": "", "expected": ""}
        with self.assertRaisesRegex(ValueError, "Unknown test-case fields"):
            parse_test_case({**base, "source": "private"})
        with self.assertRaisesRegex(ValueError, "fixtures must be a list"):
            parse_test_case({**base, "fixtures": {}})
        with self.assertRaisesRegex(ValueError, "fixtures must be a list"):
            parse_test_case({**base, "fixtures": None})
        with self.assertRaisesRegex(ValueError, "requires only name and content"):
            parse_test_case(
                {**base, "fixtures": [{"name": "input.txt", "content": "", "extra": 1}]}
            )

    def test_filenames_are_flat_portable_and_runner_names_are_reserved(self) -> None:
        invalid_names = (
            "../secret.txt",
            "/absolute.txt",
            r"folder\file.txt",
            ".hidden",
            "trailing.",
            "CON.txt",
            "program.stdout",
        )
        for name in invalid_names:
            with self.subTest(name=name), self.assertRaises(ValueError):
                TestFile(name, "content")

    def test_entry_count_duplicate_names_and_byte_limits_are_enforced(self) -> None:
        entries = tuple(TestFile(f"file-{index}.txt", "") for index in range(MAX_TEST_FILES))
        with self.assertRaisesRegex(ValueError, "at most 8 file entries"):
            TestCase("case", "", "", fixtures=entries, expected_files=(TestFile("extra", ""),))
        with self.assertRaisesRegex(ValueError, "repeat a fixture name"):
            TestCase(
                "case",
                "",
                "",
                fixtures=(TestFile("Data.txt", "a"), TestFile("data.TXT", "b")),
            )
        with self.assertRaisesRegex(ValueError, "identical spelling"):
            TestCase(
                "case",
                "",
                "",
                fixtures=(TestFile("Data.txt", "a"),),
                expected_files=(TestFile("data.TXT", "b"),),
            )
        with self.assertRaisesRegex(ValueError, "at most 32000 bytes"):
            TestFile("large.txt", "é" * (MAX_TEST_FILE_BYTES // 2 + 1))
        full_file = "a" * MAX_TEST_FILE_BYTES
        with self.assertRaisesRegex(ValueError, "may total at most 64000 bytes"):
            TestCase(
                "case",
                "",
                "",
                fixtures=(TestFile("first.txt", full_file), TestFile("second.txt", full_file)),
                expected_files=(TestFile("third.txt", "x"),),
            )

    def test_public_view_exposes_only_public_authored_file_contracts(self) -> None:
        public = TestCase(
            "public",
            "",
            "",
            fixtures=(TestFile("input.txt", "public fixture"),),
            expected_files=(TestFile("output.txt", "public result"),),
        )
        hidden = TestCase(
            "hidden",
            "",
            "",
            hidden=True,
            fixtures=(TestFile("input.txt", "hidden fixture"),),
            expected_files=(TestFile("output.txt", "hidden result"),),
        )
        view = _exercise(public, hidden).public_view()
        self.assertEqual(len(view["public_tests"]), 1)
        self.assertEqual(view["public_tests"][0]["fixtures"][0]["content"], "public fixture")
        self.assertNotIn("hidden fixture", str(view))
        self.assertNotIn("hidden result", str(view))

    def test_hidden_file_values_are_redacted_from_serialization(self) -> None:
        result = EvaluationResult(
            "file_contract",
            CompilationResult(True, 0),
            (
                TestResult(
                    "private-case",
                    True,
                    "wrong_answer",
                    "",
                    "",
                    "diagnostic",
                    0,
                    1.0,
                    (FileResult("output.txt", "wrong_answer", "secret", "leaked"),),
                ),
            ),
        )
        hidden = result.to_dict(reveal_hidden=False)["tests"][0]
        self.assertEqual(hidden["name"], "hidden-test-1")
        self.assertEqual(hidden["stderr"], "")
        self.assertEqual(hidden["file_results"][0]["name"], "hidden-file-1")
        self.assertEqual(hidden["file_results"][0]["expected"], "")
        self.assertEqual(hidden["file_results"][0]["actual"], "")

    def test_file_contract_changes_the_dataset_fingerprint(self) -> None:
        first = _exercise(
            TestCase(
                "case",
                "",
                "",
                fixtures=(TestFile("input.txt", "first"),),
                expected_files=(TestFile("output.txt", "result"),),
            )
        )
        changed_fixture = _exercise(
            TestCase(
                "case",
                "",
                "",
                fixtures=(TestFile("input.txt", "second"),),
                expected_files=(TestFile("output.txt", "result"),),
            )
        )
        changed_expected = _exercise(
            TestCase(
                "case",
                "",
                "",
                fixtures=(TestFile("input.txt", "first"),),
                expected_files=(TestFile("output.txt", "other"),),
            )
        )
        fingerprints = {
            test_suite_fingerprint(first),
            test_suite_fingerprint(changed_fixture),
            test_suite_fingerprint(changed_expected),
        }
        self.assertEqual(len(fingerprints), 3)


@unittest.skipUnless(GCC_AVAILABLE, "GCC is required for file-runner tests")
class FileRunnerTests(unittest.TestCase):
    def test_each_case_receives_a_fresh_workspace(self) -> None:
        source = r'''#include <stdio.h>

int main(void) {
    FILE *input = fopen("input.txt", "r");
    FILE *output = fopen("output.txt", "a");
    int value;
    if (input == NULL || output == NULL || fscanf(input, "%d", &value) != 1) {
        return 2;
    }
    fprintf(output, "%d\n", value * 2);
    fclose(input);
    fclose(output);
    return 0;
}
'''
        exercise = _exercise(
            TestCase(
                "first",
                "",
                "",
                fixtures=(TestFile("input.txt", "2\n"),),
                expected_files=(TestFile("output.txt", "4\n"),),
            ),
            TestCase(
                "second",
                "",
                "",
                fixtures=(TestFile("input.txt", "3\n"),),
                expected_files=(TestFile("output.txt", "6\n"),),
            ),
        )
        result = CRunner().evaluate(source, exercise)
        self.assertTrue(result.all_passed, result.to_dict(reveal_hidden=True))
        self.assertEqual(
            [case.file_results[0].status for case in result.tests],
            ["passed", "passed"],
        )

    def test_wrong_and_missing_output_files_fail_the_case(self) -> None:
        source = r'''#include <stdio.h>

int main(void) {
    FILE *output = fopen("output.txt", "w");
    if (output == NULL) {
        return 2;
    }
    fputs("wrong\n", output);
    fclose(output);
    return 0;
}
'''
        exercise = _exercise(
            TestCase(
                "wrong",
                "",
                "",
                expected_files=(TestFile("output.txt", "right\n"),),
            ),
            TestCase(
                "missing",
                "",
                "",
                expected_files=(TestFile("missing.txt", "right\n"),),
            ),
        )
        result = CRunner().evaluate(source, exercise)
        self.assertEqual([case.status for case in result.tests], ["wrong_answer", "wrong_answer"])
        self.assertEqual(
            [case.file_results[0].status for case in result.tests],
            ["wrong_answer", "missing"],
        )

    def test_output_file_size_is_bounded(self) -> None:
        source = r'''#include <stdio.h>

int main(void) {
    FILE *output = fopen("output.txt", "w");
    if (output == NULL) {
        return 2;
    }
    fputs("1234567890", output);
    fclose(output);
    return 0;
}
'''
        exercise = _exercise(
            TestCase(
                "large-output",
                "",
                "",
                expected_files=(TestFile("output.txt", "1234567890"),),
            )
        )
        result = CRunner(max_output_bytes=4).evaluate(source, exercise)
        self.assertEqual(result.tests[0].status, "wrong_answer")
        self.assertEqual(result.tests[0].file_results[0].status, "output_limit")
        self.assertIn("[output truncated]", result.tests[0].file_results[0].actual)

    def test_output_file_must_be_utf8_text(self) -> None:
        source = r'''#include <stdio.h>

int main(void) {
    FILE *output = fopen("output.txt", "wb");
    if (output == NULL) {
        return 2;
    }
    fputc(255, output);
    fclose(output);
    return 0;
}
'''
        exercise = _exercise(
            TestCase(
                "binary-output",
                "",
                "",
                expected_files=(TestFile("output.txt", "text"),),
            )
        )
        result = CRunner().evaluate(source, exercise)
        self.assertEqual(result.tests[0].status, "wrong_answer")
        self.assertEqual(result.tests[0].file_results[0].status, "invalid_encoding")

    @unittest.skipIf(os.name == "nt", "Symbolic-link setup is POSIX-specific")
    def test_symbolic_link_is_not_accepted_as_an_output_file(self) -> None:
        source = r'''int symlink(const char *target, const char *link_path);

int main(void) {
    return symlink("input.txt", "output.txt") == 0 ? 0 : 2;
}
'''
        exercise = _exercise(
            TestCase(
                "link",
                "",
                "",
                fixtures=(TestFile("input.txt", "do not follow\n"),),
                expected_files=(TestFile("output.txt", "do not follow\n"),),
            )
        )
        result = CRunner().evaluate(source, exercise)
        self.assertEqual(result.tests[0].status, "wrong_answer")
        self.assertEqual(result.tests[0].file_results[0].status, "invalid_type")
        self.assertEqual(result.tests[0].file_results[0].actual, "")


if __name__ == "__main__":
    unittest.main()

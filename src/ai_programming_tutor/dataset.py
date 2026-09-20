from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ai_programming_tutor.catalog import get_exercise, list_exercises
from ai_programming_tutor.models import Exercise
from ai_programming_tutor.runner import CRunner

# Dataset provenance changes only when mutation logic changes, not on a UI release.
GENERATOR_VERSION = "0.3.0"


@dataclass(frozen=True)
class MutationRule:
    label: str
    find: str
    replace: str
    evidence_basis: str = "author_designed_v0.1"

    def apply(self, source: str) -> str:
        if source.count(self.find) != 1:
            raise ValueError(
                f"Mutation anchor for {self.label!r} must occur exactly once; "
                f"found {source.count(self.find)} occurrences of {self.find!r}."
            )
        return source.replace(self.find, self.replace, 1)


MUTATION_RULES: dict[str, tuple[MutationRule, ...]] = {
    "vector_average": (
        MutationRule("loop_boundary", "position < item_count;", "position < item_count - 1;"),
        MutationRule("wrong_initialization", "long long total = 0;", "long long total = 1;"),
        MutationRule("missing_update", "total += values[position];", "(void) values[position];"),
        MutationRule(
            "invalid_index", "total += values[position];", "total += values[position + 1];"
        ),
        MutationRule(
            "integer_division",
            "(double) total / item_count",
            "(double) (total / item_count)",
        ),
        MutationRule(
            "accumulator_misuse", "total += values[position];", "total = values[position];"
        ),
    ),
    "min_max": (
        MutationRule(
            "loop_boundary",
            "position = 1; position < item_count;",
            "position = 1; position < item_count - 1;",
        ),
        MutationRule(
            "relational_operator", "values[position] < minimum", "values[position] > minimum"
        ),
        MutationRule("wrong_initialization", "int minimum = values[0];", "int minimum = 0;"),
        MutationRule(
            "missing_update", "maximum = values[position];", "(void) values[position];"
        ),
        MutationRule(
            "invalid_index", "values[position] < minimum", "values[position - 1] < minimum"
        ),
    ),
    "palindrome": (
        MutationRule(
            "loop_boundary", "position < length / 2 &&", "position < length / 2 - 1 &&"
        ),
        MutationRule("relational_operator", "word[position] != word[", "word[position] == word["),
        MutationRule("wrong_initialization", "int is_palindrome = 1;", "int is_palindrome = 0;"),
        MutationRule("missing_update", "is_palindrome = 0;", "(void) is_palindrome;"),
        MutationRule(
            "invalid_index", "length - position - 1]", "length - position]"
        ),
        MutationRule(
            "logical_condition", "&& is_palindrome;", "|| is_palindrome;"
        ),
    ),
    "diagonal_average": (
        MutationRule(
            "loop_boundary",
            "position = 0; position < item_count; position++",
            "position = 0; position < item_count - 1; position++",
        ),
        MutationRule("wrong_initialization", "long long total = 0;", "long long total = 1;"),
        MutationRule(
            "missing_update",
            "total += matrix[position][position];",
            "(void) matrix[position][position];",
        ),
        MutationRule(
            "invalid_index", "matrix[position][position]", "matrix[position][0]"
        ),
        MutationRule(
            "integer_division",
            "(double) total / item_count",
            "(double) (total / item_count)",
        ),
        MutationRule(
            "accumulator_misuse",
            "total += matrix[position][position];",
            "total = matrix[position][position];",
        ),
    ),
    "frequency_count": (
        MutationRule(
            "loop_boundary",
            "position = 0; position < item_count; position++) {\n        if",
            "position = 0; position < item_count - 1; position++) {\n        if",
        ),
        MutationRule("relational_operator", "values[position] == target", "values[position] != target"),
        MutationRule("wrong_initialization", "int frequency = 0;", "int frequency = 1;"),
        MutationRule("missing_update", "frequency++;", "(void) frequency;"),
        MutationRule("invalid_index", "values[position] == target", "values[0] == target"),
        MutationRule(
            "logical_condition", "&& position >= 0", "|| position >= 0"
        ),
        MutationRule("accumulator_misuse", "frequency++;", "frequency = 1;"),
    ),
    "interval_parity": (
        MutationRule(
            "logical_condition",
            "item_count % 2 == 0",
            "item_count % 2 != 0",
            "CURR-C-002",
        ),
        MutationRule(
            "wrong_identifier_or_argument",
            "upper_bound - lower_bound + 1",
            "upper_bound - upper_bound + 1",
            "CURR-C-002",
        ),
    ),
    "vector_insert": (
        MutationRule(
            "loop_boundary",
            "index > insertion_position;",
            "index > insertion_position + 1;",
            "C-SEED-006",
        ),
        MutationRule(
            "invalid_index",
            "values[index] = values[index - 1];",
            "values[index - 1] = values[index];",
            "C-SEED-006",
        ),
        MutationRule(
            "missing_update", "item_count++;", "(void) item_count;", "C-SEED-003"
        ),
        MutationRule(
            "wrong_identifier_or_argument",
            "values[insertion_position] = inserted_value;",
            "values[insertion_position] = insertion_position;",
            "C-SEED-004",
        ),
    ),
    "delete_occurrences": (
        MutationRule(
            "loop_boundary",
            "index < item_count - 1;",
            "index < item_count - 2;",
            "C-SEED-006",
        ),
        MutationRule(
            "relational_operator",
            "values[position] == target",
            "values[position] != target",
            "C-SEED-006",
        ),
        MutationRule(
            "missing_update", "removed_count++;", "(void) removed_count;", "C-SEED-003"
        ),
        MutationRule(
            "invalid_index",
            "values[index] = values[index + 1];",
            "values[index] = values[index + 2];",
            "C-SEED-006",
        ),
        MutationRule(
            "wrong_identifier_or_argument",
            "values[position] == target",
            "values[position] == item_count",
            "C-SEED-004",
        ),
    ),
    "vector_menu": (
        MutationRule("menu_dispatch", "case 'S':", "case 'A':", "C-SEED-001"),
        MutationRule(
            "input_buffer_misuse",
            'scanf(" %c", &command);',
            'scanf("%c", &command);',
            "C-SEED-002",
        ),
        MutationRule(
            "invalid_program_state",
            "case 'S':\n            if (!has_values) {",
            "case 'S':\n            if (0) {",
            "C-SEED-003",
        ),
        MutationRule(
            "wrong_identifier_or_argument",
            "vector_sum(values, item_count)",
            "vector_sum(values, item_count - 1)",
            "C-SEED-004",
        ),
        MutationRule(
            "wrong_initialization", "int has_values = 0;", "int has_values = 1;", "C-SEED-003"
        ),
        MutationRule(
            "missing_update", "has_values = 1;", "(void) has_values;", "C-SEED-003"
        ),
    ),
    "matrix_menu": (
        MutationRule("menu_dispatch", "case 'X':", "case 'M':", "C-SEED-001"),
        MutationRule(
            "input_buffer_misuse",
            'scanf(" %c", &command);',
            'scanf("%c", &command);',
            "C-SEED-002",
        ),
        MutationRule(
            "invalid_program_state",
            "case 'X':\n            if (!has_matrix) {",
            "case 'X':\n            if (0) {",
            "C-SEED-003",
        ),
        MutationRule(
            "wrong_identifier_or_argument",
            "print_row_maxima(matrix, row_count, column_count);",
            "print_row_maxima(matrix, column_count, row_count);",
            "C-SEED-004",
        ),
        MutationRule(
            "relational_operator",
            "matrix[row][column] > maximum",
            "matrix[row][column] < maximum",
            "C-SEED-004",
        ),
        MutationRule(
            "wrong_initialization",
            "int maximum = matrix[row][0];",
            "int maximum = 0;",
            "C-SEED-004",
        ),
        MutationRule(
            "missing_update", "has_matrix = 1;", "(void) has_matrix;", "C-SEED-003"
        ),
    ),
    "line_after_number": (
        MutationRule(
            "input_buffer_misuse",
            "    while ((character = getchar()) != '\\n' && character != EOF) {\n    }",
            "    (void) character;",
            "C-SEED-002",
        ),
        MutationRule(
            "relational_operator", "!= '\\n' && character", "== '\\n' && character", "C-SEED-002"
        ),
        MutationRule(
            "wrong_identifier_or_argument",
            'printf("%d:%s\\n", identifier, text);',
            'printf("%d:%s\\n", identifier, text + 1);',
            "C-SEED-004",
        ),
        MutationRule(
            "sentinel_handling",
            "    while ((character = getchar()) != '\\n' && character != EOF) {\n    }",
            "    while ((character = getchar()) != EOF) {\n    }",
            "CURR-C-002",
        ),
    ),
    "odd_digit_count": (
        MutationRule(
            "wrong_initialization", "int frequency = 0;", "int frequency = 1;", "CURR-C-002"
        ),
        MutationRule(
            "relational_operator", "digit % 2 != 0", "digit % 2 == 0", "CURR-C-002"
        ),
        MutationRule(
            "missing_update", "frequency++;", "(void) frequency;", "CURR-C-002"
        ),
        MutationRule(
            "accumulator_misuse", "frequency++;", "frequency = 1;", "CURR-C-002"
        ),
    ),
    "perfect_squares": (
        MutationRule(
            "loop_boundary", "root * root <= limit;", "root * root < limit;", "CURR-C-002"
        ),
        MutationRule(
            "wrong_initialization", "int printed = 0;", "int printed = 1;", "CURR-C-002"
        ),
        MutationRule(
            "missing_update", "printed = 1;", "(void) printed;", "CURR-C-002"
        ),
    ),
    "sentinel_average": (
        MutationRule(
            "sentinel_handling", "if (value != 0)", "if (1)", "CURR-C-002"
        ),
        MutationRule(
            "wrong_initialization", "long long total = 0;", "long long total = 1;", "CURR-C-002"
        ),
        MutationRule(
            "missing_update", "item_count++;", "(void) item_count;", "CURR-C-002"
        ),
        MutationRule(
            "integer_division",
            "(double) total / item_count",
            "(double) (total / item_count)",
            "CURR-C-002",
        ),
        MutationRule(
            "accumulator_misuse", "total += value;", "total = value;", "CURR-C-002"
        ),
        MutationRule(
            "invalid_program_state", "if (item_count == 0)", "if (0)", "CURR-C-002"
        ),
    ),
}


# The two file families remain outside frozen generator 0.3.0 until their mutation
# rules and any file-specific category receive an explicit benchmark review.
# Keeping this allowlist explicit prevents catalog additions from disappearing
# from the benchmark silently.
BENCHMARK_EXCLUDED_EXERCISES = frozenset({"file_longest_word", "file_number_summary"})


IDENTIFIER_OPTIONS: dict[str, tuple[str, str, str, str]] = {
    "item_count": ("item_count", "size", "element_count", "number_of_items"),
    "position": ("position", "index", "cursor", "pos"),
    "values": ("values", "numbers", "elements", "data"),
    "total": ("total", "sum", "aggregate", "running_total"),
    "minimum": ("minimum", "smallest", "min_value", "low"),
    "maximum": ("maximum", "largest", "max_value", "high"),
    "length": ("length", "text_length", "character_count", "word_size"),
    "is_palindrome": ("is_palindrome", "valid", "palindrome_flag", "matches"),
    "word": ("word", "text", "candidate", "token"),
    "matrix": ("matrix", "grid", "table", "cells"),
    "row": ("row", "row_index", "rpos", "line_index"),
    "column": ("column", "column_index", "cpos", "col_index"),
    "target": ("target", "needle", "searched_value", "wanted"),
    "frequency": ("frequency", "occurrences", "match_count", "answer"),
    "index": ("index", "shift_index", "source_index", "cursor_index"),
    "inserted_value": ("inserted_value", "new_value", "value_to_insert", "added_value"),
    "insertion_position": ("insertion_position", "insert_at", "target_position", "slot"),
    "removed_count": ("removed_count", "deletion_count", "removed", "deleted_total"),
    "command_count": ("command_count", "operation_count", "menu_steps", "query_count"),
    "command_index": ("command_index", "operation_index", "step", "query_index"),
    "command": ("command", "option", "choice", "operation"),
    "has_values": ("has_values", "vector_ready", "is_loaded", "data_available"),
    "row_count": ("row_count", "rows", "line_count", "matrix_height"),
    "column_count": ("column_count", "columns", "column_total", "matrix_width"),
    "has_matrix": ("has_matrix", "matrix_ready", "grid_loaded", "table_available"),
    "identifier": ("identifier", "record_id", "numeric_id", "code_number"),
    "character": ("character", "ch", "discarded_character", "current_character"),
    "text": ("text", "line", "message", "content"),
    "lower_bound": ("lower_bound", "left", "start", "lower"),
    "upper_bound": ("upper_bound", "right", "end", "upper"),
    "number": ("number", "remaining", "digits", "numeric_value"),
    "digit": ("digit", "current_digit", "remainder", "last_digit"),
    "value": ("value", "input_value", "current_value", "read_value"),
    "limit": ("limit", "upper_limit", "bound", "maximum_value"),
    "root": ("root", "candidate", "base", "square_root"),
    "square": ("square", "current_square", "power", "squared_value"),
    "printed": ("printed", "has_output", "wrote_value", "found_square"),
}


def _style_variant(source: str, variant: int) -> str:
    # Two independent four-way choices guarantee 16 distinct variants per mutation.
    offsets = {
        "item_count": variant // 4,
        "position": variant % 4,
    }
    keys = sorted(IDENTIFIER_OPTIONS, key=len, reverse=True)
    pattern = re.compile(r"\b(?:" + "|".join(map(re.escape, keys)) + r")\b")

    def replace_identifier(match: re.Match[str]) -> str:
        original = match.group(0)
        choice = offsets.get(original, (variant + keys.index(original)) % 4)
        return IDENTIFIER_OPTIONS[original][choice]

    styled = pattern.sub(replace_identifier, source)
    if variant % 2:
        styled = styled.replace("    ", "  ")
    if variant % 3 == 2:
        styled = styled.replace(") {\n", ")\n{\n")
    return styled


def _fingerprint(parts: list[str]) -> str:
    payload = "\0".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def _test_suite_fingerprint(exercise: Exercise) -> str:
    return _fingerprint(
        [
            json.dumps(
                {
                    "name": case.name,
                    "input": case.input,
                    "expected": case.expected,
                    "hidden": case.hidden,
                    "fixtures": [
                        {"name": item.name, "content": item.content}
                        for item in case.fixtures
                    ],
                    "expected_files": [
                        {"name": item.name, "content": item.content}
                        for item in case.expected_files
                    ],
                },
                sort_keys=True,
            )
            for case in exercise.tests
        ]
    )


def _compiler_identity(compiler: str) -> str:
    try:
        process = subprocess.run(
            [compiler, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return compiler
    first_line = next((line.strip() for line in process.stdout.splitlines() if line.strip()), "")
    return first_line or compiler


def iter_samples(variants: int = 16, evaluate: bool = True):
    if variants < 1 or variants > 16:
        raise ValueError("variants must be between 1 and 16")
    runner = CRunner()
    compiler_identity = _compiler_identity(runner.compiler) if evaluate else "not-evaluated"
    for exercise in list_exercises():
        if exercise.id in BENCHMARK_EXCLUDED_EXERCISES:
            continue
        try:
            rules = MUTATION_RULES[exercise.id]
        except KeyError as exc:
            raise ValueError(
                f"Exercise {exercise.id!r} needs reviewed mutation rules or an explicit "
                "benchmark-exclusion decision."
            ) from exc
        exercise_fingerprint = _fingerprint(
            [
                exercise.id,
                exercise.statement,
                exercise.input_format,
                exercise.output_format,
                exercise.reference_solution,
            ]
        )
        test_suite_fingerprint = _test_suite_fingerprint(exercise)
        for rule in rules:
            mutated = rule.apply(exercise.reference_solution)
            for variant in range(variants):
                source = _style_variant(mutated, variant)
                record: dict[str, object] = {
                    "id": f"{exercise.id}:{rule.label}:{variant:02d}",
                    "exercise_id": exercise.id,
                    "label": rule.label,
                    "variant": variant,
                    "origin": "controlled_mutation",
                    "evidence_basis": rule.evidence_basis,
                    "dataset_schema_version": "0.3",
                    "generator_version": GENERATOR_VERSION,
                    "exercise_fingerprint": exercise_fingerprint,
                    "test_suite_fingerprint": test_suite_fingerprint,
                    "compiler_identity": compiler_identity,
                    "labeler": "controlled-mutation-generator",
                    "source": source,
                }
                if evaluate:
                    result = runner.evaluate(source, exercise)
                    record["signals"] = {
                        "compiled": result.compilation.succeeded,
                        "compiler_excerpt": result.compilation.stderr[:1000],
                        "passed_count": result.passed_count,
                        "total_count": result.total_count,
                        "test_statuses": [test.status for test in result.tests],
                    }
                yield record


def generate_dataset(output: Path, variants: int = 16, evaluate: bool = True) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output.open("w", encoding="utf-8") as stream:
        for sample in iter_samples(variants=variants, evaluate=evaluate):
            stream.write(json.dumps(sample, ensure_ascii=False) + "\n")
            count += 1
    return count

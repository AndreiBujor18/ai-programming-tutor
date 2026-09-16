from __future__ import annotations

import re

from ai_programming_tutor.models import DiagnosisCandidate, EvaluationResult


def _compact(source: str) -> str:
    return re.sub(r"\s+", " ", source)


def diagnose(source: str, evaluation: EvaluationResult) -> tuple[DiagnosisCandidate, ...]:
    """Rank likely beginner mistakes using transparent, exercise-aware heuristics."""
    if not evaluation.compilation.succeeded:
        first_line = next(
            (line.strip() for line in evaluation.compilation.stderr.splitlines() if line.strip()),
            "The compiler rejected the submission.",
        )
        return (DiagnosisCandidate("compilation_error", 0.99, first_line[:240]),)
    if evaluation.all_passed:
        return ()

    code = _compact(source)
    exercise_id = evaluation.exercise_id
    ranked: dict[str, DiagnosisCandidate] = {}

    def add(category: str, confidence: float, evidence: str) -> None:
        previous = ranked.get(category)
        if previous is None or confidence > previous.confidence:
            ranked[category] = DiagnosisCandidate(category, confidence, evidence)

    index_name = r"(?:position|index|cursor|pos|i|row|column)"
    if re.search(r"for\s*\([^;]+;[^;]+<\s*[^;]+-\s*1\s*;", code):
        add("loop_boundary", 0.91, "A loop bound appears to stop one position before its stated limit.")
    if exercise_id != "delete_occurrences" and re.search(
        rf"\[\s*{index_name}\s*\+\s*1\s*\]", code
    ):
        add("invalid_index", 0.94, "An array access is shifted one place beyond the current index.")
    if exercise_id != "vector_insert" and re.search(
        rf"\[\s*{index_name}\s*-\s*1\s*\]", code
    ):
        add("invalid_index", 0.88, "An array access uses the element before the current loop position.")
    if re.search(r"\(\s*void\s*\)\s*(?:values|numbers|elements|data|matrix|grid|table|cells)", code):
        add("missing_update", 0.91, "A value is read inside the key loop but deliberately discarded.")

    if exercise_id in {"vector_average", "diagonal_average"}:
        has_float_format = "%.2f" in code
        late_cast = bool(
            re.search(r"\(\s*(?:double|float)\s*\)\s*\([^()]*\/[^()]*\)", code)
        )
        has_float_operand = bool(
            re.search(r"\(\s*(?:double|float)\s*\)", code)
            or re.search(r"(?:1\.0|1\.0f)\s*\*", code)
        )
        if has_float_format and (late_cast or not has_float_operand):
            add(
                "integer_division",
                0.96,
                "The conversion occurs after the integer operands have already been divided.",
            )
        if re.search(r"\b(?:total|sum|aggregate|running_total|result|answer)\s*=\s*1\s*;", code):
            add("wrong_initialization", 0.90, "The accumulator starts from one instead of a neutral value.")
        if re.search(
            r"\b(?:total|sum|aggregate|running_total|result|answer)\s*=\s*"
            r"(?:values|numbers|elements|data|array|matrix|grid|table|cells)\s*\[",
            code,
        ):
            add("accumulator_misuse", 0.93, "The result is replaced by the current element inside a loop.")

    if exercise_id == "min_max":
        if re.search(
            r"(?:value|values|numbers|elements|data|array).*?>\s*"
            r"(?:minimum|min_value|smallest|low)",
            code,
        ):
            add("relational_operator", 0.88, "The comparison used to update the minimum points upward.")
        if re.search(
            r"(?:value|values|numbers|elements|data|array).*?<\s*"
            r"(?:maximum|max_value|largest|high)",
            code,
        ):
            add("relational_operator", 0.88, "The comparison used to update the maximum points downward.")
        if re.search(r"\b(?:minimum|min_value|smallest|low)\s*=\s*0\s*;", code):
            add("wrong_initialization", 0.78, "The minimum is seeded with a fixed zero despite arbitrary input.")

    if exercise_id == "palindrome":
        if re.search(
            r"\bint\s+(?:is_palindrome|palindrome|palindrome_flag|valid|matches|ok)\s*=\s*0\s*;",
            code,
        ):
            add("wrong_initialization", 0.92, "The validity flag is false before any characters are compared.")
        if re.search(r"&&\s*!\s*(?:is_palindrome|palindrome|ok)", code):
            add("logical_condition", 0.94, "The loop requires the validity flag to be false before checking.")
        if re.search(r"\|\|\s*(?:is_palindrome|palindrome|palindrome_flag|valid|matches)", code):
            add("logical_condition", 0.95, "Either side can keep the comparison loop active beyond its valid range.")
        if re.search(
            r"(?:word|text|candidate|token)\s*\[[^\]]+\]\s*==\s*"
            r"(?:word|text|candidate|token)\s*\[",
            code,
        ):
            add("relational_operator", 0.92, "Matching mirrored characters are treated as a failure.")
        if re.search(r"\(\s*void\s*\)\s*(?:is_palindrome|valid|palindrome_flag|matches)", code):
            add("missing_update", 0.93, "A detected mismatch does not change the validity flag.")
        if re.search(
            r"\[[^\]]*(?:length|text_length|character_count|word_size)[^\]]*-\s*"
            r"(?:position|index|cursor|pos|i)\s*\]",
            code,
        ):
            add("invalid_index", 0.89, "The mirrored position does not subtract the zero-based offset.")

    if exercise_id == "diagonal_average" and re.search(
        r"(?:matrix|grid|table|cells)\s*\[\s*(?:position|index|cursor|pos)\s*\]\s*\[\s*0\s*\]",
        code,
    ):
        add("invalid_index", 0.90, "The second matrix index is fixed instead of following the diagonal.")

    if exercise_id == "frequency_count":
        counter_name = r"(?:frequency|matches|occurrences|match_count|answer)"
        if re.search(rf"\bint\s+{counter_name}\s*=\s*1\s*;", code):
            add("wrong_initialization", 0.93, "The counter starts with a match that has not occurred.")
        if re.search(r"!=\s*(?:target|searched_value|needle|wanted)", code):
            add("relational_operator", 0.91, "The comparison counts values different from the target.")
        if re.search(r"\|\|[^;{}]*(?:>=\s*0|<\s*(?:item_count|size|n))", code):
            add("logical_condition", 0.92, "One side of an OR condition is true for every valid iteration.")
        if re.search(rf"(?:\{{|;)\s*{counter_name}\s*=\s*1\s*;", code):
            add("accumulator_misuse", 0.94, "Each match writes a fixed value instead of retaining earlier matches.")
        if re.search(rf"\(\s*void\s*\)\s*{counter_name}\s*;", code):
            add("missing_update", 0.94, "A matching value does not increment the counter.")
        if re.search(
            r"(?:values|numbers|elements|data)\s*\[\s*0\s*\]\s*(?:==|!=)\s*"
            r"(?:target|needle|searched_value|wanted)",
            code,
        ):
            add("invalid_index", 0.90, "Every iteration compares the first element instead of the current one.")

    if exercise_id == "interval_parity":
        count_name = r"(?:item_count|size|element_count|number_of_items)"
        bound_name = r"(?:upper_bound|right|end|upper)"
        if re.search(rf"{count_name}\s*%\s*2\s*!=\s*0", code):
            add("logical_condition", 0.98, "The even and odd branches are selected in reverse.")
        if re.search(rf"(?P<bound>{bound_name})\s*-\s*(?P=bound)\s*\+\s*1", code):
            add(
                "wrong_identifier_or_argument",
                0.98,
                "Both ends of the interval expression use the same boundary.",
            )

    if exercise_id == "odd_digit_count":
        frequency_name = r"(?:frequency|occurrences|match_count|answer)"
        digit_name = r"(?:digit|current_digit|remainder|last_digit)"
        if re.search(rf"\bint\s+{frequency_name}\s*=\s*1\s*;", code):
            add("wrong_initialization", 0.98, "The digit counter starts with a match not yet seen.")
        if re.search(rf"{digit_name}\s*%\s*2\s*==\s*0", code):
            add("relational_operator", 0.98, "The branch counts even digits instead of odd digits.")
        if re.search(rf"\(\s*void\s*\)\s*{frequency_name}\s*;", code):
            add("missing_update", 0.98, "An odd digit does not increase the counter.")
        if re.search(rf"(?:\{{|;)\s*{frequency_name}\s*=\s*1\s*;", code):
            add("accumulator_misuse", 0.99, "Each odd digit overwrites the count with one.")

    if exercise_id == "perfect_squares":
        root_name = r"(?:root|candidate|base|square_root)"
        limit_name = r"(?:limit|upper_limit|bound|maximum_value)"
        printed_name = r"(?:printed|has_output|wrote_value|found_square)"
        if re.search(rf"{root_name}\s*\*\s*{root_name}\s*<\s*{limit_name}", code):
            add("loop_boundary", 0.98, "A square equal to the limit is excluded.")
        if re.search(rf"\bint\s+{printed_name}\s*=\s*1\s*;", code):
            add("wrong_initialization", 0.98, "The output flag starts as though a square was printed.")
        if re.search(rf"\(\s*void\s*\)\s*{printed_name}\s*;", code):
            add("missing_update", 0.98, "Printing a square does not update the output state.")

    if exercise_id == "sentinel_average":
        total_name = r"(?:total|sum|aggregate|running_total)"
        count_name = r"(?:item_count|size|element_count|number_of_items)"
        value_name = r"(?:value|input_value|current_value|read_value)"
        if re.search(r"if\s*\(\s*1\s*\)", code):
            add("sentinel_handling", 0.99, "The stop marker is processed as an ordinary value.")
        if re.search(rf"\blong\s+long\s+{total_name}\s*=\s*1\s*;", code):
            add("wrong_initialization", 0.98, "The total starts above its neutral value.")
        if re.search(rf"\(\s*void\s*\)\s*{count_name}\s*;", code):
            add("missing_update", 0.98, "A real input value does not increase the value count.")
        if re.search(rf"{total_name}\s*=\s*{value_name}\s*;", code):
            add("accumulator_misuse", 0.98, "The running total is replaced by the latest value.")
        if re.search(rf"\(\s*(?:double|float)\s*\)\s*\(\s*{total_name}\s*/\s*{count_name}\s*\)", code):
            add("integer_division", 0.99, "The average is converted only after integer division.")
        if re.search(r"if\s*\(\s*0\s*\)", code):
            add("invalid_program_state", 0.99, "The empty-input guard can never run.")

    if exercise_id == "vector_insert":
        if re.search(
            r"(?:index|shift_index|source_index|cursor_index)\s*>\s*"
            r"(?:insertion_position|insert_at|target_position|slot)\s*\+\s*1",
            code,
        ):
            add("loop_boundary", 0.97, "The shift stops before moving the element at the insertion boundary.")
        if re.search(
            r"(?:values|numbers|elements|data)\s*\[\s*(?:index|shift_index|source_index|cursor_index)\s*-\s*1\s*\]\s*=\s*"
            r"(?:values|numbers|elements|data)\s*\[\s*(?:index|shift_index|source_index|cursor_index)\s*\]",
            code,
        ):
            add("invalid_index", 0.98, "The shift writes toward the wrong array position.")
        if re.search(r"\(\s*void\s*\)\s*(?:item_count|size|element_count|number_of_items)\s*;", code):
            add("missing_update", 0.98, "The logical vector size is not increased after insertion.")
        if re.search(
            r"\[\s*(?:insertion_position|insert_at|target_position|slot)\s*\]\s*=\s*"
            r"(?:insertion_position|insert_at|target_position|slot)\s*;",
            code,
        ):
            add(
                "wrong_identifier_or_argument",
                0.98,
                "The destination receives the position value rather than the value requested for insertion.",
            )

    if exercise_id == "delete_occurrences":
        if re.search(
            r"(?:index|shift_index|source_index|cursor_index)\s*<\s*"
            r"(?:item_count|size|element_count|number_of_items)\s*-\s*2",
            code,
        ):
            add("loop_boundary", 0.97, "The deletion shift stops two positions before the current size.")
        if re.search(r"!=\s*(?:target|needle|searched_value|wanted)", code):
            add("relational_operator", 0.98, "The deletion branch selects non-target values.")
        if re.search(
            r"\(\s*void\s*\)\s*(?:removed_count|deletion_count|removed|deleted_total)\s*;", code
        ):
            add("missing_update", 0.98, "A successful deletion is not added to the reported count.")
        if re.search(
            r"\[\s*(?:index|shift_index|source_index|cursor_index)\s*\+\s*2\s*\]", code
        ):
            add("invalid_index", 0.98, "The shift copies from two positions ahead instead of the next element.")
        if re.search(
            r"(?:values|numbers|elements|data)\s*\[[^\]]+\]\s*==\s*"
            r"(?:item_count|size|element_count|number_of_items)",
            code,
        ):
            add(
                "wrong_identifier_or_argument",
                0.98,
                "The current element is compared with the vector size instead of the deletion target.",
            )

    if exercise_id == "vector_menu":
        if "case 'A':" in code and "case 'S':" not in code:
            add("menu_dispatch", 0.98, "The sum operation is attached to a different menu key.")
        if re.search(r'scanf\s*\(\s*"%c"\s*,', code):
            add("input_buffer_misuse", 0.98, "The command read does not skip pending whitespace.")
        if re.search(r"case\s+'S'\s*:\s*if\s*\(\s*0\s*\)", code):
            add("invalid_program_state", 0.98, "The sum command bypasses the empty-vector guard.")
        if re.search(r"vector_sum\s*\([^,]+,\s*[^,)]+-\s*1\s*\)", code):
            add(
                "wrong_identifier_or_argument",
                0.98,
                "The sum function receives a shortened vector length.",
            )
        if re.search(
            r"int\s+(?:has_values|vector_ready|is_loaded|data_available)\s*=\s*1\s*;", code
        ):
            add("wrong_initialization", 0.97, "The menu starts as though vector input already exists.")
        if re.search(
            r"\(\s*void\s*\)\s*(?:has_values|vector_ready|is_loaded|data_available)\s*;", code
        ):
            add("missing_update", 0.98, "Reading a vector does not mark the program state as ready.")

    if exercise_id == "matrix_menu":
        if "case 'M':" in code and "case 'X':" not in code:
            add("menu_dispatch", 0.98, "The row-maximum operation is attached to a different menu key.")
        if re.search(r'scanf\s*\(\s*"%c"\s*,', code):
            add("input_buffer_misuse", 0.98, "The command read does not skip pending whitespace.")
        if re.search(r"case\s+'X'\s*:\s*if\s*\(\s*0\s*\)", code):
            add("invalid_program_state", 0.98, "The row query bypasses the empty-matrix guard.")
        if re.search(
            r"print_row_maxima\s*\(\s*(?:matrix|grid|table|cells)\s*,\s*"
            r"(?:column_count|columns|column_total|matrix_width)\s*,\s*"
            r"(?:row_count|rows|line_count|matrix_height)\s*\)",
            code,
        ):
            add(
                "wrong_identifier_or_argument",
                0.98,
                "The row and column counts are passed to the function in reverse order.",
            )
        if re.search(
            r"(?:matrix|grid|table|cells)\s*\[[^\]]+\]\s*\[[^\]]+\]\s*<\s*"
            r"(?:maximum|largest|max_value|high)",
            code,
        ):
            add("relational_operator", 0.97, "The row scan updates its maximum for smaller values.")
        if re.search(r"int\s+(?:maximum|largest|max_value|high)\s*=\s*0\s*;", code):
            add("wrong_initialization", 0.97, "Each row maximum is seeded with zero despite negative input.")
        if re.search(
            r"\(\s*void\s*\)\s*(?:has_matrix|matrix_ready|grid_loaded|table_available)\s*;", code
        ):
            add("missing_update", 0.98, "Reading a matrix does not mark the program state as ready.")

    if exercise_id == "line_after_number":
        if re.search(
            r"while\s*\(\s*\([^;{}]*getchar\s*\(\s*\)\s*\)\s*!=\s*EOF\s*\)",
            code,
        ):
            add(
                "sentinel_handling",
                0.99,
                "The cleanup loop ignores the line boundary and consumes the following text.",
            )
        if "fgets" in code and "scanf" in code and "getchar" not in code:
            add(
                "input_buffer_misuse",
                0.96,
                "The full-line read follows a token read without consuming the pending newline.",
            )
        if re.search(r"\(\s*void\s*\)\s*(?:character|ch|discarded_character|current_character)\s*;", code):
            add(
                "input_buffer_misuse",
                0.98,
                "The pending newline is left in the input stream before the full-line read.",
            )
        if re.search(r"getchar\s*\(\s*\)\s*\)\s*==\s*'\\n'", code):
            add("relational_operator", 0.97, "The cleanup loop continues after the newline instead of before it.")
        if re.search(r"(?:text|line|message|content)\s*\+\s*1\s*\)", code):
            add(
                "wrong_identifier_or_argument",
                0.98,
                "The output function receives a pointer starting after the first character.",
            )

    statuses = [test.status for test in evaluation.tests]
    if "timeout" in statuses:
        add("missing_update", 0.70, "At least one test exceeded the time limit, often caused by missing progress.")
    if 0 < evaluation.passed_count < evaluation.total_count:
        add("loop_boundary", 0.42, "Some tests pass while an edge case fails.")
    if not ranked:
        add("unknown", 0.25, "The current rules do not isolate one category reliably.")

    return tuple(sorted(ranked.values(), key=lambda candidate: candidate.confidence, reverse=True)[:3])

from __future__ import annotations

import unittest

from ai_programming_tutor.style_profile import (
    analyse_c_style,
    apply_c_style,
    detect_cpp_features,
    empty_style_profile,
    learn_c_style,
    normalise_style_profile,
    replace_c_identifiers,
)


ALLMAN_COMMENTED = """#include <stdio.h>

// citește valorile
// afișează suma
int main(void)
{
    int i;
    for (i = 0; i < 3; i++)
    {
        printf("%d", i);
    }
    return 0;
}
"""

COMPACT_PREFIX = """#include <stdio.h>
int main(void) {
  int i;
  for (i = 0; i < 3; ++i) {
    printf("%d", i);
  }
  return 0;
}
"""

NATURAL_A = """#include <stdio.h>

int main() {
    int a[32],m,j;

    // Preluăm dimensiunea colecției
    scanf("%d", &m);

    // Parcurgem toate pozițiile valide
    for (j = 0; j < m; j++) {
        scanf("%d", &a[j]);
    }
    return 0;
}
"""

NATURAL_B = """#include <stdio.h>

int main() {
    int m, a[32];
    scanf("%d", &m);
    for ( int j = 0; j < m; j = j + 1 )
    {
        scanf("%d", &a[j]);
    }
    return 0;
}
"""


class StyleAnalysisTests(unittest.TestCase):
    def test_distinct_examples_produce_distinct_preferences(self) -> None:
        profile_a = learn_c_style(ALLMAN_COMMENTED)["profile"]
        profile_b = learn_c_style(COMPACT_PREFIX)["profile"]
        self.assertEqual(profile_a["preferences"]["function_brace_style"], "next_line")
        self.assertEqual(profile_a["preferences"]["control_brace_style"], "next_line")
        self.assertEqual(profile_a["preferences"]["increment_style"], "postfix")
        self.assertEqual(profile_a["preferences"]["indent_width"], 4)
        self.assertEqual(profile_a["preferences"]["comment_style"], "explanatory")
        self.assertEqual(profile_a["preferences"]["comment_syntax"], "line")
        self.assertEqual(profile_b["preferences"]["function_brace_style"], "same_line")
        self.assertEqual(profile_b["preferences"]["control_brace_style"], "same_line")
        self.assertEqual(profile_b["preferences"]["increment_style"], "prefix")
        self.assertEqual(profile_b["preferences"]["indent_width"], 2)
        self.assertEqual(profile_b["preferences"]["comment_style"], "minimal")

    def test_natural_profiles_capture_context_and_assignment_update(self) -> None:
        profile_a = learn_c_style(NATURAL_A)["profile"]
        profile_b = learn_c_style(NATURAL_B)["profile"]
        self.assertEqual(profile_a["preferences"]["main_signature"], "empty")
        self.assertEqual(profile_a["preferences"]["loop_variable_style"], "predeclared")
        self.assertEqual(profile_a["preferences"]["comment_placement"], "inline")
        self.assertEqual(profile_a["preferences"]["identifier_style"], "short")
        self.assertEqual(profile_a["preferences"]["declaration_style"], "grouped")
        self.assertEqual(profile_b["preferences"]["function_brace_style"], "same_line")
        self.assertEqual(profile_b["preferences"]["control_brace_style"], "next_line")
        self.assertEqual(profile_b["preferences"]["brace_style"], "mixed")
        self.assertEqual(profile_b["preferences"]["increment_style"], "assignment")
        self.assertEqual(profile_b["preferences"]["control_spacing"], "spaced")
        self.assertEqual(profile_b["preferences"]["declaration_style"], "grouped")
        self.assertEqual(profile_b["origins"]["increment_style"], "learned")

    def test_learning_accumulates_votes_without_returning_source(self) -> None:
        first = learn_c_style(ALLMAN_COMMENTED)
        second = learn_c_style(ALLMAN_COMMENTED, first["profile"])
        self.assertTrue(second["accepted"])
        self.assertEqual(second["profile"]["samples"], 2)
        self.assertEqual(second["profile"]["counts"]["function_brace_next_line"], 2)
        self.assertEqual(second["profile"]["counts"]["control_brace_next_line"], 2)
        self.assertNotIn("source", str(second))

    def test_cpp_is_ignored_and_comments_or_literals_do_not_trigger_it(self) -> None:
        harmless = '/* std::cout */\nprintf("cin >> x"); // #include <iostream>\n'
        self.assertEqual(detect_cpp_features(harmless), ())
        previous = learn_c_style(COMPACT_PREFIX)["profile"]
        result = learn_c_style("#include <iostream>\nint main() { std::cout << 1; }", previous)
        self.assertFalse(result["accepted"])
        self.assertEqual(result["reason"], "cpp_ignored")
        self.assertEqual(result["profile"], previous)

    def test_profile_values_are_bounded_and_unknown_fields_are_dropped(self) -> None:
        profile = normalise_style_profile(
            {
                "samples": 100_000,
                "counts": {"control_brace_next_line": 100_000, "unknown": 5},
                "preferences": {"control_brace_style": "invented"},
                "source": "must not survive",
            }
        )
        self.assertEqual(profile["samples"], 100)
        self.assertEqual(profile["counts"]["control_brace_next_line"], 10_000)
        self.assertNotIn("unknown", profile["counts"])
        self.assertNotIn("source", profile)
        self.assertEqual(profile["preferences"]["control_brace_style"], "next_line")

    def test_old_schema_is_reset_instead_of_overclaiming_migrated_evidence(self) -> None:
        profile = normalise_style_profile(
            {
                "schema_version": "0.1",
                "samples": 5,
                "counts": {"increment_postfix": 5},
            }
        )
        self.assertEqual(profile, empty_style_profile())

    def test_v02_profile_is_migrated_without_losing_existing_votes(self) -> None:
        profile = normalise_style_profile(
            {
                "schema_version": "0.2",
                "samples": 3,
                "counts": {"increment_assignment": 3, "identifiers_descriptive": 2},
            }
        )
        self.assertEqual(profile["schema_version"], "0.3")
        self.assertEqual(profile["samples"], 3)
        self.assertEqual(profile["preferences"]["increment_style"], "assignment")
        self.assertEqual(profile["origins"]["identifier_case"], "default")
        self.assertEqual(profile["origins"]["declaration_style"], "default")

    def test_style_application_handles_assignment_spacing_and_contextual_braces(self) -> None:
        profile = learn_c_style(NATURAL_B)["profile"]
        source = (
            'int main(void) {\n'
            '    for (int position = 0; position < 2; position++) {\n'
            '        if (position > 0) {\n'
            '            printf("position++ {");\n'
            '        }\n'
            '    }\n'
            '    return 0;\n'
            '}\n'
        )
        styled, normalised = apply_c_style(source, profile)
        self.assertIn("int main() {", styled)
        self.assertIn("for ( int position = 0; position < 2; position = position + 1 )\n    {", styled)
        self.assertIn("if ( position > 0 )\n        {", styled)
        self.assertIn('"position++ {"', styled)
        self.assertEqual(normalised["preferences"]["brace_style"], "mixed")

    def test_predeclared_loop_conversion_is_scoped_per_function(self) -> None:
        profile = learn_c_style(NATURAL_A)["profile"]
        source = (
            "void show(void) {\n"
            "    for (int row = 0; row < 2; row++) {\n"
            "        for (int column = 0; column < 2; column++) {\n"
            "        }\n"
            "    }\n"
            "}\n"
            "int main(void) {\n"
            "    for (int index = 0; index < 2; index++) {\n"
            "    }\n"
            "    return 0;\n"
            "}\n"
        )
        styled, _ = apply_c_style(source, profile)
        self.assertIn("void show(void) {\n    int row, column;", styled)
        self.assertIn("int main() {\n    int index;", styled)
        self.assertNotIn("for (int ", styled)

    def test_compound_update_and_mixed_votes_are_reported_honestly(self) -> None:
        compound = learn_c_style("int main(void) {\n    int i;\n    i += 1;\n}\n")
        self.assertEqual(compound["profile"]["preferences"]["increment_style"], "compound")
        prefix = learn_c_style(COMPACT_PREFIX)
        mixed = learn_c_style(ALLMAN_COMMENTED, prefix["profile"])["profile"]
        self.assertEqual(mixed["origins"]["increment_style"], "mixed")
        self.assertEqual(mixed["preferences"]["increment_style"], "postfix")
        empty = empty_style_profile()
        self.assertEqual(empty["origins"]["increment_style"], "default")

    def test_identifier_replacement_does_not_touch_comments_or_literals(self) -> None:
        source = 'int value = 1; // value\nprintf("value=%d", value);\n'
        renamed = replace_c_identifiers(source, {"value": "x"})
        self.assertIn("int x = 1;", renamed)
        self.assertIn("// value", renamed)
        self.assertIn('"value=%d"', renamed)

    def test_identifier_case_is_learned_and_applied_without_copying_names(self) -> None:
        camel_source = (
            "int calculeazaSuma(int numarElemente) {\n"
            "    int sumaElementelor = 0;\n"
            "    for (int pozitieCurenta = 0; pozitieCurenta < numarElemente; "
            "pozitieCurenta++) {\n"
            "        sumaElementelor += pozitieCurenta;\n"
            "    }\n"
            "    return sumaElementelor;\n"
            "}\n"
        )
        profile = learn_c_style(camel_source)["profile"]
        self.assertEqual(profile["preferences"]["identifier_case"], "camel")
        self.assertEqual(profile["origins"]["identifier_case"], "learned")

        authored = (
            "int calculate_sum(int item_count) {\n"
            "    int running_total = 0;\n"
            "    printf(\"running_total\"); // running_total\n"
            "    return running_total + item_count;\n"
            "}\n"
        )
        styled, _ = apply_c_style(authored, profile)
        self.assertIn("calculateSum(int itemCount)", styled)
        self.assertIn("int runningTotal = 0;", styled)
        self.assertIn('"running_total"', styled)
        self.assertIn("// running_total", styled)

        snake = analyse_c_style(
            "int main(void) {\n    int numar_elemente, suma_elementelor;\n    return 0;\n}\n"
        )
        self.assertEqual(snake["identifier_case"], "snake")

    def test_declaration_layout_is_learned_and_transformed_conservatively(self) -> None:
        grouped_profile = learn_c_style(
            "int main(void) {\n    int valori[10], numar_elemente, pozitie;\n"
            "    return 0;\n}\n"
        )["profile"]
        self.assertEqual(grouped_profile["preferences"]["declaration_style"], "grouped")
        grouped, _ = apply_c_style(
            "int main(void) {\n    int first;\n    int second = 0;\n"
            "    printf(\"separator\");\n    int third;\n    return second;\n}\n",
            grouped_profile,
        )
        self.assertIn("int first, second = 0;", grouped)
        self.assertIn('printf("separator");\n    int third;', grouped)

        separate_profile = learn_c_style(
            "int main(void) {\n    int first;\n    int second;\n    return 0;\n}\n"
        )["profile"]
        self.assertEqual(separate_profile["preferences"]["declaration_style"], "separate")
        separated, _ = apply_c_style(
            "int main(void) {\n    int first, second = 0;\n    return second;\n}\n",
            separate_profile,
        )
        self.assertIn("int first;\n    int second = 0;", separated)

    def test_analysis_can_report_only_the_dimensions_present(self) -> None:
        observation = analyse_c_style("int value = 1;\n")
        self.assertNotIn("function_brace_style", observation)
        self.assertNotIn("increment_style", observation)
        self.assertEqual(observation["comment_style"], "minimal")
        profile = learn_c_style("int value = 1;\n")["profile"]
        self.assertEqual(profile["origins"]["increment_style"], "default")


if __name__ == "__main__":
    unittest.main()

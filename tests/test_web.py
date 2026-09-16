from __future__ import annotations

import json
import re
import shutil
import subprocess
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from ai_programming_tutor.catalog import get_exercise, list_exercises
from ai_programming_tutor.runner import CRunner
from ai_programming_tutor.solutions import available_styles, cpp_features, reference_answer
from ai_programming_tutor.style_profile import learn_c_style, normalise_style_profile
from ai_programming_tutor.webserver import WEB_ROOT, create_server


class SolutionTests(unittest.TestCase):
    def test_all_exercises_have_explanations_and_only_tested_presets(self) -> None:
        for exercise in list_exercises():
            with self.subTest(exercise=exercise.id):
                classic = reference_answer(exercise, style="classic_c")
                commented = reference_answer(exercise, style="commented_c")
                self.assertEqual(classic["source"], exercise.reference_solution)
                self.assertIn("Solution outline", commented["source"])
                self.assertEqual(len(classic["explanation"]), 3)
                self.assertNotIn("source", exercise.public_view())
                self.assertEqual(
                    available_styles(exercise),
                    ("personalized_c", "pclp1_classic", "classic_c", "commented_c"),
                )
                with self.assertRaises(ValueError):
                    reference_answer(exercise, style="cpp_streams")

    def test_cpp_detection_ignores_comments_and_string_literals(self) -> None:
        source = '/* std::cout */\nprintf("cin >> x"); // #include <iostream>\n'
        self.assertEqual(cpp_features(source), ())
        self.assertIn("cout", cpp_features("std::cout << value;"))
        self.assertEqual(reference_answer(get_exercise("vector_average"), source="// detailed notes")["style"], "commented_c")
        profile = learn_c_style(
            "int main(void)\n{\n    int i;\n    for (i = 0; i < 2; i++)\n    {\n"
            "        // pasul unu\n        // pasul doi\n        printf(\"%d\", i);\n"
            "    }\n    return 0;\n}\n"
        )["profile"]
        personalised = reference_answer(
            get_exercise("vector_average"), source="int main(void) {}", profile=profile
        )
        self.assertEqual(personalised["style"], "personalized_c")
        self.assertTrue(personalised["personalization"]["applied"])
        self.assertIn("int main(void)\n{", personalised["source"])

    @unittest.skipUnless(shutil.which("gcc"), "GCC required")
    def test_commented_c_references_pass_all_tests(self) -> None:
        runner = CRunner()
        for exercise in list_exercises():
            with self.subTest(exercise=exercise.id):
                answer = reference_answer(exercise, style="commented_c")
                self.assertTrue(runner.evaluate(answer["source"], exercise).all_passed)

    @unittest.skipUnless(shutil.which("gcc"), "GCC required")
    def test_pclp1_classic_preset_is_portable_and_passes_all_tests(self) -> None:
        runner = CRunner()
        for exercise in list_exercises():
            with self.subTest(exercise=exercise.id):
                answer = reference_answer(exercise, style="pclp1_classic")
                evaluation = runner.evaluate(answer["source"], exercise)
                self.assertTrue(evaluation.all_passed, answer["source"])
                self.assertEqual(evaluation.compilation.stderr, "")
                self.assertIn("int main()\n{", answer["source"])
                self.assertIn("// ", answer["source"])

    @unittest.skipUnless(shutil.which("gcc"), "GCC required")
    def test_two_personalized_profiles_pass_every_exercise(self) -> None:
        runner = CRunner()
        profile_a = learn_c_style(
            "int main(void)\n{\n    int i;\n    for (i = 0; i < 2; i++)\n    {\n"
            "        // citire\n        // prelucrare\n        printf(\"%d\", i);\n"
            "    }\n    return 0;\n}\n"
        )["profile"]
        profile_b = learn_c_style(
            "int main(void) {\n  int i;\n  for (i = 0; i < 2; ++i) {\n"
            "    printf(\"%d\", i);\n  }\n  return 0;\n}\n"
        )["profile"]
        for exercise in list_exercises():
            for name, profile in (("A", profile_a), ("B", profile_b)):
                with self.subTest(exercise=exercise.id, profile=name):
                    answer = reference_answer(
                        exercise, style="personalized_c", profile=profile
                    )
                    self.assertTrue(
                        runner.evaluate(answer["source"], exercise).all_passed,
                        answer["source"],
                    )

    @unittest.skipUnless(shutil.which("gcc"), "GCC required")
    def test_natural_test_profiles_are_distinct_and_pass_every_exercise(self) -> None:
        runner = CRunner()
        natural_a = """#include <stdio.h>
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
        natural_b = """#include <stdio.h>
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
        profile_a = learn_c_style(natural_a)["profile"]
        profile_b = learn_c_style(natural_b)["profile"]
        self.assertEqual(profile_a["preferences"]["comment_placement"], "inline")
        self.assertEqual(profile_a["preferences"]["declaration_style"], "grouped")
        self.assertEqual(profile_b["preferences"]["increment_style"], "assignment")
        self.assertEqual(profile_b["preferences"]["brace_style"], "mixed")

        for exercise in list_exercises():
            for name, profile in (("natural-A", profile_a), ("natural-B", profile_b)):
                with self.subTest(exercise=exercise.id, profile=name):
                    answer = reference_answer(
                        exercise, style="personalized_c", profile=profile
                    )
                    self.assertTrue(
                        runner.evaluate(answer["source"], exercise).all_passed,
                        answer["source"],
                    )
                    self.assertNotIn("Preluăm dimensiunea", answer["source"])

        average_a = reference_answer(
            get_exercise("vector_average"), style="personalized_c", profile=profile_a
        )["source"]
        average_b = reference_answer(
            get_exercise("vector_average"), style="personalized_c", profile=profile_b
        )["source"]
        self.assertIn("int main() {", average_a)
        self.assertIn("int i, n;", average_a)
        self.assertIn("// Read how many values", average_a)
        self.assertIn("for (i = 0; i < n; i++) {", average_a)
        self.assertIn("for ( int i = 0; i < n; i = i + 1 )\n    {", average_b)
        self.assertNotIn("// Read how many values", average_b)

    @unittest.skipUnless(shutil.which("gcc"), "GCC required")
    def test_descriptive_romanian_identifiers_use_authored_aliases(self) -> None:
        profile = learn_c_style(
            "int main(void) {\n"
            "    int numar_elemente, suma_elementelor;\n"
            "    for (int pozitie = 0; pozitie < numar_elemente; pozitie++) {\n"
            "        suma_elementelor += pozitie;\n"
            "    }\n"
            "    return 0;\n}\n"
        )["profile"]
        self.assertEqual(profile["preferences"]["identifier_style"], "descriptive")
        self.assertEqual(profile["preferences"]["identifier_language"], "romanian")
        self.assertEqual(profile["preferences"]["identifier_case"], "snake")
        exercise = get_exercise("vector_average")
        answer = reference_answer(exercise, style="personalized_c", profile=profile)
        self.assertIn("numar_elemente", answer["source"])
        self.assertIn("valori", answer["source"])
        self.assertIn("suma", answer["source"])
        self.assertTrue(CRunner().evaluate(answer["source"], exercise).all_passed)

    @unittest.skipUnless(shutil.which("gcc"), "GCC required")
    def test_camel_case_profile_uses_authored_aliases_and_passes_every_exercise(self) -> None:
        profile = learn_c_style(
            "int main(void) {\n"
            "    int numarElemente = 3;\n"
            "    int sumaElementelor = 0;\n"
            "    for (int pozitieCurenta = 0; pozitieCurenta < numarElemente; "
            "++pozitieCurenta) {\n"
            "        sumaElementelor += pozitieCurenta;\n"
            "    }\n"
            "    return 0;\n}\n"
        )["profile"]
        self.assertEqual(profile["preferences"]["identifier_language"], "romanian")
        self.assertEqual(profile["preferences"]["identifier_case"], "camel")
        runner = CRunner()
        for exercise in list_exercises():
            with self.subTest(exercise=exercise.id):
                answer = reference_answer(exercise, style="personalized_c", profile=profile)
                self.assertTrue(runner.evaluate(answer["source"], exercise).all_passed)
        menu = reference_answer(
            get_exercise("vector_menu"), style="personalized_c", profile=profile
        )["source"]
        self.assertIn("void citesteVector(", menu)
        self.assertIn("int *numarElemente", menu)
        self.assertIn("int vectorCitit", menu)
        self.assertNotIn("numar_elemente", menu)

    @unittest.skipUnless(shutil.which("gcc"), "GCC required")
    def test_naming_and_declaration_style_matrix_passes_every_exercise(self) -> None:
        runner = CRunner()
        for identifier_case in ("snake", "camel"):
            for declaration_style in ("separate", "grouped"):
                profile = normalise_style_profile(
                    {
                        "schema_version": "0.3",
                        "samples": 1,
                        "counts": {
                            "identifiers_descriptive": 1,
                            "identifier_language_ro": 1,
                            f"identifier_case_{identifier_case}": 1,
                            f"declarations_{declaration_style}": 1,
                        },
                    }
                )
                for exercise in list_exercises():
                    with self.subTest(
                        exercise=exercise.id,
                        identifier_case=identifier_case,
                        declaration_style=declaration_style,
                    ):
                        answer = reference_answer(
                            exercise, style="personalized_c", profile=profile
                        )
                        evaluation = runner.evaluate(answer["source"], exercise)
                        self.assertTrue(
                            evaluation.all_passed,
                            answer["source"],
                        )
                        self.assertEqual(evaluation.compilation.stderr, "")


class LocalWebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = create_server(0, allow_local_execution=True)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def fetch(self, path: str, data: dict | None = None, headers: dict | None = None):
        body = json.dumps(data).encode() if data is not None else None
        request = Request(
            self.url + path,
            data=body,
            headers=headers or ({"Content-Type": "application/json"} if body else {}),
            method="POST" if body else "GET",
        )
        try:
            with urlopen(request, timeout=12) as response:
                return response.status, response.headers, response.read()
        except HTTPError as error:
            return error.code, error.headers, error.read()

    def test_page_catalog_and_complete_solution_are_separate(self) -> None:
        status, headers, html = self.fetch("/")
        self.assertEqual(status, 200)
        self.assertIn("Arată rezolvarea completă".encode("utf-8"), html)
        self.assertIn("default-src 'none'", headers["Content-Security-Policy"])
        for asset in ("/static/style.css", "/static/theme.js", "/static/i18n.js", "/static/app.js"):
            self.assertEqual(self.fetch(asset)[0], 200)
        status, _, payload = self.fetch("/exercises")
        self.assertEqual(status, 200)
        exercises = json.loads(payload)
        self.assertEqual(len(exercises), 14)
        self.assertNotIn("reference_solution", exercises[0])
        self.assertEqual(exercises[0]["course"], "PCLP1")
        self.assertEqual(
            exercises[0]["solution_styles"],
            ["personalized_c", "pclp1_classic", "classic_c", "commented_c"],
        )
        status, _, payload = self.fetch("/exam")
        self.assertEqual(status, 200)
        exam = json.loads(payload)
        self.assertEqual(exam["duration_minutes"], 60)
        self.assertEqual(exam["maximum_points"], 10.0)
        self.assertEqual(len(exam["tasks"]), 4)
        self.assertTrue(all(task["exercise_id"] in {item["id"] for item in exercises}
                            for task in exam["tasks"]))
        style_source = (
            "// citire\n// afișare\nint main(void)\n{\n"
            "    int i;\n    i++;\n    return 0;\n}\n"
        )
        status, _, profile_payload = self.fetch(
            "/style-profile/learn", {"source": style_source, "profile": None}
        )
        self.assertEqual(status, 200)
        profile_result = json.loads(profile_payload)
        self.assertTrue(profile_result["accepted"])
        self.assertEqual(profile_result["profile"]["samples"], 1)
        self.assertNotIn("source", str(profile_result))
        status, headers, payload = self.fetch(
            "/exercises/vector_average/solution", {"style": "commented_c", "source": "// I use notes"}
        )
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertIn("Solution outline", json.loads(payload)["source"])
        status, _, payload = self.fetch(
            "/exercises/vector_average/solution",
            {
                "style": "personalized_c",
                "source": "",
                "profile": profile_result["profile"],
            },
        )
        self.assertEqual(status, 200)
        personalised = json.loads(payload)
        self.assertTrue(personalised["personalization"]["applied"])
        self.assertIn("int main(void)\n{", personalised["source"])

    def test_natural_mixed_profile_round_trip_is_reported_honestly(self) -> None:
        source = (
            "#include <stdio.h>\n\n"
            "int main() {\n"
            "    int m, a[32];\n"
            "    scanf(\"%d\", &m);\n"
            "    for ( int j = 0; j < m; j = j + 1 )\n"
            "    {\n"
            "        scanf(\"%d\", &a[j]);\n"
            "    }\n"
            "    return 0;\n"
            "}\n"
        )
        status, _, payload = self.fetch(
            "/style-profile/learn", {"source": source, "profile": None}
        )
        self.assertEqual(status, 200)
        profile = json.loads(payload)["profile"]
        self.assertEqual(profile["preferences"]["function_brace_style"], "same_line")
        self.assertEqual(profile["preferences"]["control_brace_style"], "next_line")
        self.assertEqual(profile["preferences"]["increment_style"], "assignment")
        self.assertEqual(profile["preferences"]["control_spacing"], "spaced")
        self.assertEqual(profile["origins"]["increment_style"], "learned")
        self.assertEqual(profile["origins"]["comment_syntax"], "default")
        self.assertEqual(profile["preferences"]["declaration_style"], "grouped")

        status, _, payload = self.fetch(
            "/exercises/vector_average/solution",
            {"style": "personalized_c", "source": "", "profile": profile},
        )
        self.assertEqual(status, 200)
        answer = json.loads(payload)
        self.assertIn("int main() {", answer["source"])
        self.assertIn("for ( int i = 0; i < n; i = i + 1 )\n    {", answer["source"])
        self.assertEqual(answer["personalization"]["origins"]["increment_style"], "learned")

        old_profile = {
            "schema_version": "0.1", "samples": 2,
            "counts": {"increment_postfix": 2},
        }
        status, _, payload = self.fetch(
            "/exercises/vector_average/solution",
            {"style": "personalized_c", "source": "", "profile": old_profile},
        )
        self.assertEqual(status, 200)
        reset_answer = json.loads(payload)
        self.assertFalse(reset_answer["personalization"]["applied"])
        self.assertEqual(reset_answer["personalization"]["samples"], 0)

        v02_profile = {
            "schema_version": "0.2", "samples": 2,
            "counts": {"increment_assignment": 2, "identifiers_descriptive": 2},
        }
        status, _, payload = self.fetch(
            "/exercises/vector_average/solution",
            {"style": "personalized_c", "source": "", "profile": v02_profile},
        )
        self.assertEqual(status, 200)
        migrated = json.loads(payload)["personalization"]
        self.assertTrue(migrated["applied"])
        self.assertEqual(migrated["samples"], 2)
        self.assertEqual(migrated["preferences"]["increment_style"], "assignment")
        self.assertEqual(migrated["origins"]["identifier_case"], "default")

    def test_editor_controls_survive_the_visual_refresh(self) -> None:
        html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
        css = (WEB_ROOT / "style.css").read_text(encoding="utf-8")
        for control_id in (
            "language-toggle", "theme-toggle", "exercise-select", "profile-select",
            "learn-style", "reset-profile", "save-drafts", "reset-draft", "code",
            "run", "next-hint", "style",
            "show-solution", "start-exam", "finish-exam", "next-exam-task",
            "exam-timer", "exam-score", "exam-task-list", "exam-rubric-list"
        ):
            self.assertIn(f'id="{control_id}"', html)
        self.assertIn('lang="ro"', html)
        self.assertIn("Exersează programarea", html)
        self.assertIn('class="topbar-controls"', html)
        self.assertIn(':root[data-theme="dark"]', css)
        self.assertNotIn('id="dialect"', html)
        self.assertNotIn('value="cpp_streams"', html)
        self.assertNotIn("brand-mark", html)
        self.assertNotIn("linear-gradient", css)
        self.assertNotIn("box-shadow", css)

    def test_primary_text_and_buttons_keep_readable_contrast_in_both_themes(self) -> None:
        css = (WEB_ROOT / "style.css").read_text(encoding="utf-8")
        theme_blocks = re.findall(r':root(?:\[data-theme="dark"\])? \{([^}]+)\}', css)
        self.assertEqual(len(theme_blocks), 2)

        def luminance(color: str) -> float:
            if len(color) == 4:
                color = "#" + "".join(character * 2 for character in color[1:])
            channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
            linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
                      for c in channels]
            return sum(weight * component for weight, component in zip(
                (0.2126, 0.7152, 0.0722), linear
            ))

        for block in theme_blocks:
            palette = dict(re.findall(r'(--[\w-]+):\s*(#[\da-fA-F]{3,6});', block))

            def contrast(foreground: str, background: str) -> float:
                light, dark = sorted((luminance(palette[foreground]), luminance(palette[background])),
                                     reverse=True)
                return (light + 0.05) / (dark + 0.05)

            for foreground, background in (
                ("--text", "--bg"), ("--text", "--surface"),
                ("--muted", "--surface"), ("--on-primary", "--primary")
            ):
                with self.subTest(theme=palette["--bg"], pair=(foreground, background)):
                    self.assertGreaterEqual(contrast(foreground, background), 4.5)

    @unittest.skipUnless(shutil.which("node"), "Node.js required for translation contract")
    def test_ro_en_dictionaries_and_theme_preference(self) -> None:
        ids = [exercise.id for exercise in list_exercises()]
        script = r"""
const fs = require("fs");
const vm = require("vm");
const assert = require("assert");
const root = process.argv[1];
const ids = JSON.parse(process.argv[2]);
const source = fs.readFileSync(root + "/i18n.js", "utf8");
const html = fs.readFileSync(root + "/index.html", "utf8");
const ctx = {window: {}};
vm.runInNewContext(source, ctx);
const tr = ctx.window.APT_I18N;
assert.deepStrictEqual(Object.keys(tr.exercises).sort(), ids.sort());
for (const id of ids) {
  for (const key of ["title", "statement", "input_format", "output_format"]) {
    assert.ok(tr.exercises[id][key], id + ": " + key);
  }
  assert.strictEqual(tr.explanations[id].length, 3, id);
  assert.ok(tr.starterComments[id].length > 0, id);
}
for (const key of html.matchAll(/data-i18n="([^"]+)"/g)) {
  assert.ok(tr.static.ro[key[1]], "Romanian: " + key[1]);
  assert.ok(tr.static.en[key[1]], "English: " + key[1]);
}
for (const [name, hints] of Object.entries(tr.hints)) {
  assert.ok(tr.categories[name], name);
  assert.strictEqual(hints.length, 3, name);
}
for (const locale of ["ro", "en"]) {
  for (const key of [
    "removed_gets", "undefined_stdin_flush", "nonportable_console_api",
    "nonportable_case_conversion", "eof_loop_condition"
  ]) assert.ok(tr.compatibilityWarnings[locale][key], locale + ": " + key);
  for (const key of [
    "interval_size", "parity_output", "digit_traversal", "odd_counter",
    "sentinel_stop", "average_values", "empty_or_average", "square_loop", "square_output"
  ]) assert.ok(tr.examCriteria[locale][key], locale + ": " + key);
}
const theme = fs.readFileSync(root + "/theme.js", "utf8");
for (const [stored, systemDark, expected] of [
  [null, true, "dark"], [null, false, "light"], ["light", true, "light"], ["dark", false, "dark"]
]) {
  const document = {documentElement: {dataset: {}}};
  vm.runInNewContext(theme, {
    document, localStorage: {getItem: () => stored},
    window: {matchMedia: () => ({matches: systemDark})}
  });
  assert.strictEqual(document.documentElement.dataset.theme, expected);
}
"""
        result = subprocess.run(
            ["node", "-e", script, str(WEB_ROOT), json.dumps(ids)],
            capture_output=True, text=True, check=False, timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node.js required for UI interaction smoke test")
    def test_language_switch_keeps_student_draft_and_hint_progress(self) -> None:
        script = WEB_ROOT.parents[2] / "tests" / "web_interactions.cjs"
        result = subprocess.run(
            ["node", str(script)], capture_output=True, text=True, check=False, timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(shutil.which("gcc"), "GCC required")
    def test_submit_hints_and_hidden_results(self) -> None:
        exercise = get_exercise("vector_average")
        buggy = exercise.reference_solution.replace("(double) total / item_count", "(double) (total / item_count)")
        status, _, payload = self.fetch("/exercises/vector_average/submit", {"source": buggy, "dialect": "c17"})
        self.assertEqual(status, 200)
        response = json.loads(payload)
        self.assertEqual(len(response["progressive_hints"]), 3)
        self.assertEqual(response["candidates"][0]["category"], "integer_division")
        hidden = [case for case in response["evaluation"]["tests"] if case["hidden"]]
        self.assertTrue(all(case["name"].startswith("hidden-test-") for case in hidden))
        self.assertTrue(all(not case["expected"] and not case["actual"] for case in hidden))

    @unittest.skipUnless(shutil.which("gcc"), "GCC required")
    def test_submit_returns_source_free_legacy_compatibility_warnings(self) -> None:
        source = "#include <stdio.h>\nint main(void) { char s[8]; gets(s); return 0; }\n"
        status, _, payload = self.fetch(
            "/exercises/palindrome/submit", {"source": source, "dialect": "c17"}
        )
        self.assertEqual(status, 200)
        response = json.loads(payload)
        self.assertEqual(response["compatibility_warnings"][0]["id"], "removed_gets")
        self.assertNotIn("gets(s)", str(response["compatibility_warnings"]))

    def test_local_execution_is_opt_in_and_cross_origin_is_blocked(self) -> None:
        self.server.allow_local_execution = False
        try:
            self.assertEqual(self.fetch("/exercises/vector_average/submit", {"source": "int main(){}"})[0], 403)
        finally:
            self.server.allow_local_execution = True
        self.assertEqual(self.fetch("/exercises/vector_average/solution", {"style": "cpp_streams"}, {"Content-Type": "application/json", "Origin": "https://other.example"})[0], 403)
        self.assertEqual(self.fetch("/exercises/palindrome/solution", {"style": "cpp_streams"})[0], 422)
        self.assertEqual(
            self.fetch(
                "/exercises/vector_average/submit",
                {"source": "int main(void) { return 0; }", "dialect": "cpp17"},
            )[0],
            422,
        )
        status, _, payload = self.fetch(
            "/style-profile/learn",
            {"source": "#include <iostream>\nint main() { std::cout << 1; }"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(payload)["reason"], "cpp_ignored")
        self.assertEqual(self.fetch("/exercises/missing/solution", {"style": "classic_c"})[0], 404)


if __name__ == "__main__":
    unittest.main()

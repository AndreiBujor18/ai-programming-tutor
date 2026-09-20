"use strict";

// Dependency-free smoke test of the browser controller's critical state changes.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.join(__dirname, "..", "src", "ai_programming_tutor", "web");
const blobUrls = {};
let nextBlobId = 1;
let lastDownload = null;

class Element {
  constructor(tag = "div") {
    this.tag = tag;
    this.children = [];
    this.options = [];
    this.listeners = {};
    this.attributes = {};
    this.dataset = {};
    this.classList = {toggle() {}};
    this.hidden = false;
    this.value = "";
    this.textContent = "";
    this.disabled = false;
    this.checked = false;
    this.files = [];
    this.clickCount = 0;
  }
  addEventListener(name, callback) { this.listeners[name] = callback; }
  setAttribute(name, value) { this.attributes[name] = value; }
  append(...items) {
    this.children.push(...items);
    if (this.tag === "select") this.options = this.children;
  }
  replaceChildren(...items) {
    this.children = [];
    this.append(...items);
  }
  scrollIntoView() {}
  click() {
    this.clickCount += 1;
    if (this.tag === "a") {
      lastDownload = {download: this.download, blob: blobUrls[this.href]};
    } else if (this.listeners.click) {
      this.listeners.click();
    }
  }
  remove() { this.removed = true; }
}

class FakeBlob {
  constructor(parts, options) {
    this.parts = parts;
    this.type = options?.type || "";
  }
}

const fakeURL = {
  createObjectURL(blob) {
    const id = "blob:test-" + nextBlobId;
    nextBlobId += 1;
    blobUrls[id] = blob;
    return id;
  },
  revokeObjectURL(id) { delete blobUrls[id]; }
};

const ids = [
  "app-shell", "page-title", "intro-copy", "workspace-nav",
  "view-practice", "view-exam", "view-progress", "practice-panel",
  "exam-panel", "progress-panel", "exam-tab-status", "progress-tab-status",
  "profile-panel", "profile-panel-badge", "solution-panel",
  "language-toggle", "theme-toggle", "notice", "run-status", "result-card",
  "solution-answer", "hint-area", "next-hint", "public-tests",
  "exercise-select", "exercise-title", "exercise-statement", "input-format",
  "output-format", "exercise-count", "code", "style", "style-help", "hints",
  "code-editor",
  "run", "file-label", "show-solution", "copy-solution", "result-count",
  "language-warning", "compiler-output", "diagnosis", "test-results",
  "solution-meta", "solution-code", "solution-explanation", "solution-note",
  "profile-select", "learn-style", "reset-profile", "profile-summary",
  "profile-message", "save-drafts", "reset-draft", "editor-help",
  "progress-heading", "progress-summary-badge", "save-attempt-history",
  "progress-summary", "clear-progress", "progress-message",
  "favorite-exercise", "exercise-progress",
  "progress-breakdown", "concept-progress", "concept-progress-note",
  "concept-progress-overlap", "exercise-progress-list", "progress-breakdown-empty",
  "export-progress", "import-progress-trigger", "import-progress",
  "exam-heading", "exam-summary-badge", "start-exam", "finish-exam",
  "exam-session", "exam-timer", "exam-score", "exam-task-list",
  "next-exam-task", "exam-note", "exam-rubric-list"
];
const elements = Object.fromEntries(ids.map((id) => [id, new Element()]));
elements["exercise-select"].tag = "select";
elements["profile-select"].tag = "select";
elements.style.tag = "select";
elements.style.value = "personalized_c";
for (const value of ["personalized_c", "pclp1_classic", "classic_c", "commented_c"]) {
  const option = new Element("option");
  option.value = value;
  elements.style.append(option);
}
const document = {
  title: "",
  documentElement: {lang: "ro", dataset: {theme: "light"}},
  body: {children: [], append(item) { this.children.push(item); }},
  getElementById: (id) => {
    assert.ok(elements[id], "missing element " + id);
    return elements[id];
  },
  createElement: (tag) => new Element(tag),
  querySelectorAll: () => []
};
const stored = {
  "aptutor-v0.5-style-profile_a": JSON.stringify({
    schema_version: "0.1", samples: 4, counts: {increment_postfix: 4}
  }),
  "aptutor-v0.7-progress-profile_b": JSON.stringify({
    schema_version: "0.1", favorites: [],
    attempts: {vector_menu: [{at: Date.now(), passed: 1, total: 1, compiled: true}]}
  })
};
const sessionStored = {};
const exercise = {
  id: "vector_menu", title: "Vector menu", statement: "English statement.",
  input_format: "English input.", output_format: "English output.",
  tags: ["arrays", "functions", "menus", "program-state"],
  starter_code: "/* Read the array and show a result. */\nint main(void) { return 0; }\n",
  public_tests: [{name: "example A", input: "1\nS", expected: "EMPTY"}],
  solution_styles: ["personalized_c", "pclp1_classic", "classic_c", "commented_c"]
};
const fileExercise = {
  id: "file_number_summary", title: "Summarize numbers from a file",
  statement: "Read a file and write its summary.",
  input_format: "Read numbers.txt.", output_format: "Write summary.txt.",
  tags: ["files"],
  starter_code: "/* Read and summarize the file. */\nint main(void) { return 0; }\n",
  public_tests: [{
    name: "small file", input: "", expected: "",
    fixtures: [{name: "numbers.txt", content: "2\n3 5\n"}],
    expected_files: [{name: "summary.txt", content: "3 5 8\n"}]
  }],
  solution_styles: ["personalized_c", "pclp1_classic", "classic_c", "commented_c"]
};
const exam = {
  id: "smoke-exam", title: "Smoke exam", duration_minutes: 60,
  base_points: 1, maximum_points: 10,
  tasks: [{
    exercise_id: "vector_menu", points: 9,
    criteria: [{key: "interval_size", points: 9, description: "Check the task."}]
  }]
};
const response = {
  evaluation: {
    compilation: {succeeded: true, stderr: ""}, passed_count: 0,
    total_count: 1, all_passed: false,
    tests: [{
      hidden: true, name: "hidden-test-1", status: "wrong_answer",
      file_results: [{
        name: "hidden-file-1", status: "missing", expected: "", actual: ""
      }]
    }]
  },
  candidates: [{category: "menu_dispatch", evidence: "menu case mismatch"}],
  progressive_hints: ["English hint one", "English hint two", "English hint three"],
  language_warning: "", compatibility_warnings: [],
  dialect: "c17", diagnosis_scope: "C17 rules"
};
const learnedA = {
  schema_version: "0.3", samples: 1,
  counts: {
    function_brace_same_line: 1, control_brace_same_line: 1,
    increment_postfix: 1, indent_4: 1, comments_explanatory: 1,
    comment_line: 1, comment_inline: 1, main_empty: 1,
    identifiers_short: 1, declarations_grouped: 1, loop_variable_predeclared: 1,
    control_spacing_compact: 1
  }
};
const learnedB = {
  schema_version: "0.3", samples: 1,
  counts: {
    function_brace_same_line: 1, control_brace_next_line: 1,
    increment_assignment: 1, indent_4: 1, comments_minimal: 1,
    main_empty: 1, identifiers_short: 1, declarations_separate: 1,
    loop_variable_inline: 1,
    control_spacing_spaced: 1
  }
};
const answer = {
  style: "personalized_c", course: "PCLP1", compiler: "gcc -std=c17",
  source: "int main() {\n    // Read input.\n    int n;\n    // Select case.\n    n++;\n    // Print result.\n    return 0;\n}\n",
  explanation: ["Read input.", "Select case.", "Print result."],
  note: "Applied profile.",
  personalization: {
    applied: true, samples: 1,
    preferences: {
      function_brace_style: "same_line", control_brace_style: "same_line",
      increment_style: "postfix", indent_width: 4, comment_style: "explanatory",
      comment_syntax: "line", comment_placement: "inline", main_signature: "empty",
      identifier_style: "short", identifier_language: "english",
      identifier_case: "snake", declaration_style: "grouped",
      loop_variable_style: "predeclared", control_spacing: "compact", brace_style: "same_line"
    }
  }
};
let enhancedEditor = null;
const editorObservations = {themes: [], indentSizes: []};
const browserWindow = {
  confirm: () => true,
  APT_CODE_EDITOR: {
    create({textarea, onChange, theme, indentSize}) {
      const adapter = {
        getValue: () => textarea.value,
        setValue(value) { textarea.value = value; },
        setTheme(value) { editorObservations.themes.push(value); },
        setIndentSize(value) { editorObservations.indentSizes.push(value); },
        simulateInput(value) {
          textarea.value = value;
          onChange(value);
        }
      };
      editorObservations.themes.push(theme);
      editorObservations.indentSizes.push(indentSize);
      enhancedEditor = adapter;
      return adapter;
    }
  }
};
const context = vm.createContext({
  window: browserWindow,
  document,
  localStorage: {
    getItem: (key) => stored[key] ?? null,
    setItem: (key, value) => { stored[key] = value; },
    removeItem: (key) => { delete stored[key]; }
  },
  sessionStorage: {
    getItem: (key) => sessionStored[key] ?? null,
    setItem: (key, value) => { sessionStored[key] = value; },
    removeItem: (key) => { delete sessionStored[key]; }
  },
  navigator: {clipboard: {writeText: async () => {}}},
  Blob: FakeBlob,
  URL: fakeURL,
  setInterval: () => 1,
  clearInterval: () => {},
  fetch: async (url, options = {}) => {
    if (url === "/exercises") return {ok: true, json: async () => [exercise, fileExercise]};
    if (url === "/exam") return {ok: true, json: async () => exam};
    if (url.endsWith("/submit")) return {ok: true, json: async () => response};
    if (url === "/style-profile/learn") {
      const body = JSON.parse(options.body);
      const profile = body.source.includes("i = i + 1") ? learnedB : learnedA;
      return {ok: true, json: async () => ({
        accepted: true, reason: "learned", profile, observation: {}
      })};
    }
    return {ok: true, json: async () => answer};
  }
});
vm.runInContext(fs.readFileSync(path.join(root, "progress.js"), "utf8"), context);
vm.runInContext(fs.readFileSync(path.join(root, "i18n.js"), "utf8"), context);
vm.runInContext(fs.readFileSync(path.join(root, "app.js"), "utf8"), context);

(async () => {
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(document.documentElement.lang, "ro");
  assert.equal(elements["language-toggle"].textContent, "English");
  assert.equal(elements["exercise-title"].textContent, "Meniu de comenzi pentru vector");
  assert.equal(elements["practice-panel"].hidden, false);
  assert.equal(elements["exam-panel"].hidden, true);
  assert.equal(elements["progress-panel"].hidden, true);
  assert.equal(elements["view-practice"].attributes["aria-pressed"], "true");
  assert.equal(elements["page-title"].textContent, "Exersează programarea");
  elements["view-progress"].listeners.click();
  assert.equal(elements["practice-panel"].hidden, true);
  assert.equal(elements["progress-panel"].hidden, false);
  assert.equal(elements["page-title"].textContent, "Progresul tău local");
  elements["view-exam"].listeners.click();
  assert.equal(elements["practice-panel"].hidden, false);
  assert.equal(elements["exam-panel"].hidden, false);
  assert.equal(elements["page-title"].textContent, "Simulare de test");
  elements["view-practice"].listeners.click();
  assert.ok(enhancedEditor, "enhanced editor was not mounted");
  assert.equal(enhancedEditor.getValue().includes("int main(void)"), true);
  vm.runInContext(
    'renderPublicTests(state.exercises.find((item) => item.id === "file_number_summary"))',
    context
  );
  const romanianFileExample = elements["public-tests"].children[0];
  assert.equal(romanianFileExample.children.length, 2);
  assert.equal(romanianFileExample.children[0].children[0].textContent,
    "Fișier de intrare: numbers.txt");
  assert.equal(romanianFileExample.children[0].children[1].textContent, "2\n3 5\n");
  assert.equal(romanianFileExample.children[1].children[0].textContent,
    "Fișier rezultat așteptat: summary.txt");
  vm.runInContext("renderPublicTests(state.active)", context);
  assert.equal(elements["profile-select"].value, "profile_a");
  assert.equal(elements["profile-panel-badge"].textContent, "Profil A · 0 exemple");
  assert.equal(elements["profile-summary"].textContent.includes("Încă nu există"), true);
  assert.equal(elements["profile-message"].textContent.includes("resetate o singură dată"), true);
  assert.equal(elements["save-drafts"].checked, false);
  assert.equal(elements["editor-help"].textContent.includes("păstrat temporar în această filă"), true);
  assert.equal(elements["save-attempt-history"].checked, false);
  assert.equal(elements["exercise-progress"].textContent, "Istoricul încercărilor este oprit.");
  assert.equal(elements["favorite-exercise"].textContent, "☆ Adaugă la favorite");
  assert.equal(elements["concept-progress"].hidden, true);
  assert.equal(elements["concept-progress-note"].textContent.includes("Activează istoricul"), true);
  assert.equal(elements["progress-breakdown-empty"].hidden, false);
  assert.equal(stored["aptutor-v0.7-progress-profile_b"], undefined,
    "disabled history retained an old numeric attempt");
  elements["view-progress"].listeners.click();
  elements["profile-select"].value = "profile_b";
  elements["profile-select"].listeners.change({target: elements["profile-select"]});
  assert.equal(elements["profile-panel-badge"].textContent, "Profil B · 0 exemple");
  assert.equal(elements["progress-panel"].hidden, false,
    "switching profile unexpectedly left the progress view");
  elements["profile-select"].value = "profile_a";
  elements["profile-select"].listeners.change({target: elements["profile-select"]});
  elements["view-practice"].listeners.click();
  elements["favorite-exercise"].listeners.click();
  let progressA = JSON.parse(stored["aptutor-v0.7-progress-profile_a"]);
  assert.deepStrictEqual(progressA.favorites, ["vector_menu"]);
  assert.equal(JSON.stringify(progressA).includes("source"), false);
  assert.equal(elements["favorite-exercise"].attributes["aria-pressed"], "true");
  assert.equal(elements["exercise-select"].options[0].textContent.startsWith("★ "), true);
  assert.equal(elements["exercise-progress-list"].children.length, 1);
  assert.equal(elements["exercise-progress-list"].children[0].textContent.includes(
    "★ Meniu de comenzi pentru vector · fără rezultate salvate"
  ), true);
  elements["save-attempt-history"].checked = true;
  elements["save-attempt-history"].listeners.change({target: elements["save-attempt-history"]});
  assert.equal(stored["aptutor-v0.7-attempt-history-profile_a"], "yes");
  assert.equal(elements["exercise-progress"].textContent,
    "Nicio încercare salvată pentru acest exercițiu.");
  assert.equal(elements["concept-progress"].hidden, false);
  assert.equal(elements["concept-progress"].children.length, 3);
  assert.equal(elements["exam-summary-badge"].textContent, "60 min · 10p");
  elements["start-exam"].listeners.click();
  assert.equal(elements["exam-panel"].hidden, false);
  assert.equal(elements["view-exam"].attributes["aria-pressed"], "true");
  assert.equal(elements["exam-tab-status"].hidden, false);
  assert.equal(elements["exam-session"].hidden, false);
  assert.equal(elements["exam-score"].textContent, "1.00 / 10");
  assert.ok(stored["aptutor-v0.6-exam-session"]);
  const partialSummary = vm.runInContext(
    'profileSummary(sanitiseProfile({schema_version: "0.2", samples: 1, counts: {comments_minimal: 1}}))',
    context
  );
  assert.equal(partialSummary.includes("implicit; neobservat"), true);
  stored["aptutor-v0.5-style-profile_b"] = JSON.stringify({
    schema_version: "0.2", samples: 2, counts: {increment_assignment: 2}
  });
  const migrated = vm.runInContext('loadProfile("profile_b")', context);
  assert.equal(migrated.schema_version, "0.3");
  assert.equal(migrated.samples, 2);
  assert.equal(migrated.preferences.increment_style, "assignment");

  elements["save-drafts"].checked = true;
  elements["save-drafts"].listeners.change({target: elements["save-drafts"]});
  assert.equal(stored["aptutor-v0.5-save-drafts"], "yes");
  assert.equal(elements["editor-help"].textContent.includes("salvată local"), true);

  const ownCodeA = "int main() {\n    int v[10], n, i;\n    // pas 1\n    // pas 2\n    for (i = 0; i < n; i++) {\n    }\n}\n";
  enhancedEditor.simulateInput(ownCodeA);
  assert.equal(stored["aptutor-v0.5-draft-profile_a:vector_menu"], ownCodeA);
  await elements["learn-style"].listeners.click();
  assert.equal(elements["profile-summary"].textContent.includes("funcții: acoladă pe aceeași linie"), true);
  assert.equal(elements["profile-summary"].textContent.includes("comentarii lângă blocul explicat"), true);
  assert.ok(stored["aptutor-v0.5-style-profile_a"]);

  response.evaluation.compilation.succeeded = false;
  response.evaluation.total_count = 0;
  await vm.runInContext("runCode()", context);
  progressA = JSON.parse(stored["aptutor-v0.7-progress-profile_a"]);
  assert.equal(progressA.attempts.vector_menu.length, 1);
  assert.deepStrictEqual(
    Object.keys(progressA.attempts.vector_menu[0]).sort(),
    ["at", "compiled", "passed", "total"]
  );
  assert.equal(progressA.attempts.vector_menu[0].compiled, false);
  assert.equal(JSON.stringify(progressA).includes(ownCodeA), false);
  assert.equal(elements["exercise-progress"].textContent,
    "Ultimul: compilarea a eșuat · Cel mai bun: — · 1 încercare");
  let fileResultList = elements["test-results"].children[0].children[1];
  assert.equal(fileResultList.children[0].children[0].textContent, "Fișier ascuns 1");
  assert.equal(fileResultList.children[0].children[1].textContent, "fișier lipsă");
  assert.equal(elements["concept-progress"].children[0].textContent,
    "Vectori: rezolvate 0/1 · încercate 1");
  assert.equal(elements["exercise-progress-list"].children[0].textContent.includes(
    "cel mai bun — · 1 încercare"
  ), true);
  assert.equal(elements["exam-score"].textContent, "1.00 / 10");
  response.evaluation.compilation.succeeded = true;
  response.evaluation.total_count = 1;
  vm.runInContext("showNextHint()", context);
  assert.equal(elements.hints.children.length, 2);
  assert.equal(elements.hints.children[0].textContent,
    context.window.APT_I18N.hints.menu_dispatch[0]);

  elements["profile-select"].value = "profile_b";
  elements["profile-select"].listeners.change({target: elements["profile-select"]});
  assert.notEqual(elements.code.value, ownCodeA, "profile B inherited profile A's draft");
  assert.equal(elements["favorite-exercise"].attributes["aria-pressed"], "false");
  assert.equal(elements["save-attempt-history"].checked, false);
  const ownCodeB = "int main() {\n    int n;\n    for ( int i = 0; i < n; i = i + 1 )\n    {\n    }\n}\n";
  enhancedEditor.simulateInput(ownCodeB);
  await elements["learn-style"].listeners.click();
  assert.equal(elements["profile-summary"].textContent.includes("actualizare explicită"), true);
  assert.equal(elements["profile-summary"].textContent.includes("for/if/while: acoladă pe linie nouă"), true);
  assert.equal(elements["profile-summary"].textContent.includes("implicit; neobservat"), false);
  assert.ok(stored["aptutor-v0.5-style-profile_b"]);

  elements["profile-select"].value = "profile_a";
  elements["profile-select"].listeners.change({target: elements["profile-select"]});
  assert.equal(elements.code.value, ownCodeA, "profile A draft was not restored");
  assert.equal(elements["favorite-exercise"].attributes["aria-pressed"], "true");
  assert.equal(elements["save-attempt-history"].checked, true);

  vm.runInContext(`recordLearningAttempt("profile_a", "vector_menu", {
    compilation: {succeeded: true}, passed_count: 1, total_count: 1
  })`, context);
  assert.equal(elements["exercise-progress"].textContent.includes("Ultimul: 1/1"), true);
  assert.equal(elements["exercise-progress"].textContent.includes("Cel mai bun: 1/1"), true);
  assert.equal(elements["concept-progress"].children[0].textContent,
    "Vectori: rezolvate 1/1 · încercate 1");

  await vm.runInContext("runCode()", context);
  vm.runInContext("showNextHint()", context);
  vm.runInContext("showNextHint()", context);
  assert.equal(elements.hints.children.length, 3);
  assert.equal(elements["run-status"].textContent, "Gata");
  await vm.runInContext("showSolution()", context);
  assert.equal(elements["solution-code"].textContent.includes(
    context.window.APT_I18N.explanations.vector_menu[0]), true);
  // The real-browser acceptance pass exposed a stale internal hint cursor while
  // all three hints were still visible. Locale changes must preserve the rendered
  // learner state, which is authoritative for this UI-only reveal counter.
  vm.runInContext("state.hintIndex = 1", context);
  elements["language-toggle"].listeners.click();
  assert.equal(document.documentElement.lang, "en");
  assert.equal(elements["page-title"].textContent, "Practice exam");
  assert.equal(elements["workspace-nav"].attributes["aria-label"], "Application sections");
  assert.equal(elements["profile-panel-badge"].textContent, "Profile A · 1 example");
  assert.equal(elements.code.value, ownCodeA, "draft lost on language switch");
  assert.equal(elements["exercise-title"].textContent, "Vector menu");
  assert.equal(elements.hints.children.length, 3, "revealed hint count changed");
  assert.equal(elements.hints.children[0].textContent, "English hint one");
  assert.equal(elements["run-status"].textContent, "Ready");
  fileResultList = elements["test-results"].children[0].children[1];
  assert.equal(fileResultList.children[0].children[0].textContent, "Hidden file 1");
  assert.equal(fileResultList.children[0].children[1].textContent, "missing file");
  vm.runInContext(
    'renderPublicTests(state.exercises.find((item) => item.id === "file_number_summary"))',
    context
  );
  const englishFileExample = elements["public-tests"].children[0];
  assert.equal(englishFileExample.children[0].children[0].textContent,
    "Input file: numbers.txt");
  assert.equal(englishFileExample.children[1].children[0].textContent,
    "Expected result file: summary.txt");
  vm.runInContext("renderPublicTests(state.active)", context);
  assert.equal(elements["concept-progress"].children[0].textContent,
    "Arrays: solved 1/1 · attempted 1");
  assert.equal(elements["exercise-progress-list"].children[0].textContent.includes(
    "★ Vector menu · best 1/1"
  ), true);
  assert.equal(elements["profile-summary"].textContent.includes("functions: same-line brace"), true);
  assert.equal(stored["aptutor-v0.5-locale"], "en");

  assert.equal(elements["solution-code"].textContent, answer.source);
  elements["language-toggle"].listeners.click();
  assert.equal(elements["page-title"].textContent, "Simulare de test");
  assert.equal(elements.code.value, ownCodeA);
  assert.equal(elements.hints.children.length, 3);
  assert.equal(elements["run-status"].textContent, "Gata");
  assert.equal(elements["solution-code"].textContent.includes(
    context.window.APT_I18N.explanations.vector_menu[0]), true);
  assert.equal(elements["solution-explanation"].children[0].textContent,
    context.window.APT_I18N.explanations.vector_menu[0]);

  elements["export-progress"].listeners.click();
  assert.equal(lastDownload.download, "ai-programming-tutor-profile-a-progress.json");
  const exportedProgressText = lastDownload.blob.parts.join("");
  const exportedProgress = JSON.parse(exportedProgressText);
  assert.deepStrictEqual(Object.keys(exportedProgress).sort(),
    ["attempts", "favorites", "format", "history_enabled", "schema_version"]);
  assert.equal(exportedProgress.history_enabled, true);
  assert.deepStrictEqual(exportedProgress.favorites, ["vector_menu"]);
  assert.equal(exportedProgress.attempts.vector_menu.length, 3);
  assert.equal(exportedProgressText.includes(ownCodeA), false);
  assert.equal(elements["progress-message"].textContent.includes("pregătit"), true);
  elements["import-progress-trigger"].listeners.click();
  assert.equal(elements["import-progress"].clickCount, 1);

  elements["save-attempt-history"].checked = false;
  elements["save-attempt-history"].listeners.change({target: elements["save-attempt-history"]});
  progressA = JSON.parse(stored["aptutor-v0.7-progress-profile_a"]);
  assert.deepStrictEqual(progressA.attempts, {});
  assert.deepStrictEqual(progressA.favorites, ["vector_menu"]);
  assert.equal(stored["aptutor-v0.7-attempt-history-profile_a"], "no");
  assert.equal(elements["concept-progress"].hidden, true);
  assert.equal(elements["exercise-progress-list"].children.length, 1);
  elements["clear-progress"].listeners.click();
  assert.equal(stored["aptutor-v0.7-progress-profile_a"], undefined);
  assert.equal(elements["favorite-exercise"].attributes["aria-pressed"], "false");
  assert.equal(elements["exercise-progress-list"].hidden, true);
  assert.equal(elements["progress-breakdown-empty"].hidden, false);

  elements["import-progress"].files = [{
    size: exportedProgressText.length,
    text: async () => exportedProgressText
  }];
  await elements["import-progress"].listeners.change({target: elements["import-progress"]});
  progressA = JSON.parse(stored["aptutor-v0.7-progress-profile_a"]);
  assert.deepStrictEqual(progressA.favorites, ["vector_menu"]);
  assert.equal(progressA.attempts.vector_menu.length, 3);
  assert.equal(stored["aptutor-v0.7-attempt-history-profile_a"], "yes");
  assert.equal(elements["save-attempt-history"].checked, true);
  assert.equal(elements["progress-message"].textContent.includes("înlocuit"), true);
  assert.equal(elements.code.value, ownCodeA, "progress import changed the active draft");
  assert.ok(stored["aptutor-v0.5-style-profile_a"], "progress import changed the style profile");
  assert.equal(stored["aptutor-v0.7-progress-profile_b"], undefined,
    "progress import changed the other profile");
  assert.equal(elements["import-progress"].value, "");

  const invalidProgressText = JSON.stringify({...exportedProgress, source: ownCodeA});
  elements["import-progress"].files = [{
    size: invalidProgressText.length,
    text: async () => invalidProgressText
  }];
  await elements["import-progress"].listeners.change({target: elements["import-progress"]});
  assert.equal(JSON.parse(stored["aptutor-v0.7-progress-profile_a"])
    .attempts.vector_menu.length, 3);
  assert.equal(elements["progress-message"].textContent.includes("respins"), true);

  elements["import-progress"].files = [{
    size: 100001,
    text: async () => exportedProgressText
  }];
  await elements["import-progress"].listeners.change({target: elements["import-progress"]});
  assert.equal(JSON.parse(stored["aptutor-v0.7-progress-profile_a"])
    .attempts.vector_menu.length, 3);
  assert.equal(elements["progress-message"].textContent.includes("respins"), true);
  elements["clear-progress"].listeners.click();
  assert.equal(stored["aptutor-v0.7-progress-profile_a"], undefined);

  elements["theme-toggle"].listeners.click();
  assert.equal(document.documentElement.dataset.theme, "dark");
  assert.equal(stored["aptutor-v0.5-theme"], "dark");
  elements["theme-toggle"].listeners.click();
  assert.equal(document.documentElement.dataset.theme, "light");
  assert.equal(editorObservations.themes.at(-1), "light");
  enhancedEditor.simulateInput("");
  assert.equal(stored["aptutor-v0.5-draft-profile_a:vector_menu"], "");
  vm.runInContext("state.drafts.clear(); state.edited.clear();", context);
  const emptyDraft = vm.runInContext('loadDraft("profile_a:vector_menu")', context);
  assert.equal(emptyDraft, "", "an intentionally empty draft was not restored");
  elements["reset-draft"].listeners.click();
  assert.equal(stored["aptutor-v0.5-draft-profile_a:vector_menu"], undefined);
  assert.equal(elements.code.value.includes("int main(void)"), true);
  elements["save-drafts"].checked = false;
  elements["save-drafts"].listeners.change({target: elements["save-drafts"]});
  assert.equal(stored["aptutor-v0.5-save-drafts"], "no");
  assert.equal(stored["aptutor-v0.5-draft-profile_b:vector_menu"], undefined);
  elements["reset-profile"].listeners.click();
  assert.equal(stored["aptutor-v0.5-style-profile_a"], undefined);
  assert.equal(elements["profile-summary"].textContent.includes("Încă nu există"), true);

  // Exam source is kept only in tab-scoped storage when persistent drafts are
  // disabled. Finishing snapshots the remaining time so it cannot resume after
  // a reload, while the source remains available for review in the same tab.
  const examReviewCode = "int main(void) {\n  int rezultat = 42;\n  return rezultat == 42 ? 0 : 1;\n}\n";
  enhancedEditor.simulateInput(examReviewCode);
  assert.equal(stored["aptutor-v0.5-draft-profile_a:vector_menu"], undefined);
  assert.equal(JSON.parse(sessionStored["aptutor-v0.6-exam-drafts"])
    .drafts["profile_a:vector_menu"], examReviewCode);
  elements["finish-exam"].listeners.click();
  assert.equal(vm.runInContext("state.exam.finished", context), true);
  assert.equal(vm.runInContext("state.exam.active", context), false);
  assert.equal(elements["exam-tab-status"].hidden, true);
  const frozenTimer = elements["exam-timer"].textContent;
  assert.ok(Number.isFinite(JSON.parse(stored["aptutor-v0.6-exam-session"]).remaining_ms));
  assert.equal(stored["aptutor-v0.6-exam-session"].includes(examReviewCode), false);
  vm.runInContext("state.exam.startedAt -= 600000; renderExam();", context);
  assert.equal(elements["exam-timer"].textContent, frozenTimer,
    "finished exam timer resumed after time advanced");

  vm.runInContext(`
    state.active = null;
    state.drafts.clear();
    state.edited.clear();
    state.exam.active = false;
    state.exam.finished = false;
    state.exam.remainingMs = null;
    restoreExamSession();
    restoreExamDrafts();
    selectExercise("vector_menu");
  `, context);
  assert.equal(elements["exam-timer"].textContent, frozenTimer,
    "finished exam timer changed after session restoration");
  assert.equal(elements.code.value, examReviewCode,
    "exam source was not restored from tab-scoped storage");
  assert.equal(elements["start-exam"].hidden, false);
})().catch((error) => { console.error(error); process.exitCode = 1; });

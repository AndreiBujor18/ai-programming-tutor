"use strict";

const element = (id) => document.getElementById(id);
const translations = window.APT_I18N;
const progressTools = window.APT_PROGRESS;
const STORAGE_PREFIX = "aptutor-v0.5-";
const LEGACY_PREFIX = "aptutor-v0.3-";
const PROFILE_SCHEMA_VERSION = "0.3";
const PREVIOUS_PROFILE_SCHEMA_VERSION = "0.2";
const MAX_PERSISTED_DRAFT_LENGTH = 100000;
const EXAM_SESSION_KEY = "aptutor-v0.6-exam-session";
const EXAM_DRAFTS_KEY = "aptutor-v0.6-exam-drafts";
const PROGRESS_STORAGE_PREFIX = "aptutor-v0.7-progress-";
const HISTORY_SETTING_PREFIX = "aptutor-v0.7-attempt-history-";
const PROGRESS_CONCEPTS = [
  {id: "arrays", tags: ["arrays"]},
  {id: "loops", tags: ["loops", "sentinels"]},
  {id: "conditions", tags: ["conditions", "comparisons", "intervals", "boundaries"]},
  {
    id: "numeric",
    tags: ["numeric-types", "arithmetic", "digits", "number-properties", "averages", "counters"]
  },
  {id: "strings_input", tags: ["strings", "input", "buffers"]},
  {id: "matrices", tags: ["matrices"]},
  {id: "functions_menus", tags: ["functions", "menus"]}
];
const PROFILE_DIMENSIONS = {
  function_brace_style: {
    choices: [["function_brace_same_line", "same_line"], ["function_brace_next_line", "next_line"]],
    fallback: "same_line"
  },
  control_brace_style: {
    choices: [["control_brace_same_line", "same_line"], ["control_brace_next_line", "next_line"]],
    fallback: "same_line"
  },
  increment_style: {
    choices: [
      ["increment_prefix", "prefix"], ["increment_postfix", "postfix"],
      ["increment_assignment", "assignment"], ["increment_compound", "compound"]
    ],
    fallback: "postfix"
  },
  indent_width: {choices: [["indent_2", 2], ["indent_4", 4]], fallback: 4},
  comment_style: {
    choices: [["comments_minimal", "minimal"], ["comments_explanatory", "explanatory"]],
    fallback: "minimal"
  },
  comment_syntax: {choices: [["comment_line", "line"], ["comment_block", "block"]], fallback: "block"},
  comment_placement: {
    choices: [["comment_inline", "inline"], ["comment_outline", "outline"]],
    fallback: "outline"
  },
  main_signature: {choices: [["main_empty", "empty"], ["main_void", "void"]], fallback: "void"},
  identifier_style: {
    choices: [["identifiers_short", "short"], ["identifiers_descriptive", "descriptive"]],
    fallback: "descriptive"
  },
  identifier_language: {
    choices: [["identifier_language_ro", "romanian"], ["identifier_language_en", "english"]],
    fallback: "english"
  },
  identifier_case: {
    choices: [["identifier_case_snake", "snake"], ["identifier_case_camel", "camel"]],
    fallback: "snake"
  },
  declaration_style: {
    choices: [["declarations_grouped", "grouped"], ["declarations_separate", "separate"]],
    fallback: "separate"
  },
  loop_variable_style: {
    choices: [["loop_variable_predeclared", "predeclared"], ["loop_variable_inline", "inline"]],
    fallback: "inline"
  },
  control_spacing: {
    choices: [["control_spacing_compact", "compact"], ["control_spacing_spaced", "spaced"]],
    fallback: "compact"
  }
};
const PROFILE_COUNT_KEYS = Object.values(PROFILE_DIMENSIONS)
  .flatMap((dimension) => dimension.choices.map((choice) => choice[0]));
let legacyProfileReset = false;
let previousProfileMigrated = false;

function resolvedDimension(counts, dimension) {
  const maximum = Math.max(0, ...dimension.choices.map((choice) => counts[choice[0]] || 0));
  if (maximum === 0) return {value: dimension.fallback, origin: "default"};
  const winners = dimension.choices.filter((choice) => (counts[choice[0]] || 0) === maximum);
  if (winners.length === 1) return {value: winners[0][1], origin: "learned"};
  const fallback = winners.find((choice) => choice[1] === dimension.fallback);
  return {value: (fallback || winners[0])[1], origin: "mixed"};
}

function resolvedProfile(samples, counts) {
  const preferences = {};
  const origins = {};
  for (const [name, dimension] of Object.entries(PROFILE_DIMENSIONS)) {
    const resolved = resolvedDimension(counts, dimension);
    preferences[name] = resolved.value;
    origins[name] = resolved.origin;
  }
  preferences.brace_style = preferences.function_brace_style === preferences.control_brace_style
    ? preferences.function_brace_style : "mixed";
  const hasEvidence = Object.values(counts).some((count) => count > 0);
  return {
    schema_version: PROFILE_SCHEMA_VERSION,
    samples: hasEvidence ? samples : 0,
    counts,
    preferences,
    origins
  };
}

function blankProfile() {
  return resolvedProfile(0, Object.fromEntries(PROFILE_COUNT_KEYS.map((key) => [key, 0])));
}

function sanitiseProfile(value) {
  if (!value || typeof value !== "object" ||
      ![PROFILE_SCHEMA_VERSION, PREVIOUS_PROFILE_SCHEMA_VERSION].includes(value.schema_version)) {
    return blankProfile();
  }
  const samples = Number.isInteger(value.samples)
    ? Math.max(0, Math.min(value.samples, 100)) : 0;
  const counts = {};
  if (value.counts && typeof value.counts === "object") {
    for (const key of PROFILE_COUNT_KEYS) {
      const count = value.counts[key];
      counts[key] = Number.isInteger(count)
        ? Math.max(0, Math.min(count, 10000)) : 0;
    }
  } else {
    for (const key of PROFILE_COUNT_KEYS) counts[key] = 0;
  }
  return resolvedProfile(samples, counts);
}

const state = {
  exercises: [], active: null, drafts: new Map(), edited: new Set(),
  persistDrafts: false,
  locale: "ro", hints: [], hintIndex: 0, answer: "",
  lastResponse: null, lastAnswer: null, statusKey: "",
  profileId: "profile_a",
  profiles: {profile_a: blankProfile(), profile_b: blankProfile()},
  profileMessageKey: "", profileMessageError: false,
  learningProgress: {profile_a: progressTools.blank(), profile_b: progressTools.blank()},
  attemptHistoryEnabled: {profile_a: false, profile_b: false},
  progressMessageKey: "", progressMessageError: false,
  exam: {
    definition: null, active: false, finished: false, expired: false,
    startedAt: 0, remainingMs: null, currentIndex: 0, scores: {},
    drafts: {}, intervalId: null
  }
};

function tr(key) { return translations.static[state.locale][key] || key; }

function notice(message, isError = false) {
  const box = element("notice");
  box.textContent = message;
  box.classList.toggle("error", isError);
  box.hidden = !message;
}

function rememberPreference(key, value) {
  try { localStorage.setItem(STORAGE_PREFIX + key, value); } catch (_) { /* optional */ }
}

function forgetPreference(key) {
  try { localStorage.removeItem(STORAGE_PREFIX + key); } catch (_) { /* optional */ }
}

function preferred(key, fallback) {
  try {
    const current = localStorage.getItem(STORAGE_PREFIX + key);
    if (current !== null) return current;
    if (["locale", "theme", "style"].includes(key)) {
      return localStorage.getItem(LEGACY_PREFIX + key) || fallback;
    }
    return fallback;
  } catch (_) {
    return fallback;
  }
}

function exerciseIds() {
  return state.exercises.map((exercise) => exercise.id);
}

function progressStorageKey(profileId) {
  return PROGRESS_STORAGE_PREFIX + profileId;
}

function historySettingKey(profileId) {
  return HISTORY_SETTING_PREFIX + profileId;
}

function currentLearningProgress() {
  return state.learningProgress[state.profileId];
}

function loadLearningProgress(profileId) {
  let progress = progressTools.blank();
  try {
    const raw = localStorage.getItem(progressStorageKey(profileId));
    if (raw) progress = progressTools.sanitise(JSON.parse(raw), exerciseIds());
  } catch (_) { /* ignore malformed or unavailable local storage */ }
  try {
    state.attemptHistoryEnabled[profileId] =
      localStorage.getItem(historySettingKey(profileId)) === "yes";
  } catch (_) {
    state.attemptHistoryEnabled[profileId] = false;
  }
  const storedAttemptCount = progressTools.totals(progress, exerciseIds()).attemptCount;
  if (!state.attemptHistoryEnabled[profileId]) {
    progress = progressTools.clearAttempts(progress, exerciseIds());
  }
  state.learningProgress[profileId] = progress;
  if (!state.attemptHistoryEnabled[profileId] && storedAttemptCount > 0) {
    saveLearningProgress(profileId);
  }
}

function saveLearningProgress(profileId) {
  const progress = progressTools.sanitise(state.learningProgress[profileId], exerciseIds());
  state.learningProgress[profileId] = progress;
  try {
    const totals = progressTools.totals(progress, exerciseIds());
    if (totals.favoriteCount === 0 && totals.attemptCount === 0) {
      localStorage.removeItem(progressStorageKey(profileId));
    } else {
      localStorage.setItem(progressStorageKey(profileId), JSON.stringify(progress));
    }
  } catch (_) { /* optional */ }
}

function saveHistorySetting(profileId) {
  try {
    localStorage.setItem(
      historySettingKey(profileId),
      state.attemptHistoryEnabled[profileId] ? "yes" : "no"
    );
  } catch (_) { /* optional */ }
}

function loadProfile(id) {
  try {
    const saved = preferred("style-" + id, "");
    if (!saved) return blankProfile();
    const profile = JSON.parse(saved);
    if (profile?.schema_version === PREVIOUS_PROFILE_SCHEMA_VERSION) {
      previousProfileMigrated = true;
      const migrated = sanitiseProfile(profile);
      rememberPreference("style-" + id, JSON.stringify(migrated));
      return migrated;
    }
    if (profile?.schema_version !== PROFILE_SCHEMA_VERSION) {
      legacyProfileReset = true;
      const reset = blankProfile();
      rememberPreference("style-" + id, JSON.stringify(reset));
      return reset;
    }
    return sanitiseProfile(profile);
  } catch (_) {
    return blankProfile();
  }
}

function currentProfile() { return state.profiles[state.profileId]; }

function saveCurrentProfile() {
  rememberPreference("style-" + state.profileId, JSON.stringify(currentProfile()));
}

function draftKey(exerciseId = state.active?.id, profileId = state.profileId) {
  return exerciseId ? profileId + ":" + exerciseId : "";
}

function persistedDraftKey(key) { return "draft-" + key; }

function readPersistedDraft(key) {
  if (!state.persistDrafts || !key) return {found: false, value: ""};
  try {
    const value = localStorage.getItem(STORAGE_PREFIX + persistedDraftKey(key));
    return value === null ? {found: false, value: ""} : {found: true, value};
  } catch (_) {
    return {found: false, value: ""};
  }
}

function writePersistedDraft(key, value) {
  if (!state.persistDrafts || !key || value.length > MAX_PERSISTED_DRAFT_LENGTH) return;
  rememberPreference(persistedDraftKey(key), value);
}

function storeDraft(key, value) {
  if (!key) return;
  state.drafts.set(key, value);
  writePersistedDraft(key, value);
  writeExamDraft(key, value);
}

function loadDraft(key) {
  if (state.drafts.has(key)) return state.drafts.get(key);
  if ((state.exam.active || state.exam.finished) &&
      Object.prototype.hasOwnProperty.call(state.exam.drafts, key)) {
    const value = state.exam.drafts[key];
    state.drafts.set(key, value);
    state.edited.add(key);
    return value;
  }
  const persisted = readPersistedDraft(key);
  if (!persisted.found) return undefined;
  state.drafts.set(key, persisted.value);
  state.edited.add(key);
  return persisted.value;
}

function forgetPersistedDraft(key) {
  if (key) forgetPreference(persistedDraftKey(key));
}

function clearAllPersistedDrafts() {
  for (const profileId of ["profile_a", "profile_b"]) {
    for (const exercise of state.exercises) {
      forgetPersistedDraft(draftKey(exercise.id, profileId));
    }
  }
}

function refreshDraftControls() {
  element("save-drafts").checked = state.persistDrafts;
  element("editor-help").textContent = tr(
    state.persistDrafts ? "editorHelpStored" : "editorHelp"
  );
}

function setStatus(key) {
  state.statusKey = key;
  element("run-status").textContent = key ? tr(key) : "";
}

function setProfileMessage(key, isError = false) {
  state.profileMessageKey = key;
  state.profileMessageError = isError;
  const message = element("profile-message");
  message.textContent = key ? tr(key) : "";
  message.classList.toggle("error", isError);
}

function setProgressMessage(key, isError = false) {
  state.progressMessageKey = key;
  state.progressMessageError = isError;
  const message = element("progress-message");
  message.textContent = key ? tr(key) : "";
  message.classList.toggle("error", isError);
}

function localizedExerciseTitle(exercise) {
  if (!exercise) return "";
  return state.locale === "ro" ? translations.exercises[exercise.id].title : exercise.title;
}

function refreshExerciseOptions() {
  const list = element("exercise-select");
  const favorites = new Set(currentLearningProgress().favorites);
  for (const option of list.options) {
    const exercise = state.exercises.find((item) => item.id === option.value);
    if (exercise) {
      option.textContent = (favorites.has(exercise.id) ? "★ " : "")
        + localizedExerciseTitle(exercise);
    }
  }
}

function progressTotalsText(totals) {
  if (state.locale === "ro") {
    return totals.favoriteCount + " " + (totals.favoriteCount === 1 ? "favorit" : "favorite")
      + " · " + totals.attemptCount + " " + (totals.attemptCount === 1 ? "încercare" : "încercări")
      + " · " + totals.solvedCount + " "
      + (totals.solvedCount === 1 ? "exercițiu rezolvat complet" : "exerciții rezolvate complet");
  }
  return totals.favoriteCount + " " + (totals.favoriteCount === 1 ? "favorite" : "favorites")
    + " · " + totals.attemptCount + " " + (totals.attemptCount === 1 ? "attempt" : "attempts")
    + " · " + totals.solvedCount + " fully solved "
    + (totals.solvedCount === 1 ? "exercise" : "exercises");
}

function attemptResultText(attempt) {
  if (!attempt) return "—";
  if (!attempt.compiled) return tr("attemptCompilationFailed");
  return attempt.passed + "/" + attempt.total;
}

function exerciseProgressText() {
  if (!state.active) return "";
  if (!state.attemptHistoryEnabled[state.profileId]) return tr("attemptHistoryOff");
  const summary = progressTools.summary(
    currentLearningProgress(), state.active.id, exerciseIds()
  );
  if (!summary.count) return tr("noSavedAttempts");
  const count = state.locale === "ro"
    ? summary.count + " " + (summary.count === 1 ? "încercare" : "încercări")
    : summary.count + " " + (summary.count === 1 ? "attempt" : "attempts");
  return state.locale === "ro"
    ? "Ultimul: " + attemptResultText(summary.last)
      + " · Cel mai bun: " + attemptResultText(summary.best) + " · " + count
    : "Last: " + attemptResultText(summary.last)
      + " · Best: " + attemptResultText(summary.best) + " · " + count;
}

function fullySolved(summary) {
  return Boolean(
    summary.best && summary.best.total > 0 && summary.best.passed === summary.best.total
  );
}

function trackedExerciseText(exercise, summary, isFavorite) {
  const title = localizedExerciseTitle(exercise);
  const prefix = isFavorite ? "★ " : "";
  if (!summary.count) return prefix + title + " · " + tr("trackedExerciseNoResults");
  const count = state.locale === "ro"
    ? summary.count + " " + (summary.count === 1 ? "încercare" : "încercări")
    : summary.count + " " + (summary.count === 1 ? "attempt" : "attempts");
  return state.locale === "ro"
    ? prefix + title + " · cel mai bun " + attemptResultText(summary.best) + " · " + count
    : prefix + title + " · best " + attemptResultText(summary.best) + " · " + count;
}

function refreshProgressBreakdown(progress) {
  const summaries = new Map(state.exercises.map((exercise) => [
    exercise.id,
    progressTools.summary(progress, exercise.id, exerciseIds())
  ]));
  const conceptList = element("concept-progress");
  const conceptNote = element("concept-progress-note");
  const conceptOverlap = element("concept-progress-overlap");
  conceptList.replaceChildren();
  const historyEnabled = state.attemptHistoryEnabled[state.profileId];
  conceptList.hidden = !historyEnabled;
  conceptOverlap.hidden = !historyEnabled;
  conceptNote.hidden = historyEnabled;
  conceptNote.textContent = historyEnabled ? "" : tr("conceptProgressHistoryOff");
  if (historyEnabled) {
    for (const concept of PROGRESS_CONCEPTS) {
      const matching = state.exercises.filter((exercise) =>
        Array.isArray(exercise.tags) && exercise.tags.some((tag) => concept.tags.includes(tag))
      );
      if (!matching.length) continue;
      const attempted = matching.filter((exercise) => summaries.get(exercise.id).count > 0).length;
      const solved = matching.filter((exercise) => fullySolved(summaries.get(exercise.id))).length;
      const label = translations.progressConcepts[state.locale][concept.id];
      const text = state.locale === "ro"
        ? label + ": rezolvate " + solved + "/" + matching.length + " · încercate " + attempted
        : label + ": solved " + solved + "/" + matching.length + " · attempted " + attempted;
      addTextItem(conceptList, text);
    }
  }

  const favorites = new Set(progress.favorites);
  const tracked = state.exercises.filter((exercise) =>
    favorites.has(exercise.id) || summaries.get(exercise.id).count > 0
  );
  const exerciseList = element("exercise-progress-list");
  exerciseList.replaceChildren();
  for (const exercise of tracked) {
    addTextItem(
      exerciseList,
      trackedExerciseText(exercise, summaries.get(exercise.id), favorites.has(exercise.id))
    );
  }
  exerciseList.hidden = tracked.length === 0;
  element("progress-breakdown-empty").hidden = tracked.length > 0;
}

function refreshProgress() {
  const progress = currentLearningProgress();
  const totals = progressTools.totals(progress, exerciseIds());
  element("save-attempt-history").checked = state.attemptHistoryEnabled[state.profileId];
  element("progress-summary-badge").textContent = totals.favoriteCount + " ★ · "
    + totals.solvedCount + "/" + state.exercises.length + " ✓";
  element("progress-summary").textContent = progressTotalsText(totals);
  const favoriteButton = element("favorite-exercise");
  const isFavorite = Boolean(state.active && progress.favorites.includes(state.active.id));
  favoriteButton.disabled = !state.active;
  favoriteButton.textContent = tr(isFavorite ? "favoriteRemove" : "favoriteAdd");
  favoriteButton.setAttribute("aria-pressed", String(isFavorite));
  element("exercise-progress").textContent = exerciseProgressText();
  refreshProgressBreakdown(progress);
  setProgressMessage(state.progressMessageKey, state.progressMessageError);
}

function refreshHeader() {
  document.documentElement.lang = state.locale;
  const languageButton = element("language-toggle");
  languageButton.textContent = state.locale === "ro" ? "English" : "Română";
  languageButton.setAttribute("aria-pressed", String(state.locale === "en"));
  languageButton.setAttribute("aria-label", state.locale === "ro" ? "Schimbă în engleză" : "Switch to Romanian");
  const themeButton = element("theme-toggle");
  const isDark = document.documentElement.dataset.theme === "dark";
  themeButton.textContent = tr(isDark ? "lightMode" : "darkMode");
  themeButton.setAttribute("aria-label", themeButton.textContent);
  themeButton.setAttribute("aria-pressed", String(isDark));
}

function traitWithOrigin(label, origin) {
  if (origin === "default") return label + " (" + tr("traitDefault") + ")";
  if (origin === "mixed") return label + " (" + tr("traitMixed") + ")";
  return label;
}

function profileSummary(profile) {
  if (!profile || !Number.isInteger(profile.samples) || profile.samples < 1) return tr("profileEmpty");
  const preferences = profile.preferences || blankProfile().preferences;
  const origins = profile.origins || blankProfile().origins;
  const incrementKeys = {
    prefix: "incrementPrefix", postfix: "incrementPostfix",
    assignment: "incrementAssignment", compound: "incrementCompound"
  };
  const traits = [
    traitWithOrigin(
      tr(preferences.function_brace_style === "next_line" ? "functionBraceNext" : "functionBraceSame"),
      origins.function_brace_style
    ),
    traitWithOrigin(
      tr(preferences.control_brace_style === "next_line" ? "controlBraceNext" : "controlBraceSame"),
      origins.control_brace_style
    ),
    traitWithOrigin(tr(incrementKeys[preferences.increment_style]), origins.increment_style),
    traitWithOrigin(tr(preferences.indent_width === 2 ? "indent2" : "indent4"), origins.indent_width),
    traitWithOrigin(
      tr(preferences.comment_style === "explanatory" ? "commentsExplanatory" : "commentsMinimal"),
      origins.comment_style
    ),
    traitWithOrigin(
      tr(preferences.main_signature === "empty" ? "mainEmpty" : "mainVoid"),
      origins.main_signature
    ),
    traitWithOrigin(
      tr(preferences.identifier_style === "short" ? "identifiersShort" : "identifiersDescriptive"),
      origins.identifier_style
    ),
    traitWithOrigin(
      tr(preferences.declaration_style === "grouped" ? "declarationsGrouped" : "declarationsSeparate"),
      origins.declaration_style
    ),
    traitWithOrigin(
      tr(preferences.loop_variable_style === "predeclared" ? "loopPredeclared" : "loopInline"),
      origins.loop_variable_style
    ),
    traitWithOrigin(
      tr(preferences.control_spacing === "spaced" ? "controlSpacingSpaced" : "controlSpacingCompact"),
      origins.control_spacing
    )
  ];
  if (preferences.comment_style === "explanatory") {
    traits.push(traitWithOrigin(
      preferences.comment_syntax === "line" ? "//" : "/* … */",
      origins.comment_syntax
    ));
    traits.push(traitWithOrigin(
      tr(preferences.comment_placement === "inline" ? "commentsInline" : "commentsOutline"),
      origins.comment_placement
    ));
  }
  if (preferences.identifier_style === "descriptive" && origins.identifier_language !== "default") {
    traits.push(traitWithOrigin(
      tr(preferences.identifier_language === "romanian" ? "identifiersRomanian" : "identifiersEnglish"),
      origins.identifier_language
    ));
  }
  if (preferences.identifier_style === "descriptive" && origins.identifier_case !== "default") {
    traits.push(traitWithOrigin(
      tr(preferences.identifier_case === "camel" ? "identifierCaseCamel" : "identifierCaseSnake"),
      origins.identifier_case
    ));
  }
  const examples = state.locale === "ro"
    ? profile.samples + " " + (profile.samples === 1 ? "exemplu" : "exemple")
    : profile.samples + " " + (profile.samples === 1 ? "example" : "examples");
  return examples + " · " + traits.join(" · ");
}

function refreshProfile() {
  element("profile-select").value = state.profileId;
  element("profile-summary").textContent = profileSummary(currentProfile());
  setProfileMessage(state.profileMessageKey, state.profileMessageError);
}

function translateStatic() {
  document.querySelectorAll("[data-i18n]").forEach((item) => {
    item.textContent = tr(item.dataset.i18n);
  });
  document.title = tr("browserTitle");
  refreshHeader();
  refreshProfile();
  refreshDraftControls();
  refreshProgress();
  setStatus(state.statusKey);
  renderExam();
}

async function requestJSON(path, options) {
  const response = await fetch(path, {cache: "no-store", ...options});
  const data = await response.json();
  if (!response.ok) {
    const description = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    throw new Error(description || "Request failed (" + response.status + ").");
  }
  return data;
}

function addTextItem(parent, text, tag = "li") {
  const item = document.createElement(tag);
  item.textContent = text;
  parent.append(item);
  return item;
}

function examTasks() {
  return Array.isArray(state.exam.definition?.tasks) ? state.exam.definition.tasks : [];
}

function examTaskTitle(exerciseId) {
  const exercise = state.exercises.find((item) => item.id === exerciseId);
  if (!exercise) return exerciseId;
  return localizedExerciseTitle(exercise);
}

function examMaximum() {
  return Number(state.exam.definition?.maximum_points) || 10;
}

function estimatedExamScore() {
  const base = Number(state.exam.definition?.base_points) || 0;
  return examTasks().reduce((total, task) => {
    const score = Number(state.exam.scores[task.exercise_id]?.points) || 0;
    return total + Math.max(0, Math.min(Number(task.points) || 0, score));
  }, base);
}

function examDurationMs() {
  return (Number(state.exam.definition?.duration_minutes) || 60) * 60 * 1000;
}

function examRemainingMs() {
  if (state.exam.finished && Number.isFinite(state.exam.remainingMs)) {
    return Math.max(0, Math.min(examDurationMs(), state.exam.remainingMs));
  }
  if (!state.exam.startedAt) return examDurationMs();
  return Math.max(0, state.exam.startedAt + examDurationMs() - Date.now());
}

function formatExamTime(milliseconds) {
  const seconds = Math.max(0, Math.ceil(milliseconds / 1000));
  const minutes = Math.floor(seconds / 60);
  return String(minutes).padStart(2, "0") + ":" + String(seconds % 60).padStart(2, "0");
}

function persistExamSession() {
  if (!state.exam.definition) return;
  const payload = {
    exam_id: state.exam.definition.id,
    active: state.exam.active,
    finished: state.exam.finished,
    expired: state.exam.expired,
    started_at: state.exam.startedAt,
    remaining_ms: examRemainingMs(),
    current_index: state.exam.currentIndex,
    scores: state.exam.scores
  };
  try { localStorage.setItem(EXAM_SESSION_KEY, JSON.stringify(payload)); } catch (_) { /* optional */ }
}

function validExamDraftKey(key) {
  if (typeof key !== "string") return false;
  const separator = key.indexOf(":");
  if (separator <= 0) return false;
  const profileId = key.slice(0, separator);
  const exerciseId = key.slice(separator + 1);
  return ["profile_a", "profile_b"].includes(profileId) &&
    examTasks().some((task) => task.exercise_id === exerciseId);
}

function persistExamDrafts() {
  if (!state.exam.definition) return;
  const payload = {exam_id: state.exam.definition.id, drafts: state.exam.drafts};
  try { sessionStorage.setItem(EXAM_DRAFTS_KEY, JSON.stringify(payload)); } catch (_) { /* optional */ }
}

function restoreExamDrafts() {
  state.exam.drafts = {};
  if (!state.exam.definition || (!state.exam.active && !state.exam.finished)) return;
  try {
    const raw = sessionStorage.getItem(EXAM_DRAFTS_KEY);
    if (!raw) return;
    const saved = JSON.parse(raw);
    if (!saved || saved.exam_id !== state.exam.definition.id ||
        !saved.drafts || typeof saved.drafts !== "object") return;
    for (const [key, value] of Object.entries(saved.drafts)) {
      if (validExamDraftKey(key) && typeof value === "string" &&
          value.length <= MAX_PERSISTED_DRAFT_LENGTH) {
        state.exam.drafts[key] = value;
      }
    }
  } catch (_) { /* ignore malformed or unavailable tab storage */ }
}

function writeExamDraft(key, value) {
  if (!state.exam.active || !validExamDraftKey(key) ||
      value.length > MAX_PERSISTED_DRAFT_LENGTH) return;
  state.exam.drafts[key] = value;
  persistExamDrafts();
}

function forgetExamDraft(key) {
  if (!key || !Object.prototype.hasOwnProperty.call(state.exam.drafts, key)) return;
  delete state.exam.drafts[key];
  persistExamDrafts();
}

function clearExamDrafts(removeFromMemory = false) {
  const keys = Object.keys(state.exam.drafts);
  state.exam.drafts = {};
  if (removeFromMemory) {
    for (const key of keys) {
      state.drafts.delete(key);
      state.edited.delete(key);
    }
  }
  try { sessionStorage.removeItem(EXAM_DRAFTS_KEY); } catch (_) { /* optional */ }
}

function restoreExamSession() {
  if (!state.exam.definition) return;
  try {
    const raw = localStorage.getItem(EXAM_SESSION_KEY);
    if (!raw) return;
    const saved = JSON.parse(raw);
    if (!saved || saved.exam_id !== state.exam.definition.id ||
        !Number.isFinite(saved.started_at) || saved.started_at <= 0) return;
    const tasks = examTasks();
    const scores = {};
    if (saved.scores && typeof saved.scores === "object") {
      for (const task of tasks) {
        const candidate = saved.scores[task.exercise_id];
        if (!candidate || !Number.isFinite(candidate.points) ||
            !Number.isInteger(candidate.passed) || !Number.isInteger(candidate.total)) continue;
        scores[task.exercise_id] = {
          passed: Math.max(0, candidate.passed),
          total: Math.max(0, candidate.total),
          points: Math.max(0, Math.min(Number(task.points), candidate.points))
        };
      }
    }
    state.exam.active = Boolean(saved.active);
    state.exam.finished = Boolean(saved.finished);
    state.exam.expired = Boolean(saved.expired);
    state.exam.startedAt = saved.started_at;
    const savedRemaining = Number(saved.remaining_ms);
    state.exam.remainingMs = state.exam.finished
      ? state.exam.expired
        ? 0
        : Number.isFinite(savedRemaining)
          ? Math.max(0, Math.min(examDurationMs(), savedRemaining))
          : Math.max(0, saved.started_at + examDurationMs() - Date.now())
      : null;
    state.exam.currentIndex = Number.isInteger(saved.current_index)
      ? Math.max(0, Math.min(tasks.length - 1, saved.current_index)) : 0;
    state.exam.scores = scores;
    if (state.exam.active && examRemainingMs() <= 0) {
      state.exam.active = false;
      state.exam.finished = true;
      state.exam.expired = true;
      state.exam.remainingMs = 0;
      persistExamSession();
    } else if (state.exam.finished && !Number.isFinite(savedRemaining)) {
      persistExamSession();
    }
  } catch (_) { /* ignore malformed local state */ }
}

function renderExamRubric() {
  const list = element("exam-rubric-list");
  if (!list) return;
  list.replaceChildren();
  const criteriaTranslations = translations.examCriteria?.[state.locale] || {};
  for (const task of examTasks()) {
    const item = addTextItem(
      list,
      examTaskTitle(task.exercise_id) + " · " + Number(task.points).toFixed(1) + "p"
    );
    const criteria = document.createElement("ul");
    for (const criterion of task.criteria || []) {
      const description = criteriaTranslations[criterion.key] || criterion.description;
      addTextItem(criteria, Number(criterion.points).toFixed(1) + "p · " + description);
    }
    item.append(criteria);
  }
}

function renderExam() {
  const definition = state.exam.definition;
  if (!definition || !element("exam-summary-badge")) return;
  element("exam-summary-badge").textContent = definition.duration_minutes + " min · "
    + Number(definition.maximum_points).toFixed(0) + (state.locale === "ro" ? "p" : " pts");
  element("start-exam").hidden = state.exam.active;
  element("finish-exam").hidden = !state.exam.active;
  element("next-exam-task").hidden = !state.exam.active;
  const hasSession = state.exam.active || state.exam.finished || Object.keys(state.exam.scores).length > 0;
  element("exam-session").hidden = !hasSession;
  element("exam-timer").textContent = formatExamTime(examRemainingMs());
  element("exam-score").textContent = estimatedExamScore().toFixed(2) + " / "
    + examMaximum().toFixed(0);
  const taskList = element("exam-task-list");
  taskList.replaceChildren();
  examTasks().forEach((task, index) => {
    const result = state.exam.scores[task.exercise_id];
    let status = tr("examNotTested");
    if (result) {
      status = result.passed + "/" + result.total + " "
        + (state.locale === "ro" ? "teste" : "tests") + " · "
        + Number(result.points).toFixed(2) + "p";
    }
    const item = addTextItem(
      taskList,
      examTaskTitle(task.exercise_id) + " · " + Number(task.points).toFixed(1) + "p · " + status
    );
    if (state.exam.active && index === state.exam.currentIndex) item.className = "current";
    if (result && result.passed === result.total && result.total > 0) item.className = "completed";
  });
  element("exam-note").textContent = tr(
    state.exam.active ? "examActiveNote" : "examFinishedNote"
  );
  renderExamRubric();
}

function clearExamClock() {
  if (state.exam.intervalId !== null) clearInterval(state.exam.intervalId);
  state.exam.intervalId = null;
}

function updateExamClock() {
  if (!state.exam.active) return;
  const remaining = examRemainingMs();
  if (remaining <= 0) {
    finishExam(true);
    return;
  }
  element("exam-timer").textContent = formatExamTime(remaining);
}

function startExamClock() {
  clearExamClock();
  updateExamClock();
  if (state.exam.active) state.exam.intervalId = setInterval(updateExamClock, 1000);
}

function startExam() {
  const tasks = examTasks();
  if (!tasks.length) return;
  clearExamDrafts(true);
  state.exam.active = true;
  state.exam.finished = false;
  state.exam.expired = false;
  state.exam.startedAt = Date.now();
  state.exam.remainingMs = null;
  state.exam.currentIndex = 0;
  state.exam.scores = {};
  persistExamSession();
  startExamClock();
  selectExercise(tasks[0].exercise_id);
  renderExam();
  notice(tr("examStarted"));
}

function finishExam(expired = false) {
  if (!state.exam.active) return;
  if (!expired && !window.confirm(tr("examFinishConfirm"))) return;
  const remaining = expired ? 0 : examRemainingMs();
  state.exam.active = false;
  state.exam.finished = true;
  state.exam.expired = expired;
  state.exam.remainingMs = remaining;
  clearExamClock();
  persistExamSession();
  renderExam();
  notice(tr(expired ? "examExpired" : "examFinished"));
}

function nextExamTask() {
  const tasks = examTasks();
  if (!state.exam.active || !tasks.length) return;
  state.exam.currentIndex = (state.exam.currentIndex + 1) % tasks.length;
  persistExamSession();
  selectExercise(tasks[state.exam.currentIndex].exercise_id);
  renderExam();
}

function recordExamResult(exerciseId, evaluation) {
  if (!state.exam.active || !evaluation) return;
  const task = examTasks().find((item) => item.exercise_id === exerciseId);
  if (!task || !evaluation.total_count) return;
  const points = Number((Number(task.points) * evaluation.passed_count /
    evaluation.total_count).toFixed(2));
  const previous = state.exam.scores[exerciseId];
  if (previous && previous.points >= points) return;
  state.exam.scores[exerciseId] = {
    passed: evaluation.passed_count,
    total: evaluation.total_count,
    points
  };
  persistExamSession();
  renderExam();
}

function displayStarter(exercise) {
  if (state.locale === "en") return exercise.starter_code;
  const comments = translations.starterComments[exercise.id] || [];
  let index = 0;
  return exercise.starter_code.replace(/\/\*[\s\S]*?\*\//g, (original) => {
    const translation = comments[index++];
    return translation ? "/* " + translation + " */" : original;
  });
}

function clearFeedback() {
  state.hints = [];
  state.hintIndex = 0;
  state.lastResponse = null;
  state.lastAnswer = null;
  state.answer = "";
  element("result-card").hidden = true;
  element("solution-answer").hidden = true;
  element("hint-area").hidden = true;
  element("next-hint").hidden = true;
}

function renderPublicTests(exercise) {
  const list = element("public-tests");
  list.replaceChildren();
  exercise.public_tests.forEach((example, index) => {
    const name = state.locale === "ro" ? tr("example") + " " + (index + 1) : example.name;
    const item = addTextItem(list, name);
    const input = document.createElement("pre");
    input.textContent = tr("input") + ": " + example.input;
    const output = document.createElement("pre");
    output.textContent = tr("output") + ": " + example.expected;
    item.append(input, output);
  });
}

function refreshExercise() {
  const exercise = state.active;
  if (!exercise) return;
  const view = state.locale === "ro" ? translations.exercises[exercise.id] : exercise;
  element("exercise-select").value = exercise.id;
  element("exercise-title").textContent = view.title;
  element("exercise-statement").textContent = view.statement;
  element("input-format").textContent = view.input_format;
  element("output-format").textContent = view.output_format;
  element("exercise-count").textContent = state.locale === "ro"
    ? state.exercises.length + " exerciții · câte 2 exemple publice"
    : state.exercises.length + " curated exercises · 2 public examples each";
  const key = draftKey(exercise.id);
  if (!state.edited.has(key)) {
    element("code").value = displayStarter(exercise);
    state.drafts.set(key, element("code").value);
  }
  renderPublicTests(exercise);
  refreshProgress();
}

function selectExercise(id) {
  if (state.active) {
    const currentKey = draftKey();
    state.drafts.set(currentKey, element("code").value);
    if (state.edited.has(currentKey)) {
      writePersistedDraft(currentKey, element("code").value);
      writeExamDraft(currentKey, element("code").value);
    }
  }
  const exercise = state.exercises.find((candidate) => candidate.id === id);
  if (!exercise) return;
  state.active = exercise;
  if (state.exam.active) {
    const examIndex = examTasks().findIndex((task) => task.exercise_id === id);
    if (examIndex >= 0) {
      state.exam.currentIndex = examIndex;
      persistExamSession();
    }
  }
  const key = draftKey(id);
  const savedDraft = loadDraft(key);
  element("code").value = state.edited.has(key)
    ? savedDraft ?? ""
    : displayStarter(exercise);
  refreshExercise();
  clearFeedback();
  setStatus("");
  setProfileMessage("");
  setProgressMessage("");
  notice("");
  renderExam();
}

function switchProfile(id) {
  if (!["profile_a", "profile_b"].includes(id) || id === state.profileId) return;
  if (state.active) {
    const currentKey = draftKey();
    state.drafts.set(currentKey, element("code").value);
    if (state.edited.has(currentKey)) {
      writePersistedDraft(currentKey, element("code").value);
      writeExamDraft(currentKey, element("code").value);
    }
  }
  state.profileId = id;
  rememberPreference("active-profile", id);
  if (state.active) {
    const key = draftKey();
    const savedDraft = loadDraft(key);
    element("code").value = state.edited.has(key)
      ? savedDraft ?? ""
      : displayStarter(state.active);
  }
  clearFeedback();
  setStatus("");
  setProfileMessage("");
  setProgressMessage("");
  refreshProfile();
  refreshExerciseOptions();
  refreshProgress();
  notice("");
}

function showNextHint() {
  if (state.hintIndex >= state.hints.length) return;
  addTextItem(element("hints"), state.hints[state.hintIndex]);
  state.hintIndex += 1;
  const button = element("next-hint");
  button.hidden = state.hintIndex >= state.hints.length;
  button.textContent = state.locale === "ro"
    ? "Arată indiciul " + (state.hintIndex + 1) + " din " + state.hints.length
    : "Show hint " + (state.hintIndex + 1) + " of " + state.hints.length;
}

function renderFeedback(response, revealed = 1) {
  const result = response.evaluation;
  const candidate = response.candidates[0];
  element("result-card").hidden = false;
  element("result-count").textContent = result.compilation.succeeded
    ? state.locale === "ro"
      ? result.passed_count + " din " + result.total_count + " reușite"
      : result.passed_count + "/" + result.total_count + " passed"
    : tr("compilationFailed");
  const warning = element("language-warning");
  warning.replaceChildren();
  const warningMessages = [];
  if (response.language_warning) {
    warningMessages.push(state.locale === "ro" ? tr("warningCpp") : response.language_warning);
  }
  const compatibilityTranslations = translations.compatibilityWarnings?.[state.locale] || {};
  for (const item of response.compatibility_warnings || []) {
    warningMessages.push(compatibilityTranslations[item.id] || item.message);
  }
  if (warningMessages.length) {
    const warningList = document.createElement("ul");
    for (const message of warningMessages) addTextItem(warningList, message);
    warning.append(warningList);
  }
  warning.hidden = warningMessages.length === 0;

  const compilation = element("compiler-output");
  compilation.replaceChildren();
  addTextItem(compilation, tr(result.compilation.succeeded ? "compilationSucceeded" : "compilationFailed"), "p");
  if (result.compilation.stderr) {
    const diagnostics = document.createElement("pre");
    diagnostics.className = "compilation-error";
    diagnostics.textContent = result.compilation.stderr;
    compilation.append(diagnostics);
  }
  const diagnosis = element("diagnosis");
  diagnosis.replaceChildren();
  if (candidate) {
    let description;
    if (state.locale === "ro") {
      const category = translations.categories[candidate.category] || translations.categories.unknown;
      description = tr("possibleIssue") + ": " + category + ". (" + tr("ruleScope") + ")";
    } else {
      description = tr("possibleIssue") + ": " + candidate.category.replaceAll("_", " ")
        + ". " + candidate.evidence + " (" + response.diagnosis_scope + ")";
    }
    addTextItem(diagnosis, description, "p").className = "diagnostic";
  } else if (result.all_passed) {
    addTextItem(diagnosis, tr("allPassed"), "p");
  }

  const tests = element("test-results");
  tests.replaceChildren();
  let visibleIndex = 0;
  let hiddenIndex = 0;
  for (const test of result.tests) {
    const item = document.createElement("li");
    const name = document.createElement("span");
    if (state.locale === "ro") {
      name.textContent = test.hidden
        ? tr("hiddenTest") + " " + (++hiddenIndex)
        : tr("publicTest") + " " + (++visibleIndex);
    } else {
      name.textContent = test.hidden ? test.name + " (hidden)" : test.name;
    }
    const status = document.createElement("strong");
    status.className = test.status;
    status.textContent = tr(test.status).replaceAll("_", " ");
    item.append(name, status);
    tests.append(item);
  }
  state.hints = candidate && state.locale === "ro"
    ? translations.hints[candidate.category] || translations.hints.unknown
    : response.progressive_hints;
  state.hintIndex = 0;
  element("hints").replaceChildren();
  element("hint-area").hidden = state.hints.length === 0;
  for (let index = 0; index < Math.min(revealed, state.hints.length); index++) showNextHint();
}

function translatedAnswerSource(answer) {
  if (state.locale !== "ro") return answer.source;
  const personalisedComments = answer.style === "personalized_c"
    && answer.personalization?.preferences?.comment_style === "explanatory";
  const pclpComments = answer.style === "pclp1_classic";
  if (answer.style !== "commented_c" && !personalisedComments && !pclpComments) return answer.source;
  const steps = translations.explanations[state.active.id];
  let translated = answer.source;
  const lineComments = pclpComments || (personalisedComments
    && answer.personalization?.preferences?.comment_syntax === "line");
  if (lineComments) {
    const outline = "// " + tr("commentOutline") + ":\n"
      + steps.map((step, index) => "// " + (index + 1) + ". " + step + "\n").join("")
      + "\n";
    translated = translated.replace(/\/\/ Solution outline:\n(?:\/\/[^\n]*\n){3}\n?/, outline);
  } else {
    const outline = "/* " + tr("commentOutline") + ":\n"
      + steps.map((step, index) => " * " + (index + 1) + ". " + step + "\n").join("")
      + " */\n\n";
    translated = translated.replace(/\/\* Solution outline:[\s\S]*?\*\/\s*/, outline);
  }
  for (let index = 0; index < steps.length; index++) {
    const english = answer.explanation?.[index];
    if (english) translated = translated.split(english).join(steps[index]);
  }
  return translated;
}

function renderAnswer(answer) {
  state.answer = translatedAnswerSource(answer);
  const styleKey = {
    personalized_c: "stylePersonalized",
    pclp1_classic: "stylePclp1Classic",
    classic_c: "styleClassic",
    commented_c: "styleCommented"
  }[answer.style];
  element("solution-meta").textContent = answer.course + " · " + tr(styleKey) + " · " + answer.compiler;
  element("solution-code").textContent = state.answer;
  const list = element("solution-explanation");
  list.replaceChildren();
  const steps = state.locale === "ro" ? translations.explanations[state.active.id] : answer.explanation;
  for (const step of steps) addTextItem(list, step);
  if (answer.style === "personalized_c") {
    element("solution-note").textContent = tr(
      answer.personalization?.applied ? "personalizedNote" : "personalizedEmptyNote"
    );
  } else if (answer.style === "pclp1_classic") {
    element("solution-note").textContent = tr("pclpPresetNote");
  } else {
    element("solution-note").textContent = state.locale === "ro" ? tr("styleNote") : answer.note;
  }
  element("solution-answer").hidden = false;
}

function switchLanguage() {
  // Preserve the state the learner can actually see. Browser interaction during
  // the locale refresh must not collapse revealed hints or mark unchanged source
  // as a new draft.
  const revealedHints = element("hints").children.length;
  const statusKey = state.statusKey;
  const source = element("code").value;
  const keepEditedSource = state.active && state.edited.has(draftKey());
  state.locale = state.locale === "ro" ? "en" : "ro";
  rememberPreference("locale", state.locale);
  translateStatic();
  refreshExerciseOptions();
  refreshExercise();
  if (keepEditedSource) element("code").value = source;
  if (state.lastResponse) renderFeedback(state.lastResponse, revealedHints);
  if (state.lastAnswer) renderAnswer(state.lastAnswer);
  renderExam();
  setStatus(statusKey);
  notice("");
}

function switchTheme() {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  rememberPreference("theme", next);
  refreshHeader();
}

function localizedError(error) {
  if (state.locale === "en") return error.message;
  return error.message && error.message.includes("Local code execution is disabled")
    ? tr("executionDisabled") : tr("generalError");
}

async function learnStyle() {
  const source = element("code").value;
  if (!source.trim()) {
    setProfileMessage("codeRequired", true);
    return;
  }
  const profileId = state.profileId;
  const button = element("learn-style");
  button.disabled = true;
  button.textContent = tr("learningStyle");
  setProfileMessage("");
  try {
    const result = await requestJSON("/style-profile/learn", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({source, profile: currentProfile()})
    });
    if (state.profileId !== profileId || element("code").value !== source) return;
    if (result.accepted) {
      state.profiles[profileId] = sanitiseProfile(result.profile);
      saveCurrentProfile();
      state.lastAnswer = null;
      element("solution-answer").hidden = true;
      refreshProfile();
      setProfileMessage("profileLearned");
    } else {
      setProfileMessage(
        result.reason === "cpp_ignored" ? "profileCppIgnored" : "profileNotEnough",
        true
      );
    }
  } catch (_) {
    setProfileMessage("generalError", true);
  } finally {
    button.disabled = false;
    button.textContent = tr("learnStyle");
  }
}

function resetProfile() {
  if (!window.confirm(tr("resetConfirm"))) return;
  state.profiles[state.profileId] = blankProfile();
  forgetPreference("style-" + state.profileId);
  state.lastAnswer = null;
  element("solution-answer").hidden = true;
  refreshProfile();
  setProfileMessage("profileReset");
}

function toggleFavorite() {
  if (!state.active) return;
  const profileId = state.profileId;
  const wasFavorite = currentLearningProgress().favorites.includes(state.active.id);
  state.learningProgress[profileId] = progressTools.toggleFavorite(
    currentLearningProgress(), state.active.id, exerciseIds()
  );
  saveLearningProgress(profileId);
  refreshExerciseOptions();
  setProgressMessage(wasFavorite ? "favoriteRemoved" : "favoriteAdded");
  refreshProgress();
}

function toggleAttemptHistory(event) {
  const profileId = state.profileId;
  const enable = Boolean(event.target.checked);
  const totals = progressTools.totals(currentLearningProgress(), exerciseIds());
  if (!enable && totals.attemptCount > 0 && !window.confirm(tr("disableHistoryConfirm"))) {
    event.target.checked = true;
    return;
  }
  state.attemptHistoryEnabled[profileId] = enable;
  saveHistorySetting(profileId);
  if (!enable) {
    state.learningProgress[profileId] = progressTools.clearAttempts(
      currentLearningProgress(), exerciseIds()
    );
    saveLearningProgress(profileId);
  }
  setProgressMessage(enable ? "historySavingEnabled" : "historySavingDisabled");
  refreshProgress();
}

function clearLearningProgress() {
  if (!window.confirm(tr("clearProgressConfirm"))) return;
  state.learningProgress[state.profileId] = progressTools.blank();
  try { localStorage.removeItem(progressStorageKey(state.profileId)); } catch (_) { /* optional */ }
  refreshExerciseOptions();
  setProgressMessage("progressCleared");
  refreshProgress();
}

function recordLearningAttempt(profileId, exerciseId, evaluation) {
  if (!state.attemptHistoryEnabled[profileId]) return;
  state.learningProgress[profileId] = progressTools.recordAttempt(
    state.learningProgress[profileId], exerciseId, evaluation, exerciseIds()
  );
  saveLearningProgress(profileId);
  if (state.profileId === profileId) refreshProgress();
}

function toggleDraftPersistence(event) {
  state.persistDrafts = Boolean(event.target.checked);
  rememberPreference("save-drafts", state.persistDrafts ? "yes" : "no");
  if (state.persistDrafts) {
    for (const key of state.edited) {
      if (state.drafts.has(key)) writePersistedDraft(key, state.drafts.get(key));
    }
    notice(tr("draftSavingEnabled"));
  } else {
    clearAllPersistedDrafts();
    notice(tr("draftSavingDisabled"));
  }
  refreshDraftControls();
}

function resetDraft() {
  if (!state.active || !window.confirm(tr("resetDraftConfirm"))) return;
  const key = draftKey();
  forgetPersistedDraft(key);
  forgetExamDraft(key);
  state.edited.delete(key);
  const starter = displayStarter(state.active);
  state.drafts.set(key, starter);
  element("code").value = starter;
  clearFeedback();
  setStatus("");
  setProfileMessage("");
  notice(tr("draftReset"));
}

async function runCode() {
  if (!state.active) return;
  const exerciseId = state.active.id;
  const profileId = state.profileId;
  const source = element("code").value;
  if (!source.trim()) { notice(tr("codeRequired"), true); return; }
  const button = element("run");
  button.disabled = true;
  setStatus("running");
  notice("");
  try {
    const response = await requestJSON("/exercises/" + encodeURIComponent(exerciseId) + "/submit", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({source, dialect: "c17"})
    });
    if (!state.active || state.active.id !== exerciseId || state.profileId !== profileId ||
        element("code").value !== source) return;
    state.lastResponse = response;
    renderFeedback(response);
    recordLearningAttempt(profileId, exerciseId, response.evaluation);
    recordExamResult(exerciseId, response.evaluation);
    setStatus("ready");
  } catch (error) {
    notice(localizedError(error), true);
    setStatus("couldNotRun");
  } finally {
    button.disabled = false;
  }
}

async function showSolution() {
  if (!state.active) return;
  const exerciseId = state.active.id;
  const source = element("code").value;
  const style = element("style").value;
  const profileId = state.profileId;
  const button = element("show-solution");
  button.disabled = true;
  button.textContent = tr("preparing");
  notice("");
  try {
    const answer = await requestJSON("/exercises/" + encodeURIComponent(exerciseId) + "/solution", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({style, source, profile: currentProfile()})
    });
    if (!state.active || state.active.id !== exerciseId ||
        state.profileId !== profileId || element("code").value !== source ||
        element("style").value !== style) return;
    state.lastAnswer = answer;
    renderAnswer(answer);
    element("solution-answer").scrollIntoView({behavior: "smooth", block: "nearest"});
  } catch (error) {
    notice(localizedError(error), true);
  } finally {
    button.disabled = false;
    button.textContent = tr("showSolution");
  }
}

async function start() {
  state.locale = preferred("locale", "ro") === "en" ? "en" : "ro";
  state.persistDrafts = preferred("save-drafts", "no") === "yes";
  state.profileId = preferred("active-profile", "profile_a") === "profile_b"
    ? "profile_b" : "profile_a";
  state.profiles.profile_a = loadProfile("profile_a");
  state.profiles.profile_b = loadProfile("profile_b");
  translateStatic();
  element("language-toggle").addEventListener("click", switchLanguage);
  element("theme-toggle").addEventListener("click", switchTheme);
  element("profile-select").addEventListener("change", (event) => switchProfile(event.target.value));
  element("learn-style").addEventListener("click", learnStyle);
  element("reset-profile").addEventListener("click", resetProfile);
  element("favorite-exercise").addEventListener("click", toggleFavorite);
  element("save-attempt-history").addEventListener("change", toggleAttemptHistory);
  element("clear-progress").addEventListener("click", clearLearningProgress);
  element("save-drafts").addEventListener("change", toggleDraftPersistence);
  element("reset-draft").addEventListener("click", resetDraft);
  element("run").addEventListener("click", runCode);
  element("show-solution").addEventListener("click", showSolution);
  element("next-hint").addEventListener("click", showNextHint);
  element("start-exam").addEventListener("click", startExam);
  element("finish-exam").addEventListener("click", () => finishExam(false));
  element("next-exam-task").addEventListener("click", nextExamTask);
  element("exercise-select").addEventListener("change", (event) => selectExercise(event.target.value));
  element("code").addEventListener("input", () => {
    if (state.active) {
      const key = draftKey();
      state.edited.add(key);
      storeDraft(key, element("code").value);
    }
    clearFeedback();
    setStatus("draftChanged");
    setProfileMessage("");
  });
  element("style").addEventListener("change", () => {
    rememberPreference("style", element("style").value);
    state.lastAnswer = null;
    element("solution-answer").hidden = true;
  });
  element("copy-solution").addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(state.answer); notice(tr("copied")); }
    catch (_) { notice(tr("copyUnavailable"), true); }
  });
  const savedStyle = preferred("style", "personalized_c");
  element("style").value = ["personalized_c", "pclp1_classic", "classic_c", "commented_c"].includes(savedStyle)
    ? savedStyle : "personalized_c";

  try {
    const loaded = await Promise.all([requestJSON("/exercises"), requestJSON("/exam")]);
    state.exercises = loaded[0];
    state.exam.definition = loaded[1];
    loadLearningProgress("profile_a");
    loadLearningProgress("profile_b");
    const list = element("exercise-select");
    list.replaceChildren();
    for (const exercise of state.exercises) {
      const option = document.createElement("option");
      option.value = exercise.id;
      option.textContent = localizedExerciseTitle(exercise);
      list.append(option);
    }
    refreshExerciseOptions();
    if (!state.persistDrafts) clearAllPersistedDrafts();
    restoreExamSession();
    restoreExamDrafts();
    const currentExamTask = examTasks()[state.exam.currentIndex];
    const initialExercise = (state.exam.active || state.exam.finished) && currentExamTask
      ? currentExamTask.exercise_id
      : state.exercises.some((exercise) => exercise.id === "vector_menu")
        ? "vector_menu" : state.exercises[0].id;
    selectExercise(initialExercise);
    if (state.exam.active) startExamClock();
    renderExam();
    if (state.exam.expired) notice(tr("examExpired"));
    if (legacyProfileReset) setProfileMessage("profileSchemaReset");
    else if (previousProfileMigrated) setProfileMessage("profileSchemaMigrated");
  } catch (error) {
    notice(tr("loadFailed") + ": " + localizedError(error), true);
  }
}

start();

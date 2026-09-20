# Changelog

## Unreleased

## 0.10.0

- Completed focused Windows manual acceptance for the second file-processing
  family: Romanian/English contracts, public and hidden result rendering, the
  verified solution, first-on-tie diagnosis and hints, and source-free progress all
  behaved as intended.
- Added the independent `file_longest_word` exercise with two public and three
  hidden `words.txt`/`longest.txt` contracts, including first-on-tie and maximum
  100-character boundary cases.
- Added Romanian/English problem text, all four tested solution styles, Files and
  Strings progress coverage, and an existing-category diagnostic for replacing the
  first longest word when lengths are equal.
- Kept both file exercises outside frozen generator 0.3.0. The second family makes
  a file-specific benchmark review possible, but does not itself justify a new label
  or a revised metric claim.

## 0.9.0

- Completed focused Windows visual acceptance for the editor and workspace refresh
  in Romanian and English, light and dark themes, and a half-width desktop window.
- Replaced the plain learner textarea with a locally bundled CodeMirror 6 editor
  for C17 syntax highlighting, line numbers, active-line and bracket feedback,
  automatic closing, profile-aware two/four-space indentation, and `Ctrl+F`
  search. The original textarea remains as a no-enhancement fallback.
- Routed editor reads and writes through a small adapter so exercise, profile,
  locale, draft, exam, test, and complete-solution state keep their existing
  behavior.
- Kept the strict content-security policy: CodeMirror's generated styles receive
  a per-page nonce, and no remote script/style source or `unsafe-inline` exception
  was introduced.
- Reorganized the browser interface into Exercises, Practice exam, and Progress
  modes. The problem now sits beside the editor on desktop, while style settings
  and the complete solution use progressive disclosure instead of occupying the
  primary workspace permanently.
- Kept the exam workbench available below its timer and score, added compact
  navigation badges for an active exam and solved count, and collapsed the layout
  cleanly on narrower screens.

## 0.8.0

- Completed the focused Windows manual acceptance of the fixed file workflow:
  public contracts, failed and successful per-file results, Romanian/English
  continuity, profile-specific drafts and progress, and the Files concept all
  behaved as intended without adding an upload surface.
- Added the original `file_number_summary` exercise with two public and three
  hidden authored `numbers.txt`/`summary.txt` contracts, existing-category
  diagnosis, and tested classic, commented, PCLP1, and personalized solutions.
- Render public fixture and expected-file contents explicitly in Romanian and
  English, show nested per-file result statuses, and keep hidden file names and
  contents redacted in both locales.
- Added Files to the derived progress concepts and kept generator 0.3.0 frozen at
  14 exercises and 1,136 programs until an independent second file family can
  support honest held-out evaluation.
- Added strict project-authored `fixtures` and `expected_files` entries to the
  exercise test schema: portable flat filenames, at most eight total entries,
  32,000 bytes per text file, and 64,000 bytes across one test contract.
- Run every test in a fresh disposable working directory, populate only its
  declared fixtures, and remove that directory before the next test.
- Added bounded structured file-result checks for missing, wrong, oversized,
  unreadable, invalid-UTF-8, and non-regular outputs; symbolic links are not
  accepted as output files and hidden file names/contents are redacted with the
  rest of a hidden test.
- Extended dataset test-suite fingerprints to cover file contracts and added
  cross-platform regressions for schema validation, workspace isolation, output
  limits, and file-result serialization.
- Kept the fixed file exercise within the trusted-local boundary. No arbitrary
  browser upload or public-sandbox claim is included.

## 0.7.0

- Documented successful manual acceptance of strict JSON transfer, including the
  source-free envelope, confirmation flow, profile isolation, cleanup, and bilingual
  interface states; the planned v0.7.0 local-progress sprint is complete.
- Added active-profile JSON export/import for favorites, the history setting, and
  bounded numeric attempts. Import requires confirmation and rejects unknown
  fields, unknown exercises, duplicate favorites, invalid results, oversized
  histories, and disabled-history files that still contain attempts.
- Documented successful bilingual manual acceptance of the compact concept/exercise
  view, including profile isolation and the empty-history state.
- Added a collapsible profile-specific progress view that derives solved/attempted
  concept coverage from exercise tags and lists only favorited or attempted
  exercises with their best numeric result; it adds no new stored learner data.
- Documented successful manual acceptance of the first v0.7.0 local-progress
  slice, including profile isolation, refresh persistence, last/best behavior,
  and immediate profile-scoped deletion.
- Added profile-specific favorite exercises and a compact local progress summary.
- Added opt-in, device-local attempt history with bounded last/best numeric results;
  stored attempts contain only a timestamp, compilation status, and passed/total
  test counts, never source, compiler output, diagnoses, hints, or profile traits.
- Added immediate deletion for the active profile: disabling history removes all
  saved attempts while retaining favorites, and the clear action removes both.
- Added schema sanitization and browser-state regressions for profile isolation,
  bounded retention, source-free storage, and deletion behavior.
- Report failed compilations explicitly in per-exercise progress instead of as
  `0/0`, and exclude attempts without test results from the best-result field.
- Kept the evaluated program's process cap while removing the user-wide
  `RLIMIT_NPROC` cap from GCC, allowing compiler helper processes to start on
  shared Linux and GitHub-hosted runners.
- Added POSIX resource-profile regressions and made the ML baseline fail if a
  controlled mutation does not compile.
- Split GitHub Actions into independently visible core and ML matrix jobs so a
  runner failure is reported before expensive model evaluation can obscure it.

## 0.6.3

- Completed the six-stage local Windows acceptance protocol, including same-tab
  finished-exam recovery and removal of temporary source after tab closure when
  permanent drafts are disabled.
- Snapshotted the remaining practice-exam time when the learner finishes, so the
  displayed timer remains frozen across refreshes instead of being recalculated
  from the original start time.
- Retained edited practice-exam code in tab-scoped session storage for refresh and
  post-exam review while keeping permanent draft saving opt-in and disabled by
  default.
- Restored the last practice-exam task after refresh for both active and finished
  sessions, rather than returning to the unrelated default exercise starter.
- Added browser regressions for frozen final time, source restoration, and the
  separation between temporary source and the persistent numeric exam record.
- Updated Romanian and English privacy text to explain the temporary exam behavior.

## 0.6.2

- Preserved the number of hints visibly revealed when switching between Romanian
  and English, including the full three-hint sequence after opening a solution.
- Preserved the exact edited source and run-status message during locale refreshes,
  so an unchanged submission is not presented as a newly modified draft.
- Expanded the dependency-free browser interaction test to cover the manual
  acceptance sequence: three hints, complete solution, language switch, and return.

## 0.6.1

- Fixed local GCC execution on Windows when the parent process does not provide a
  writable compiler temp directory. `TMP`, `TEMP`, and `TMPDIR` now point to the
  evaluator's private `aptutor-*` directory instead of allowing MinGW to fall back
  to a protected location such as `C:\\WINDOWS`.
- Preserved only the Windows toolchain and system paths required for process
  creation; unrelated environment values are not forwarded to learner programs.
- Resolved the compiler executable before launching it, used a native `.exe` output
  name on Windows, and kept source/output paths relative to the isolated workdir.
- Added cross-platform environment regression tests after the manual Windows
  acceptance test exposed the issue.

## 0.6.0

- Expanded the catalog from 10 to 14 original C17 exercises, adding closed-interval
  parity, odd-digit counting, a sentinel-controlled average, and perfect squares.
- Added `sentinel_handling` as the thirteenth semantic label and expanded the
  reproducible dataset from 880 to 1,136 controlled single-bug programs.
- Added an original 60-minute, four-task practice exam with a 10-point rubric,
  browser-only timer and progress, best-attempt partial-credit estimate, and an
  explicit notice that the estimate is not an official grade.
- Added an author-defined `PCLP1 classic · FIESC` portable-C preset. It reflects
  abstract course conventions without copying learner or course source.
- Added source-free warnings for `gets`, `fflush(stdin)`, selected non-portable
  console/case APIs, and `while (!feof(...))`; warnings never rewrite submitted code.
- Added a curriculum-alignment record and provenance boundary that exclude all raw
  course documents, extracted text, filenames, authorship, and metadata.
- Re-trained the grouped baseline and documented the weaker ML-only result alongside
  rule-only and hybrid results instead of presenting the hybrid as model accuracy.

## 0.5.2

- Added aggregate detection and deterministic application of `snake_case` and
  `camelCase` without retaining or copying learner identifiers.
- Added grouped-versus-separate declaration learning. The formatter may split a
  declaration or merge adjacent declarations with the same C type, but never moves
  declarations across executable statements.
- Migrated schema-0.2 profiles to schema 0.3 without losing v0.5.1 evidence; the new
  dimensions remain visibly unobserved until a submitted example supports them.
- Added explicit device-local draft saving, disabled by default and separated by
  profile and exercise. Empty drafts remain distinguishable from missing drafts.
- Added a restore-starter action and deletion of all persistent drafts when saving
  is disabled, together with clear Romanian and English privacy text.
- Added browser, migration, naming, declaration, C17 compilation, and behavioral
  regression coverage for the new workflow.

## 0.5.1

- Reproduced the abstract structure of the project owner's natural two-profile
  test and fixed the false `i++` claim when the submitted code actually used
  `i = i + 1`.
- Split brace learning into independent function and control-structure choices,
  allowing a profile to keep `main() {` while placing a `for` brace on the next line.
- Added prefix, postfix, compound, and explicit assignment update styles, plus
  `main` signature, loop-declaration, control-spacing, comment-placement, and
  aggregate identifier preferences.
- Added authored short and Romanian identifier aliases and inline explanation
  anchors; no learner identifier or comment text is retained or copied.
- Added a learned/mixed/default origin for every displayed preference. Unobserved
  choices remain safe defaults but are now labeled honestly in the UI.
- Replaced profile schema 0.1 with 0.2. Old test profiles reset once because their
  global brace counts cannot be reconstructed as function/control evidence.
- Added natural-style regression coverage across every exercise and retained C17
  compilation and behavioral checks for all generated references.
- Removed a pre-C23 pedantic array-qualifier warning from the matrix-menu reference
  while preserving its behavior.
- Removed the two dormant C++ answer files from the current classic-C release;
  earlier versions retain them for future separate C++ work.

## 0.5.0

- Narrowed the current learner workflow to classic C17/GCC for PCLP1 students
  in Computer Engineering; removed C++ compiler and answer options from the UI.
- Added two local test profiles with separate in-tab drafts, allowing one tester
  to simulate two learners without implementing authentication prematurely.
- Added explicit, consent-based style learning for brace placement, prefix versus
  postfix updates, two- versus four-space indentation, and comment density/syntax.
- Added deterministic personalized C references. Formatting is applied only to
  author-owned tested solutions; program logic and identifiers are not inferred
  from or copied out of a learner's code.
- Persisted only bounded aggregate counters and resolved preferences. Raw source
  is not stored in the profile and C++ examples are rejected by style learning.
- Added backend, browser-state, privacy, and compilation regression tests for two
  deliberately different profiles across all 10 exercises.

## 0.4.0

- Made Romanian the default for the local interface, exercises, hints, and
  authored reference explanations; added a reversible English switch in the
  header without losing the current draft or revealed hints.
- Added a light/dark switch beside the language switch. On first use the theme
  follows the system preference, then remembers the explicit choice locally.
- Replaced the former green interface with restrained navy and pale-blue colors
  inspired by USV/FIESC public-facing materials, without presenting them as
  official brand specifications or shipping their logos.
- Kept program-required output literals, original C/C++ source code, and raw
  compiler diagnostics unchanged; language and theme are presentation settings.

## 0.3.1

- Simplified the local web interface: plain-language headings, restrained colors,
  flat panels, readable editor, and straightforward buttons instead of decorative
  icons, gradients, shadows, oversized slogans, and hover motion.
- Kept the exercise, hint, compiler, and full-solution behavior unchanged.

## 0.3.0

- Added an accessible local browser workflow for exercise selection, code editing,
  public/hidden test feedback, three progressively revealed hints, and an optional
  full, explained reference answer for each of the 10 exercises.
- Added curated classic and outline-commented C answer styles for all exercises;
  added tested C++-stream alternatives for `vector_average` and `vector_menu`.
- Separated course label PCLP1 from the selected compiler: `gcc -std=c17` or
  `g++ -std=c++17`, with a C++-syntax warning; C-trained diagnostic labels are
  not reported as validated on C++ submissions.
- Added a dependency-free, loopback-only web demo with explicit execution opt-in;
  kept the optional FastAPI integration behind a local-only execution guard.
- Kept previous classifier dataset and benchmark unchanged: no student-authored
  code or style-learning model was added in this release.

## 0.2.0

- Expanded the catalog from five to 10 C exercises.
- Added menu, function-contract, program-state, input-buffer, insertion, deletion,
  and rectangular-matrix coverage.
- Expanded the semantic taxonomy from eight to 12 labels.
- Increased the reproducible mutation dataset from 480 to 880 programs.
- Added public-safe evidence seeds and an explicit privacy/provenance boundary.
- Added ML-only, rule-only, and deployed-hybrid grouped evaluation tracks.
- Preserved the weaker ML-only result instead of presenting hybrid scores as model
  accuracy.

## 0.1.0

- Added the first five C exercises, GCC runner, eight-label diagnosis, progressive
  hints, synthetic data generator, grouped ML baseline, CLI, optional API, and tests.

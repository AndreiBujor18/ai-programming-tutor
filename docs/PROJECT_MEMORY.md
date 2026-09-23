# Project memory — AI Programming Tutor v0.11.0 + natural-evaluation gate

This is the maintainer handoff and continuity record for the project. It contains
only public-safe decisions and implementation state. Private tutoring exports,
course files, learner identities, raw learner code, filenames, and source metadata
must never be copied into this document or the repository.

## Current checkpoint — 2026-09-23

- `v0.11.0` is the latest tagged release at commit `9376c31`. It closes the
  16-exercise controlled benchmark with 1,312 programs and 72/72 release tests.
- The public `main` used as this slice's base is one public-safe commit ahead at
  `348b304`, **Add private natural-code evaluation harness**. The package and
  release tag deliberately remain at `0.11.0`; no follow-up tag has been created
  yet.
- The post-release harness adds `aptutor evaluate-natural`, an exact private JSONL
  schema, consent/de-identification/two-labeler gates, frozen exercise and test
  fingerprints, aggregate rule/ML/hybrid reporting, and suppression below five
  samples per reported class. Imported natural source is never executed by this
  command.
- The natural-evaluation harness checkpoint passed 76/76 automated tests. The
  editor bundle, installable wheel, and public GitHub Actions matrix were also
  verified at that checkpoint.
- This is infrastructure, not a human-code result. No natural submission, private
  dataset, participant record, per-sample prediction, or human-code metric is
  committed or claimed.
- The first worker slice was built from public commit `348b304`. It adds a strict
  source-bound job/result protocol, the `aptutor run-isolated`
  host command, and a no-network/no-volume non-root reference container. It remains
  unreleased and does not turn the localhost runner into a public service.
- The unreleased worker worktree passes 85/85 automated tests. Its installable wheel
  contains both worker modules and exposes `run-isolated`; CI also has a real
  hardened-container smoke job. Focused Windows/Docker Desktop integration is
  accepted for a 5/5 reference, a bounded 0/5 starter receipt, automatic container
  removal, and an ignored-output-clean Git tree. Dedicated-host and adversarial
  acceptance remain deliberately open.
- The worker reference must be accepted on a dedicated secret-free host and reviewed
  adversarially before a small informed-consent pilot: manually de-identified
  submissions, independently labeled by two reviewers or adjudicated, frozen before
  tutor predictions are inspected, and kept outside Git.

## Product direction

- The product is a web tutor for first-year PCLP1 students learning classic C.
- It supports two legitimate study paths: progressive Socratic hints and an
  explicitly requested complete, explained solution.
- Complete solutions start from authored, tested references. Personalization changes
  bounded style traits; it does not imitate arbitrary program logic.
- Romanian is the default interface language. English is available from the
  top-right control, beside light/dark mode.
- The visual direction is restrained and human-made, with a comfortable palette
  inspired by public USV/FIESC colors but no official logo or brand-code claim.
- Current scope is Computer Engineering-style classic C17/GCC. Mixed introductory
  C/C++ material and IETTI-specific shortcuts are excluded from the current mode.
- Python, C++, accounts, server-side history, plagiarism detection, and arbitrary
  user-authored problems are future work, not current claims. The accepted local
  progress feature stores only the deliberately bounded device-local state below.

## User and privacy decisions

- The first controlled personalization study is performed by one tester acting as
  two deliberately different learners through Profile A and Profile B.
- A learner must explicitly choose **Learn from current code** before a style profile
  changes.
- Profiles retain bounded aggregate preferences and evidence origins, never raw
  source, identifiers, or comment text.
- Permanent draft persistence is separate, device-local,
  profile/exercise-specific, optional, and off by default. Disabling it deletes
  persistent drafts.
- The persistent practice-exam record contains only its identifier, timer/final-time
  state, active task, and numeric best-attempt results. Edited exam source is kept
  separately in tab-scoped session storage for refresh and review, then disappears
  when the tab is closed unless permanent drafts were explicitly enabled.
- Local learning progress is isolated by profile. Favorites require an explicit
  click. Attempt history is optional and off by default; it retains at most 20
  timestamped numeric results per exercise and never source, compiler output,
  diagnoses, hints, or style evidence. Disabling history deletes its attempts, and
  clearing progress also deletes favorites for the active profile.
- JSON transfer operates on only the active profile's favorites, history setting,
  and bounded numeric attempts. Imports replace that profile only after confirmation
  and reject unknown fields or exercises rather than silently retaining them.
- Private tutoring and course materials may inform abstract topic coverage and bug
  hypotheses only. Originals, extracted text, screenshots, filenames, authorship,
  metadata, and copied code are excluded from the repository, dataset, model, and
  release archive.
- Real learner submissions require informed consent, de-identification, restricted
  storage, retention/deletion rules, and a separate frozen evaluation set.

## Release history

| Version | Outcome |
| --- | --- |
| 0.1.0 | Five C exercises, eight labels, GCC runner, progressive hints, 480 synthetic programs, first grouped ML baseline |
| 0.2.0 | Ten exercises, twelve labels, menus/program state/mixed input, 880 programs, separate ML/rule/hybrid reporting |
| 0.3.0–0.3.1 | Local browser workflow, explicit full solutions, then a flatter and less synthetic-looking visual design |
| 0.4.0 | Romanian-first UI, English switch, light/dark themes, FIESC/USV-inspired color direction |
| 0.5.0 | Classic-C-only learner mode, two isolated local profiles, deterministic style personalization |
| 0.5.1 | Independent function/control braces, four update styles, comment placement, Romanian aliases, explicit learned/mixed/default origins |
| 0.5.2 | `snake_case`/`camelCase`, grouped/separate declarations, optional device-local drafts, profile migration |
| 0.6.0 | Four new curriculum-aligned exercises, thirteenth label, practice exam, PCLP1 preset, legacy warnings, 1,136-program benchmark |
| 0.6.1 | Windows runner fix: private writable compiler temp variables, required toolchain/system paths only, native executable name |
| 0.6.2 | Locale-switch fix: visible hint depth, edited source, feedback, and run status remain synchronized |
| 0.6.3 | Finished-exam timer snapshot and tab-scoped source recovery across refresh |
| 0.7.0 | Profile-specific favorites, opt-in bounded numeric attempt history, last/best summaries, a derived concept/exercise view, and strict JSON transfer |
| 0.8.0 | Strict project-authored file contracts, isolated per-test directories, the first original file exercise, bilingual file feedback, Files progress, and a frozen 14-exercise benchmark |
| 0.9.0 | Locally bundled CodeMirror 6 C editor, Exercises/Practice exam/Progress modes, side-by-side desktop workbench, progressive disclosure, and responsive manual acceptance |
| 0.10.0 | Second independent fixed-file family for bounded string processing, first-on-tie diagnosis and hints, bilingual manual acceptance, and the frozen benchmark boundary preserved |
| 0.11.0 | Generator 0.4.0 includes both file families through 11 reviewed mutation pairs, retains 13 labels after rejecting an overlapping file-cursor category, and adds a 1,312-program grouped evaluation |
| Unreleased | Private-input aggregate evaluator plus a strict one-job worker protocol and hardened reference container path; no human dataset, result, or production-sandbox claim yet |

## Current development capabilities

- 16 original C17 exercises; every exercise has two public and three hidden tests.
- 13 semantic diagnostic labels plus compiler errors and unknown fallbacks.
- Three progressive hint levels and a separate complete-solution action.
- Locally bundled CodeMirror 6 editor with C17 highlighting, line numbers, bracket
  feedback, search, light/dark themes, and profile-aware indentation. The original
  textarea remains the no-enhancement fallback.
- Three top-level browser modes for exercises, the practice exam, and progress. The
  normal desktop workbench places the requirement beside the editor; style settings
  and the complete solution remain collapsed until requested, and narrower windows
  stack the workspace into one column.
- Four complete-solution styles: active profile, PCLP1 classic, plain classic C,
  and C with explanatory comments.
- Style learning covers contextual braces, update form, indentation, comment density,
  comment syntax/placement, `main` signature, counter placement, control spacing,
  identifier length/language/convention, and declaration layout.
- Original four-task practice exam: 60 minutes, one base point, nine task points,
  transparent rubric, best-attempt estimate, and explicit non-official-grade notice.
- Source-free compatibility warnings for unbounded `gets`, undefined
  `fflush(stdin)`, selected console-only helpers, non-standard case conversion, and
  checking `feof` before a read. Warnings preserve source and compiler diagnostics.
- Dependency-free local HTTP server, optional FastAPI adapter, CLI, installable
  wheel, deterministic dataset generator, and optional scikit-learn baseline.
- Strict offline natural-code evaluator with exact private-input validation,
  frozen exercise/test fingerprints, no imported-source execution, and aggregate
  rule/ML/hybrid output that omits source and per-sample predictions.
- Strict worker job/result protocol plus a reference one-container-per-submission
  invocation with no network or volumes, a read-only root, non-root execution,
  bounded tmpfs/resources, immutable image references, and source-free receipts.
- Strict project-authored text fixtures and expected-file contracts with portable
  flat names, eight combined entries at most, per-entry and per-test byte limits,
  fresh per-test work directories, structured file statuses, and hidden-content
  redaction.
- Two fixed file exercises provide independent numeric and string families. One
  reads `numbers.txt` and writes `summary.txt`; the other reads bounded words from
  `words.txt` and writes the first longest word plus its length to `longest.txt`.
  The browser presents public contracts and nested file-result statuses in Romanian
  and English, and the derived progress view includes Files. This does not add
  arbitrary browser uploads or a public execution boundary.

## Current exercise catalog

1. delete all occurrences from a vector;
2. main-diagonal average;
3. frequency count;
4. closed-interval parity;
5. number followed by a full line;
6. matrix command menu;
7. vector minimum and maximum;
8. odd-digit count;
9. palindrome word;
10. positive perfect squares up to a limit;
11. sentinel-controlled average;
12. vector average;
13. vector insertion;
14. vector command menu;
15. summarize numbers from a file;
16. find the first longest word in a file.

The practice exam uses interval parity, odd-digit count, sentinel average, and
perfect squares. The file exercises are separate practice items and do not alter
the four-task exam.

## Data and evaluation state

- Dataset schema: 0.3; generator: 0.4.0.
- 82 reviewed exercise/mutation pairs × 16 identifier/layout variants = 1,312 rows.
- The benchmark covers all 16 exercises, including separate held-out folds for both
  file families. Five string-file and six numeric-file pairs reuse existing labels;
  `file_cursor_state` was not admitted because its candidate cases overlap
  `loop_boundary` and `wrong_identifier_or_argument`.
- Every row is a controlled single-bug mutation of a project-authored reference.
- Release audit: 1,312 unique IDs; every row compiles, fails at least one test, and
  surfaces its intended label in the rule layer's top three.
- Evaluation is leave-one-exercise-out; variants of the held-out exercise never
  appear in that fold's training data.

| Track | Accuracy | Macro-F1 | Top-3 recall |
| --- | ---: | ---: | ---: |
| ML only | 0.7675 | 0.6473 | 0.8704 |
| Rules only | 1.0000 | 1.0000 | 1.0000 |
| Hybrid | 0.9665 | 0.9524 | 1.0000 |

The honest model result is the ML-only 0.6473 macro-F1. The perfect rule result is
expected on mutations co-designed with those rules and is not real-student accuracy.
The `sentinel_handling` label still has 0.0 ML-only F1, making it a priority for future
natural-data evaluation. The browser currently uses rules without loading the model.

No natural-code dataset or human-code metric exists yet. The evaluator and protocol
are ready, but real collection remains gated on informed consent, a separate
withdrawal ledger, manual de-identification, a disposable execution worker, and two
independent labels or adjudication. See `docs/NATURAL_CODE_EVALUATION.md`.

## Validation and security state

- The v0.6.3 release passed 49/49 automated tests in both the working tree and an
  independently extracted release archive. The browser regression covers three
  revealed hints, an open complete solution, both locale transitions, exact
  edited-source retention, frozen finished time, and tab-scoped exam-source
  recovery. The Windows compiler-environment regressions remain covered.
- The v0.7.0 release tree passes 53/53 automated tests, including a package/project
  version-consistency check. The progress-state contract verifies schema sanitization,
  bounded retention,
  source-free storage, profile isolation, and deletion; the browser regression
  also verifies the complete favorite/history interaction, the derived bilingual
  concept/exercise view, and strict source-free JSON export/import.
- The v0.8.0 release tree passes 68/68 automated tests. Regressions cover exact
  schema parsing, filename and byte bounds, fresh per-test workspaces, structured
  file failures, POSIX symbolic-link rejection, hidden redaction, the fifteenth
  reference, all four solution styles, bilingual public file blocks, nested file
  statuses, and the Files progress concept.
- The v0.9.0 release tree passes 69/69 automated tests. The browser regression also
  covers the locally bundled editor adapter, three-mode navigation, profile changes
  from Progress, active-exam navigation and timer status, and locale changes without
  losing edited source or visible feedback. The committed editor bundle rebuilds
  byte-for-byte from its source configuration.
- The v0.10.0 release tree passes 71/71 automated tests. The sixteenth
  reference and every generated solution style pass all five string-file cases; the
  first-on-tie mutation is diagnosed through the existing relational-operator
  category, and the built wheel includes the complete second exercise family.
- The v0.11.0 release tree passes 72/72 automated tests. Generator 0.4.0
  independently audits 1,312/1,312 unique controlled programs: all compile, all fail
  at least one authored test, and all surface their intended label in the rule
  layer's top three. The two held-out file folds reach ML-only macro-F1 of 1.0000
  and 0.7667 respectively, while the hybrid reaches 1.0000 on both. See
  `docs/EXPERIMENT_004.md`.
- The natural-evaluation harness checkpoint passes 76/76 automated tests.
  Natural-evaluation regressions cover exact schema and privacy rejection, frozen
  revision and duplicate checks, source-free aggregate output, and optional
  ML/hybrid evaluation using the existing controlled-mutation model. Imported
  natural source is never executed by that command.
- The unreleased isolated-worker slice passes 85/85 automated tests. Its nine new
  regressions cover exact identity-free and source-bound envelopes, stale-content
  rejection, C++ rejection, immutable image references, hardened Docker arguments,
  strict source-free results, suppression of untrusted container stderr,
  compile-failure minimization, and forced cleanup after a host-side timeout. The
  wheel includes the new modules and CLI command.
- The focused Windows/Docker Desktop integration pass is accepted. The reference
  produced a source-free 5/5 receipt, the incomplete authored starter produced five
  bounded `wrong_answer` statuses, completed containers were removed, and both
  ignored receipts left Git clean. This is local integration evidence only; see
  `docs/ACCEPTANCE_WORKER_01_WINDOWS.md`.
- The first v0.7.0 feature slice also passed its complete manual Windows protocol.
  Profile-specific favorites, opt-in history, latest/best results, forced-refresh
  persistence, history disablement, full progress clearing, and cross-profile
  deletion isolation behaved as intended. See
  `docs/ACCEPTANCE_V070_LOCAL_PROGRESS.md`.
- The derived concept/exercise view passed its bilingual manual check as well. Its
  seven concept groups, tracked-exercise rows, empty-history state, and profile
  isolation remained correct across Romanian/English and A/B switches.
- Strict JSON transfer passed its manual check. Export produced the documented
  source-free envelope; confirmed import replaced only the active profile, Profile A
  remained unchanged, Profile B was restored to empty, and both locales rendered the
  transfer states correctly.
- All 16 reference solutions and every complete-solution style pass their exercise
  tests; generated variants compile without warnings in the tested matrix.
- The release wheel installs as version 0.11.0 and exposes all 16 exercises plus the
  four-task, 10-point practice exam.
- The v0.11.0 release privacy scan found no uploaded archive, private filename, Library ID,
  workspace path, PDF, image, office document, or raw tutoring export.
- The focused v0.8.0 Windows protocol passed the public file contracts, starter
  failure, verified 5/5 solution, Romanian/English continuity, generic hidden-file
  labels, Files progress, and Profile A/B draft and history isolation. See
  `docs/ACCEPTANCE_V080_FILES.md`.
- The focused v0.9.0 Windows protocol accepted the highlighted C editor, the three
  top-level modes, side-by-side and half-width layouts, both themes, and both locales
  without changing the accepted local-state or execution boundaries. See
  `docs/ACCEPTANCE_V090_INTERFACE.md`.
- The focused v0.10.0 Windows protocol accepted the second file family's Romanian
  and English contracts, public and hidden result rendering, verified solution,
  first-on-tie diagnosis and hints, and source-free Files/Strings progress. See
  `docs/ACCEPTANCE_V0100_SECOND_FILE.md`.
- The six-stage manual Windows acceptance protocol is complete. The final regression
  confirmed frozen finished time, same-tab source recovery, and removal of temporary
  exam source after tab closure with permanent drafts disabled. See
  `docs/ACCEPTANCE_V063.md`.
- The public GitHub Actions portability issue is resolved. Compiler helper processes
  no longer inherit the learner program's user-wide `RLIMIT_NPROC` cap, while
  evaluated programs retain it; the independently visible core and ML jobs complete
  on the supported Python matrix.
- The runner is for trusted localhost use only. Resource limits, loopback binding,
  Host/Origin checks, and explicit execution enablement are not a production sandbox.
- Public deployment requires disposable isolated workers with no network, no host
  secrets/mounts, strict resource/syscall controls, quotas, and cleanup.

## Completed manual acceptance

All six manual acceptance stages now pass. Tests 1–5 cover the exercise catalog,
practice exam, Windows runner, diagnosis, progressive hints, locale transitions,
style personalization, best-attempt scoring, and source-free compatibility warnings.
Test 6 confirms the complete v0.6.3 lifecycle: finished time remains frozen, the
numeric result and edited source survive a same-tab refresh, and temporary exam
source disappears after the tab is closed when permanent drafts are disabled.

The focused v0.8.0 protocol confirms the complete fixed-file lifecycle: public
contracts render without empty console blocks, starter and reference results expose
only the intended per-file detail, both locales preserve active state, Files
progress is derived correctly, and Profile A/B drafts and history remain isolated.

The focused v0.9.0 protocol confirms the editor and information-architecture
refresh in Romanian and English, both themes, and full and half-width desktop
layouts. The coding, exam, and progress workflows remain intact.

The focused v0.10.0 protocol confirms the second fixed-file family's complete
learner workflow in both locales. Public fixtures remain visible, hidden fixtures
remain redacted, strict first-on-tie behavior receives an existing-category
diagnosis and three hints, and the final 5/5 result appears only as bounded numeric
progress.

The public-safe evidence records are in `docs/ACCEPTANCE_V063.md`,
`docs/ACCEPTANCE_V070_LOCAL_PROGRESS.md`, `docs/ACCEPTANCE_V080_FILES.md`, and
`docs/ACCEPTANCE_V090_INTERFACE.md`, and `docs/ACCEPTANCE_V0100_SECOND_FILE.md`.
The v0.8.0 schema and automated acceptance boundary are in
`docs/FILE_TEST_CONTRACT.md`.

## Recommended next step

The v0.9.0 interface sprint is implemented and manually accepted. Its locally
bundled C editor and three-mode workspace preserve drafts, profiles, locale changes,
tests, exam state, and the accepted local privacy schemas. No further interface
migration is required before returning to curriculum and evaluation work.

The v0.8.0 file-aware runner and first original browser exercise are implemented,
automatically verified, and manually accepted on Windows in both locales. Public
contracts, structured file statuses, hidden redaction, profile-specific drafts and
progress, and the Files concept behave as intended. Learner uploads remain out of
scope.

On the curriculum/evaluation track, generator 0.4.0 now includes both independent
file-processing families. The review found no distinct file-specific misconception
and retains the 13-label taxonomy. Reconsider that decision only if independently
labeled natural submissions reveal a recurring non-overlapping cause.
Accounts and a server database remain deliberately outside the current local scope.

The aggregate evaluator, frozen-set schema, and first disposable-worker reference
slice are implemented. Next accept that worker on a dedicated secret-free host:
build it, invoke it by immutable image ID/digest, verify its source-free receipt and
resource boundary, record the compiler/runtime identity privately, and perform an
adversarial review. Only then recruit and independently label a small consented,
de-identified pilot before inspecting predictions. Prioritize sentinel handling and
naturally structured file processing; do not tune on the frozen set or describe the
harness or worker itself as a human-code result.

The completed local sprint validates the future account/history/favorites experience
cheaply and privately.

## Restart commands

```bash
export PYTHONPATH=src
python -m ai_programming_tutor.webserver --enable-local-execution
python -m unittest discover -s tests -v
```

Open `http://127.0.0.1:8000/`. Never forward or publicly expose that port.

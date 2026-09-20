# Project memory — AI Programming Tutor v0.8.0 development

This is the maintainer handoff and continuity record for the project. It contains
only public-safe decisions and implementation state. Private tutoring exports,
course files, learner identities, raw learner code, filenames, and source metadata
must never be copied into this document or the repository.

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
| 0.8.0-dev0 | Strict project-authored file contracts, a fresh disposable directory per test, and bounded regular-file result checks |
| 0.8.0-dev1 | First original file exercise, bilingual file-contract/result rendering, Files progress concept, and an explicitly frozen 14-exercise benchmark |

## Current v0.8.0.dev1 capabilities

- 15 original C17 exercises; every exercise has two public and three hidden tests.
- 13 semantic diagnostic labels plus compiler errors and unknown fallbacks.
- Three progressive hint levels and a separate complete-solution action.
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
- Strict project-authored text fixtures and expected-file contracts with portable
  flat names, eight combined entries at most, per-entry and per-test byte limits,
  fresh per-test work directories, structured file statuses, and hidden-content
  redaction.
- One fixed file exercise reads `numbers.txt` and writes `summary.txt`; the browser
  presents public contracts and nested file-result statuses in Romanian and English,
  and the derived progress view includes Files. This does not add arbitrary browser
  uploads or a public execution boundary.

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
15. summarize numbers from a file.

The practice exam uses interval parity, odd-digit count, sentinel average, and
perfect squares. The file exercise is a separate practice item and does not alter
the four-task exam.

## Data and evaluation state

- Dataset schema: 0.3; generator: 0.3.0.
- 71 reviewed exercise/mutation pairs × 16 identifier/layout variants = 1,136 rows.
- The benchmark deliberately remains on the 14 pre-file exercises. The single file
  family is excluded until an independent second family makes held-out evaluation
  and any file-specific label scientifically meaningful.
- Every row is a controlled single-bug mutation of a project-authored reference.
- Release audit: 1,136 unique IDs; every row compiles, fails at least one test, and
  surfaces its intended label in the rule layer's top three.
- Evaluation is leave-one-exercise-out; variants of the held-out exercise never
  appear in that fold's training data.

| Track | Accuracy | Macro-F1 | Top-3 recall |
| --- | ---: | ---: | ---: |
| ML only | 0.7509 | 0.6375 | 0.8750 |
| Rules only | 1.0000 | 1.0000 | 1.0000 |
| Hybrid | 0.9718 | 0.9610 | 1.0000 |

The honest model result is the ML-only 0.6375 macro-F1. The perfect rule result is
expected on mutations co-designed with those rules and is not real-student accuracy.
The new `sentinel_handling` label has 0.0 ML-only F1, making it a priority for future
natural-data evaluation. The browser currently uses rules without loading the model.

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
- The first v0.8.0 development slice passes 65/65 automated tests. New regressions
  cover exact schema parsing, portable filename and byte bounds, a fresh workspace
  for every test, missing/wrong/oversized/invalid-UTF-8 output files, POSIX
  symbolic-link rejection, and hidden file-name/content redaction. Every existing
  reference and generated solution style continues to pass its original
  stdin/stdout tests.
- The second v0.8.0 development slice passes 68/68 automated tests and adds the
  fifteenth reference plus file-aware browser regressions. It verifies the authored
  public/hidden file contracts,
  existing-category diagnosis, all four generated solution styles, bilingual public
  file blocks, nested file-result statuses, hidden redaction, and the Files progress
  concept.
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
- All 15 reference solutions and every complete-solution style pass their exercise
  tests; generated variants compile without warnings in the tested matrix.
- The release wheel installs as version 0.7.0 and exposes all 14 exercises plus the
  four-task, 10-point practice exam.
- The v0.7.0 release privacy scan found no uploaded archive, private filename, Library ID,
  workspace path, PDF, image, office document, or raw tutoring export.
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

The public-safe evidence records are in `docs/ACCEPTANCE_V063.md` and
`docs/ACCEPTANCE_V070_LOCAL_PROGRESS.md`. The v0.8.0 development schema and
automated acceptance boundary are in `docs/FILE_TEST_CONTRACT.md`.

## Recommended next step

The complete v0.7.0 local-progress sprint is implemented and manually accepted:
profile-specific favorites, opt-in numeric attempt history, per-exercise last/best
summaries, refresh persistence, and immediate profile-scoped deletion. The compact
concept/exercise view and strict active-profile JSON transfer are also accepted.
Accounts and a server database remain deliberately outside this sprint.

The file-aware runner foundation and first original browser exercise are now
implemented. Next, run the focused manual Windows acceptance for public file
contracts, per-file statuses, both locales, draft/profile behavior, and the Files
progress concept. Keep learner uploads out of scope. A file-specific diagnostic
label must wait for a second independent exercise family and a new reviewed
benchmark version.

In parallel planning, prioritize consented natural-code evaluation before improving
the model or deploying public code execution.

The completed local sprint validates the future account/history/favorites experience
cheaply and privately.

## Restart commands

```bash
export PYTHONPATH=src
python -m ai_programming_tutor.webserver --enable-local-execution
python -m unittest discover -s tests -v
```

Open `http://127.0.0.1:8000/`. Never forward or publicly expose that port.

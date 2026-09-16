# Project memory — AI Programming Tutor v0.6.3

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
- Python, C++, accounts, server-side history, favorites, plagiarism detection, and
  arbitrary user-authored problems are future work, not current claims.

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
- Private tutoring and course materials may inform abstract topic coverage and bug
  hypotheses only. Originals, extracted text, screenshots, filenames, authorship,
  metadata, and copied code are excluded from the repository, dataset, model, and
  release archive.
- Real learner submissions require informed consent, de-identification, restricted
  storage, retention/deletion rules, and a separate frozen evaluation set.

## Release history

| Version | Stable outcome |
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

## Current v0.6.3 capabilities

- 14 original C17 exercises; every exercise has two public and three hidden tests.
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
14. vector command menu.

The practice exam uses interval parity, odd-digit count, sentinel average, and
perfect squares. File-based exercises remain deferred until the runner can provide
isolated fixtures cleanly.

## Data and evaluation state

- Dataset schema: 0.3; generator: 0.3.0.
- 71 reviewed exercise/mutation pairs × 16 identifier/layout variants = 1,136 rows.
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
- All 14 reference solutions and every complete-solution style pass their exercise
  tests; generated variants compile without warnings in the tested matrix.
- The release wheel installs as version 0.6.3 and exposes all 14 exercises plus the
  four-task, 10-point practice exam.
- The v0.6.3 release privacy scan found no uploaded archive, private filename, Library ID,
  workspace path, PDF, image, office document, or raw tutoring export.
- The runner is for trusted localhost use only. Resource limits, loopback binding,
  Host/Origin checks, and explicit execution enablement are not a production sandbox.
- Public deployment requires disposable isolated workers with no network, no host
  secrets/mounts, strict resource/syscall controls, quotas, and cleanup.

## Recommended next step

Complete the final manual acceptance recheck on v0.6.3. Test 1 passed on Windows: the
14-exercise catalog, dark Romanian UI, exam start, task navigation, timer, and score
persisted correctly across refresh. Test 2 passed after the protected Windows temp
fallback was fixed in v0.6.1: correct and deliberately wrong submissions, diagnosis,
three hints, personalized complete solution, and best-attempt scoring all behaved as
intended. Test 3 confirmed translated code feedback and preserved exam state, then
exposed the hint-depth and false-dirty locale regressions fixed in v0.6.2. Test 4
confirmed distinct Profile A/Profile B/PCLP1 formatting on vector-average and
palindrome solutions, all passing 5/5 tests. Test 5 confirmed that `fflush(stdin)`
produces a compatibility warning without rewriting the learner's source and while
the valid solution still passes 5/5 tests. Test 6 exposed a moving finished timer
and lost exam source after refresh; v0.6.3 snapshots the final time and retains exam
source temporarily in the current tab.

Remaining acceptance checks:

1. finish a fresh practice exam on v0.6.3;
2. refresh in the same tab and confirm that the timer is frozen, the score remains,
   the last exam task is selected, and its edited source is restored;
3. close the tab and confirm that temporary exam source is not treated as an
   opt-in permanent draft.

If that pass succeeds, the recommended v0.7.0 sprint is **local learning progress**:

- favorite exercises;
- opt-in local attempt history and last/best result;
- a small progress view by concept and exercise;
- one-click deletion plus JSON export/import;
- no accounts or server database yet.

This validates the future account/history/favorites experience cheaply and privately.
Afterwards, prioritize a file-aware isolated runner and consented natural-code
evaluation before improving the model or deploying public code execution.

## Restart commands

```bash
export PYTHONPATH=src
python -m ai_programming_tutor.webserver --enable-local-execution
python -m unittest discover -s tests -v
```

Open `http://127.0.0.1:8000/`. Never forward or publicly expose that port.

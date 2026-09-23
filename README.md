# AI Programming Tutor

A local prototype for PCLP1 students with different ways of learning. It can
compile a submission, run public and hidden tests, identify a possible C bug
category, and reveal progressive hints. If the learner asks, it also presents a
complete, explained, tested reference solution as a separate action.

The repository name is intentionally neutral. Product branding can change later
without renaming the Python package or rewriting the architecture.

## Complete file-family benchmark in v0.11.0

The controlled diagnostic benchmark now covers all 16 exercises. Generator 0.4.0
adds five reviewed mutation pairs for longest-word selection and six for numeric
file summaries, bringing the reproducible dataset to 82 pairs and 1,312 programs.
Each file family has its own held-out fold in the grouped evaluation.

The review retains the existing 13-label taxonomy. Counted over-reading and
under-reading are loop-boundary mistakes, while reading through the wrong stream is
a wrong-identifier-or-argument mistake; a separate `file_cursor_state` label would
duplicate those causal explanations. Experiment 004 documents the complete audit,
metrics, limitations, and the need for a future natural-code evaluation.

## Second file-processing family in v0.10.0

The catalog now contains 16 exercises, including two independent fixed-file
families. The new string exercise reads bounded lowercase words from `words.txt`
and writes the first longest word plus its length to `longest.txt`. Its two public
and three hidden cases cover a single word, a last-word maximum, ties, and the
100-character boundary.

Focused Windows acceptance confirmed the complete workflow in Romanian and
English: public contracts, generic hidden-file labels, the verified 5/5 solution,
the existing relational-operator diagnosis for an incorrect tie update, all three
hints, and source-free Files/Strings progress. At the v0.10.0 release boundary, the
diagnostic benchmark remained frozen at the reviewed 14 pre-file exercises; the
later generator 0.4.0 review described below now includes both file families.

## Interface refresh in v0.9.0

The browser now uses a locally bundled CodeMirror 6 editor with C17 syntax
highlighting, line numbers, bracket matching, search, light/dark themes, and
profile-aware indentation. The committed browser asset runs without Node.js or a
remote CDN; Node is needed only when a maintainer rebuilds the editor bundle.

Exercises, the practice exam, and local progress now have separate top-level modes.
On wider screens, the active problem sits beside the editor. Style-profile details
and the complete solution stay collapsed until requested, the exam keeps its timer
and score above the same workbench, and narrower windows stack the workspace into a
single readable column. Existing drafts, profiles, exam state, progress, locale,
and theme behavior are preserved.

## File-aware execution in v0.8.0

The runner now understands bounded, project-authored text fixtures and expected
output files. Each test receives a fresh disposable working directory; output-file
checks reject missing, oversized, unreadable, and non-regular entries, including
symbolic links. Test-suite fingerprints include these file contracts, and hidden
file names and contents are redacted from learner-facing results.

The current catalog contains 16 exercises and two independent file-processing
families. `file_number_summary` reads `numbers.txt` and writes `summary.txt`;
`file_longest_word` reads bounded words from `words.txt` and writes the first
longest word plus its length to `longest.txt`. Each has two public plus three hidden
authored file cases. The Romanian/English browser shows public fixture and
expected-file contents, then reports each result-file status while redacting hidden
names and contents. The progress view includes a Files concept.

This remains a fixed, trusted-local exercise: there are no arbitrary file uploads,
and the local runner is still not a security sandbox. Generator 0.4.0 includes both
families through 11 reviewed mutation pairs and separate held-out folds. The review
did not add a file-specific label: counted over/under-reading overlaps
`loop_boundary`, while choosing the wrong stream overlaps
`wrong_identifier_or_argument`.

## What works in v0.11.0

- 16 fixed C exercises with public and hidden tests;
- an original four-task, 60-minute PCLP1 practice exam with a transparent
  10-point rubric and browser-only progress;
- a local browser interface: editor, test feedback, three hint levels, and an
  explicitly requested full reference solution;
- a locally bundled CodeMirror 6 C editor with syntax highlighting, line numbers,
  bracket matching, search, light/dark themes, and profile-aware indentation;
- a focused three-mode interface for exercises, the practice exam, and local
  progress, with the problem and editor side by side on wider screens;
- Romanian interface by default, English switch in the top-right corner, and
  a comfortable light/dark palette inspired by USV/FIESC public-facing blue
  colors (not official brand codes or logos);
- a deliberately narrow classic-C17/GCC workflow for PCLP1/Computer Engineering;
- two local test profiles with separate drafts and explicit, opt-in persistence on
  the current device;
- profile-specific favorites, opt-in bounded numeric attempt history, and a compact
  concept/exercise progress view that never stores submitted source;
- strict JSON export/import for only the active profile's sanitized progress, with
  confirmation before replacement and rejection of unknown fields or exercises;
- explicit style learning from code chosen by the learner: separate function and
  control braces; prefix, postfix, compound, or explicit updates; two/four-space
  indentation; comment syntax and placement; `main` signature; loop declarations;
  control spacing; declaration layout; and aggregate identifier
  style/language/`snake_case`/`camelCase`;
- personalized, PCLP1-classic, plain, and explained C references for all 16 exercises;
- source-free warnings for five legacy or non-portable C patterns without silently
  rewriting the learner's program;
- local GCC runner with time, memory, process, source-size, and output limits;
- deterministic diagnosis for 13 common beginner bug categories;
- three-level Socratic hints;
- synthetic mutation generator (1,312 labeled examples by default);
- TF-IDF + logistic-regression baseline with leave-one-exercise-out evaluation;
- separate ML-only, rule-only, and deployed-hybrid evaluation tracks;
- an aggregate-only evaluator for a future private, consented, independently
  labeled natural-code test set; no human submissions or natural-code metric are
  included yet;
- a strict one-job worker protocol, namespace-root controller separated from the
  non-root submission UID, bounded host transport, and a source-free adversarial
  command for the reference no-network container; profile 0.2 passed local
  Windows/Docker Desktop integration and all authored probes but still requires
  rootless/user-namespace dedicated-host acceptance before real collection;
- a read-only `aptutor inspect-host` preflight with 17 fail-closed infrastructure
  checks and permanently separate manual attestations; it emits no host identity and
  cannot authorize natural-code processing;
- privacy-safe provenance from tutoring observations without copied student code;
- dependency-free local web server and optional FastAPI endpoints;
- standard-library test suite.

Personalization is deterministic and deliberately bounded. It transforms an
author-owned, tested C solution from aggregate preferences and may select authored
short or Romanian identifier aliases before applying a learned naming convention.
It does **not** copy program logic, names, or comments from the learner, train a
style model, infer a degree program, or claim to reproduce every aspect of someone's
style. Every displayed trait is marked as learned, mixed, or an unobserved default.
The current browser and API reject C++ as a learner mode, keeping this experiment
aligned with the classic-C material.

Profile schema 0.3 migrates v0.5.1 schema-0.2 counters without deleting them; the
new naming and declaration dimensions begin as visibly unobserved defaults. Much
older v0.5.0 schema-0.1 profiles still reset because their global brace vote cannot
be reconstructed safely.

The `PCLP1 classic · FIESC` preset is author-defined rather than learned. It uses
portable C17, next-line braces, grouped declarations, predeclared loop counters,
postfix increments, short identifiers, and explanatory line comments. It captures
recurring course conventions without copying private examples.

## Current benchmark

On 1,312 controlled single-bug programs across all 16 exercises, the hybrid reaches
**0.9524 macro-F1** and **1.0000 top-3 recall** under leave-one-exercise-out
evaluation. The ML-only track reaches 0.6473 macro-F1 and 0.8704 top-3 recall. Its
held-out file folds reach 1.0000 macro-F1 for longest-word selection and 0.7667 for
numeric summary; the hybrid reaches 1.0000 on both. `sentinel_handling` still
receives 0.0 F1 from ML alone, so the model does not yet generalise reliably across
the full curriculum.

Generator 0.4.0 retains 13 labels. The proposed `file_cursor_state` category was
not admitted because its reviewed cases have existing causal explanations and hint
goals. This is a deliberate taxonomy decision, not evidence that naturally written
file-processing bugs are already covered.

Rule-only accuracy is 1.0 on the controlled mutations that those rules helped
define; that is an integration check, not evidence about real student code. The
browser currently uses the rule layer without loading the optional model. See
`docs/EXPERIMENT_004.md` for the full comparison and limitations;
`docs/EXPERIMENT_001.md`, `docs/EXPERIMENT_002.md`, and `docs/EXPERIMENT_003.md`
preserve earlier results.

## Natural-code evaluation gate

The next evaluation layer is implemented as a private-input, aggregate-output
workflow. `aptutor evaluate-natural` validates a frozen JSONL set, reuses only
precomputed source-free test signals, and emits rule/ML/hybrid summaries without
source, participant keys, sample IDs, or individual predictions. Imported programs
are deliberately not executed because the included local runner is not a sandbox
for untrusted participant code.

No natural-code dataset or result is committed. Real collection still requires
informed consent, separate withdrawal records, manual de-identification, an external
disposable execution worker on a dedicated reviewed host, and two independent labels
or adjudication before the split is frozen. The repository now includes the first
strict worker contract, hardened profile 0.2 container path, and authored adversarial
gate, but does not claim that these alone prove host isolation. See
`docs/ISOLATED_WORKER.md`, `docs/WORKER_ADVERSARIAL_REVIEW.md`,
`docs/ACCEPTANCE_WORKER_02_WINDOWS.md`, `docs/DEDICATED_WORKER_HOST.md`,
`docs/DEDICATED_HOST_OPERATIONS_TEMPLATE.md`, and
`docs/NATURAL_CODE_EVALUATION.md` for the exact boundaries and commands.

## Quick start

Requirements: Python 3.11+ and GCC. Start the local-only browser demo without
installing Python dependencies:

```bash
export PYTHONPATH=src
python -m ai_programming_tutor.webserver --enable-local-execution
```

On Windows PowerShell, run from the extracted project directory:

```powershell
$env:PYTHONPATH = "src"
python -m ai_programming_tutor.webserver --enable-local-execution
```

Open `http://127.0.0.1:8000/`. The service binds to loopback only and code
execution requires the explicit flag. Omitting it provides a read-only demo of
exercises and worked solutions. By default, student code is kept only in the current
browser tab. During a practice exam, edited task source is retained in tab-scoped
session storage so a refresh and post-exam review do not erase it; closing the tab
clears that temporary copy. The learner may explicitly enable local draft saving;
those raw drafts
then remain on that device, separated by profile and exercise, and can be deleted by
restoring the starter or disabling the option. Bounded style counters never contain
raw source, names, or comments. On first use, the theme follows the operating-system
setting. The persistent practice-exam record stores only timestamps, frozen remaining
time, task position, and test counts; raw source is not added to that record.
Program-required output tokens
(such as YES/NO/EMPTY), C syntax, and raw GCC diagnostics remain unchanged when the
display language changes.
Do not forward this port or use the local runner on a public website.

The prebuilt browser editor is included in the Python package, so Node.js is not
required to run the tutor. Maintainers who change `frontend/editor-entry.js` can
rebuild the committed asset with `npm install` followed by
`npm run build:editor`. The bundled third-party licenses are recorded in
`THIRD_PARTY_NOTICES.md`.

For the CLI and unit tests:

```bash
export PYTHONPATH=src
python -m ai_programming_tutor.cli list
python -m ai_programming_tutor.cli evaluate vector_average examples/buggy_average.c
python -m ai_programming_tutor.cli evaluate line_after_number examples/buggy_line_input.c
python -m unittest discover -s tests -v
```

To verify that the committed editor asset matches its source:

```bash
npm ci
npm run check:editor
```

Generate the initial dataset and train the baseline (scikit-learn and joblib are
required for the training command):

```bash
export PYTHONPATH=src
python -m ai_programming_tutor.cli generate-data \
  --output data/synthetic_bugs.jsonl --variants 16
python -m ai_programming_tutor.cli train \
  --dataset data/synthetic_bugs.jsonl \
  --model artifacts/baseline.joblib \
  --metrics artifacts/metrics.json \
  --confusion-matrix artifacts/confusion_matrix.csv

# Use the trained model together with the rule layer.
python -m ai_programming_tutor.cli evaluate vector_average \
  examples/buggy_average.c --model artifacts/baseline.joblib --hint-level 2
```

To use the optional FastAPI integration, install its dependencies separately and
launch on loopback only:

```bash
python -m pip install -e '.[api]'
APTUTOR_ENABLE_LOCAL_EXECUTION=1 uvicorn ai_programming_tutor.api:app --host 127.0.0.1
```

It serves the same page at `http://127.0.0.1:8000/` and the OpenAPI schema at
`/openapi.json`. This is **not** a production sandbox; the FastAPI submit endpoint denies
requests unless execution was explicitly enabled and the client is on loopback.

## Example CLI result

```text
Exercise: Vector average
Tests: 2/5 passed
Likely issue: integer_division
Hint 1: Check the types involved when the sum is divided by the number of values.
```

## Architecture

The core is deliberately independent of the web framework:

1. `catalog.py` loads versioned exercises and tests.
2. `runner.py` compiles and evaluates C code locally, with a fresh work directory
   for every test and bounded project-authored file contracts where declared.
3. `diagnosis.py` ranks likely bug categories from code and test signals.
4. `hints.py` selects a progressive hint.
5. `dataset.py` creates labeled controlled mutations.
6. `baseline.py` trains and evaluates the first ML model.
7. `natural_evaluation.py` validates private frozen records and writes only
   aggregate rule/ML/hybrid metrics without executing imported source.
8. `worker_protocol.py`, `worker_audit.py`, and `host_preflight.py` provide the
   source-bound disposable worker transport, authored source-free adversarial gate,
   and non-identifying dedicated-host inspection.
9. `style_profile.py` extracts bounded style preferences, records their evidence
   origin, and applies safe transformations without retaining source.
10. `solutions.py` provides authored explanations and tested reference variants.
11. `exam.py` defines the original practice simulation and rubric;
   `compatibility.py` explains recognized legacy constructs.
12. `service.py` exposes the application interface; `webserver.py` and `api.py`
   deliver it to the local browser.

See `docs/PROJECT_BRIEF.md`, `docs/ACCEPTANCE_V063.md`,
`docs/ACCEPTANCE_V070_LOCAL_PROGRESS.md`, `docs/ACCEPTANCE_V080_FILES.md`,
`docs/ACCEPTANCE_V090_INTERFACE.md`, `docs/ACCEPTANCE_V0100_SECOND_FILE.md`,
`docs/ACCEPTANCE_WORKER_02_WINDOWS.md`, `docs/BUG_TAXONOMY.md`,
`docs/EXPERIMENT_004.md`,
`docs/DATA_PROVENANCE.md`, `docs/NATURAL_CODE_EVALUATION.md`,
`docs/ISOLATED_WORKER.md`, `docs/WORKER_ADVERSARIAL_REVIEW.md`,
`docs/DEDICATED_WORKER_HOST.md`, `docs/DEDICATED_HOST_OPERATIONS_TEMPLATE.md`,
`docs/CURRICULUM_ALIGNMENT.md`,
`docs/STYLE_PERSONALIZATION.md`, and
`docs/SECURITY.md` for the product scope, labels, privacy boundary, manual
two-profile experiment, and execution threat model.

`docs/PROJECT_MEMORY.md` is the concise maintainer handoff: settled decisions,
release history, current metrics, privacy rules, and the exact next sprint.
`docs/FILE_TEST_CONTRACT.md` defines the project-authored fixture schema,
per-test lifecycle, file-result statuses, and its trusted-local boundary.

## License

This project is available under the [MIT License](LICENSE).

## Important security note

The included runner is for trusted local development and automated tests. Resource
limits, localhost binding, and an opt-in flag reduce accidental exposure but are
not a complete security boundary. Do **not** expose it to arbitrary internet users.
A public deployment needs an isolated execution worker with no network, a read-only
base filesystem, strict syscall controls, quotas, and disposable storage.

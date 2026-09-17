# AI Programming Tutor

A local prototype for PCLP1 students with different ways of learning. It can
compile a submission, run public and hidden tests, identify a possible C bug
category, and reveal progressive hints. If the learner asks, it also presents a
complete, explained, tested reference solution as a separate action.

The repository name is intentionally neutral. Product branding can change later
without renaming the Python package or rewriting the architecture.

## Unreleased v0.8.0 development

The runner now understands bounded, project-authored text fixtures and expected
output files. Each test receives a fresh disposable working directory; output-file
checks reject missing, oversized, unreadable, and non-regular entries, including
symbolic links. Test-suite fingerprints include these file contracts, and hidden
file names and contents are redacted from learner-facing results.

This is infrastructure only. The 14-item browser catalog remains unchanged, it does
not accept arbitrary file uploads, and the local runner is still not a security
sandbox. The next slice can add the first original file-processing exercise and its
browser presentation on top of this reviewed contract.

## What works in stable v0.7.0

- 14 fixed C exercises with public and hidden tests;
- an original four-task, 60-minute PCLP1 practice exam with a transparent
  10-point rubric and browser-only progress;
- a local browser interface: editor, test feedback, three hint levels, and an
  explicitly requested full reference solution;
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
- personalized, PCLP1-classic, plain, and explained C references for all 14 exercises;
- source-free warnings for five legacy or non-portable C patterns without silently
  rewriting the learner's program;
- local GCC runner with time, memory, process, source-size, and output limits;
- deterministic diagnosis for 13 common beginner bug categories;
- three-level Socratic hints;
- synthetic mutation generator (1,136 labeled examples by default);
- TF-IDF + logistic-regression baseline with leave-one-exercise-out evaluation;
- separate ML-only, rule-only, and deployed-hybrid evaluation tracks;
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

On 1,136 controlled single-bug programs, the hybrid reaches **0.9610 macro-F1**
and **1.0000 top-3 recall** under leave-one-exercise-out evaluation. The ML-only
track reaches 0.6375 macro-F1 and 0.8750 top-3 recall. In particular, the new
`sentinel_handling` class receives 0.0 F1 from ML alone, while the explicit rule
recognises its authored mutations. This is useful evidence that the current model
does not yet generalise reliably to the expanded curriculum.

Rule-only accuracy is 1.0 on the controlled mutations that those rules helped
define; that is an integration check, not evidence about real student code. The
browser currently uses the rule layer without loading the optional model. See
`docs/EXPERIMENT_003.md` for the full comparison and limitations;
`docs/EXPERIMENT_001.md` and `docs/EXPERIMENT_002.md` preserve earlier results.

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

For the CLI and unit tests:

```bash
export PYTHONPATH=src
python -m ai_programming_tutor.cli list
python -m ai_programming_tutor.cli evaluate vector_average examples/buggy_average.c
python -m ai_programming_tutor.cli evaluate line_after_number examples/buggy_line_input.c
python -m unittest discover -s tests -v
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
7. `style_profile.py` extracts bounded style preferences, records their evidence
   origin, and applies safe transformations without retaining source.
8. `solutions.py` provides authored explanations and tested reference variants.
9. `exam.py` defines the original practice simulation and rubric;
   `compatibility.py` explains recognized legacy constructs.
10. `service.py` exposes the application interface; `webserver.py` and `api.py`
   deliver it to the local browser.

See `docs/PROJECT_BRIEF.md`, `docs/ACCEPTANCE_V063.md`, `docs/BUG_TAXONOMY.md`,
`docs/DATA_PROVENANCE.md`, `docs/CURRICULUM_ALIGNMENT.md`,
`docs/STYLE_PERSONALIZATION.md`, and
`docs/SECURITY.md` for the product scope, labels, privacy boundary, manual
two-profile experiment, and execution threat model.

`docs/PROJECT_MEMORY.md` is the concise maintainer handoff: settled decisions,
release history, current metrics, privacy rules, and the exact next sprint.
`docs/FILE_TEST_CONTRACT.md` defines the unreleased project-authored fixture schema,
per-test lifecycle, file-result statuses, and its trusted-local boundary.

## License

This project is available under the [MIT License](LICENSE).

## Important security note

The included runner is for trusted local development and automated tests. Resource
limits, localhost binding, and an opt-in flag reduce accidental exposure but are
not a complete security boundary. Do **not** expose it to arbitrary internet users.
A public deployment needs an isolated execution worker with no network, a read-only
base filesystem, strict syscall controls, quotas, and disposable storage.

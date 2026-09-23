# Frozen natural-code evaluation protocol

## Current status

The repository contains an aggregate-only evaluator and a strict private-input
schema. It does **not** contain a natural-code dataset and does not claim a human-code
accuracy result yet. Controlled mutations remain the only populated benchmark.

The next evidence step is to collect a small consented, de-identified set, label it
independently, freeze it before inspecting model results, and evaluate the existing
rules/model without fitting on those submissions.

## Scope

The first frozen set accepts only:

- classic C17 submissions for one of the 16 fixed exercises;
- programs that compiled but failed at least one authored test;
- one primary label from the existing 13-category semantic taxonomy;
- agreement by at least two independent labelers, or documented adjudication;
- execution signals produced before import by an isolated disposable worker;
- source that passed manual de-identification and the evaluator's conservative
  automated checks.

Compilation failures, fully correct solutions, C++, ambiguous multi-bug programs,
and submissions that cannot be safely de-identified stay outside this first metric.
Their exclusion must be counted separately in any study report so the result is not
presented as accuracy over every learner attempt.

## Security boundary

`aptutor evaluate-natural` does not compile or run imported source. It reconstructs
only the source-free test statuses needed by the rule and model layers. This is
intentional: the included localhost runner has resource limits but is not a sandbox
for untrusted participant code.

The required `isolated_disposable_worker` provenance is a protocol assertion, not a
fact proved by the repository's reference container. Before real collection, that
worker path must be accepted on a dedicated host with no network, a read-only base
filesystem, strict syscall/process/time/memory limits, and disposable
per-submission storage. The evaluator can validate the declared schema and
fingerprints; it cannot prove consent or isolation.

## Private record schema

The input is UTF-8 JSON Lines stored under the ignored `private_evaluation/`
directory. Every line has exactly these fields:

| Field | Required value |
| --- | --- |
| `schema_version` | `0.1` |
| `dataset_id` | One stable ID shared by the frozen set |
| `sample_id` | Non-identifying unique key |
| `participant_key` | Pseudonymous stable key; never emitted in the report |
| `exercise_id` | One current catalog exercise |
| `source` | De-identified C17 source, at most 50,000 UTF-8 bytes |
| `source_sha256` | SHA-256 of the exact source text |
| `label` | One existing semantic label |
| `origin` | `consented_natural_submission` |
| `consent_confirmed` | `true` |
| `deidentified` | `true` |
| `labeler_count` | Integer at least 2 |
| `label_status` | `agreed` or `adjudicated` |
| `split` | `frozen_test` |
| `exercise_fingerprint` | Current authored exercise fingerprint |
| `test_suite_fingerprint` | Current five-test fingerprint |
| `signal_provenance` | `isolated_disposable_worker` |
| `signals` | Exact object described below |

`signals` contains only `compiled`, `passed_count`, `total_count`, and
`test_statuses`. The evaluator requires `compiled=true`, five statuses matching the
current exercise, an internally consistent pass count, and at least one failed test.
It never accepts compiler excerpts, names, free-text notes, consent documents, or
additional metadata. Consequently, the model's compiler-text feature is empty on
this natural set; that conservative domain difference must remain in the reported
limitations rather than being filled with potentially identifying diagnostics.

The automatic privacy check rejects common email addresses, web addresses, local
user paths, identity-bearing comment headers, and source containing its sample or
participant key. This is a backstop, not a replacement for manual review.

Aggregate output requires at least 10 distinct source programs from at least five
participants. Per-class values and label-support counts are emitted only for cells
with support of five or more; smaller cells are counted as suppressed. These are
privacy floors, not evidence that the sample is statistically sufficient. They are
not differential privacy or a formal anonymization guarantee; keep the pilot report
under access control until it has passed a separate disclosure review.

## Collection and freeze procedure

1. Give each participant a plain-language consent notice covering purpose, storage,
   retention, withdrawal, and the fact that code will not be published.
2. Keep the consent/withdrawal ledger separately from source. Assign a random
   participant key with no embedded name, email, university ID, or group.
3. Remove identity-bearing comments, paths, URLs, filenames, and other metadata.
   Have a second reviewer verify de-identification.
4. Run the code only in the external disposable worker and capture the four bounded
   signal fields plus the current exercise/test fingerprints. The repository's
   schema-0.1 worker protocol and no-volume/no-network container invocation provide
   the first reference path; follow `docs/ISOLATED_WORKER.md`, use a dedicated
   secret-free host, pin the built image by digest, and record the private operations
   evidence before treating its provenance assertion as accepted.
5. Have two reviewers label independently using `docs/BUG_TAXONOMY.md`. Resolve
   disagreements without showing tutor predictions. Exclude unresolved or
   genuinely multi-bug cases from the single-label metric.
6. Finalize inclusion/exclusion counts, assign a dataset ID, compute source hashes,
   and set `split=frozen_test` before running either the rule or ML track.
7. Preserve the private frozen file under access control. Never add it, a model
   trained on it, per-sample predictions, or consent records to Git.
8. If a participant withdraws, delete their source and ledger entry, mint a new
   dataset ID, and rerun the aggregate report. Do not silently reuse the old result.

## Evaluation command

Generate the controlled-mutation model first if ML and hybrid tracks are required:

```bash
export PYTHONPATH=src
python -m ai_programming_tutor.cli generate-data \
  --output data/synthetic_bugs.jsonl --variants 16
python -m ai_programming_tutor.cli train \
  --dataset data/synthetic_bugs.jsonl \
  --model artifacts/baseline.joblib \
  --metrics artifacts/metrics.json \
  --confusion-matrix artifacts/confusion_matrix.csv
```

Then evaluate the already frozen private set:

```bash
python -m ai_programming_tutor.cli evaluate-natural \
  --dataset private_evaluation/natural_samples.jsonl \
  --output private_evaluation/aggregate_metrics.json \
  --model artifacts/baseline.joblib
```

Omit `--model` for a rule-only report. The JSON output contains dataset/model
fingerprints, aggregate sample/participant/exercise/label counts, accuracy,
macro-F1 over labels observed in that frozen set, top-three recall, rule coverage,
and sufficiently supported aggregate per-class values. Cells below five are
suppressed. The report contains no source, participant keys, sample IDs, compiler
text, or per-sample predictions. Because joblib model files are executable
serialized objects, load only the model generated locally by the command above;
never use an untrusted `.joblib` download.

## Interpretation gate

A label-incomplete pilot is useful for finding failures, but its macro-F1 is not
directly comparable with the 13-label controlled benchmark. Even a complete frozen
set measures diagnosis on the included compiling, single-primary-bug submissions;
it does not establish classroom learning impact, hint usefulness, or safe public
execution. Report the participant and selection counts, label coverage, agreement
procedure, exclusions, and confidence intervals alongside any eventual metric.

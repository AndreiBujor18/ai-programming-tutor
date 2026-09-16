# Experiment 002: evidence-informed taxonomy and hybrid diagnosis

## Question

What changes when the curated benchmark grows from basic loops and arrays to
functions, command menus, program-state preconditions, mixed input modes, insertion,
deletion, and matrices? Can the deployed hybrid retain useful top-k coverage when a
lightweight ML baseline encounters an entirely unseen exercise?

## Dataset

- 10 exercises, each with two public and three hidden tests;
- 12 semantic labels;
- 55 applicable exercise/label mutation pairs;
- 16 identifier and formatting variants per pair;
- 880 controlled single-bug programs;
- zero compilation failures and zero accidentally correct mutations;
- abstract `evidence_basis` metadata with all private source material excluded.

The five new exercises are `vector_insert`, `delete_occurrences`, `vector_menu`,
`matrix_menu`, and `line_after_number`. Four new classifier labels are
`menu_dispatch`, `input_buffer_misuse`, `invalid_program_state`, and
`wrong_identifier_or_argument`.

All variants of the held-out exercise stay together. The model therefore never
trains on another formatting variant of the exercise it is asked to classify.

## Compared tracks

1. **ML-only:** character 3–5-gram TF-IDF, structural reference diff, execution
   signals, and class-balanced logistic regression.
2. **Rule-only:** transparent exercise-aware patterns and test signals.
3. **Deployed hybrid:** the same ranked merge used by `TutorService`, combining the
   top three ML candidates with rule evidence.

## Results

| Track | Accuracy | Macro-F1 | Top-3 recall |
|---|---:|---:|---:|
| ML-only | 0.7705 | 0.7102 | 0.8795 |
| Rule-only | 1.0000 | 1.0000 | 1.0000 |
| Deployed hybrid | **0.9557** | **0.9514** | **1.0000** |

The original v0.1 ML-only benchmark reported 0.8396 accuracy, 0.8518 macro-F1,
and 0.9583 top-3 recall on five exercises and eight labels. That benchmark is
preserved in `EXPERIMENT_001.md`; it is not directly comparable because v0.2 adds
new tasks and harder labels rather than evaluating the same test distribution.

## What failed in ML-only

The weakest per-label F1 values are:

| Label | F1 |
|---|---:|
| `menu_dispatch` | 0.0000 |
| `input_buffer_misuse` | 0.4000 |
| `wrong_identifier_or_argument` | 0.4658 |
| `invalid_program_state` | 0.6667 |

The token-normalised diff intentionally abstracts identifiers and literals. That
helps basic operator and boundary transfer but hides precisely the semantic role
changes involved in a wrong argument or menu key. Raw character features do not
recover that relation reliably when the entire target exercise is absent.

The weakest folds are `line_after_number` and `vector_menu`. In contrast,
`vector_insert` reaches 0.9686 ML-only macro-F1 and the older `min_max` fold rises
from 0.2933 to 0.8255 after the training set gains more independent exercises.

## Interpretation without score inflation

Rule-only perfection is expected on this controlled set because both mutations and
detectors are authored within the same taxonomy. Leave-one-exercise-out splitting
prevents formatting leakage into the statistical model, but it does not turn the
rule score into independent human validation. The hybrid score demonstrates that
the application combines its two diagnostic layers correctly; it is not a
real-student accuracy claim.

The useful result is therefore twofold: the curated product path remains reliable,
while the honest ML track identifies exactly where more diverse code and a
role-aware representation are needed.

## Reproduction

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

## Next experiment

Freeze the current 10-exercise suite, then obtain a small consented and fully
de-identified set of naturally written attempts that was not used to create rules.
Compare the existing baseline with identifier-role features and an AST/code-encoder
representation. Calibrate the hybrid merge on validation data rather than tuning it
against this synthetic benchmark, and measure hint usefulness plus next-attempt
improvement in a blind review.

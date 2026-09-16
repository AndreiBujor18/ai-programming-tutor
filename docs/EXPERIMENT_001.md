# Experiment 001: transferable bug-category baseline

## Question

Can a lightweight model classify a controlled C bug when the entire target
exercise is absent from training, and does a reference-aware structural feature
improve transfer over raw source text and execution signals?

## Dataset

- 5 exercises;
- 8 semantic labels;
- 30 applicable exercise/label mutation pairs;
- 16 identifier and formatting variants per pair;
- 480 examples total;
- one controlled mutation per example;
- GCC compilation outcome and five test statuses stored per example.

All variants of an exercise remain in the same fold. This prevents near-duplicate
versions of one solution from appearing in both train and test.

## Models

Both runs use character 3–5-gram TF-IDF and class-balanced logistic regression.

1. **Raw baseline:** submission source plus compiler/test signals.
2. **Reference-aware baseline:** raw features plus a token-normalised structural
   diff between the submission and the known reference solution. Identifiers,
   comments, strings, and most numeric literals are abstracted before the diff.

The reference solution is available at inference for every curated exercise, so
the second feature is compatible with the intended product setting. It would not
transfer unchanged to arbitrary user-authored exercises.

## Results

| Feature set | Accuracy | Macro-F1 | Top-3 recall |
|---|---:|---:|---:|
| Raw source + execution signals | 0.4646 | 0.4592 | 0.6667 |
| + structural reference diff | **0.8396** | **0.8518** | **0.9583** |

The stronger run exceeds the Sprint-1 targets of 0.75 macro-F1 and 0.90 top-3
recall on this synthetic benchmark.

Per-label F1 for the stronger run:

| Label | F1 |
|---|---:|
| `accumulator_misuse` | 0.7071 |
| `integer_division` | 1.0000 |
| `invalid_index` | 0.6906 |
| `logical_condition` | 1.0000 |
| `loop_boundary` | 0.8333 |
| `missing_update` | 0.9524 |
| `relational_operator` | 0.8000 |
| `wrong_initialization` | 0.8312 |

## Interpretation

The ablation shows that the useful signal is not merely exercise vocabulary or
test-failure count. Abstracting the change against a known-good program makes
operator, boundary, update, and initialisation patterns transferable across several
exercises. The rule layer remains valuable because it provides human-readable
evidence and a safe fallback.

The main weakness is the `min_max` held-out fold: 0.40 accuracy and 0.2933 macro-F1
across its five present labels. The confusion matrix also shows that invalid-index
and accumulator mistakes remain the least cleanly separated categories.

## Limitations

- Every program is derived from one author-written solution; naming variants do
  not reproduce the structural diversity of student code.
- Mutations are single-label and intentionally clean, while real submissions often
  contain interacting mistakes.
- The reference diff can become noisy when a student uses a substantially different
  but correct algorithm.
- The sample count is too small for a defensible production claim or demographic
  fairness analysis.
- Probabilities have not been calibrated, and hint helpfulness requires human study.

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

Create at least three independently written correct solutions per exercise, add
multi-line and algorithmic rewrites, and collect a small consented, de-identified
human set for a frozen external test. Compare rules, raw TF-IDF, structural diff,
and a pretrained code encoder. Report calibration and top-k coverage in addition
to F1, then run a blind human review of hint correctness and solution leakage.

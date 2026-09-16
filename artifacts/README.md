# Model artifacts

The training command writes the serialized baseline, metrics, and confusion matrix
here. Binary model artifacts are reproducible and intentionally excluded from
version control.

The checked-in JSON and CSV summarize the latest grouped evaluation. Historical
results remain documented in the corresponding `docs/EXPERIMENT_*.md` report.
`confusion_matrix.csv` belongs to the ML-only track; rule and hybrid summaries are
stored explicitly inside `metrics.json`.

The current 14-exercise/13-label result is documented in
`docs/EXPERIMENT_003.md`. A perfect rule-only score on controlled mutations is not
a real-student accuracy claim.

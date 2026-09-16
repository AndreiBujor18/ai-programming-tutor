from __future__ import annotations

import csv
import difflib
import json
import re
from pathlib import Path
from typing import Any

from ai_programming_tutor.catalog import get_exercise
from ai_programming_tutor.diagnosis import diagnose
from ai_programming_tutor.models import (
    CompilationResult,
    DiagnosisCandidate,
    EvaluationResult,
    TestResult,
)


C_KEYWORDS = {
    "auto", "break", "case", "char", "const", "continue", "default", "do",
    "double", "else", "enum", "extern", "float", "for", "goto", "if", "inline",
    "int", "long", "register", "restrict", "return", "short", "signed", "sizeof",
    "static", "struct", "switch", "typedef", "union", "unsigned", "void", "volatile",
    "while", "main", "printf", "scanf", "strlen",
}
TOKEN_PATTERN = re.compile(
    r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
    r"|==|!=|<=|>=|\+\+|--|\+=|-=|\*=|/=|&&|\|\||<<|>>|->"
    r"|[A-Za-z_]\w*|(?:\d+\.\d*|\.\d+|\d+)|[^\s]",
    re.DOTALL,
)


def _imports():
    try:
        import joblib
        import numpy as np
        from sklearn.base import clone
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
        from sklearn.model_selection import LeaveOneGroupOut
        from sklearn.pipeline import Pipeline
    except ImportError as exc:
        raise RuntimeError("Install the ML dependencies with: python -m pip install -e '.[ml]'") from exc
    return {
        "joblib": joblib,
        "np": np,
        "clone": clone,
        "TfidfVectorizer": TfidfVectorizer,
        "LogisticRegression": LogisticRegression,
        "accuracy_score": accuracy_score,
        "classification_report": classification_report,
        "confusion_matrix": confusion_matrix,
        "f1_score": f1_score,
        "LeaveOneGroupOut": LeaveOneGroupOut,
        "Pipeline": Pipeline,
    }


def _normalised_tokens(source: str) -> list[str]:
    tokens: list[str] = []
    for token in TOKEN_PATTERN.findall(source):
        if token.startswith("//") or token.startswith("/*"):
            continue
        if token.startswith(('"', "'")):
            tokens.append("STRING")
        elif re.fullmatch(r"[A-Za-z_]\w*", token):
            tokens.append(token if token in C_KEYWORDS else "IDENTIFIER")
        elif re.fullmatch(r"(?:\d+\.\d*|\.\d+|\d+)", token):
            tokens.append(token if token in {"0", "1"} else "NUMBER")
        else:
            tokens.append(token)
    return tokens


def structural_diff(reference_source: str, source: str) -> str:
    reference = _normalised_tokens(reference_source)
    submission = _normalised_tokens(source)
    matcher = difflib.SequenceMatcher(a=reference, b=submission, autojunk=False)
    changes: list[str] = []
    for operation, old_start, old_end, new_start, new_end in matcher.get_opcodes():
        if operation == "equal":
            continue
        removed = " ".join(reference[old_start:old_end]) or "EMPTY"
        added = " ".join(submission[new_start:new_end]) or "EMPTY"
        before = reference[old_start - 1] if old_start else "START"
        after = reference[old_end] if old_end < len(reference) else "END"
        changes.append(
            f"OP={operation} BEFORE={before} REMOVE=[{removed}] ADD=[{added}] AFTER={after}"
        )
    return " ; ".join(changes) if changes else "NO_STRUCTURAL_CHANGE"


def feature_text(
    source: str,
    signals: dict[str, Any] | None,
    reference_source: str | None = None,
) -> str:
    sections = [source]
    if reference_source is not None:
        sections.append(f"<STRUCTURAL_DIFF> {structural_diff(reference_source, source)}")
    if signals:
        statuses = ",".join(signals.get("test_statuses", []))
        compiler = str(signals.get("compiler_excerpt", ""))[:1000]
        signal_line = (
            f"compiled={int(bool(signals.get('compiled')))} "
            f"passed={signals.get('passed_count', 0)}/{signals.get('total_count', 0)} "
            f"statuses={statuses} compiler={compiler}"
        )
        sections.append(f"<EXECUTION_SIGNALS> {signal_line}")
    return "\n".join(sections)


def _pipeline(modules: dict[str, Any]):
    return modules["Pipeline"](
        [
            (
                "features",
                modules["TfidfVectorizer"](
                    analyzer="char_wb",
                    ngram_range=(3, 5),
                    min_df=2,
                    sublinear_tf=True,
                    max_features=40_000,
                ),
            ),
            (
                "classifier",
                modules["LogisticRegression"](
                    max_iter=2_000,
                    class_weight="balanced",
                    C=4.0,
                    random_state=42,
                ),
            ),
        ]
    )


def _read_dataset(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON on line {line_number} of {path}") from exc
    if not records:
        raise ValueError(f"Dataset is empty: {path}")
    return records


def _evaluation_from_record(record: dict[str, Any]) -> EvaluationResult:
    signals = record.get("signals", {})
    compiled = bool(signals.get("compiled"))
    compilation = CompilationResult(
        compiled,
        0 if compiled else 1,
        stderr=str(signals.get("compiler_excerpt", "")),
    )
    tests = tuple(
        TestResult(str(index), False, status, "", "", "", 0, 0.0)
        for index, status in enumerate(signals.get("test_statuses", []))
    )
    return EvaluationResult(record["exercise_id"], compilation, tests)


def train_baseline(
    dataset_path: Path,
    model_path: Path,
    metrics_path: Path,
    confusion_matrix_path: Path,
) -> dict[str, Any]:
    modules = _imports()
    np = modules["np"]
    records = _read_dataset(dataset_path)
    texts = np.array(
        [
            feature_text(
                record["source"],
                record.get("signals"),
                get_exercise(record["exercise_id"]).reference_solution,
            )
            for record in records
        ]
    )
    labels = np.array([record["label"] for record in records])
    groups = np.array([record["exercise_id"] for record in records])
    label_names = sorted(set(labels.tolist()))

    predicted = np.empty(labels.shape, dtype=object)
    top_three_hits = np.zeros(labels.shape, dtype=bool)
    rule_predicted = np.empty(labels.shape, dtype=object)
    rule_top_three_hits = np.zeros(labels.shape, dtype=bool)
    hybrid_predicted = np.empty(labels.shape, dtype=object)
    hybrid_top_three_hits = np.zeros(labels.shape, dtype=bool)
    splitter = modules["LeaveOneGroupOut"]()
    fold_metrics: list[dict[str, Any]] = []

    def score_track(
        expected: Any,
        track_predictions: Any,
        track_top_three: Any,
        present_labels: list[str],
    ) -> dict[str, float]:
        return {
            "accuracy": round(
                float(modules["accuracy_score"](expected, track_predictions)), 4
            ),
            "macro_f1": round(
                float(
                    modules["f1_score"](
                        expected,
                        track_predictions,
                        labels=present_labels,
                        average="macro",
                        zero_division=0,
                    )
                ),
                4,
            ),
            "top_3_recall": round(float(track_top_three.mean()), 4),
        }

    for train_indices, test_indices in splitter.split(texts, labels, groups):
        model = _pipeline(modules)
        model.fit(texts[train_indices].tolist(), labels[train_indices].tolist())
        fold_predictions = model.predict(texts[test_indices].tolist())
        probabilities = model.predict_proba(texts[test_indices].tolist())
        classes = model.named_steps["classifier"].classes_
        top_indices = np.argsort(probabilities, axis=1)[:, -3:]
        predicted[test_indices] = fold_predictions
        top_three_hits[test_indices] = [
            labels[index] in classes[row_top]
            for index, row_top in zip(test_indices, top_indices, strict=True)
        ]
        from ai_programming_tutor.service import _merge_candidates

        for row, index in enumerate(test_indices):
            evaluation = _evaluation_from_record(records[index])
            rule_candidates = diagnose(records[index]["source"], evaluation)
            semantic_rule_candidates = tuple(
                candidate for candidate in rule_candidates if candidate.category in label_names
            )
            rule_labels = [candidate.category for candidate in semantic_rule_candidates]
            rule_predicted[index] = rule_labels[0] if rule_labels else fold_predictions[row]
            rule_top_three_hits[index] = labels[index] in rule_labels[:3]

            ml_order = np.argsort(probabilities[row])[-3:][::-1]
            ml_candidates = tuple(
                DiagnosisCandidate(
                    str(classes[class_index]),
                    float(probabilities[row][class_index]),
                    "Out-of-fold ML prediction.",
                )
                for class_index in ml_order
            )
            hybrid_candidates = _merge_candidates(ml_candidates, semantic_rule_candidates)
            hybrid_labels = [candidate.category for candidate in hybrid_candidates]
            hybrid_predicted[index] = hybrid_labels[0]
            hybrid_top_three_hits[index] = labels[index] in hybrid_labels

        held_out = sorted(set(groups[test_indices].tolist()))
        held_out_labels = sorted(set(labels[test_indices].tolist()))
        ml_fold = score_track(
            labels[test_indices],
            fold_predictions,
            top_three_hits[test_indices],
            held_out_labels,
        )
        fold_metrics.append(
            {
                "held_out_exercise": held_out[0],
                "sample_count": int(len(test_indices)),
                "label_count": len(held_out_labels),
                **ml_fold,
                "rule_only": score_track(
                    labels[test_indices],
                    rule_predicted[test_indices],
                    rule_top_three_hits[test_indices],
                    held_out_labels,
                ),
                "hybrid": score_track(
                    labels[test_indices],
                    hybrid_predicted[test_indices],
                    hybrid_top_three_hits[test_indices],
                    held_out_labels,
                ),
            }
        )

    report = modules["classification_report"](
        labels,
        predicted,
        labels=label_names,
        output_dict=True,
        zero_division=0,
    )
    matrix = modules["confusion_matrix"](labels, predicted, labels=label_names)
    rule_summary = score_track(labels, rule_predicted, rule_top_three_hits, label_names)
    hybrid_summary = score_track(labels, hybrid_predicted, hybrid_top_three_hits, label_names)
    hybrid_report = modules["classification_report"](
        labels,
        hybrid_predicted,
        labels=label_names,
        output_dict=True,
        zero_division=0,
    )
    metrics: dict[str, Any] = {
        "sample_count": len(records),
        "exercise_count": len(set(groups.tolist())),
        "label_count": len(label_names),
        "labels": label_names,
        "evaluation": "leave-one-exercise-out",
        "feature_set": "source_char_ngrams+structural_reference_diff+execution_signals",
        "accuracy": round(float(modules["accuracy_score"](labels, predicted)), 4),
        "macro_f1": round(
            float(modules["f1_score"](labels, predicted, average="macro", zero_division=0)), 4
        ),
        "top_3_recall": round(float(top_three_hits.mean()), 4),
        "primary_track": "ml_only",
        "rule_only": rule_summary,
        "hybrid": hybrid_summary,
        "folds": fold_metrics,
        "per_class": {
            label: {
                metric: round(float(value), 4)
                for metric, value in report[label].items()
                if metric in {"precision", "recall", "f1-score", "support"}
            }
            for label in label_names
        },
        "hybrid_per_class": {
            label: {
                metric: round(float(value), 4)
                for metric, value in hybrid_report[label].items()
                if metric in {"precision", "recall", "f1-score", "support"}
            }
            for label in label_names
        },
    }

    final_model = _pipeline(modules)
    final_model.fit(texts.tolist(), labels.tolist())
    bundle = {
        "pipeline": final_model,
        "labels": label_names,
        "training_exercises": sorted(set(groups.tolist())),
        "dataset_size": len(records),
        "metrics": metrics,
    }

    model_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    confusion_matrix_path.parent.mkdir(parents=True, exist_ok=True)
    modules["joblib"].dump(bundle, model_path)
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    with confusion_matrix_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["actual\\predicted", *label_names])
        for label, row in zip(label_names, matrix.tolist(), strict=True):
            writer.writerow([label, *row])
    return metrics


def load_model(model_path: Path) -> dict[str, Any]:
    modules = _imports()
    return modules["joblib"].load(model_path)


def predict_candidates(
    bundle: dict[str, Any],
    source: str,
    evaluation: EvaluationResult,
    limit: int = 3,
) -> tuple[DiagnosisCandidate, ...]:
    signals = {
        "compiled": evaluation.compilation.succeeded,
        "compiler_excerpt": evaluation.compilation.stderr[:1000],
        "passed_count": evaluation.passed_count,
        "total_count": evaluation.total_count,
        "test_statuses": [test.status for test in evaluation.tests],
    }
    model = bundle["pipeline"]
    reference = get_exercise(evaluation.exercise_id).reference_solution
    probabilities = model.predict_proba([feature_text(source, signals, reference)])[0]
    classes = model.named_steps["classifier"].classes_
    ranked = sorted(zip(classes, probabilities, strict=True), key=lambda pair: pair[1], reverse=True)
    return tuple(
        DiagnosisCandidate(
            str(label),
            round(float(probability), 4),
            "ML baseline trained on controlled single-bug mutations.",
        )
        for label, probability in ranked[:limit]
    )

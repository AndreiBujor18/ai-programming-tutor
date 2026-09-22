"""Privacy-gated evaluation on a frozen, consented natural-code dataset."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai_programming_tutor.catalog import get_exercise, list_exercises
from ai_programming_tutor.dataset import exercise_fingerprint, test_suite_fingerprint
from ai_programming_tutor.diagnosis import diagnose
from ai_programming_tutor.hints import HINTS
from ai_programming_tutor.models import CompilationResult, EvaluationResult, TestResult
from ai_programming_tutor.solutions import cpp_features


NATURAL_EVALUATION_SCHEMA_VERSION = "0.1"
SEMANTIC_LABELS = tuple(
    sorted(set(HINTS) - {"compilation_error", "unknown"})
)
MAX_DATASET_BYTES = 10_000_000
MAX_SOURCE_BYTES = 50_000
MIN_AGGREGATE_SAMPLES = 10
MIN_AGGREGATE_PARTICIPANTS = 5
MIN_REPORTED_CLASS_SUPPORT = 5

_RECORD_FIELDS = {
    "schema_version",
    "dataset_id",
    "sample_id",
    "participant_key",
    "exercise_id",
    "source",
    "source_sha256",
    "label",
    "origin",
    "consent_confirmed",
    "deidentified",
    "labeler_count",
    "label_status",
    "split",
    "exercise_fingerprint",
    "test_suite_fingerprint",
    "signal_provenance",
    "signals",
}
_SIGNAL_FIELDS = {"compiled", "passed_count", "total_count", "test_statuses"}
_ALLOWED_TEST_STATUSES = {"passed", "wrong_answer", "runtime_error", "timeout"}
_SAFE_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
_PRIVACY_PATTERNS = (
    (
        "email address",
        re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    ),
    ("web address", re.compile(r"(?:https?://|www\.)", re.IGNORECASE)),
    (
        "local user path",
        re.compile(
            r"(?:[A-Za-z]:\\(?:Users|Documents|Desktop|Downloads)\\|"
            r"/(?:home|Users)/[^/\s]+)",
            re.IGNORECASE,
        ),
    ),
    (
        "identity-bearing comment",
        re.compile(
            r"(?://|/\*)[^\n]*(?:name|nume|student|grupa|group|matricol)\s*[:=]",
            re.IGNORECASE,
        ),
    ),
)


@dataclass(frozen=True)
class NaturalSample:
    dataset_id: str
    sample_id: str
    participant_key: str
    exercise_id: str
    source: str
    label: str
    labeler_count: int
    label_status: str
    test_statuses: tuple[str, ...]


def _exact_fields(value: dict[str, Any], expected: set[str], line_number: int) -> None:
    missing = expected - set(value)
    unknown = set(value) - expected
    if missing:
        raise ValueError(
            f"Natural dataset line {line_number} is missing fields: "
            + ", ".join(sorted(missing))
        )
    if unknown:
        raise ValueError(
            f"Natural dataset line {line_number} has unknown fields: "
            + ", ".join(sorted(unknown))
        )


def _required_string(value: dict[str, Any], field: str, line_number: int) -> str:
    result = value[field]
    if not isinstance(result, str) or not result:
        raise ValueError(f"Natural dataset line {line_number} requires string field {field}.")
    return result


def _required_true(value: dict[str, Any], field: str, line_number: int) -> None:
    if value[field] is not True:
        raise ValueError(f"Natural dataset line {line_number} requires {field}=true.")


def _source_privacy_issue(source: str, sample_id: str, participant_key: str) -> str | None:
    if "\x00" in source:
        return "NUL byte"
    lowered = source.casefold()
    for identifier, name in (
        (sample_id, "sample identifier"),
        (participant_key, "participant key"),
    ):
        if identifier.casefold() in lowered:
            return name
    for name, pattern in _PRIVACY_PATTERNS:
        if pattern.search(source):
            return name
    return None


def _parse_record(value: object, line_number: int) -> NaturalSample:
    if not isinstance(value, dict):
        raise ValueError(f"Natural dataset line {line_number} must be a JSON object.")
    _exact_fields(value, _RECORD_FIELDS, line_number)

    schema_version = _required_string(value, "schema_version", line_number)
    if schema_version != NATURAL_EVALUATION_SCHEMA_VERSION:
        raise ValueError(
            f"Natural dataset line {line_number} uses unsupported schema {schema_version!r}."
        )

    dataset_id = _required_string(value, "dataset_id", line_number)
    sample_id = _required_string(value, "sample_id", line_number)
    participant_key = _required_string(value, "participant_key", line_number)
    for field, identifier in (
        ("dataset_id", dataset_id),
        ("sample_id", sample_id),
        ("participant_key", participant_key),
    ):
        if _SAFE_IDENTIFIER.fullmatch(identifier) is None:
            raise ValueError(
                f"Natural dataset line {line_number} has an invalid {field}."
            )

    exercise_id = _required_string(value, "exercise_id", line_number)
    source = _required_string(value, "source", line_number)
    if len(source.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise ValueError(
            f"Natural dataset line {line_number} exceeds the source-size limit."
        )
    privacy_issue = _source_privacy_issue(source, sample_id, participant_key)
    if privacy_issue is not None:
        raise ValueError(
            f"Natural dataset line {line_number} may contain a {privacy_issue}; "
            "de-identify it before evaluation."
        )
    features = cpp_features(source)
    if features:
        raise ValueError(
            f"Natural dataset line {line_number} contains C++ features; "
            "the frozen evaluation is C17-only."
        )

    source_sha256 = _required_string(value, "source_sha256", line_number)
    actual_source_sha256 = hashlib.sha256(source.encode("utf-8")).hexdigest()
    if source_sha256 != actual_source_sha256:
        raise ValueError(
            f"Natural dataset line {line_number} does not match its source fingerprint."
        )

    label = _required_string(value, "label", line_number)
    if label not in SEMANTIC_LABELS:
        raise ValueError(
            f"Natural dataset line {line_number} has unsupported semantic label {label!r}."
        )
    if value["origin"] != "consented_natural_submission":
        raise ValueError(
            f"Natural dataset line {line_number} must declare consented natural origin."
        )
    _required_true(value, "consent_confirmed", line_number)
    _required_true(value, "deidentified", line_number)
    if value["split"] != "frozen_test":
        raise ValueError(f"Natural dataset line {line_number} must use the frozen_test split.")
    if value["signal_provenance"] != "isolated_disposable_worker":
        raise ValueError(
            f"Natural dataset line {line_number} requires isolated-worker signals."
        )

    labeler_count = value["labeler_count"]
    if isinstance(labeler_count, bool) or not isinstance(labeler_count, int):
        raise ValueError(
            f"Natural dataset line {line_number} requires an integer labeler_count."
        )
    if labeler_count < 2:
        raise ValueError(
            f"Natural dataset line {line_number} requires at least two labelers."
        )
    label_status = _required_string(value, "label_status", line_number)
    if label_status not in {"agreed", "adjudicated"}:
        raise ValueError(
            f"Natural dataset line {line_number} requires agreed or adjudicated labeling."
        )

    exercise = get_exercise(exercise_id)
    if value["exercise_fingerprint"] != exercise_fingerprint(exercise):
        raise ValueError(
            f"Natural dataset line {line_number} targets a different exercise revision."
        )
    if value["test_suite_fingerprint"] != test_suite_fingerprint(exercise):
        raise ValueError(
            f"Natural dataset line {line_number} targets a different test-suite revision."
        )

    signals = value["signals"]
    if not isinstance(signals, dict):
        raise ValueError(f"Natural dataset line {line_number} requires a signals object.")
    _exact_fields(signals, _SIGNAL_FIELDS, line_number)
    if signals["compiled"] is not True:
        raise ValueError(
            f"Natural dataset line {line_number} is outside the compiling-semantic scope."
        )
    statuses = signals["test_statuses"]
    if not isinstance(statuses, list) or not all(
        isinstance(status, str) and status in _ALLOWED_TEST_STATUSES for status in statuses
    ):
        raise ValueError(
            f"Natural dataset line {line_number} has invalid precomputed test statuses."
        )
    passed_count = signals["passed_count"]
    total_count = signals["total_count"]
    if any(
        isinstance(item, bool) or not isinstance(item, int)
        for item in (passed_count, total_count)
    ):
        raise ValueError(
            f"Natural dataset line {line_number} requires integer signal counts."
        )
    if total_count != len(exercise.tests) or len(statuses) != total_count:
        raise ValueError(
            f"Natural dataset line {line_number} has signals for a different test count."
        )
    if passed_count != statuses.count("passed"):
        raise ValueError(
            f"Natural dataset line {line_number} has inconsistent passed_count."
        )
    if passed_count == total_count:
        raise ValueError(
            f"Natural dataset line {line_number} passes every test and has no diagnosis target."
        )

    return NaturalSample(
        dataset_id=dataset_id,
        sample_id=sample_id,
        participant_key=participant_key,
        exercise_id=exercise_id,
        source=source,
        label=label,
        labeler_count=labeler_count,
        label_status=label_status,
        test_statuses=tuple(statuses),
    )


def read_natural_dataset(path: Path) -> tuple[tuple[NaturalSample, ...], str]:
    if path.stat().st_size > MAX_DATASET_BYTES:
        raise ValueError(f"Natural dataset exceeds the {MAX_DATASET_BYTES}-byte limit.")
    payload = path.read_bytes()
    if len(payload) > MAX_DATASET_BYTES:
        raise ValueError(f"Natural dataset exceeds the {MAX_DATASET_BYTES}-byte limit.")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Natural dataset must be UTF-8 text.") from exc

    samples: list[NaturalSample] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on natural dataset line {line_number}.") from exc
        samples.append(_parse_record(value, line_number))
    if not samples:
        raise ValueError("Natural dataset is empty.")

    dataset_ids = {sample.dataset_id for sample in samples}
    if len(dataset_ids) != 1:
        raise ValueError("Every natural sample must use the same dataset_id.")
    sample_ids = [sample.sample_id for sample in samples]
    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError("Natural dataset sample_id values must be unique.")
    source_fingerprints = [
        hashlib.sha256(sample.source.encode("utf-8")).hexdigest() for sample in samples
    ]
    if len(source_fingerprints) != len(set(source_fingerprints)):
        raise ValueError("Natural dataset may not contain duplicate source programs.")
    if len(samples) < MIN_AGGREGATE_SAMPLES:
        raise ValueError(
            f"Natural dataset requires at least {MIN_AGGREGATE_SAMPLES} samples "
            "for aggregate reporting."
        )
    participant_count = len({sample.participant_key for sample in samples})
    if participant_count < MIN_AGGREGATE_PARTICIPANTS:
        raise ValueError(
            "Natural dataset requires at least "
            f"{MIN_AGGREGATE_PARTICIPANTS} participants for aggregate reporting."
        )

    return tuple(samples), hashlib.sha256(payload).hexdigest()


def _evaluation(sample: NaturalSample) -> EvaluationResult:
    exercise = get_exercise(sample.exercise_id)
    tests = tuple(
        TestResult(case.name, case.hidden, status, "", "", "", 0, 0.0)
        for case, status in zip(exercise.tests, sample.test_statuses, strict=True)
    )
    return EvaluationResult(sample.exercise_id, CompilationResult(True, 0), tests)


def _track_metrics(
    expected: list[str], ranked_predictions: list[tuple[str, ...]]
) -> dict[str, Any]:
    predicted = [ranking[0] if ranking else "unknown" for ranking in ranked_predictions]
    observed_labels = sorted(set(expected))
    per_class: dict[str, dict[str, float | int]] = {}
    f1_values: list[float] = []
    for label in observed_labels:
        true_positive = sum(
            actual == label and prediction == label
            for actual, prediction in zip(expected, predicted, strict=True)
        )
        false_positive = sum(
            actual != label and prediction == label
            for actual, prediction in zip(expected, predicted, strict=True)
        )
        false_negative = sum(
            actual == label and prediction != label
            for actual, prediction in zip(expected, predicted, strict=True)
        )
        precision = (
            true_positive / (true_positive + false_positive)
            if true_positive + false_positive
            else 0.0
        )
        recall = (
            true_positive / (true_positive + false_negative)
            if true_positive + false_negative
            else 0.0
        )
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        f1_values.append(f1)
        support = expected.count(label)
        if support >= MIN_REPORTED_CLASS_SUPPORT:
            per_class[label] = {
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
                "support": support,
            }

    sample_count = len(expected)
    accuracy = sum(
        actual == prediction
        for actual, prediction in zip(expected, predicted, strict=True)
    ) / sample_count
    top_three_recall = sum(
        actual in ranking
        for actual, ranking in zip(expected, ranked_predictions, strict=True)
    ) / sample_count
    coverage = sum(bool(ranking) for ranking in ranked_predictions) / sample_count
    macro_f1 = sum(f1_values) / len(f1_values)
    return {
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "top_3_recall": round(top_three_recall, 4),
        "coverage": round(coverage, 4),
        "unknown_rate": round(1.0 - coverage, 4),
        "per_class_min_support": MIN_REPORTED_CLASS_SUPPORT,
        "suppressed_class_count": len(observed_labels) - len(per_class),
        "per_class": per_class,
    }


def _model_metadata(bundle: dict[str, Any], model_path: Path) -> dict[str, Any]:
    if not isinstance(bundle, dict) or "pipeline" not in bundle:
        raise ValueError("The model bundle is missing its prediction pipeline.")
    labels = bundle.get("labels")
    if (
        not isinstance(labels, list)
        or len(labels) != len(SEMANTIC_LABELS)
        or set(labels) != set(SEMANTIC_LABELS)
    ):
        raise ValueError("The model does not cover the frozen 13-label taxonomy.")
    training_exercises = bundle.get("training_exercises")
    if not isinstance(training_exercises, list) or len(training_exercises) != len(
        list_exercises()
    ):
        raise ValueError("The model bundle is missing its training exercise list.")
    if set(training_exercises) != {exercise.id for exercise in list_exercises()}:
        raise ValueError("The model was not trained across the current exercise catalog.")
    pipeline = bundle["pipeline"]
    try:
        classifier_labels = set(pipeline.named_steps["classifier"].classes_)
    except (AttributeError, KeyError, TypeError) as exc:
        raise ValueError("The model bundle has an incompatible prediction pipeline.") from exc
    if classifier_labels != set(SEMANTIC_LABELS):
        raise ValueError("The model pipeline does not cover the frozen 13-label taxonomy.")
    dataset_size = bundle.get("dataset_size")
    if (
        isinstance(dataset_size, bool)
        or not isinstance(dataset_size, int)
        or dataset_size < 1
    ):
        raise ValueError("The model bundle is missing its training dataset size.")
    return {
        "sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "training_dataset_size": dataset_size,
        "training_exercise_count": len(training_exercises),
        "label_count": len(labels),
    }


def evaluate_natural_dataset(
    dataset_path: Path,
    output_path: Path,
    model_path: Path | None = None,
) -> dict[str, Any]:
    if dataset_path.resolve() == output_path.resolve():
        raise ValueError("Natural dataset and aggregate report paths must differ.")
    if model_path is not None and model_path.resolve() == output_path.resolve():
        raise ValueError("Model and aggregate report paths must differ.")
    samples, dataset_sha256 = read_natural_dataset(dataset_path)
    expected = [sample.label for sample in samples]
    rule_rankings: list[tuple[str, ...]] = []
    ml_rankings: list[tuple[str, ...]] = []
    hybrid_rankings: list[tuple[str, ...]] = []

    model_bundle = None
    model_metadata = None
    if model_path is not None:
        from ai_programming_tutor.baseline import load_model

        model_bundle = load_model(model_path)
        model_metadata = _model_metadata(model_bundle, model_path)

    for sample in samples:
        evaluation = _evaluation(sample)
        rule_candidates = tuple(
            candidate
            for candidate in diagnose(sample.source, evaluation)
            if candidate.category in SEMANTIC_LABELS
        )
        rule_rankings.append(tuple(candidate.category for candidate in rule_candidates))
        if model_bundle is not None:
            from ai_programming_tutor.baseline import predict_candidates
            from ai_programming_tutor.service import _merge_candidates

            ml_candidates = predict_candidates(
                model_bundle, sample.source, evaluation, limit=3
            )
            ml_candidates = tuple(
                candidate
                for candidate in ml_candidates
                if candidate.category in SEMANTIC_LABELS
            )
            hybrid_candidates = _merge_candidates(ml_candidates, rule_candidates)
            ml_rankings.append(tuple(candidate.category for candidate in ml_candidates))
            hybrid_rankings.append(
                tuple(
                    candidate.category
                    for candidate in hybrid_candidates
                    if candidate.category in SEMANTIC_LABELS
                )
            )

    label_support = Counter(expected)
    reported_label_support = {
        label: support
        for label, support in sorted(label_support.items())
        if support >= MIN_REPORTED_CLASS_SUPPORT
    }
    status_support = Counter(sample.label_status for sample in samples)
    report: dict[str, Any] = {
        "report_schema_version": "0.1",
        "evaluation": "frozen-natural-code",
        "dataset": {
            "id": samples[0].dataset_id,
            "schema_version": NATURAL_EVALUATION_SCHEMA_VERSION,
            "sha256": dataset_sha256,
            "sample_count": len(samples),
            "participant_count": len({sample.participant_key for sample in samples}),
            "exercise_count": len({sample.exercise_id for sample in samples}),
            "label_count": len(label_support),
            "taxonomy_label_count": len(SEMANTIC_LABELS),
            "all_taxonomy_labels_present": set(label_support) == set(SEMANTIC_LABELS),
            "label_support_minimum": MIN_REPORTED_CLASS_SUPPORT,
            "reported_label_support": reported_label_support,
            "suppressed_label_count": len(label_support) - len(reported_label_support),
            "minimum_labeler_count": min(sample.labeler_count for sample in samples),
            "label_status_counts": dict(sorted(status_support.items())),
        },
        "scope": {
            "dialect": "c17",
            "targets": "compiling submissions that fail at least one authored test",
            "label_policy": "single primary semantic label",
            "macro_f1_labels": "labels observed in this frozen set",
        },
        "tracks": {"rule_only": _track_metrics(expected, rule_rankings)},
        "model": model_metadata,
        "privacy": {
            "contains_source": False,
            "contains_participant_keys": False,
            "contains_sample_predictions": False,
            "input_execution": "none; precomputed isolated-worker signals only",
            "formal_privacy_guarantee": "none; thresholds are not differential privacy",
        },
        "limitations": [
            "The evaluator validates declared provenance but cannot prove consent "
            "or worker isolation.",
            "Small or label-incomplete sets are not directly comparable with the "
            "13-label synthetic benchmark.",
            "Compiler diagnostics are excluded from the private schema, so that "
            "model feature is intentionally empty.",
            "Aggregation and suppression thresholds are not a formal "
            "anonymization guarantee.",
            "Aggregate results do not establish learning impact or public-runner safety.",
        ],
    }
    if model_bundle is not None:
        report["tracks"]["ml_only"] = _track_metrics(expected, ml_rankings)
        report["tracks"]["hybrid"] = _track_metrics(expected, hybrid_rankings)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report

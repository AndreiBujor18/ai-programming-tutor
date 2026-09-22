from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from ai_programming_tutor.catalog import get_exercise
from ai_programming_tutor.dataset import exercise_fingerprint, test_suite_fingerprint
from ai_programming_tutor.natural_evaluation import (
    MAX_DATASET_BYTES,
    NATURAL_EVALUATION_SCHEMA_VERSION,
    evaluate_natural_dataset,
    read_natural_dataset,
)
from ai_programming_tutor.runner import CRunner


GCC_AVAILABLE = shutil.which("gcc") is not None


def _record(
    exercise_id: str,
    source: str,
    label: str,
    sample_id: str,
    participant_key: str,
) -> dict[str, object]:
    exercise = get_exercise(exercise_id)
    evaluation = CRunner().evaluate(source, exercise)
    if not evaluation.compilation.succeeded or evaluation.all_passed:
        raise AssertionError("The natural-evaluation fixture must compile and fail tests.")
    return {
        "schema_version": NATURAL_EVALUATION_SCHEMA_VERSION,
        "dataset_id": "natural-pilot-v1",
        "sample_id": sample_id,
        "participant_key": participant_key,
        "exercise_id": exercise_id,
        "source": source,
        "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "label": label,
        "origin": "consented_natural_submission",
        "consent_confirmed": True,
        "deidentified": True,
        "labeler_count": 2,
        "label_status": "agreed",
        "split": "frozen_test",
        "exercise_fingerprint": exercise_fingerprint(exercise),
        "test_suite_fingerprint": test_suite_fingerprint(exercise),
        "signal_provenance": "isolated_disposable_worker",
        "signals": {
            "compiled": True,
            "passed_count": evaluation.passed_count,
            "total_count": evaluation.total_count,
            "test_statuses": [test.status for test in evaluation.tests],
        },
    }


def _write_records(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


@unittest.skipUnless(GCC_AVAILABLE, "GCC is required for natural-evaluation fixtures")
class NaturalEvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        sentinel = get_exercise("sentinel_average")
        sentinel_source = sentinel.reference_solution.replace(
            "if (value != 0)", "if (1)", 1
        )
        longest = get_exercise("file_longest_word")
        longest_source = longest.reference_solution.replace(
            "current_length > longest_length",
            "current_length >= longest_length",
            1,
        )
        base_records = [
            _record(
                "sentinel_average",
                sentinel_source,
                "sentinel_handling",
                "NAT-0001",
                "P-001",
            ),
            _record(
                "file_longest_word",
                longest_source,
                "relational_operator",
                "NAT-0002",
                "P-002",
            ),
        ]
        self.records = []
        for index in range(10):
            record = deepcopy(base_records[index % len(base_records)])
            source = str(record["source"]) + "\n" * (index + 1)
            record["source"] = source
            record["source_sha256"] = hashlib.sha256(source.encode("utf-8")).hexdigest()
            record["sample_id"] = f"NAT-{index + 1:04d}"
            record["participant_key"] = f"P-{index % 5 + 1:03d}"
            self.records.append(record)

    def test_report_is_aggregate_source_free_and_uses_precomputed_signals(self) -> None:
        with tempfile.TemporaryDirectory(prefix="aptutor-natural-") as directory:
            root = Path(directory)
            dataset = root / "natural.jsonl"
            output = root / "aggregate.json"
            _write_records(dataset, self.records)

            report = evaluate_natural_dataset(dataset, output)

            self.assertEqual(report["evaluation"], "frozen-natural-code")
            self.assertEqual(report["dataset"]["sample_count"], 10)
            self.assertEqual(report["dataset"]["participant_count"], 5)
            self.assertEqual(report["tracks"]["rule_only"]["accuracy"], 1.0)
            self.assertEqual(report["tracks"]["rule_only"]["top_3_recall"], 1.0)
            self.assertIsNone(report["model"])
            self.assertIn("not differential privacy", report["privacy"]["formal_privacy_guarantee"])
            written = output.read_text(encoding="utf-8")
            self.assertNotIn(self.records[0]["source"], written)
            self.assertNotIn("P-001", written)
            self.assertNotIn("NAT-0001", written)

    def test_privacy_and_exact_schema_checks_reject_risky_records(self) -> None:
        cases: list[tuple[str, dict[str, object], str]] = []
        identity_comment = deepcopy(self.records[0])
        identity_comment["source"] = "// nume: redacted\n" + str(
            identity_comment["source"]
        )
        identity_comment["source_sha256"] = hashlib.sha256(
            str(identity_comment["source"]).encode("utf-8")
        ).hexdigest()
        cases.append(("identity comment", identity_comment, "identity-bearing comment"))

        unknown_field = deepcopy(self.records[0])
        unknown_field["student_name"] = "redacted"
        cases.append(("unknown field", unknown_field, "unknown fields"))

        one_labeler = deepcopy(self.records[0])
        one_labeler["labeler_count"] = 1
        cases.append(("one labeler", one_labeler, "at least two labelers"))

        for name, record, message in cases:
            with self.subTest(case=name), tempfile.TemporaryDirectory(
                prefix="aptutor-natural-"
            ) as directory:
                dataset = Path(directory) / "natural.jsonl"
                _write_records(dataset, [record])
                with self.assertRaisesRegex(ValueError, message):
                    read_natural_dataset(dataset)

    def test_frozen_revision_and_duplicate_checks_are_enforced(self) -> None:
        revision_mismatch = deepcopy(self.records[0])
        revision_mismatch["test_suite_fingerprint"] = "0" * 16
        duplicate = deepcopy(self.records[0])
        duplicate["sample_id"] = "NAT-0003"
        duplicate["participant_key"] = "P-003"

        with tempfile.TemporaryDirectory(prefix="aptutor-natural-") as directory:
            root = Path(directory)
            mismatch_path = root / "mismatch.jsonl"
            _write_records(mismatch_path, [revision_mismatch])
            with self.assertRaisesRegex(ValueError, "different test-suite revision"):
                read_natural_dataset(mismatch_path)

            duplicate_path = root / "duplicate.jsonl"
            _write_records(duplicate_path, [self.records[0], duplicate])
            with self.assertRaisesRegex(ValueError, "duplicate source programs"):
                read_natural_dataset(duplicate_path)

            small_path = root / "small.jsonl"
            _write_records(small_path, self.records[:9])
            with self.assertRaisesRegex(ValueError, "at least 10 samples"):
                read_natural_dataset(small_path)

            few_participants = deepcopy(self.records)
            for record in few_participants:
                record["participant_key"] = "P-001"
            participant_path = root / "few-participants.jsonl"
            _write_records(participant_path, few_participants)
            with self.assertRaisesRegex(ValueError, "at least 5 participants"):
                read_natural_dataset(participant_path)

            suppressed_records = deepcopy(self.records)
            relational_records = [
                record
                for record in suppressed_records
                if record["label"] == "relational_operator"
            ]
            relational_records[0]["label"] = "sentinel_handling"
            suppressed_path = root / "suppressed.jsonl"
            suppressed_output = root / "suppressed-report.json"
            _write_records(suppressed_path, suppressed_records)
            suppressed_report = evaluate_natural_dataset(
                suppressed_path, suppressed_output
            )
            self.assertEqual(suppressed_report["dataset"]["suppressed_label_count"], 1)
            self.assertNotIn(
                "relational_operator",
                suppressed_report["tracks"]["rule_only"]["per_class"],
            )

    def test_size_and_output_path_guards_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory(prefix="aptutor-natural-") as directory:
            root = Path(directory)
            dataset = root / "natural.jsonl"
            _write_records(dataset, self.records)

            model_and_output = root / "baseline.joblib"
            with self.assertRaisesRegex(ValueError, "Model and aggregate report"):
                evaluate_natural_dataset(dataset, model_and_output, model_and_output)

            oversized = root / "oversized.jsonl"
            with oversized.open("wb") as stream:
                stream.seek(MAX_DATASET_BYTES)
                stream.write(b"\0")
            with self.assertRaisesRegex(ValueError, "exceeds the .*byte limit"):
                read_natural_dataset(oversized)


if __name__ == "__main__":
    unittest.main()

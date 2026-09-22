from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from ai_programming_tutor.baseline import load_model, train_baseline
from ai_programming_tutor.dataset import generate_dataset
from ai_programming_tutor.natural_evaluation import evaluate_natural_dataset


ML_AVAILABLE = all(importlib.util.find_spec(name) is not None for name in ("sklearn", "joblib"))


@unittest.skipUnless(ML_AVAILABLE, "scikit-learn and joblib are optional")
class BaselineTests(unittest.TestCase):
    def test_training_uses_grouped_evaluation_and_writes_artifacts(self) -> None:
        with tempfile.TemporaryDirectory(prefix="aptutor-test-") as directory:
            root = Path(directory)
            dataset = root / "samples.jsonl"
            model = root / "model.joblib"
            metrics_path = root / "metrics.json"
            matrix = root / "matrix.csv"
            generate_dataset(dataset, variants=2, evaluate=True)
            records = [
                json.loads(line)
                for line in dataset.read_text(encoding="utf-8").splitlines()
            ]
            compilation_failures = [
                record["id"] for record in records if not record["signals"]["compiled"]
            ]
            self.assertFalse(
                compilation_failures,
                f"Controlled mutations failed to compile: {compilation_failures[:5]}",
            )
            metrics = train_baseline(dataset, model, metrics_path, matrix)

            self.assertEqual(metrics["evaluation"], "leave-one-exercise-out")
            self.assertEqual(metrics["sample_count"], 164)
            self.assertEqual(metrics["exercise_count"], 16)
            self.assertEqual(metrics["label_count"], 13)
            self.assertEqual(len(metrics["folds"]), 16)
            self.assertIn("rule_only", metrics)
            self.assertIn("hybrid", metrics)
            self.assertGreaterEqual(metrics["hybrid"]["top_3_recall"], metrics["top_3_recall"])
            self.assertTrue(model.exists() and metrics_path.exists() and matrix.exists())
            self.assertIn("pipeline", load_model(model))

            natural_dataset = root / "natural.jsonl"
            natural_metrics = root / "natural-metrics.json"
            natural_records = []
            for index, record in enumerate(records[:10], start=1):
                source = record["source"]
                signals = record["signals"]
                natural_records.append(
                    {
                        "schema_version": "0.1",
                        "dataset_id": "model-path-fixture",
                        "sample_id": f"NAT-{index:04d}",
                        "participant_key": f"P-{(index - 1) % 5 + 1:03d}",
                        "exercise_id": record["exercise_id"],
                        "source": source,
                        "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
                        "label": record["label"],
                        "origin": "consented_natural_submission",
                        "consent_confirmed": True,
                        "deidentified": True,
                        "labeler_count": 2,
                        "label_status": "agreed",
                        "split": "frozen_test",
                        "exercise_fingerprint": record["exercise_fingerprint"],
                        "test_suite_fingerprint": record["test_suite_fingerprint"],
                        "signal_provenance": "isolated_disposable_worker",
                        "signals": {
                            "compiled": signals["compiled"],
                            "passed_count": signals["passed_count"],
                            "total_count": signals["total_count"],
                            "test_statuses": signals["test_statuses"],
                        },
                    }
                )
            natural_dataset.write_text(
                "".join(json.dumps(record) + "\n" for record in natural_records),
                encoding="utf-8",
            )
            natural_report = evaluate_natural_dataset(
                natural_dataset, natural_metrics, model
            )
            self.assertIn("ml_only", natural_report["tracks"])
            self.assertIn("hybrid", natural_report["tracks"])
            self.assertEqual(natural_report["model"]["training_dataset_size"], 164)
            self.assertFalse(natural_report["privacy"]["contains_source"])


if __name__ == "__main__":
    unittest.main()

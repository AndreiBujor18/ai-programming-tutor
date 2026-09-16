from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

from ai_programming_tutor.baseline import load_model, train_baseline
from ai_programming_tutor.dataset import generate_dataset


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
            metrics = train_baseline(dataset, model, metrics_path, matrix)

            self.assertEqual(metrics["evaluation"], "leave-one-exercise-out")
            self.assertEqual(metrics["label_count"], 13)
            self.assertEqual(len(metrics["folds"]), 14)
            self.assertIn("rule_only", metrics)
            self.assertIn("hybrid", metrics)
            self.assertGreaterEqual(metrics["hybrid"]["top_3_recall"], metrics["top_3_recall"])
            self.assertTrue(model.exists() and metrics_path.exists() and matrix.exists())
            self.assertIn("pipeline", load_model(model))


if __name__ == "__main__":
    unittest.main()

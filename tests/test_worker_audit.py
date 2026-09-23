from __future__ import annotations

import io
import json
import sys
import unittest
from unittest import mock

from ai_programming_tutor import worker
from ai_programming_tutor.cli import build_parser
from ai_programming_tutor.worker_audit import run_worker_adversarial_audit
from ai_programming_tutor.worker_protocol import WORKER_UNTRUSTED_UID, create_worker_job


PINNED_IMAGE = "sha256:" + "b" * 64


def _passing_probe_result(job: dict) -> dict:
    if job["job_id"] == "audit-compile_canary_denied":
        signals = {
            "compiled": False,
            "passed_count": 0,
            "total_count": 0,
            "test_statuses": [],
        }
    elif job["job_id"] in {
        "audit-cpu_loop_bounded",
        "audit-stdout_flood_bounded",
    }:
        signals = {
            "compiled": True,
            "passed_count": 0,
            "total_count": 5,
            "test_statuses": ["runtime_error"] * 5,
        }
    else:
        signals = {
            "compiled": True,
            "passed_count": 0,
            "total_count": 5,
            "test_statuses": ["wrong_answer"] * 5,
        }
    return {"signals": signals}


class WorkerAuditTests(unittest.TestCase):
    def test_controller_status_requires_kill_setuid_nnp_and_seccomp(self) -> None:
        valid = """CapInh:\t0000000000000000
CapPrm:\t00000000000000a0
CapEff:\t00000000000000a0
CapBnd:\t00000000000000a0
CapAmb:\t0000000000000000
NoNewPrivs:\t1
Seccomp:\t2
"""
        self.assertTrue(worker._controller_status_is_valid(valid))
        self.assertFalse(
            worker._controller_status_is_valid(
                valid.replace("CapEff:\t00000000000000a0", "CapEff:\t00000000000000e0")
            )
        )
        self.assertFalse(
            worker._controller_status_is_valid(
                valid.replace("Seccomp:\t2", "Seccomp:\t0")
            )
        )

    def test_passing_report_is_source_free_and_explicitly_limited(self) -> None:
        with mock.patch(
            "ai_programming_tutor.worker_audit.run_docker_worker",
            side_effect=lambda job, **_: _passing_probe_result(job),
        ), mock.patch(
            "ai_programming_tutor.worker_audit._cleanup_observation",
            return_value=(True, {"outcome": "no_remaining_containers", "remaining_count": 0}),
        ):
            report = run_worker_adversarial_audit(image=PINNED_IMAGE)

        self.assertTrue(report["passed"])
        self.assertEqual(len(report["checks"]), 13)
        serialized = json.dumps(report)
        self.assertNotIn("protected_canary.h", serialized)
        self.assertNotIn("emit_reference_answer", serialized)
        self.assertIn("secret_free_host_requires_manual_attestation", serialized)

    def test_any_probe_failure_closes_the_gate(self) -> None:
        def result(job: dict, **_: object) -> dict:
            if job["job_id"] == "audit-installed_tests_denied":
                return {
                    "signals": {
                        "compiled": True,
                        "passed_count": 5,
                        "total_count": 5,
                        "test_statuses": ["passed"] * 5,
                    }
                }
            return _passing_probe_result(job)

        with mock.patch(
            "ai_programming_tutor.worker_audit.run_docker_worker",
            side_effect=result,
        ), mock.patch(
            "ai_programming_tutor.worker_audit._cleanup_observation",
            return_value=(True, {"outcome": "no_remaining_containers", "remaining_count": 0}),
        ):
            report = run_worker_adversarial_audit(image=PINNED_IMAGE)

        self.assertFalse(report["passed"])
        failed = [check["check_id"] for check in report["checks"] if not check["passed"]]
        self.assertEqual(failed, ["installed_tests_denied"])

    def test_worker_entrypoint_requests_the_untrusted_uid(self) -> None:
        job = create_worker_job(
            "sentinel_average",
            "int main(void) { return 0; }",
            job_id="job-entrypoint-test",
        )
        fake_stdin = mock.Mock()
        fake_stdin.buffer = io.BytesIO(json.dumps(job).encode("utf-8"))
        fake_stdout = io.StringIO()
        result = {"source_free": True}
        with mock.patch.object(worker, "_validate_runtime_boundary"), mock.patch.object(
            worker, "evaluate_worker_job", return_value=result
        ) as evaluator, mock.patch.object(sys, "stdin", fake_stdin), mock.patch.object(
            sys, "stdout", fake_stdout
        ):
            worker.main()

        evaluator.assert_called_once_with(
            job,
            execution_uid=WORKER_UNTRUSTED_UID,
            isolated_pid_namespace=True,
        )
        self.assertEqual(json.loads(fake_stdout.getvalue()), result)

    def test_cli_exposes_the_adversarial_gate(self) -> None:
        args = build_parser().parse_args(
            ["audit-isolated", "--image", PINNED_IMAGE]
        )
        self.assertEqual(args.image, PINNED_IMAGE)
        self.assertEqual(args.output.name, "worker_adversarial_report.json")


if __name__ == "__main__":
    unittest.main()

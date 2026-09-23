from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import unittest
from copy import deepcopy
from unittest import mock

from ai_programming_tutor.catalog import get_exercise
from ai_programming_tutor.worker_protocol import (
    WORKER_PROFILE,
    create_worker_job,
    docker_worker_command,
    evaluate_worker_job,
    run_docker_worker,
    validate_worker_job,
    validate_worker_result,
)


GCC_AVAILABLE = shutil.which("gcc") is not None
PINNED_IMAGE = "sha256:" + "a" * 64


class WorkerContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.exercise = get_exercise("sentinel_average")
        self.job = create_worker_job(
            self.exercise.id,
            self.exercise.reference_solution,
            job_id="job-test-0001",
        )

    def test_job_is_exact_source_bound_and_identity_free(self) -> None:
        validated = validate_worker_job(self.job)
        self.assertEqual(validated["worker_profile"], WORKER_PROFILE)
        self.assertEqual(validated["dialect"], "c17")
        self.assertEqual(
            validated["source_sha256"],
            hashlib.sha256(self.exercise.reference_solution.encode("utf-8")).hexdigest(),
        )
        serialized = json.dumps(validated)
        self.assertNotIn("participant", serialized)
        self.assertNotIn("sample_id", serialized)
        self.assertNotIn("label", serialized)

    def test_job_rejects_unknown_stale_or_changed_content(self) -> None:
        cases = []
        unknown = deepcopy(self.job)
        unknown["participant_key"] = "P-001"
        cases.append((unknown, "unknown fields"))
        changed = deepcopy(self.job)
        changed["source"] += "\n"
        cases.append((changed, "fingerprint"))
        stale = deepcopy(self.job)
        stale["test_suite_fingerprint"] = "0" * 16
        cases.append((stale, "different test-suite revision"))
        cpp = deepcopy(self.job)
        cpp["source"] = "#include <iostream>\nint main() { return 0; }\n"
        cpp["source_sha256"] = hashlib.sha256(cpp["source"].encode()).hexdigest()
        cases.append((cpp, "classic C17 only"))
        for value, message in cases:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                validate_worker_job(value)

    def test_docker_command_has_no_network_mount_or_privilege_path(self) -> None:
        command = docker_worker_command(PINNED_IMAGE)
        joined = " ".join(command)
        self.assertIn("--network=none", command)
        self.assertIn("--ipc=none", command)
        self.assertIn("--read-only", command)
        self.assertIn("--cap-drop=ALL", command)
        self.assertIn("--security-opt=no-new-privileges", command)
        self.assertIn("--attach=stdout", command)
        self.assertIn("--log-driver=none", command)
        self.assertIn("--user=65532:65532", command)
        self.assertNotIn("--volume", command)
        self.assertNotIn("-v", command)
        self.assertNotIn(self.job["source"], joined)
        with self.assertRaisesRegex(ValueError, "immutable sha256"):
            docker_worker_command("aptutor-worker:latest")

    def test_host_rejects_unbound_or_source_bearing_result(self) -> None:
        result = {
            "schema_version": "0.1",
            "worker_profile": WORKER_PROFILE,
            "job_id": self.job["job_id"],
            "job_sha256": "0" * 64,
            "exercise_id": self.job["exercise_id"],
            "exercise_fingerprint": self.job["exercise_fingerprint"],
            "test_suite_fingerprint": self.job["test_suite_fingerprint"],
            "source_sha256": self.job["source_sha256"],
            "signals": {
                "compiled": True,
                "passed_count": 5,
                "total_count": 5,
                "test_statuses": ["passed"] * 5,
            },
        }
        with self.assertRaisesRegex(ValueError, "mismatched job_sha256"):
            validate_worker_result(result, self.job)
        result["source"] = self.job["source"]
        with self.assertRaisesRegex(ValueError, "unknown fields"):
            validate_worker_result(result, self.job)

    def test_host_validates_container_json_before_returning_it(self) -> None:
        expected = evaluate_worker_job(self.job) if GCC_AVAILABLE else {
            "schema_version": "0.1",
            "worker_profile": WORKER_PROFILE,
            "job_id": self.job["job_id"],
            "job_sha256": "unused",
            "exercise_id": self.job["exercise_id"],
            "exercise_fingerprint": self.job["exercise_fingerprint"],
            "test_suite_fingerprint": self.job["test_suite_fingerprint"],
            "source_sha256": self.job["source_sha256"],
            "signals": {},
        }
        if not GCC_AVAILABLE:
            self.skipTest("GCC is required to build a valid worker receipt")
        completed = subprocess.CompletedProcess(
            args=["docker"],
            returncode=0,
            stdout=json.dumps(expected).encode("utf-8"),
            stderr=b"",
        )
        with mock.patch(
            "ai_programming_tutor.worker_protocol.subprocess.run",
            return_value=completed,
        ) as runner:
            actual = run_docker_worker(self.job, image=PINNED_IMAGE)
        self.assertEqual(actual, expected)
        sent = runner.call_args.kwargs["input"]
        self.assertIn(self.job["source_sha256"].encode(), sent)
        self.assertNotIn(self.job["source"], json.dumps(actual))

    def test_host_never_relays_container_stderr(self) -> None:
        private_marker = "student-name-and-source-must-not-escape"
        completed = subprocess.CompletedProcess(
            args=["docker"],
            returncode=2,
            stdout=b"",
            stderr=private_marker.encode("utf-8"),
        )
        with mock.patch(
            "ai_programming_tutor.worker_protocol.subprocess.run",
            return_value=completed,
        ), self.assertRaisesRegex(ValueError, "failed without a usable result") as raised:
            run_docker_worker(self.job, image=PINNED_IMAGE)
        self.assertNotIn(private_marker, str(raised.exception))

    def test_outer_timeout_forces_container_cleanup(self) -> None:
        timeout = subprocess.TimeoutExpired(["docker", "run"], 1)
        removed = subprocess.CompletedProcess(
            args=["docker", "rm"],
            returncode=0,
            stdout=b"",
            stderr=b"",
        )
        with mock.patch(
            "ai_programming_tutor.worker_protocol.subprocess.run",
            side_effect=[timeout, removed],
        ) as runner, self.assertRaisesRegex(ValueError, "outer wall timeout"):
            run_docker_worker(self.job, image=PINNED_IMAGE, timeout_seconds=1)
        cleanup_command = runner.call_args_list[1].args[0]
        self.assertEqual(cleanup_command[:3], ["docker", "rm", "--force"])


@unittest.skipUnless(GCC_AVAILABLE, "GCC is required for worker execution tests")
class WorkerExecutionTests(unittest.TestCase):
    def test_worker_result_is_source_free_and_reports_five_statuses(self) -> None:
        exercise = get_exercise("sentinel_average")
        buggy = exercise.reference_solution.replace("if (value != 0)", "if (1)", 1)
        job = create_worker_job(exercise.id, buggy, job_id="job-test-0002")
        result = evaluate_worker_job(job)
        self.assertTrue(result["signals"]["compiled"])
        self.assertEqual(result["signals"]["total_count"], 5)
        self.assertLess(result["signals"]["passed_count"], 5)
        self.assertEqual(len(result["signals"]["test_statuses"]), 5)
        serialized = json.dumps(result)
        self.assertNotIn(buggy, serialized)
        self.assertNotIn("stderr", serialized)
        self.assertNotIn("actual", serialized)

    def test_compilation_failure_emits_no_diagnostics_or_test_claims(self) -> None:
        job = create_worker_job(
            "sentinel_average",
            "int main(void) { this is not C; }",
            job_id="job-test-0003",
        )
        result = evaluate_worker_job(job)
        self.assertEqual(
            result["signals"],
            {
                "compiled": False,
                "passed_count": 0,
                "total_count": 0,
                "test_statuses": [],
            },
        )
        self.assertNotIn("not C", json.dumps(result))


if __name__ == "__main__":
    unittest.main()

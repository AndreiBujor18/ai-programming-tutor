from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest import mock

from ai_programming_tutor.catalog import get_exercise
from ai_programming_tutor.cli import _read_bounded_utf8
from ai_programming_tutor.runner import (
    CRunner,
    _clear_isolated_pid_namespace,
    _subprocess_setup,
)
from ai_programming_tutor.worker_protocol import (
    MAX_WORKER_RESULT_BYTES,
    WORKER_PROFILE,
    _run_bounded_process,
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
        old_profile = deepcopy(self.job)
        old_profile["worker_profile"] = "docker-disposable-v0.1"
        cases.append((old_profile, "unsupported isolation profile"))
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

    def test_docker_command_has_exact_network_mount_and_capability_boundary(self) -> None:
        command = docker_worker_command(PINNED_IMAGE)
        joined = " ".join(command)
        self.assertIn("--network=none", command)
        self.assertIn("--ipc=none", command)
        self.assertIn("--pid=private", command)
        self.assertIn("--read-only", command)
        self.assertIn("--cap-drop=ALL", command)
        self.assertIn("--cap-add=KILL", command)
        self.assertIn("--cap-add=SETUID", command)
        self.assertEqual(
            [argument for argument in command if argument.startswith("--cap-add=")],
            ["--cap-add=KILL", "--cap-add=SETUID"],
        )
        self.assertIn("--security-opt=no-new-privileges", command)
        self.assertIn("--security-opt=seccomp=builtin", command)
        self.assertIn("--attach=stdout", command)
        self.assertIn("--log-driver=none", command)
        self.assertIn("--user=0:65532", command)
        self.assertIn(
            "--tmpfs=/work:rw,nosuid,nodev,exec,size=128m,mode=710,uid=0,gid=65532",
            command,
        )
        self.assertNotIn("--volume", command)
        self.assertNotIn("-v", command)
        self.assertNotIn(self.job["source"], joined)
        with self.assertRaisesRegex(ValueError, "immutable sha256"):
            docker_worker_command("aptutor-worker:latest")
        with self.assertRaisesRegex(ValueError, "immutable sha256"):
            docker_worker_command("--privileged@sha256:" + "a" * 64)

    def test_host_source_read_is_bounded_before_utf8_decoding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "submission.c"
            source.write_bytes(b"x" * 11)
            with self.assertRaisesRegex(ValueError, "10-byte limit"):
                _read_bounded_utf8(source, 10, "Worker source")
            source.write_bytes(b"\xff")
            with self.assertRaisesRegex(ValueError, "UTF-8"):
                _read_bounded_utf8(source, 10, "Worker source")

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
            "ai_programming_tutor.worker_protocol._run_bounded_process",
            return_value=completed,
        ) as runner:
            actual = run_docker_worker(self.job, image=PINNED_IMAGE)
        self.assertEqual(actual, expected)
        sent = runner.call_args.kwargs["input_bytes"]
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
            "ai_programming_tutor.worker_protocol._run_bounded_process",
            return_value=completed,
        ), mock.patch(
            "ai_programming_tutor.worker_protocol._force_remove_container"
        ) as remove, self.assertRaisesRegex(
            ValueError, "failed without a usable result"
        ) as raised:
            run_docker_worker(self.job, image=PINNED_IMAGE)
        self.assertNotIn(private_marker, str(raised.exception))
        remove.assert_called_once()

    def test_oversized_container_stdout_is_rejected_and_cleaned_up(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["docker"],
            returncode=0,
            stdout=b"x" * (MAX_WORKER_RESULT_BYTES + 1),
            stderr=b"",
        )
        with mock.patch(
            "ai_programming_tutor.worker_protocol._run_bounded_process",
            return_value=completed,
        ), mock.patch(
            "ai_programming_tutor.worker_protocol._force_remove_container"
        ) as remove, self.assertRaisesRegex(ValueError, "transport limit"):
            run_docker_worker(self.job, image=PINNED_IMAGE)
        remove.assert_called_once()

    def test_outer_timeout_forces_container_cleanup(self) -> None:
        timeout = subprocess.TimeoutExpired(["docker", "run"], 1)
        with mock.patch(
            "ai_programming_tutor.worker_protocol._run_bounded_process",
            side_effect=timeout,
        ), mock.patch(
            "ai_programming_tutor.worker_protocol._force_remove_container"
        ) as remove, self.assertRaisesRegex(ValueError, "outer wall timeout"):
            run_docker_worker(self.job, image=PINNED_IMAGE, timeout_seconds=1)
        remove.assert_called_once()
        self.assertTrue(remove.call_args.args[1].startswith("aptutor-worker-"))

        with mock.patch(
            "ai_programming_tutor.worker_protocol._run_bounded_process",
            side_effect=OSError("private transport detail"),
        ), mock.patch(
            "ai_programming_tutor.worker_protocol._force_remove_container"
        ) as remove, self.assertRaisesRegex(ValueError, "transport failed") as raised:
            run_docker_worker(self.job, image=PINNED_IMAGE)
        self.assertNotIn("private transport detail", str(raised.exception))
        remove.assert_called_once()

    def test_host_capture_stops_after_bounded_stdout(self) -> None:
        completed = _run_bounded_process(
            [
                sys.executable,
                "-c",
                "import sys; sys.stdout.buffer.write(b'x' * 1000000)",
            ],
            input_bytes=b"",
            max_stdout_bytes=1024,
            timeout_seconds=5,
        )
        self.assertEqual(len(completed.stdout), 1025)
        self.assertLessEqual(len(completed.stdout), MAX_WORKER_RESULT_BYTES)

    @unittest.skipIf(sys.platform == "win32", "UID separation is a POSIX worker control")
    def test_subprocess_setup_sets_all_untrusted_uids_after_limits(self) -> None:
        events: list[str] = []
        setup = _subprocess_setup(lambda: events.append("limits"), 65533)
        self.assertIsNotNone(setup)
        with mock.patch(
            "ai_programming_tutor.runner.os.setresuid",
            side_effect=lambda *_: events.append("uid"),
        ) as setresuid:
            setup()
        self.assertEqual(events, ["limits", "uid"])
        setresuid.assert_called_once_with(65533, 65533, 65533)

    def test_runner_rejects_root_or_noninteger_execution_uid(self) -> None:
        for value in (0, -1, True, "65533"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                CRunner(execution_uid=value)  # type: ignore[arg-type]

        with self.assertRaisesRegex(ValueError, "requires an untrusted UID"):
            CRunner(isolated_pid_namespace=True)
        with self.assertRaisesRegex(ValueError, "must be a boolean"):
            CRunner(isolated_pid_namespace="yes")  # type: ignore[arg-type]

    @unittest.skipIf(sys.platform != "linux", "PID namespaces are Linux-only")
    def test_isolated_pid_cleanup_requires_pid1_and_reaps_children(self) -> None:
        with mock.patch(
            "ai_programming_tutor.runner.os.getpid", return_value=2
        ), self.assertRaisesRegex(RuntimeError, "requires a Linux PID 1"):
            _clear_isolated_pid_namespace(True)

        with mock.patch(
            "ai_programming_tutor.runner.os.getpid", return_value=1
        ), mock.patch(
            "ai_programming_tutor.runner.os.kill"
        ) as kill, mock.patch(
            "ai_programming_tutor.runner.os.waitpid",
            side_effect=[(123, 0), ChildProcessError()],
        ) as waitpid:
            _clear_isolated_pid_namespace(True)

        kill.assert_called_once_with(-1, signal.SIGKILL)
        self.assertEqual(waitpid.call_args_list, [
            mock.call(-1, os.WNOHANG),
            mock.call(-1, os.WNOHANG),
        ])


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

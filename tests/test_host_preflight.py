from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from ai_programming_tutor.cli import build_parser
from ai_programming_tutor.host_preflight import (
    HostSnapshot,
    _classify_docker_endpoint,
    _read_docker_info,
    build_host_preflight_report,
    write_host_preflight_report,
)


def _ready_snapshot() -> HostSnapshot:
    return HostSnapshot(
        system="Linux",
        os_id="fedora",
        os_version_id="44",
        architecture="x86_64",
        kernel_release="6.17.1-300.fc44.x86_64",
        effective_uid=1000,
        cgroup_v2=True,
        cgroup_controllers=("cpu", "cpuset", "io", "memory", "pids"),
        systemd_running=True,
        systemd_version="258",
        host_lsms=("selinux",),
        rootful_socket_accessible=False,
        docker_outcome="connected",
        docker_server_version="29.8.0",
        docker_os="linux",
        docker_architecture="x86_64",
        docker_cgroup_version="2",
        docker_cgroup_driver="systemd",
        docker_rootless=True,
        docker_builtin_seccomp=True,
        docker_lsms=("selinux",),
        docker_endpoint_outcome="rootless_user_unix_socket",
    )


class HostPreflightTests(unittest.TestCase):
    def test_ready_report_keeps_manual_attestation_open(self) -> None:
        report = build_host_preflight_report(_ready_snapshot())

        self.assertEqual(
            set(report),
            {
                "schema_version",
                "preflight_profile",
                "worker_profile",
                "status",
                "environment",
                "automated_checks",
                "manual_requirements",
                "limitations",
            },
        )
        self.assertEqual(
            set(report["environment"]),
            {
                "os_id",
                "os_version_id",
                "architecture",
                "kernel_release",
                "systemd_version",
                "docker_server_version",
            },
        )
        self.assertEqual(report["status"], "automated_ready")
        self.assertEqual(len(report["automated_checks"]), 17)
        self.assertTrue(all(check["passed"] for check in report["automated_checks"]))
        self.assertTrue(
            all(
                set(check) == {"check_id", "passed", "observation"}
                and set(check["observation"]) == {"outcome"}
                for check in report["automated_checks"]
            )
        )
        self.assertTrue(report["manual_requirements"])
        self.assertTrue(
            all(
                set(requirement) == {"requirement_id", "status"}
                and requirement["status"] == "not_attested"
                for requirement in report["manual_requirements"]
            )
        )
        self.assertIn(
            "report_does_not_authorize_natural_code_processing",
            report["limitations"],
        )

    def test_rootful_or_nonlocal_docker_fails_closed(self) -> None:
        snapshot = replace(
            _ready_snapshot(),
            rootful_socket_accessible=True,
            docker_rootless=False,
            docker_endpoint_outcome="remote_or_non_unix_endpoint",
        )
        report = build_host_preflight_report(snapshot)

        self.assertEqual(report["status"], "blocked")
        failed = {
            check["check_id"]
            for check in report["automated_checks"]
            if not check["passed"]
        }
        self.assertEqual(
            failed,
            {
                "rootful_docker_socket_inaccessible",
                "docker_rootless",
                "docker_rootless_user_socket",
            },
        )

    def test_missing_resource_boundary_fails_closed(self) -> None:
        snapshot = replace(
            _ready_snapshot(),
            cgroup_controllers=("cpu", "pids"),
            docker_cgroup_driver="none",
        )
        report = build_host_preflight_report(snapshot)

        failed = {
            check["check_id"]
            for check in report["automated_checks"]
            if not check["passed"]
        }
        self.assertEqual(
            failed,
            {"required_cgroup_controllers", "docker_systemd_cgroup_driver"},
        )
        self.assertEqual(report["status"], "blocked")

    def test_report_sanitizes_environment_and_has_no_identity_fields(self) -> None:
        snapshot = replace(
            _ready_snapshot(),
            os_id="private-user-marker-linux",
            os_version_id="44-private-user-marker",
            kernel_release="6.17.1-private-user-marker",
            docker_server_version="29.8.0-private-user-marker",
            docker_outcome="/home/private-user-marker/docker-error",
            docker_endpoint_outcome="unix:///home/private-user-marker/docker.sock",
        )
        report = build_host_preflight_report(snapshot)
        serialized = json.dumps(report).casefold()

        self.assertEqual(report["environment"]["os_id"], "unavailable")
        self.assertEqual(report["environment"]["os_version_id"], "44")
        self.assertEqual(report["environment"]["kernel_release"], "6.17.1")
        self.assertEqual(report["environment"]["docker_server_version"], "29.8.0")
        self.assertNotIn("private-user-marker", serialized)
        self.assertIn("runtime_error", serialized)
        for forbidden_key in ("hostname", "username", "ip_address", "mac_address"):
            self.assertNotIn(forbidden_key, serialized)

    def test_invalid_or_oversized_docker_info_is_not_relayed(self) -> None:
        private_marker = b'/home/private-user-marker/private\n{"broken":'
        completed = subprocess.CompletedProcess(
            args=["docker"],
            returncode=0,
            stdout=private_marker,
            stderr=b"secret stderr",
        )
        with mock.patch(
            "ai_programming_tutor.host_preflight._run_bounded_process",
            return_value=completed,
        ):
            outcome, info = _read_docker_info("docker")

        self.assertEqual(outcome, "invalid_response")
        self.assertEqual(info, {})
        self.assertNotIn("private-user-marker", json.dumps(info))

        completed = subprocess.CompletedProcess(
            args=["docker"],
            returncode=0,
            stdout=b"x" * 64_001,
            stderr=b"",
        )
        with mock.patch(
            "ai_programming_tutor.host_preflight._run_bounded_process",
            return_value=completed,
        ):
            outcome, info = _read_docker_info("docker")
        self.assertEqual(outcome, "oversized_output")
        self.assertEqual(info, {})

    def test_endpoint_classification_requires_standard_user_socket(self) -> None:
        self.assertEqual(
            _classify_docker_endpoint(
                "unix:///run/user/1000/docker.sock",
                1000,
            ),
            "rootless_user_unix_socket",
        )
        self.assertEqual(
            _classify_docker_endpoint("unix:///var/run/docker.sock", 1000),
            "other_local_unix_socket",
        )
        self.assertEqual(
            _classify_docker_endpoint("tcp://127.0.0.1:2375", 1000),
            "remote_or_non_unix_endpoint",
        )

    def test_cli_and_writer_use_ignored_private_default(self) -> None:
        args = build_parser().parse_args(["inspect-host"])
        self.assertEqual(args.output, Path("private_evaluation/host_preflight.json"))
        self.assertEqual(args.docker, "docker")

        report = build_host_preflight_report(_ready_snapshot())
        with tempfile.TemporaryDirectory(prefix="aptutor-host-") as directory:
            output = Path(directory) / "nested" / "preflight.json"
            write_host_preflight_report(output, report)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), report)


if __name__ == "__main__":
    unittest.main()

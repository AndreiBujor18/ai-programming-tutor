"""Read-only, privacy-safe preflight for a dedicated worker host."""

from __future__ import annotations

import json
import os
import platform
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai_programming_tutor.worker_protocol import WORKER_PROFILE, _run_bounded_process


HOST_PREFLIGHT_SCHEMA_VERSION = "0.1"
HOST_PREFLIGHT_PROFILE = "dedicated-worker-host-preflight-v0.1"
MAX_HOST_COMMAND_BYTES = 64_000
HOST_COMMAND_TIMEOUT_SECONDS = 10.0

_REQUIRED_CGROUP_CONTROLLERS = frozenset({"cpu", "memory", "pids"})
_SAFE_FACT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,79}")
_PUBLIC_OS_IDS = frozenset(
    {
        "almalinux",
        "arch",
        "centos",
        "debian",
        "fedora",
        "nixos",
        "opensuse-leap",
        "opensuse-tumbleweed",
        "rhel",
        "rocky",
        "sles",
        "ubuntu",
    }
)
_VERSION_PREFIX = re.compile(
    r"(?P<version>[0-9]{1,4}(?:\.[0-9]{1,4}){0,3})(?:$|[-+_])"
)
_DOCKER_OUTCOMES = {
    "connected",
    "not_found",
    "timeout",
    "runtime_error",
    "command_failed",
    "oversized_output",
    "invalid_response",
}
_DOCKER_ENDPOINT_OUTCOMES = {
    "rootless_user_unix_socket",
    "other_local_unix_socket",
    "remote_or_non_unix_endpoint",
    "unavailable",
}
_MANUAL_REQUIREMENTS = (
    "dedicated_reimaged_and_secret_free",
    "maintained_os_security_updates_and_hardware_stability_verified",
    "no_cloud_role_metadata_agent_forwarding_or_remote_daemon",
    "swap_dumps_logs_backups_telemetry_and_retention_reviewed",
    "offline_evaluation_network_policy_verified",
    "encrypted_or_ram_backed_inbox_verified",
    "immutable_image_toolchain_runtime_and_build_recorded",
    "unit_smoke_adversarial_and_cleanup_gates_passed",
    "post_reboot_and_simulated_failure_cleanup_passed",
    "operations_record_reviewed_and_kept_outside_git",
)


@dataclass(frozen=True)
class HostSnapshot:
    """Allowlisted host facts used to build the source-free report."""

    system: str
    os_id: str
    os_version_id: str
    architecture: str
    kernel_release: str
    effective_uid: int | None
    cgroup_v2: bool
    cgroup_controllers: tuple[str, ...]
    systemd_running: bool
    systemd_version: str
    host_lsms: tuple[str, ...]
    rootful_socket_accessible: bool
    docker_outcome: str
    docker_server_version: str
    docker_os: str
    docker_architecture: str
    docker_cgroup_version: str
    docker_cgroup_driver: str
    docker_rootless: bool
    docker_builtin_seccomp: bool
    docker_lsms: tuple[str, ...]
    docker_endpoint_outcome: str


def _safe_fact(value: object) -> str:
    if not isinstance(value, str):
        return "unavailable"
    stripped = value.strip()
    if _SAFE_FACT.fullmatch(stripped) is None:
        return "unavailable"
    return stripped


def _safe_os_id(value: object) -> str:
    fact = _safe_fact(value).lower()
    return fact if fact in _PUBLIC_OS_IDS else "unavailable"


def _safe_version(value: object) -> str:
    if not isinstance(value, str):
        return "unavailable"
    match = _VERSION_PREFIX.match(value.strip())
    return match.group("version") if match is not None else "unavailable"


def _normalize_architecture(value: object) -> str:
    fact = _safe_fact(value).lower()
    if fact in {"amd64", "x86_64"}:
        return "x86_64"
    if fact in {"arm64", "aarch64"}:
        return "aarch64"
    return fact


def _read_small_text(path: Path, max_bytes: int = 4_096) -> str | None:
    try:
        with path.open("rb") as stream:
            payload = stream.read(max_bytes + 1)
    except (OSError, ValueError):
        return None
    if len(payload) > max_bytes:
        return None
    try:
        return payload.decode("utf-8").strip()
    except UnicodeDecodeError:
        return None


def _run_public_command(
    command: list[str],
    *,
    max_stdout_bytes: int = MAX_HOST_COMMAND_BYTES,
) -> tuple[str, bytes]:
    try:
        completed = _run_bounded_process(
            command,
            input_bytes=b"",
            max_stdout_bytes=max_stdout_bytes,
            timeout_seconds=HOST_COMMAND_TIMEOUT_SECONDS,
        )
    except FileNotFoundError:
        return "not_found", b""
    except subprocess.TimeoutExpired:
        return "timeout", b""
    except OSError:
        return "runtime_error", b""
    if len(completed.stdout) > max_stdout_bytes:
        return "oversized_output", b""
    if completed.returncode != 0:
        return "command_failed", b""
    return "ok", completed.stdout


def _read_docker_info(docker_executable: str) -> tuple[str, dict[str, Any]]:
    outcome, payload = _run_public_command(
        [docker_executable, "info", "--format={{json .}}"]
    )
    if outcome != "ok":
        return outcome, {}
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "invalid_response", {}
    if not isinstance(value, dict):
        return "invalid_response", {}
    return "connected", value


def _classify_docker_endpoint(endpoint: object, effective_uid: int | None) -> str:
    if not isinstance(endpoint, str) or effective_uid is None:
        return "unavailable"
    expected = f"unix:///run/user/{effective_uid}/docker.sock"
    if endpoint == expected:
        return "rootless_user_unix_socket"
    if endpoint.startswith("unix://"):
        return "other_local_unix_socket"
    if endpoint.startswith(("tcp://", "http://", "https://", "ssh://", "npipe://")):
        return "remote_or_non_unix_endpoint"
    return "unavailable"


def _read_docker_endpoint(
    docker_executable: str,
    effective_uid: int | None,
) -> str:
    endpoint = os.environ.get("DOCKER_HOST")
    if endpoint:
        return _classify_docker_endpoint(endpoint, effective_uid)
    outcome, payload = _run_public_command(
        [
            docker_executable,
            "context",
            "inspect",
            "--format={{json .Endpoints.docker.Host}}",
        ],
        max_stdout_bytes=4_096,
    )
    if outcome != "ok":
        return "unavailable"
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "unavailable"
    return _classify_docker_endpoint(value, effective_uid)


def _systemd_observation() -> tuple[bool, str]:
    if not Path("/run/systemd/system").is_dir():
        return False, "unavailable"
    outcome, payload = _run_public_command(
        ["systemctl", "--version"],
        max_stdout_bytes=4_096,
    )
    if outcome != "ok":
        return False, "unavailable"
    first_line = payload.decode("ascii", errors="ignore").splitlines()
    if not first_line:
        return False, "unavailable"
    match = re.match(r"systemd\s+([0-9]{1,4})\b", first_line[0])
    if match is None:
        return False, "unavailable"
    return True, match.group(1)


def _host_lsms() -> tuple[str, ...]:
    result: list[str] = []
    if _read_small_text(Path("/sys/fs/selinux/enforce")) == "1":
        result.append("selinux")
    apparmor = _read_small_text(Path("/sys/module/apparmor/parameters/enabled"))
    if apparmor is not None and apparmor.casefold() in {"y", "yes", "1"}:
        result.append("apparmor")
    return tuple(result)


def _os_release() -> tuple[str, str]:
    try:
        release = platform.freedesktop_os_release()
    except (OSError, ValueError):
        return "unavailable", "unavailable"
    return _safe_os_id(release.get("ID")), _safe_version(release.get("VERSION_ID"))


def collect_host_snapshot(docker_executable: str = "docker") -> HostSnapshot:
    """Read allowlisted facts without changing host configuration."""
    system = _safe_fact(platform.system())
    architecture = _normalize_architecture(platform.machine())
    kernel_release = _safe_version(platform.release())
    os_id, os_version_id = _os_release()
    effective_uid_getter = getattr(os, "geteuid", None)
    effective_uid = effective_uid_getter() if effective_uid_getter is not None else None

    controller_text = _read_small_text(Path("/sys/fs/cgroup/cgroup.controllers"))
    cgroup_v2 = controller_text is not None
    controllers = tuple(sorted(controller_text.split())) if controller_text else ()
    systemd_running, systemd_version = _systemd_observation()
    host_lsms = _host_lsms()
    rootful_socket_accessible = any(
        path.exists() and os.access(path, os.R_OK | os.W_OK)
        for path in (Path("/var/run/docker.sock"), Path("/run/docker.sock"))
    )

    docker_outcome, docker_info = _read_docker_info(docker_executable)
    security_options_value = docker_info.get("SecurityOptions")
    security_options = (
        tuple(
            option
            for option in security_options_value
            if isinstance(option, str)
        )
        if isinstance(security_options_value, list)
        else ()
    )
    docker_rootless = any(
        option == "name=rootless" or option.startswith("name=rootless,")
        for option in security_options
    )
    docker_builtin_seccomp = any(
        option.startswith("name=seccomp") and "profile=builtin" in option
        for option in security_options
    )
    docker_lsms = tuple(
        name
        for name in ("selinux", "apparmor")
        if any(
            option == f"name={name}" or option.startswith(f"name={name},")
            for option in security_options
        )
    )
    docker_endpoint_outcome = (
        _read_docker_endpoint(docker_executable, effective_uid)
        if docker_outcome == "connected"
        else "unavailable"
    )

    return HostSnapshot(
        system=system,
        os_id=os_id,
        os_version_id=os_version_id,
        architecture=architecture,
        kernel_release=kernel_release,
        effective_uid=effective_uid,
        cgroup_v2=cgroup_v2,
        cgroup_controllers=controllers,
        systemd_running=systemd_running,
        systemd_version=_safe_fact(systemd_version),
        host_lsms=host_lsms,
        rootful_socket_accessible=rootful_socket_accessible,
        docker_outcome=(
            docker_outcome if docker_outcome in _DOCKER_OUTCOMES else "runtime_error"
        ),
        docker_server_version=_safe_version(docker_info.get("ServerVersion")),
        docker_os=_safe_fact(docker_info.get("OSType")),
        docker_architecture=_normalize_architecture(docker_info.get("Architecture")),
        docker_cgroup_version=_safe_fact(str(docker_info.get("CgroupVersion", ""))),
        docker_cgroup_driver=_safe_fact(docker_info.get("CgroupDriver")),
        docker_rootless=docker_rootless,
        docker_builtin_seccomp=docker_builtin_seccomp,
        docker_lsms=docker_lsms,
        docker_endpoint_outcome=docker_endpoint_outcome,
    )


def _check(check_id: str, passed: bool, outcome: str) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "passed": passed,
        "observation": {"outcome": outcome},
    }


def _lsm_outcome(lsms: tuple[str, ...]) -> str:
    if "selinux" in lsms:
        return "selinux_enforcing"
    if "apparmor" in lsms:
        return "apparmor_enabled"
    return "unavailable"


def build_host_preflight_report(snapshot: HostSnapshot) -> dict[str, Any]:
    """Convert a snapshot to an exact, non-identifying fail-closed report."""
    host_architecture = _normalize_architecture(snapshot.architecture)
    docker_architecture = _normalize_architecture(snapshot.docker_architecture)
    controllers_complete = _REQUIRED_CGROUP_CONTROLLERS.issubset(
        snapshot.cgroup_controllers
    )
    docker_outcome = (
        snapshot.docker_outcome
        if snapshot.docker_outcome in _DOCKER_OUTCOMES
        else "runtime_error"
    )
    docker_endpoint_outcome = (
        snapshot.docker_endpoint_outcome
        if snapshot.docker_endpoint_outcome in _DOCKER_ENDPOINT_OUTCOMES
        else "unavailable"
    )
    checks = [
        _check(
            "linux_host",
            snapshot.system == "Linux",
            "linux" if snapshot.system == "Linux" else "not_linux",
        ),
        _check(
            "supported_architecture",
            host_architecture == "x86_64",
            "x86_64" if host_architecture == "x86_64" else "unsupported",
        ),
        _check(
            "non_root_operator",
            snapshot.effective_uid not in {None, 0},
            "non_root" if snapshot.effective_uid not in {None, 0} else "root_or_unavailable",
        ),
        _check(
            "cgroup_v2",
            snapshot.cgroup_v2,
            "available" if snapshot.cgroup_v2 else "unavailable",
        ),
        _check(
            "required_cgroup_controllers",
            controllers_complete,
            "complete" if controllers_complete else "incomplete",
        ),
        _check(
            "systemd_running",
            snapshot.systemd_running,
            "running" if snapshot.systemd_running else "unavailable",
        ),
        _check(
            "enforcing_host_lsm",
            bool(snapshot.host_lsms),
            _lsm_outcome(snapshot.host_lsms),
        ),
        _check(
            "rootful_docker_socket_inaccessible",
            not snapshot.rootful_socket_accessible,
            "inaccessible" if not snapshot.rootful_socket_accessible else "accessible",
        ),
        _check(
            "docker_connected",
            docker_outcome == "connected",
            docker_outcome,
        ),
        _check(
            "docker_linux_server",
            snapshot.docker_os == "linux",
            "linux" if snapshot.docker_os == "linux" else "unavailable_or_non_linux",
        ),
        _check(
            "docker_architecture_matches",
            host_architecture == "x86_64" and docker_architecture == host_architecture,
            "matches" if docker_architecture == host_architecture else "mismatch_or_unavailable",
        ),
        _check(
            "docker_rootless",
            snapshot.docker_rootless,
            "enabled" if snapshot.docker_rootless else "disabled_or_unavailable",
        ),
        _check(
            "docker_rootless_user_socket",
            docker_endpoint_outcome == "rootless_user_unix_socket",
            docker_endpoint_outcome,
        ),
        _check(
            "docker_cgroup_v2",
            snapshot.docker_cgroup_version == "2",
            "version_2" if snapshot.docker_cgroup_version == "2" else "unavailable_or_other",
        ),
        _check(
            "docker_systemd_cgroup_driver",
            snapshot.docker_cgroup_driver == "systemd",
            "systemd" if snapshot.docker_cgroup_driver == "systemd" else "unavailable_or_other",
        ),
        _check(
            "docker_builtin_seccomp",
            snapshot.docker_builtin_seccomp,
            "builtin" if snapshot.docker_builtin_seccomp else "unavailable_or_other",
        ),
        _check(
            "docker_lsm_integration",
            bool(snapshot.docker_lsms),
            _lsm_outcome(snapshot.docker_lsms),
        ),
    ]
    automated_ready = all(check["passed"] for check in checks)
    return {
        "schema_version": HOST_PREFLIGHT_SCHEMA_VERSION,
        "preflight_profile": HOST_PREFLIGHT_PROFILE,
        "worker_profile": WORKER_PROFILE,
        "status": "automated_ready" if automated_ready else "blocked",
        "environment": {
            "os_id": _safe_os_id(snapshot.os_id),
            "os_version_id": _safe_version(snapshot.os_version_id),
            "architecture": host_architecture,
            "kernel_release": _safe_version(snapshot.kernel_release),
            "systemd_version": _safe_version(snapshot.systemd_version),
            "docker_server_version": _safe_version(snapshot.docker_server_version),
        },
        "automated_checks": checks,
        "manual_requirements": [
            {"requirement_id": requirement_id, "status": "not_attested"}
            for requirement_id in _MANUAL_REQUIREMENTS
        ],
        "limitations": [
            "automated_preflight_does_not_attest_a_secret_free_host",
            "manual_requirements_remain_blocking",
            "shared_kernel_requires_adversarial_and_incident_acceptance",
            "report_does_not_authorize_natural_code_processing",
        ],
    }


def inspect_worker_host(docker_executable: str = "docker") -> dict[str, Any]:
    return build_host_preflight_report(collect_host_snapshot(docker_executable))


def write_host_preflight_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

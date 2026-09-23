"""Single-job stdin/stdout entry point used inside the disposable worker image."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from ai_programming_tutor.worker_protocol import (
    MAX_WORKER_JOB_BYTES,
    WORKER_CONTROLLER_UID,
    WORKER_SHARED_GID,
    WORKER_UNTRUSTED_UID,
    evaluate_worker_job,
)


PROTECTED_CANARY_PATH = Path("/opt/aptutor-private/protected_canary.h")
PROTECTED_CANARY = "#define APTUTOR_PROTECTED_CANARY 1\n"
EXPECTED_PACKAGE_ROOT = Path(
    "/usr/local/lib/python3.12/site-packages/ai_programming_tutor"
)
WORK_ROOT = Path("/work")
_CAP_KILL_MASK = 1 << 5
_CAP_SETUID_MASK = 1 << 7
_CONTROLLER_CAP_MASK = _CAP_KILL_MASK | _CAP_SETUID_MASK


def _controller_status_is_valid(status_text: str) -> bool:
    fields: dict[str, str] = {}
    for line in status_text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key] = value.strip()
    try:
        capabilities = {
            key: int(fields[key], 16)
            for key in ("CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb")
        }
    except (KeyError, ValueError):
        return False
    return (
        capabilities
        == {
            "CapInh": 0,
            "CapPrm": _CONTROLLER_CAP_MASK,
            "CapEff": _CONTROLLER_CAP_MASK,
            "CapBnd": _CONTROLLER_CAP_MASK,
            "CapAmb": 0,
        }
        and fields.get("NoNewPrivs") == "1"
        and fields.get("Seccomp") == "2"
    )


def _validate_runtime_boundary() -> None:
    """Fail closed unless the image's controller-only boundary is intact."""
    if (
        sys.platform != "linux"
        or os.getuid() != WORKER_CONTROLLER_UID
        or os.getgid() != WORKER_SHARED_GID
        or any(group != WORKER_SHARED_GID for group in os.getgroups())
        or os.getpid() != 1
    ):
        raise RuntimeError("Worker controller identity is invalid.")
    try:
        status_text = Path("/proc/self/status").read_text(encoding="ascii")
    except OSError as exc:
        raise RuntimeError("Worker process boundary is unavailable.") from exc
    if not _controller_status_is_valid(status_text):
        raise RuntimeError("Worker process boundary is invalid.")
    package_root = Path(__file__).resolve().parent
    try:
        package_stat = package_root.stat()
    except OSError as exc:
        raise RuntimeError("Worker package boundary is unavailable.") from exc
    if (
        package_root != EXPECTED_PACKAGE_ROOT
        or package_stat.st_uid != WORKER_CONTROLLER_UID
        or package_stat.st_mode & 0o077
    ):
        raise RuntimeError("Worker package boundary is invalid.")
    try:
        work_stat = WORK_ROOT.stat()
    except OSError as exc:
        raise RuntimeError("Worker workspace boundary is unavailable.") from exc
    if (
        Path.cwd().resolve() != WORK_ROOT
        or not WORK_ROOT.is_dir()
        or work_stat.st_uid != WORKER_CONTROLLER_UID
        or work_stat.st_gid != WORKER_SHARED_GID
        or work_stat.st_mode & 0o777 != 0o710
    ):
        raise RuntimeError("Worker workspace boundary is invalid.")
    try:
        canary = PROTECTED_CANARY_PATH.read_text(encoding="ascii")
    except OSError as exc:
        raise RuntimeError("Worker protected boundary is unavailable.") from exc
    if canary != PROTECTED_CANARY:
        raise RuntimeError("Worker protected boundary is invalid.")


def main() -> None:
    try:
        _validate_runtime_boundary()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from None
    payload = sys.stdin.buffer.read(MAX_WORKER_JOB_BYTES + 1)
    if len(payload) > MAX_WORKER_JOB_BYTES:
        print("Worker job exceeds the transport limit.", file=sys.stderr)
        raise SystemExit(2)
    try:
        value = json.loads(payload.decode("utf-8"))
        result = evaluate_worker_job(
            value,
            execution_uid=WORKER_UNTRUSTED_UID,
            isolated_pid_namespace=True,
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        KeyError,
        RuntimeError,
        ValueError,
    ) as exc:
        print(f"Worker rejected the job: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
    sys.stdout.write(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()

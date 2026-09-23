"""Strict, source-bound protocol for a disposable execution worker."""

from __future__ import annotations

import hashlib
import json
import re
import secrets
import subprocess
from pathlib import Path
from typing import Any

from ai_programming_tutor.catalog import get_exercise
from ai_programming_tutor.dataset import exercise_fingerprint, test_suite_fingerprint
from ai_programming_tutor.runner import CRunner
from ai_programming_tutor.solutions import cpp_features


WORKER_SCHEMA_VERSION = "0.1"
WORKER_PROFILE = "docker-disposable-v0.1"
MAX_WORKER_JOB_BYTES = 100_000
MAX_WORKER_RESULT_BYTES = 64_000
MAX_WORKER_SOURCE_BYTES = 50_000
DEFAULT_WORKER_TIMEOUT_SECONDS = 20.0

_JOB_FIELDS = {
    "schema_version",
    "worker_profile",
    "job_id",
    "dialect",
    "exercise_id",
    "exercise_fingerprint",
    "test_suite_fingerprint",
    "source_sha256",
    "source",
}
_RESULT_FIELDS = {
    "schema_version",
    "worker_profile",
    "job_id",
    "job_sha256",
    "exercise_id",
    "exercise_fingerprint",
    "test_suite_fingerprint",
    "source_sha256",
    "signals",
}
_SIGNAL_FIELDS = {"compiled", "passed_count", "total_count", "test_statuses"}
_ALLOWED_TEST_STATUSES = {"passed", "wrong_answer", "runtime_error", "timeout"}
_SAFE_JOB_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
_IMAGE_ID = re.compile(r"sha256:[0-9a-f]{64}")
_IMAGE_DIGEST = re.compile(r"[^\s@]+@sha256:[0-9a-f]{64}")


def _exact_fields(value: dict[str, Any], expected: set[str], label: str) -> None:
    missing = expected - set(value)
    unknown = set(value) - expected
    if missing:
        raise ValueError(f"Worker {label} is missing fields: " + ", ".join(sorted(missing)))
    if unknown:
        raise ValueError(f"Worker {label} has unknown fields: " + ", ".join(sorted(unknown)))


def _canonical_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def worker_job_sha256(job: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(job)).hexdigest()


def create_worker_job(
    exercise_id: str,
    source: str,
    *,
    job_id: str | None = None,
) -> dict[str, Any]:
    """Create one identity-free C17 worker job bound to the current exercise."""
    exercise = get_exercise(exercise_id)
    if not isinstance(source, str) or not source:
        raise ValueError("Worker source must be nonempty text.")
    if "\x00" in source:
        raise ValueError("Worker source may not contain a NUL byte.")
    if len(source.encode("utf-8")) > MAX_WORKER_SOURCE_BYTES:
        raise ValueError(
            f"Worker source exceeds the {MAX_WORKER_SOURCE_BYTES}-byte limit."
        )
    if cpp_features(source):
        raise ValueError("The disposable worker accepts classic C17 only.")

    resolved_job_id = job_id or f"job-{secrets.token_hex(16)}"
    if (
        not isinstance(resolved_job_id, str)
        or _SAFE_JOB_ID.fullmatch(resolved_job_id) is None
    ):
        raise ValueError("Worker job_id must be a non-identifying portable identifier.")

    return {
        "schema_version": WORKER_SCHEMA_VERSION,
        "worker_profile": WORKER_PROFILE,
        "job_id": resolved_job_id,
        "dialect": "c17",
        "exercise_id": exercise.id,
        "exercise_fingerprint": exercise_fingerprint(exercise),
        "test_suite_fingerprint": test_suite_fingerprint(exercise),
        "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "source": source,
    }


def validate_worker_job(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("Worker job must be a JSON object.")
    _exact_fields(value, _JOB_FIELDS, "job")
    if value["schema_version"] != WORKER_SCHEMA_VERSION:
        raise ValueError("Worker job uses an unsupported schema version.")
    if value["worker_profile"] != WORKER_PROFILE:
        raise ValueError("Worker job uses an unsupported isolation profile.")
    if value["dialect"] != "c17":
        raise ValueError("Worker job dialect must be c17.")

    job_id = value["job_id"]
    if not isinstance(job_id, str) or _SAFE_JOB_ID.fullmatch(job_id) is None:
        raise ValueError("Worker job_id is invalid.")
    exercise_id = value["exercise_id"]
    if not isinstance(exercise_id, str) or not exercise_id:
        raise ValueError("Worker exercise_id is invalid.")
    source = value["source"]
    if not isinstance(source, str) or not source:
        raise ValueError("Worker source must be nonempty text.")
    if "\x00" in source:
        raise ValueError("Worker source may not contain a NUL byte.")
    if len(source.encode("utf-8")) > MAX_WORKER_SOURCE_BYTES:
        raise ValueError(
            f"Worker source exceeds the {MAX_WORKER_SOURCE_BYTES}-byte limit."
        )
    if cpp_features(source):
        raise ValueError("The disposable worker accepts classic C17 only.")

    source_sha256 = value["source_sha256"]
    if not isinstance(source_sha256, str) or source_sha256 != hashlib.sha256(
        source.encode("utf-8")
    ).hexdigest():
        raise ValueError("Worker source does not match its fingerprint.")

    exercise = get_exercise(exercise_id)
    if value["exercise_fingerprint"] != exercise_fingerprint(exercise):
        raise ValueError("Worker job targets a different exercise revision.")
    if value["test_suite_fingerprint"] != test_suite_fingerprint(exercise):
        raise ValueError("Worker job targets a different test-suite revision.")
    return dict(value)


def evaluate_worker_job(value: object) -> dict[str, Any]:
    """Evaluate a validated job and return only source-free bounded signals."""
    job = validate_worker_job(value)
    exercise = get_exercise(job["exercise_id"])
    evaluation = CRunner().evaluate(job["source"], exercise, dialect="c17")
    result = {
        "schema_version": WORKER_SCHEMA_VERSION,
        "worker_profile": WORKER_PROFILE,
        "job_id": job["job_id"],
        "job_sha256": worker_job_sha256(job),
        "exercise_id": exercise.id,
        "exercise_fingerprint": job["exercise_fingerprint"],
        "test_suite_fingerprint": job["test_suite_fingerprint"],
        "source_sha256": job["source_sha256"],
        "signals": {
            "compiled": evaluation.compilation.succeeded,
            "passed_count": evaluation.passed_count,
            "total_count": evaluation.total_count,
            "test_statuses": [test.status for test in evaluation.tests],
        },
    }
    return validate_worker_result(result, job)


def validate_worker_result(value: object, job_value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("Worker result must be a JSON object.")
    _exact_fields(value, _RESULT_FIELDS, "result")
    job = validate_worker_job(job_value)

    expected_bindings = {
        "schema_version": WORKER_SCHEMA_VERSION,
        "worker_profile": WORKER_PROFILE,
        "job_id": job["job_id"],
        "job_sha256": worker_job_sha256(job),
        "exercise_id": job["exercise_id"],
        "exercise_fingerprint": job["exercise_fingerprint"],
        "test_suite_fingerprint": job["test_suite_fingerprint"],
        "source_sha256": job["source_sha256"],
    }
    for field, expected in expected_bindings.items():
        if value[field] != expected:
            raise ValueError(f"Worker result has a mismatched {field}.")

    signals = value["signals"]
    if not isinstance(signals, dict):
        raise ValueError("Worker result requires a signals object.")
    _exact_fields(signals, _SIGNAL_FIELDS, "signals")
    compiled = signals["compiled"]
    if not isinstance(compiled, bool):
        raise ValueError("Worker compiled signal must be a boolean.")
    passed_count = signals["passed_count"]
    total_count = signals["total_count"]
    if any(
        isinstance(item, bool) or not isinstance(item, int)
        for item in (passed_count, total_count)
    ):
        raise ValueError("Worker signal counts must be integers.")
    statuses = signals["test_statuses"]
    if not isinstance(statuses, list) or not all(
        isinstance(status, str) and status in _ALLOWED_TEST_STATUSES
        for status in statuses
    ):
        raise ValueError("Worker test statuses are invalid.")

    exercise = get_exercise(job["exercise_id"])
    if compiled:
        if total_count != len(exercise.tests) or len(statuses) != total_count:
            raise ValueError("Worker result has signals for a different test count.")
        if passed_count != statuses.count("passed"):
            raise ValueError("Worker result has an inconsistent passed_count.")
    elif passed_count != 0 or total_count != 0 or statuses:
        raise ValueError("A failed compilation may not claim executed tests.")
    return dict(value)


def is_pinned_worker_image(image: str) -> bool:
    return bool(_IMAGE_ID.fullmatch(image) or _IMAGE_DIGEST.fullmatch(image))


def docker_worker_command(
    image: str,
    docker_executable: str = "docker",
    *,
    container_name: str | None = None,
) -> list[str]:
    """Build the no-volume, no-network one-job container invocation."""
    if not isinstance(image, str) or not is_pinned_worker_image(image):
        raise ValueError(
            "Worker image must be an immutable sha256 image ID or repository digest."
        )
    if container_name is not None and _SAFE_JOB_ID.fullmatch(container_name) is None:
        raise ValueError("Worker container name is invalid.")
    command = [
        docker_executable,
        "run",
        "--rm",
        "--interactive",
        "--attach=stdout",
        "--log-driver=none",
        "--pull=never",
        "--network=none",
        "--ipc=none",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--pids-limit=64",
        "--memory=256m",
        "--cpus=1.0",
        "--ulimit=nofile=64:64",
        "--tmpfs=/work:rw,nosuid,nodev,exec,size=128m,mode=700,uid=65532,gid=65532",
        "--user=65532:65532",
        "--workdir=/work",
        "--env=HOME=/nonexistent",
        "--env=TMPDIR=/work",
        "--env=TMP=/work",
        "--env=TEMP=/work",
        "--env=PYTHONDONTWRITEBYTECODE=1",
    ]
    if container_name is not None:
        command.append(f"--name={container_name}")
    command.append(image)
    return command


def _force_remove_container(docker_executable: str, container_name: str) -> None:
    try:
        subprocess.run(
            [docker_executable, "rm", "--force", container_name],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def run_docker_worker(
    job_value: object,
    *,
    image: str,
    docker_executable: str = "docker",
    timeout_seconds: float = DEFAULT_WORKER_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Run one job in a fresh hardened container and validate its bounded result."""
    job = validate_worker_job(job_value)
    if timeout_seconds <= 0 or timeout_seconds > 60:
        raise ValueError("Worker wall timeout must be between 0 and 60 seconds.")
    container_name = f"aptutor-worker-{secrets.token_hex(8)}"
    command = docker_worker_command(
        image,
        docker_executable,
        container_name=container_name,
    )
    payload = _canonical_bytes(job) + b"\n"
    if len(payload) > MAX_WORKER_JOB_BYTES:
        raise ValueError("Worker job exceeds the transport limit.")
    try:
        process = subprocess.run(
            command,
            input=payload,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=timeout_seconds,
        )
    except FileNotFoundError as exc:
        raise ValueError(f"Container runtime {docker_executable!r} was not found.") from exc
    except subprocess.TimeoutExpired as exc:
        _force_remove_container(docker_executable, container_name)
        raise ValueError("Disposable worker exceeded its outer wall timeout.") from exc
    if process.returncode != 0:
        # Container stderr is deliberately untrusted. A hostile program may try to
        # reach the worker's inherited descriptors, so never relay it into operator
        # output, logs, or the source-free receipt.
        raise ValueError("Disposable worker failed without a usable result.")
    if len(process.stdout) > MAX_WORKER_RESULT_BYTES:
        raise ValueError("Disposable worker result exceeds the transport limit.")
    try:
        result = json.loads(process.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Disposable worker returned invalid UTF-8 JSON.") from exc
    return validate_worker_result(result, job)


def write_worker_result(path: Path, result: dict[str, Any], job: dict[str, Any]) -> None:
    """Write a validated source-free receipt without creating a public-data claim."""
    validated = validate_worker_result(result, job)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(validated, indent=2) + "\n", encoding="utf-8")

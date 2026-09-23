"""Source-free adversarial acceptance probes for the disposable worker."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from ai_programming_tutor.worker_protocol import (
    WORKER_PROFILE,
    _run_bounded_process,
    create_worker_job,
    is_pinned_worker_image,
    run_docker_worker,
)


WORKER_AUDIT_SCHEMA_VERSION = "0.1"
WORKER_AUDIT_PROFILE = "dedicated-host-adversarial-v0.1"
_EXERCISE_ID = "sentinel_average"

_REFERENCE_FUNCTION = r"""
static int emit_reference_answer(void) {
    long long value = 0;
    long long sum = 0;
    long long count = 0;
    while (scanf("%lld", &value) == 1 && value != 0) {
        sum += value;
        count++;
    }
    if (count == 0) {
        puts("EMPTY");
    } else {
        printf("%.2f\n", (double)sum / count);
    }
    return 0;
}
"""


@dataclass(frozen=True)
class _Probe:
    probe_id: str
    source: str
    accepts: Callable[[dict[str, Any]], bool]


def _compilation_rejected(signals: dict[str, Any]) -> bool:
    return signals == {
        "compiled": False,
        "passed_count": 0,
        "total_count": 0,
        "test_statuses": [],
    }


def _five_wrong_answers(signals: dict[str, Any]) -> bool:
    return signals == {
        "compiled": True,
        "passed_count": 0,
        "total_count": 5,
        "test_statuses": ["wrong_answer"] * 5,
    }


def _five_bounded_failures(signals: dict[str, Any]) -> bool:
    statuses = signals.get("test_statuses")
    return (
        signals.get("compiled") is True
        and signals.get("passed_count") == 0
        and signals.get("total_count") == 5
        and isinstance(statuses, list)
        and len(statuses) == 5
        and all(status in {"runtime_error", "timeout"} for status in statuses)
    )


_PROBES = (
    _Probe(
        "compile_canary_denied",
        '#include "/opt/aptutor-private/protected_canary.h"\n'
        "#include <stdio.h>\n"
        + _REFERENCE_FUNCTION
        + "int main(void) { return emit_reference_answer(); }\n",
        _compilation_rejected,
    ),
    _Probe(
        "runtime_canary_denied",
        "#include <stdio.h>\n"
        + _REFERENCE_FUNCTION
        + r"""
int main(void) {
    FILE *stream = fopen("/opt/aptutor-private/protected_canary.h", "r");
    if (stream == NULL) {
        puts("BLOCKED");
        return 0;
    }
    fclose(stream);
    return emit_reference_answer();
}
""",
        _five_wrong_answers,
    ),
    _Probe(
        "installed_tests_denied",
        "#include <stdio.h>\n"
        + _REFERENCE_FUNCTION
        + r"""
int main(void) {
    FILE *stream = fopen(
        "/usr/local/lib/python3.12/site-packages/ai_programming_tutor/"
        "exercises/sentinel_average/tests.json",
        "r"
    );
    if (stream == NULL) {
        puts("BLOCKED");
        return 0;
    }
    fclose(stream);
    return emit_reference_answer();
}
""",
        _five_wrong_answers,
    ),
    _Probe(
        "controller_stdout_denied",
        "#include <fcntl.h>\n#include <stdio.h>\n#include <unistd.h>\n"
        + _REFERENCE_FUNCTION
        + r"""
int main(void) {
    char path[64];
    int descriptor;
    snprintf(path, sizeof path, "/proc/%ld/fd/1", (long)getppid());
    descriptor = open(path, O_WRONLY);
    if (descriptor < 0) {
        puts("BLOCKED");
        return 0;
    }
    write(descriptor, "X", 1);
    close(descriptor);
    return emit_reference_answer();
}
""",
        _five_wrong_answers,
    ),
    _Probe(
        "uid_drop_irreversible",
        "#include <stdio.h>\n#include <unistd.h>\n"
        + _REFERENCE_FUNCTION
        + r"""
int main(void) {
    if (getuid() == 65533 && getgid() == 65532 && setuid(0) != 0) {
        puts("BLOCKED");
        return 0;
    }
    return emit_reference_answer();
}
""",
        _five_wrong_answers,
    ),
    _Probe(
        "root_filesystem_read_only",
        "#include <stdio.h>\n"
        + _REFERENCE_FUNCTION
        + r"""
int main(void) {
    FILE *stream = fopen("/aptutor-adversarial-write", "w");
    if (stream == NULL) {
        puts("BLOCKED");
        return 0;
    }
    fclose(stream);
    return emit_reference_answer();
}
""",
        _five_wrong_answers,
    ),
    _Probe(
        "network_namespace_only_loopback",
        "#include <stdio.h>\n#include <string.h>\n"
        + _REFERENCE_FUNCTION
        + r"""
int main(void) {
    char line[256];
    int saw_loopback = 0;
    int unsafe = 0;
    FILE *stream = fopen("/proc/net/dev", "r");
    if (stream == NULL) {
        return emit_reference_answer();
    }
    while (fgets(line, sizeof line, stream) != NULL) {
        char *name = line;
        char *colon = strchr(line, ':');
        char *end;
        if (colon == NULL) {
            continue;
        }
        *colon = '\0';
        while (*name == ' ' || *name == '\t') {
            name++;
        }
        end = colon - 1;
        while (end >= name && (*end == ' ' || *end == '\t')) {
            *end = '\0';
            end--;
        }
        if (strcmp(name, "lo") == 0) {
            saw_loopback = 1;
        } else {
            unsafe = 1;
        }
    }
    fclose(stream);
    if (!saw_loopback || unsafe) {
        return emit_reference_answer();
    }
    puts("BLOCKED");
    return 0;
}
""",
        _five_wrong_answers,
    ),
    _Probe(
        "memory_allocation_bounded",
        "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n"
        + _REFERENCE_FUNCTION
        + r"""
int main(void) {
    void *blocks[32];
    int count = 0;
    while (count < 32) {
        blocks[count] = malloc(8U * 1024U * 1024U);
        if (blocks[count] == NULL) {
            break;
        }
        memset(blocks[count], 0xA5, 8U * 1024U * 1024U);
        count++;
    }
    if (count == 32) {
        return emit_reference_answer();
    }
    puts("BLOCKED");
    return 0;
}
""",
        _five_wrong_answers,
    ),
    _Probe(
        "process_creation_bounded",
        "#include <stdio.h>\n#include <sys/types.h>\n#include <unistd.h>\n"
        + _REFERENCE_FUNCTION
        + r"""
int main(void) {
    int children = 0;
    while (children < 128) {
        pid_t child = fork();
        if (child < 0) {
            break;
        }
        if (child == 0) {
            for (;;) {
                pause();
            }
        }
        children++;
    }
    if (children == 128) {
        return emit_reference_answer();
    }
    puts("BLOCKED");
    return 0;
}
""",
        _five_wrong_answers,
    ),
    _Probe(
        "detached_process_cleanup",
        "#define _POSIX_C_SOURCE 200809L\n"
        "#include <fcntl.h>\n#include <stdio.h>\n#include <string.h>\n"
        "#include <time.h>\n"
        "#include <unistd.h>\n"
        + _REFERENCE_FUNCTION
        + r"""
static void wait_ms(long milliseconds) {
    struct timespec delay;
    delay.tv_sec = milliseconds / 1000;
    delay.tv_nsec = (milliseconds % 1000) * 1000000L;
    while (nanosleep(&delay, &delay) != 0) {}
}

int main(void) {
    static const char marker_name[] = "aptutor-detached-survived";
    char marker[4096];
    char *separator;
    pid_t child;
    size_t prefix_length;
    if (getcwd(marker, sizeof marker) == NULL) {
        return emit_reference_answer();
    }
    separator = strrchr(marker, '/');
    if (separator == NULL) {
        return emit_reference_answer();
    }
    prefix_length = (size_t)(separator - marker) + 1U;
    if (prefix_length + sizeof marker_name > sizeof marker) {
        return emit_reference_answer();
    }
    memcpy(marker + prefix_length, marker_name, sizeof marker_name);
    wait_ms(200);
    if (access(marker, F_OK) == 0) {
        return emit_reference_answer();
    }
    child = fork();
    if (child == 0) {
        int descriptor;
        if (setsid() < 0) {
            _exit(0);
        }
        while (getppid() != 1) {
            wait_ms(1);
        }
        wait_ms(50);
        descriptor = open(marker, O_CREAT | O_WRONLY, 0600);
        if (descriptor >= 0) {
            close(descriptor);
        }
        wait_ms(2000);
        _exit(0);
    }
    puts("BLOCKED");
    return 0;
}
""",
        _five_wrong_answers,
    ),
    _Probe(
        "cpu_loop_bounded",
        "int main(void) { for (;;) {} }\n",
        _five_bounded_failures,
    ),
    _Probe(
        "stdout_flood_bounded",
        r"""#include <stdio.h>
int main(void) {
    long long index;
    for (index = 0; index < 2000000; index++) {
        putchar('A');
    }
    return 0;
}
""",
        _five_bounded_failures,
    ),
)


def _cleanup_observation(docker_executable: str) -> tuple[bool, dict[str, Any]]:
    try:
        completed = _run_bounded_process(
            [
                docker_executable,
                "ps",
                "-a",
                "--filter",
                "name=aptutor-worker-",
                "--format={{.ID}}",
            ],
            input_bytes=b"",
            max_stdout_bytes=4_096,
            timeout_seconds=5,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return False, {"outcome": "runtime_error"}
    if completed.returncode != 0 or len(completed.stdout) > 4_096:
        return False, {"outcome": "runtime_error"}
    remaining = [
        line
        for line in completed.stdout.decode("ascii", errors="ignore").splitlines()
        if line
    ]
    return not remaining, {
        "outcome": "no_remaining_containers" if not remaining else "containers_remain",
        "remaining_count": len(remaining),
    }


def run_worker_adversarial_audit(
    *,
    image: str,
    docker_executable: str = "docker",
    timeout_seconds: float = 20.0,
) -> dict[str, Any]:
    """Run authored hostile probes and return a source-free gate report."""
    if not is_pinned_worker_image(image):
        raise ValueError("Worker audit requires an immutable image ID or digest.")
    if timeout_seconds <= 0 or timeout_seconds > 60:
        raise ValueError("Worker audit timeout must be between 0 and 60 seconds.")

    checks: list[dict[str, Any]] = []
    for probe in _PROBES:
        job = create_worker_job(
            _EXERCISE_ID,
            probe.source,
            job_id=f"audit-{probe.probe_id}",
        )
        try:
            result = run_docker_worker(
                job,
                image=image,
                docker_executable=docker_executable,
                timeout_seconds=timeout_seconds,
            )
        except ValueError:
            checks.append(
                {
                    "check_id": probe.probe_id,
                    "passed": False,
                    "observation": {"outcome": "worker_error"},
                }
            )
            continue
        signals = result["signals"]
        checks.append(
            {
                "check_id": probe.probe_id,
                "passed": probe.accepts(signals),
                "observation": {"outcome": "worker_result", "signals": signals},
            }
        )

    cleanup_passed, cleanup_observation = _cleanup_observation(docker_executable)
    checks.append(
        {
            "check_id": "disposable_cleanup",
            "passed": cleanup_passed,
            "observation": cleanup_observation,
        }
    )
    return {
        "schema_version": WORKER_AUDIT_SCHEMA_VERSION,
        "audit_profile": WORKER_AUDIT_PROFILE,
        "worker_profile": WORKER_PROFILE,
        "image": image,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "limitations": [
            "software_boundary_only",
            "secret_free_host_requires_manual_attestation",
            "shared_kernel_requires_separate_host_acceptance",
        ],
    }


def write_worker_audit_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

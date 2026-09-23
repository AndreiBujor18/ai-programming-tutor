# Disposable-worker adversarial review

## Gate status

The gate is **closed** until the current image passes `aptutor audit-isolated` on
the dedicated secret-free Linux host and that host separately passes the manual
acceptance in `docs/DEDICATED_WORKER_HOST.md`. A green unit suite or Docker Desktop
run is not enough. No natural submission may be sent to the worker before both
parts are recorded.

The complete source-free audit did pass in the Windows/Docker Desktop integration
environment on 2026-09-23, including all twelve hostile probes and cleanup. That
result accepts profile-0.2 integration only; see
`docs/ACCEPTANCE_WORKER_02_WINDOWS.md`. The dedicated-host image must repeat the
entire gate rather than inherit this result.

This review uses only project-authored probes. It contains no learner source,
identity, private dataset, prediction, or human-code result.

## Assets and trust boundaries

The boundary protects five distinct assets:

1. unrelated host data and credentials;
2. the de-identified source while it is being evaluated;
3. the integrity of the authored tests and returned status signals;
4. host availability and bounded resource use;
5. source-free operational evidence and reliable cleanup.

The trusted components are the dedicated host operator, host-side CLI, pinned
worker image, Python controller, Docker daemon, and authored catalog. The C
preprocessor/compiler and compiled submission are treated as untrusted. Docker,
the host kernel, and the built image remain part of the trusted computing base;
this project does not claim otherwise.

## Findings and treatment

| ID | Finding | Evidence | Treatment | Residual status |
| --- | --- | --- | --- | --- |
| A-01 | The protocol-0.1 image ran the controller, compiler, and submission as UID 65532. A submitted program could read controller-visible exercise files and open the controller's stdout through `/proc`. | Reproduced locally with authored C probes before the v0.2 hardening. | Profile `docker-disposable-v0.2` uses a trusted UID 0 controller inside a required rootless/user-remapped container, runs GCC and the program with real/effective/saved UID 65533, makes the installed package and canary controller-only, and retains only `CAP_SETUID` for the transition plus `CAP_KILL` for namespace cleanup. The controller fails startup unless capability sets, PID identity, `NoNewPrivs`, and seccomp exactly match this boundary; changing all UIDs to a nonzero value clears capabilities. | Must pass startup plus the compile/runtime canary, installed-tests, parent-descriptor, and irreversible-UID probes in the actual image. |
| A-02 | Host `subprocess.run(..., stdout=PIPE)` checked the 64 KiB limit only after buffering all container output. A corrupted worker could exhaust host memory. | Confirmed by code review. | A cross-platform bounded pump now retains at most 64 KiB plus one proof byte and closes the pipe immediately after that. | Unit-tested; must also survive the parent-descriptor and flood probes on the dedicated host. |
| A-03 | A container still shares the host kernel. Docker flags are defense in depth, not a formally verified sandbox. | Architectural fact. | Use only a dedicated host with no unrelated secrets, a rootless or user-namespace-separated daemon, active seccomp plus an LSM, host quotas, and no natural data until acceptance. | Accepted risk only for a small de-identified pilot after host review; not suitable for anonymous public execution. |
| A-04 | A mutable base tag and Debian package repositories affect rebuilds even though runtime uses an immutable image ID/digest. | Dockerfile review. | Record public commit, build date, final image digest, base image resolution, compiler, kernel, and runtime versions in the private operations record. Never run a mutable tag. | Builds are not bit-for-bit reproducible yet. |
| A-05 | `--rm` covers normal completion, while a host/runtime crash may leave a stopped or running container. | Runtime lifecycle review. | Inspect the dedicated prefix before and after a batch and after reboot; treat any remaining container as a failed gate and reimage after an incident. | Requires operational acceptance; the repository cannot prove recovery from host loss. |
| A-06 | CPU, process, memory, disk, and output exhaustion can deny service. | Threat model plus authored loop/flood probes. | Container cgroup limits, runner limits, outer timeout, bounded host capture, single-job containers, bounded queue, and disposable host storage. | Kernel/runtime bugs and aggregate multi-job pressure remain host concerns. |
| A-07 | Unexpected network or mounts could expose services or data. | Docker-command regression. | `--network=none`, no volume/device/socket mounts, private IPC, read-only root, bounded tmpfs, minimal environment, and explicit built-in seccomp. | Host firewall and cloud-metadata isolation still require manual verification. |
| A-08 | Diagnostics, command lines, daemon logs, swap, or crash dumps could retain source. | Data-flow review. | Source travels over stdin, container logging is disabled, stderr is discarded, the result schema is source-free, host source files live only on encrypted or RAM-backed disposable storage, and core dumps are disabled. | The operator must verify host logging, swap, backup, and retention configuration. |
| A-09 | A child that called `setsid()` could leave the original process group and survive into a later hidden test. | Found during final process-lifecycle review and reproduced locally: the first test failed while the next four observed state left by the detached child. | The controller must be PID 1 in Docker's default isolated process tree, retains only the additional `CAP_KILL`, sends `SIGKILL` to every other namespace process, and reaps all children between invocations. Cleanup failure aborts the worker. | Must pass the detached-process probe in the actual image; kernel/runtime isolation remains part of the trusted base. |

## Automated adversarial profile

Build the public image, resolve its immutable ID, and run:

```bash
export PYTHONPATH=src
worker_image="$(docker image inspect aptutor-worker:0.2 --format '{{.Id}}')"
python -m ai_programming_tutor.cli audit-isolated \
  --image "$worker_image" \
  --output private_evaluation/worker_adversarial_report.json
```

The command runs these source-free checks:

| Check | Required observation |
| --- | --- |
| `compile_canary_denied` | The untrusted compiler cannot include the controller-only header. |
| `runtime_canary_denied` | The program cannot open the controller-only header. |
| `installed_tests_denied` | The program cannot open the installed exercise test file. |
| `controller_stdout_denied` | The program cannot open the controller's stdout descriptor through `/proc`. |
| `uid_drop_irreversible` | The program runs as UID 65533 and cannot regain controller UID 0. |
| `root_filesystem_read_only` | An absolute write outside the disposable workspace fails. |
| `network_namespace_only_loopback` | The worker network namespace exposes no interface except loopback. |
| `memory_allocation_bounded` | The program cannot allocate and touch memory beyond the configured bound. |
| `process_creation_bounded` | Forking stops below the probe threshold and ordinary descendants are terminated with the test process group. |
| `detached_process_cleanup` | A child that starts a new session cannot persist into the next authored test. |
| `cpu_loop_bounded` | Every authored test terminates as a bounded runtime failure or timeout. |
| `stdout_flood_bounded` | Every authored test terminates without flooding the host transport. |
| `disposable_cleanup` | No container with the dedicated worker prefix remains. |

One failed or unavailable check closes the entire gate. The report intentionally
does not contain probe source, compiler text, program output, host paths, learner
data, or a claim that the host is secret-free.

## Residual limitations

- The audit does not prove the absence of kernel, Docker, compiler, or Python
  vulnerabilities.
- The default Docker seccomp profile and host LSM are broader than a future
  purpose-built syscall policy.
- The test catalog is public, so this boundary prevents runtime inspection and
  signal manipulation; it is not a claim that the authored cases are secret from
  a motivated participant.
- The v0.2 profile is still a shared-kernel design. A stronger future boundary may
  use gVisor, a microVM, or a separately reviewed executor, but changing runtimes
  requires repeating this gate rather than inheriting its result.
- Availability under concurrent load, queue abuse, physical compromise, and
  disclosure review of a future aggregate report are separate acceptances.

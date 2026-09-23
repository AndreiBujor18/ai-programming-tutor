# Disposable worker reference — schema 0.1, profile 0.2

## Purpose and claim boundary

This slice supplies a strict job/result protocol and a one-container-per-submission
reference path for producing the precomputed signals required by the private
natural-code evaluation. It sends source through standard input, mounts no host
directory, exposes no network, and returns only source-free test statuses bound to
the exact source, exercise revision, and test-suite revision.

Profile `docker-disposable-v0.2` separates a trusted UID 0 controller inside the
container's user namespace from GCC and every submitted program (UID 65533). Both
use only the dedicated workspace group 65532; no untrusted process keeps GID 0.
The installed exercise package and a startup canary are readable only by the
controller. It retains only `CAP_SETUID` for that irreversible transition and
`CAP_KILL` to clear every other process from its private PID namespace between
tests; changing all IDs to a nonzero UID clears capabilities before the untrusted
executable starts, and `no-new-privileges` remains inherited. Host stdout is
captured with a live 64 KiB bound rather than buffered without limit. A
dedicated host must therefore use rootless Docker or reviewed user-namespace
remapping; rootful UID 0 mapping is outside the accepted topology.

The image's default `USER` remains UID 65532 and cannot read the protected package,
so a bare or mutable-tag `docker run` fails closed. Only the reviewed host command
overrides the controller to UID 0 while simultaneously dropping every capability
except `KILL` and `SETUID` and enabling the remaining isolation flags.
At startup the controller reads `/proc/self/status` and fails closed unless its
inheritable/ambient sets are empty, permitted/effective/bounding sets contain only
`KILL` and `SETUID`, it is PID 1, `NoNewPrivs` is active, and seccomp filter mode is
active.

This is a reviewable reference boundary, not a claim that Docker alone is a formally
verified sandbox. Before collecting real submissions, the operator must use a
dedicated worker host with no secrets, pin the built image by digest, retain the
runtime's default seccomp confinement or a stricter tested profile, apply host-level
quotas, and complete adversarial review. Do not run the worker on a developer machine
that contains sensitive mounts or privileged Docker configuration.

## Protocol

The host creates one schema-0.1 job containing:

- a random non-identifying job ID;
- `c17` as the only dialect;
- the current exercise and test-suite fingerprints;
- the exact source SHA-256 and bounded source text.

Participant keys, sample IDs, names, consent records, and labels are deliberately
absent. The container validates every field and fingerprint, runs the existing five
authored tests, and emits only:

- the job/source/exercise/test bindings;
- compilation success;
- passed and total counts;
- the ordered bounded status list.

Compiler text, stdout/stderr, expected/actual values, filenames, source, individual
diagnoses, and labels are not emitted. A result with `compiled=false` has no executed
test signals and remains outside the first natural-code metric.

## Build and pin the image

Build locally from the public tree:

```powershell
docker build --file worker/Dockerfile --tag aptutor-worker:0.2 .
$WorkerImage = docker image inspect aptutor-worker:0.2 --format '{{.Id}}'
```

`$WorkerImage` is an immutable local `sha256:...` image ID. A remote deployment
should use a registry reference pinned as `repository@sha256:...`, not a mutable tag.
The Python base tag and Debian packages are inputs to the build; the resulting image
digest, compiler identity, Docker/host versions, and build date belong in the private
pilot operations record.

## Run one submission

The source stays in the private collection area. The result contains no source:

```powershell
$env:PYTHONPATH = "src"
python -m ai_programming_tutor.cli run-isolated sentinel_average `
  private_evaluation\submission.c `
  --image $WorkerImage `
  --output private_evaluation\worker_result.json
```

The command always creates a fresh container with:

- `--network=none`, no volumes, and `--pull=never`;
- private IPC and PID namespaces, stdout-only attachment, and disabled container
  logging;
- a read-only root filesystem and one bounded executable tmpfs;
- a namespace-root UID 0 controller, UID 65533 untrusted compiler/program, and
  dedicated shared workspace GID 65532;
- every capability dropped except controller-only `KILL` and `SETUID`, explicit
  built-in seccomp, and `no-new-privileges`;
- whole-PID-namespace termination and reaping between compiler/test invocations,
  including descendants that detach from the original process group;
- CPU, memory, PID, file-descriptor, runner, and outer wall-time bounds.

The host never relays container stderr and validates the returned schema and every
job binding before writing the receipt. A completed command does not by itself prove
informed consent, de-identification, label independence, host isolation, or
statistical sufficiency.

## Local integration acceptance

The focused Windows/Docker Desktop protocol for profile 0.1 passed on 2026-09-23: the authored
reference returned 5/5, the authored incomplete starter returned five bounded
`wrong_answer` statuses, no worker container remained, and Git stayed clean after
both ignored receipts were written. See `docs/ACCEPTANCE_WORKER_01_WINDOWS.md`.

That historical pass does not accept the changed profile 0.2 image. Rebuild it and
repeat the reference/starter checks, then run the authored adversarial gate:

```powershell
python -m ai_programming_tutor.cli audit-isolated `
  --image $WorkerImage `
  --output private_evaluation\worker_adversarial_report.json
```

See `docs/WORKER_ADVERSARIAL_REVIEW.md` and
`docs/DEDICATED_WORKER_HOST.md`. Dedicated-host acceptance remains open before any
real submission is collected.

## Pilot handoff

Only after manual de-identification and independent labeling should the operator
merge the receipt's `signals` into the private natural-code record described by
`docs/NATURAL_CODE_EVALUATION.md`. Keep the consent/withdrawal ledger separate. If a
source is changed for de-identification, discard the old receipt and rerun it so the
SHA-256 and frozen fingerprints continue to match.

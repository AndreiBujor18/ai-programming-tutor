# Disposable worker reference — protocol 0.1

## Purpose and claim boundary

This slice supplies a strict job/result protocol and a one-container-per-submission
reference path for producing the precomputed signals required by the private
natural-code evaluation. It sends source through standard input, mounts no host
directory, exposes no network, and returns only source-free test statuses bound to
the exact source, exercise revision, and test-suite revision.

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
docker build --file worker/Dockerfile --tag aptutor-worker:0.1 .
$WorkerImage = docker image inspect aptutor-worker:0.1 --format '{{.Id}}'
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
- a private IPC namespace, stdout-only attachment, and disabled container logging;
- a read-only root filesystem and one bounded executable tmpfs;
- non-root UID/GID 65532;
- all Linux capabilities dropped and `no-new-privileges` enabled;
- CPU, memory, PID, file-descriptor, runner, and outer wall-time bounds.

The host never relays container stderr and validates the returned schema and every
job binding before writing the receipt. A completed command does not by itself prove
informed consent, de-identification, label independence, host isolation, or
statistical sufficiency.

## Pilot handoff

Only after manual de-identification and independent labeling should the operator
merge the receipt's `signals` into the private natural-code record described by
`docs/NATURAL_CODE_EVALUATION.md`. Keep the consent/withdrawal ledger separate. If a
source is changed for de-identification, discard the old receipt and rerun it so the
SHA-256 and frozen fingerprints continue to match.

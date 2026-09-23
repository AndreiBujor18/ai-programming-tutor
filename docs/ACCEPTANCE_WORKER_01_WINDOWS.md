# Disposable worker local Windows integration acceptance

Date: 2026-09-23

> Historical scope: this record accepts `docker-disposable-v0.1` only. The current
> unreleased profile 0.2 changes the UID/capability and host-capture boundary and
> therefore required a fresh image build, reference/starter rerun, and adversarial
> pass. This record must not be cited as profile-0.2 or dedicated-host acceptance.
> That fresh local integration pass is recorded separately in
> `docs/ACCEPTANCE_WORKER_02_WINDOWS.md`.

This record covers the focused Windows/Docker Desktop integration pass for the
schema-0.1 disposable worker. It contains only public-safe outcomes. No learner
source, private submission, job identifier, source fingerprint, local path, or
participant information is included.

## Scope

The accepted slice builds the reference Linux worker image, invokes it by an
immutable local image ID, transfers one strict C17 job through standard input, and
accepts only a source-free result bound to the exact job, source, exercise, and test
suite. The invocation uses no network or host volume, a read-only root filesystem,
a bounded executable tmpfs, non-root execution, dropped capabilities, disabled
container logging, and outer-timeout cleanup.

## Environment

- Windows build 10.0.26200.9457;
- WSL 2.6.3 with Linux kernel 6.6.87.2-1;
- Docker Desktop 4.92.0 using the `desktop-linux` context;
- Docker Engine 29.8.0, Linux/amd64, non-experimental mode.

The exact local image ID and build-input identities are intentionally not treated as
a reusable pilot record. A real pilot must capture its own immutable image,
compiler, runtime, host, and build-date evidence under access control.

## Automated prerequisite

The complete development tree passed 85/85 automated tests on Linux. The same tree
completed all 85 discovered tests on Windows with 81 passes and four expected skips:
one optional ML-dependency test and three POSIX-specific resource/symbolic-link
checks. All nine worker contract and execution regressions passed on Windows.

## Manual protocol and outcome

The Windows/Docker Desktop workflow passed all of the following checks:

1. The reference Dockerfile built all 13 steps successfully and produced a local
   image addressable by an immutable `sha256:` ID.
2. Running the authored `sentinel_average` reference through `run-isolated` compiled
   successfully and returned five ordered `passed` statuses (5/5).
3. Running the authored incomplete starter through the same path compiled
   successfully and returned five ordered `wrong_answer` statuses (0/5).
4. Both receipts used schema 0.1 and contained only the documented fingerprints,
   bindings, compilation flag, counts, and ordered statuses. They contained no
   source, compiler text, stdout/stderr, expected/actual values, or diagnosis.
5. Listing containers by the worker-name prefix after both runs returned no entry,
   confirming removal of the disposable containers on the completed paths.
6. Git remained clean after writing both receipts under the ignored private
   evaluation directory.

## Accepted boundary

This pass accepts local integration of the protocol, image build, success/failure
signals, source-free receipt, cleanup, and ignored-output path. It does not establish
hostile-code resistance, prove the runtime's isolation properties, accept a
dedicated secret-free worker host, or authorize collection of real submissions.

Before a consented pilot, the project still requires a dedicated host, immutable
image and compiler/runtime recording, host-level quotas and monitoring, adversarial
review, and a tested incident path. Consent, withdrawal, de-identification,
independent labeling, and frozen-set requirements remain unchanged.

## Result

The disposable worker's first local Windows/Docker Desktop integration pass is
accepted. The next gate is dedicated-host and adversarial acceptance, not natural
submission collection or a human-code accuracy claim.

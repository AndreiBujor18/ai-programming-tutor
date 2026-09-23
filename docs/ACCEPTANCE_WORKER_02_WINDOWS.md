# Hardened worker local Windows integration acceptance

Date: 2026-09-23

> Scope: this record accepts the local Windows/Docker Desktop integration of
> `docker-disposable-v0.2` and its project-authored adversarial gate. It does not
> accept a dedicated host, authorize natural-code collection, or establish a
> production-sandbox claim.

This record contains only public-safe outcomes. No learner source, private
submission, job identifier, source fingerprint, local path, participant
information, or individual prediction is included.

## Tree and environment

The tested local tree applied the following untagged commits over public checkpoint
`4e648e2`:

- `ea3cdb3` — **Harden worker and add adversarial gate**;
- `61c08da` — **Fix Docker PID namespace compatibility**.

The package and latest release tag remain at `0.11.0`.

The integration environment was:

- Windows build 10.0.26200.9457;
- WSL 2.6.3 with Linux kernel 6.6.87.2-1;
- Docker Desktop 4.92.0 using the `desktop-linux` context;
- Docker client and server 29.8.0, API 1.56, Linux/amd64 server;
- local worker image ID
  `sha256:635f64b1f068540d9c58567a7682726a27acfed284e4ba667e90d444323055d1`.

The image ID identifies only this public-input integration build. The future
dedicated-host build must record its own image digest, base-image resolution,
compiler/runtime versions, host configuration, and build time in the private
operations record.

## Automated prerequisite

The complete hardened development tree passed 96/96 automated tests in the Linux
patch-preparation environment. The tests cover the strict protocol, immutable image
selection, split controller/submission identity, bounded source and result
transport, PID-namespace cleanup, failure cleanup, gate aggregation, and source-free
reporting. The installable wheel also contains all worker and audit modules.

## Compatibility correction

The first Docker Desktop build completed, but its audit stopped before controller
startup because Docker Engine 29.8 rejected the redundant explicit value
`--pid=private`. Every unavailable hostile probe was reported as `worker_error`, the
gate remained closed, and the residual-container cleanup check still passed.

The compatibility commit removed only that rejected flag. Docker's default isolated
process tree remains in use, and the controller still fails closed unless it is PID
1. A fresh image was then built and the complete audit and smoke protocol were run
again; no result from the failed attempt was treated as acceptance evidence.

## Adversarial protocol and outcome

`aptutor audit-isolated` returned `passed: true`, schema 0.1, audit profile
`dedicated-host-adversarial-v0.1`, and worker profile
`docker-disposable-v0.2`. All twelve hostile-code probes plus cleanup passed:

- controller canary access denied during compilation and execution;
- installed authored tests and controller stdout denied to submitted code;
- UID drop irreversible and root filesystem read-only;
- network namespace limited to loopback;
- memory allocation, process creation, CPU loop, and stdout flood bounded;
- detached descendants removed between test cases;
- no container with the worker prefix remained.

The report contained only source-free check names, statuses, profiles, aggregate
pass state, and documented limitations.

## Reference and starter smoke checks

After the green audit, both authored smoke inputs were run through the same immutable
image ID:

1. The `sentinel_average` reference compiled and returned five ordered `passed`
   statuses (5/5).
2. The incomplete starter compiled and returned five ordered `wrong_answer`
   statuses (0/5).
3. Both receipts used schema 0.1 and worker profile
   `docker-disposable-v0.2`; they exposed no source, compiler text, stdout/stderr,
   expected/actual values, or diagnosis.
4. Listing containers by the worker prefix returned no entry after the runs.
5. Git remained clean after the ignored private-evaluation receipts were written.

## Accepted boundary

This pass accepts the profile-0.2 image build and command compatibility on the stated
Windows/Docker Desktop environment, controller startup checks, all authored hostile
probes, reference/starter behavior, source-free receipts, and completed-path cleanup.

Docker Desktop/WSL is an integration environment, not the required secret-free
worker host. This pass does not attest rootless Docker or reviewed user-namespace
remapping, an enforcing host LSM, cgroup and host-level monitoring, absent
credentials or unrelated data, offline network policy, encrypted/RAM-backed inbox
handling, post-reboot cleanup, or the incident path. The shared-kernel and
software-only limitations remain.

## Result and next gate

Local profile-0.2 integration and the authored adversarial audit are accepted. The
overall natural-code gate remains **closed** until a freshly prepared dedicated
Linux host passes every item in `docs/DEDICATED_WORKER_HOST.md`, including a rebuild
and repeat of the same unit, smoke, adversarial, residual-container, and simulated-
failure checks. No natural submission may be processed before that separate record
exists.

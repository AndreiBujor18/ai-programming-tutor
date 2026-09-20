# Code execution security

## Current boundary

`CRunner` is a development runner. It uses a temporary directory, direct argument
lists rather than a shell, source and output caps, process-group termination, and
Unix CPU, address-space, file-size, and core-dump limits. Evaluated programs also
receive a process-count cap. GCC does not receive that cap because `RLIMIT_NPROC`
counts every process owned by the real user and can block the compiler's helper
processes on a shared host; compilation remains bounded by the other resource
limits and a wall-clock timeout. These controls reduce accidental damage and make
automated tests predictable.

The v0.8.0 runner adds file-aware tests without accepting learner file
uploads. Fixtures and expected file contents are project-authored text only. Their
schema allows portable flat filenames, at most eight combined entries per test,
32,000 UTF-8 bytes per entry, and 64,000 bytes across the complete file contract.
The runner reserves its stdout/stderr capture names, creates a new disposable
working directory for each test, writes only that test's fixtures, and deletes the
directory before continuing.

Expected outputs are read up to the runner's output cap. The checker compares
`lstat` and `fstat` metadata, accepts regular files only, and opens with
`O_NOFOLLOW` where the operating system provides it. Missing, unreadable,
non-regular, oversized, invalid-UTF-8, and wrong outputs are returned as structured
file results. Hidden file names and contents are redacted from learner-facing
serialization. On POSIX, the runner also terminates the process group after each
test so descendants do not keep writing after their parent exits. The Windows
prototype cannot guarantee equivalent descendant-tree cleanup without a job-object
worker, reinforcing the trusted-local boundary.

The v0.8.0 dependency-free demo binds only to `127.0.0.1`, checks the Host and Origin
for local requests, and requires `--enable-local-execution` to run user source.
The optional FastAPI runner endpoint requires both a loopback client and explicit
`APTUTOR_ENABLE_LOCAL_EXECUTION=1`; launch it with `--host 127.0.0.1`. Neither
setting should be combined with port forwarding, reverse proxies, or a public
deployment. The current browser workflow compiles classic C17 only.

The unreleased enhanced editor is built into the Python package and loads no
remote scripts, styles, workers, or language services. Its generated style element
receives a fresh per-page CSP nonce, so the policy does not need `unsafe-inline`.
The dependency lockfile and committed bundle are checked together in CI, and the
plain textarea remains available if the enhancement cannot initialize.

Compiler and learner processes receive a deliberately small environment. On all
platforms, `TMP`, `TEMP`, and `TMPDIR` point to the disposable evaluation directory.
On Windows, only the current toolchain `PATH` and required system process locations
are additionally retained; arbitrary parent-environment values are not forwarded.
Unix resource limits are unavailable in the Windows prototype, which is another
reason it remains restricted to trusted localhost testing.

They do not form a sufficient sandbox against a hostile submission. In particular,
the process still shares the host kernel and may be able to read resources visible
to the API account. The runner must not be exposed directly to anonymous users.

## Required public architecture

The API should enqueue an immutable submission and receive only a structured result
from a dedicated execution worker. Each job must use a fresh container or stronger
sandbox with:

- no network namespace access;
- read-only base filesystem and a small disposable writable directory;
- non-root user and no host mounts or secrets;
- dropped Linux capabilities and a strict seccomp/AppArmor profile;
- hard CPU, wall-clock, memory, process, disk, and output quotas;
- pinned compiler image and dependency inventory;
- bounded queue, rate limits, audit events, and automatic cleanup.

Judge0, nsjail, gVisor, or a purpose-built isolated worker are candidates to
evaluate. The choice requires adversarial testing before deployment.

## Data handling

Submission source may contain personal information. The local demo does not persist
submitted source on the server. Browser drafts live in memory by default; an explicit
device-local option may place raw drafts in localStorage, separated by profile and
exercise. Restoring a starter deletes that draft, and disabling the option deletes all
persistent drafts. The style profile remains separate and contains only bounded
aggregate preferences/evidence origins—never raw source, identifiers, or comments.
Authored alias maps—not learner names—produce short or Romanian identifiers before a
learned `snake_case`/`camelCase` transformation. HTTP response bodies containing test
feedback, learned preferences, or reference code use `Cache-Control: no-store`. A future persistence
layer should use random attempt identifiers, avoid raw source in logs by default,
encrypt retained code, apply retention limits, and require explicit consent before
using any submission for model training.

The v0.7.0 local-progress feature keeps favorites separately for each profile.
Its attempt history is off by default and stores only a timestamp, compilation
status, and passed/total test counts, bounded to the latest 20 attempts per exercise.
It never stores submitted source, compiler output, diagnoses, hints, or learned
style evidence. Turning history off deletes its numeric attempts immediately;
clearing progress deletes both attempts and favorites for the active profile.
The concept/exercise breakdown is calculated in browser memory from this sanitized
state and public exercise tags; it does not add fields, identifiers, or another
storage location. A displayed solved count means only that every local test passed
at least once, not that the system inferred learner mastery.

Progress JSON transfer is limited to the active profile's favorites, history
setting, and sanitized numeric attempts. The browser caps input at 100,000 bytes
and requires an exact format/version and exact object keys. It rejects unknown
exercise IDs, duplicate favorites, out-of-range results, timestamps more than 24
hours in the future, more than 20 attempts per exercise, and any extra field such
as source or compiler output.
A valid import still requires confirmation before replacing the active profile;
it cannot alter drafts, style profiles, exam state, or the other profile.

The practice-exam session persists only its exam identifier, timer origin, active
task, and numeric best-attempt results in browser storage. It does not duplicate the
editor source. Draft persistence remains a separate, off-by-default learner choice.

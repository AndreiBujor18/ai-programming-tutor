# Dedicated secret-free worker host

## Meaning of “secret-free”

The host inevitably receives one de-identified source program in memory while it
runs a job. “Secret-free” means that an escape from the worker finds no unrelated
credentials, personal files, private course material, consent ledger, identity
mapping, model artifact, other submissions, cloud role, SSH private key, browser
profile, password store, mounted share, or developer workspace.

This document is a deployment and acceptance runbook, not evidence that a host has
already passed it. Docker Desktop/WSL on the development PC and GitHub Actions are
integration environments only. The dedicated-host gate remains closed until a
separate Linux machine or disposable VM is selected, prepared, and recorded.

## Required topology

- Start from a freshly installed or freshly reimaged Linux host used only for this
  worker. Do not dual-purpose a developer machine.
- Use a dedicated unprivileged operator account. Prefer rootless Docker; an
  explicitly reviewed user-namespace-remapped daemon is the fallback. Never expose
  the Docker API over TCP and never mount its socket into a worker.
- Profile 0.2 intentionally starts its trusted controller as UID 0 and PID 1 inside
  private user/PID namespaces, with only `CAP_SETUID` and `CAP_KILL`, then runs GCC
  and submitted code as UID 65533. Controller and child processes use dedicated
  workspace GID 65532 rather than GID 0. `CAP_KILL` exists only so the controller
  can remove detached descendants between tests. A rootful daemon without user-
  namespace remapping is therefore a blocking host configuration, even if the
  software probes pass.
- Require cgroup v2, Docker's built-in seccomp profile, and an enforcing host LSM
  such as AppArmor or SELinux. Do not use `seccomp=unconfined`, `--privileged`, host
  networking, host PID/IPC namespaces, devices, or host volumes.
- Default-deny inbound traffic. Use local console access or an authorized public
  SSH key without agent forwarding; the private key remains off-host. Disable SSH
  during an offline evaluation batch when practical.
- Allow outbound traffic only during OS update and public-image build/transfer.
  Evaluation mode has no general outbound route. A cloud VM must have no instance
  role/service account, no secret user-data, and no reachable metadata credential
  endpoint.
- Disable unencrypted swap, crash dumps, telemetry that records process content,
  shell history for data commands, automated backups, indexing, and cloud sync.
  Use encrypted ephemeral storage or a RAM-backed inbox for the de-identified source.
- Keep the consent/withdrawal ledger, identity mapping, raw collection area,
  labeling notes, other submissions, and aggregate evaluator on a different trusted
  system. Transfer only one manually de-identified C file into the worker inbox.

## Automated non-mutating preflight

After installing the public tree and rootless Docker, but before building or
processing any natural source, run:

```bash
export PYTHONPATH=src
python -m ai_programming_tutor.cli inspect-host \
  --output private_evaluation/host_preflight.json
```

The command performs bounded read-only inspection and writes schema 0.1 profile
`dedicated-worker-host-preflight-v0.1`. It reports only allowlisted OS/runtime
versions and categorical outcomes—never hostname, username, IP/MAC address, Docker
endpoint path, local filesystem path, or raw command error.

Its 17 automated checks cover Linux/x86-64, a non-root operator, cgroup v2 with the
`cpu`, `memory`, and `pids` controllers, running systemd, an active host LSM, an
inaccessible rootful Docker socket, and a local rootless Docker daemon with matching
architecture, cgroup-v2/systemd delegation, built-in seccomp, and LSM integration.
The first automated profile covers the recommended rootless topology only. A
user-namespace-remapped rootful fallback remains blocked unless separately reviewed
and explicitly implemented.

Exit zero and `status: automated_ready` mean only that every automated check passed.
Every manual requirement deliberately remains `not_attested`; the command cannot
prove that a host was reimaged, contains no secrets, has safe retention/network
configuration, or passed the later build, audit, reboot, and incident checks. A
blocked result must be fixed and rerun without natural data.

Copy `docs/DEDICATED_HOST_OPERATIONS_TEMPLATE.md` outside Git for the private
operations record. Never complete that template inside the repository.

## Two operating phases

### 1. Public build and verification

No natural source is present in this phase.

1. Patch and reboot the clean host.
2. Obtain the public repository tree without credentials and verify the intended
   public commit.
3. Run `aptutor inspect-host`; require `automated_ready` and review the still-open
   manual requirements without treating the report as host acceptance.
4. Build the image and immediately resolve its immutable image ID or repository
   digest:

   ```bash
   docker build --file worker/Dockerfile --tag aptutor-worker:0.2 .
   worker_image="$(docker image inspect aptutor-worker:0.2 --format '{{.Id}}')"
   printf '%s\n' "$worker_image"
   ```

5. Record privately: public Git commit, build UTC time, resolved base image,
   immutable worker digest, GCC/Python versions, Linux kernel, Docker client/server,
   cgroup version, security options, LSM state, and whether the daemon is rootless
   or user-namespace-remapped. Do not record hostname, IP, usernames, paths, tokens,
   or source.
6. Run the full unit suite, reference/starter smoke checks, and the adversarial
   command in `docs/WORKER_ADVERSARIAL_REVIEW.md`.
7. Confirm that the adversarial report says `passed: true`, its
   `worker_profile` is `docker-disposable-v0.2`, and no worker container remains.

### 2. Offline evaluation

1. Remove build-time network access or enforce the documented outbound deny rule.
2. Confirm the inbox is empty, RAM-backed or encrypted, excluded from backup, and
   contains no earlier submission.
3. Transfer one manually de-identified, consented C17 source under a random generic
   filename. Do not transfer the consent record or participant key.
4. Invoke the pinned digest, never the tag. Keep the source path and all data out of
   shell history and command-line metadata; source itself is sent to the container
   only over stdin by `run-isolated`.
5. Copy back only the validated source-free receipt. Verify its source hash against
   the de-identified file on the trusted collection system before merging signals.
6. Delete the inbox entry, inspect the worker prefix for remaining containers, and
   clear the disposable inbox before the next job.

## Acceptance checklist

Every item is blocking:

- [ ] The host is dedicated/reimaged and contains none of the excluded data or
  credentials above.
- [ ] Rootless Docker or reviewed user-namespace remapping is active; the rootful
  system daemon/socket is disabled or inaccessible to the operator workflow.
- [ ] The source-free host preflight reports `automated_ready` with 17/17 checks,
  while every manual requirement remains separately attested below.
- [ ] cgroup v2, built-in seccomp, and an enforcing LSM are recorded.
- [ ] No cloud role, metadata credential, secret user-data, agent forwarding,
  remote Docker API, host mount, or unrelated network route is available.
- [ ] Swap, dumps, logs, backups, telemetry, and inbox retention satisfy the
  source-handling rules.
- [ ] The image is built from the intended public commit and invoked only by its
  immutable ID/digest; compiler/runtime/build evidence is recorded privately.
- [ ] All project tests and the reference/starter smoke checks pass.
- [ ] All twelve hostile-code probes plus the cleanup check pass and their report
  remains source-free.
- [ ] Pre-run, post-run, and post-reboot inspections show no remaining worker
  container or persistent job workspace.
- [ ] A simulated failure/timeout produces no container stderr in operator output,
  no raw source in logs, a failed job rather than a partial receipt, and successful
  cleanup.
- [ ] The operations record names the reviewer and date but stays outside Git; the
  public repository records only a sanitized acceptance summary.

## Incident rule

Stop the batch on any failed check, unexpected interface, residual container,
runtime update, digest change, LSM/seccomp warning, source-bearing log, or cleanup
failure. Do not “retry until green” on real data. Isolate and reimage the host,
invalidate the affected receipts, review only source-free operational evidence,
rebuild a new digest, and repeat the complete public-probe gate before resuming.

## What acceptance authorizes

Passing this runbook authorizes only the already defined small, de-identified,
consented, independently labeled pilot. It does not authorize anonymous/public code
execution, storage of raw submissions, publication of per-sample results, reuse for
training, a production sandbox claim, or a human-code accuracy claim.

# Dedicated worker host operations record template

> Copy this template into the access-controlled operations area and complete it
> there. A filled record must never be committed to Git. The repository may receive
> only a separately reviewed, sanitized acceptance summary.

This template records the evidence required by `docs/DEDICATED_WORKER_HOST.md`
without mixing identities, consent records, source code, or host identifiers into
the public project.

Do not enter a hostname, IP or MAC address, local username, filesystem path, SSH key,
token, participant key, sample/job ID, learner source, or per-sample result. The
reviewer identity may be retained in the private record when governance requires it;
use a role or internal reference in any sanitized derivative.

## 1. Review scope

- Review date and time (UTC):
- Reviewer/reference (private record only):
- Decision: `blocked` / `accepted_for_defined_pilot`
- Public repository commit (full SHA):
- Worker profile: `docker-disposable-v0.2`
- Preflight profile: `dedicated-worker-host-preflight-v0.1`
- Preflight report SHA-256:

## 2. Non-identifying environment evidence

- Maintained OS ID and version:
- Linux kernel version:
- Architecture:
- systemd version:
- Docker client/server version:
- Rootless Docker confirmed: yes / no
- cgroup version and driver:
- Required `cpu`, `memory`, and `pids` controllers present: yes / no
- Docker built-in seccomp active: yes / no
- Enforcing host/Docker LSM mechanism:
- Rootful daemon/socket disabled or inaccessible: yes / no

## 3. Automated preflight

- [ ] `aptutor inspect-host` returned `status: automated_ready`.
- [ ] All 17 automated checks passed.
- [ ] The report contains no hostname, username, network address, local path, token,
      source, or participant/sample/job identifier.
- [ ] Every `manual_requirements` entry still says `not_attested`; none was inferred
      from the automated result.

Preflight does not accept the host. Complete every manual item below independently.

## 4. Manual host attestations

- [ ] The machine was freshly reimaged and is dedicated to this worker.
- [ ] It contains no unrelated credential, personal file, private teaching material,
      consent/identity mapping, other submission, developer workspace, browser
      profile, mounted share, cloud role, or secret user-data.
- [ ] The OS is maintained, all security updates and current Intel/CPU microcode are
      installed, and the storage, cooling, power, and sleep behavior are stable for
      an unattended evaluation.
- [ ] Inbound traffic is default-denied; no remote Docker API or SSH agent forwarding
      is available.
- [ ] General outbound access is removed for the offline evaluation phase, including
      access to any cloud metadata credential endpoint.
- [ ] Swap, crash dumps, logs, telemetry, indexing, backups, and cloud sync satisfy
      the source-retention policy.
- [ ] The one-file inbox is RAM-backed or encrypted, excluded from backup, and empty
      before and after every job.
- [ ] The consent ledger, identity mapping, labeling records, collection system, and
      aggregate evaluator stay on a separate trusted system.

## 5. Immutable build evidence

- Build date and time (UTC):
- Resolved public base-image digest:
- Final immutable worker image ID/digest:
- Python version:
- GCC version:
- Build completed from the recorded public commit: yes / no
- Runtime used only the immutable ID/digest, never a mutable tag: yes / no

Changing the public commit, base image, compiler/runtime, kernel, Docker version,
security settings, or final image digest invalidates this record and requires the
complete gate again.

## 6. Software and adversarial gates

- [ ] Complete project suite: ____ / ____ passed.
- [ ] Authored reference: compiled, 5/5 passed.
- [ ] Authored incomplete starter: compiled, 0/5 with five `wrong_answer` statuses.
- [ ] All twelve hostile-code probes passed.
- [ ] `disposable_cleanup` passed with zero remaining containers.
- [ ] Reports contain only the documented source-free fields.

## 7. Lifecycle and incident checks

- [ ] Pre-run prefix inspection found no worker container.
- [ ] Post-run prefix inspection found no worker container.
- [ ] Post-reboot inspection found no worker container or persistent job workspace.
- [ ] A simulated timeout/failure produced no container stderr or raw source in
      operator output or logs, emitted no partial receipt, and completed cleanup.
- [ ] The stop/reimage/invalidate/rebuild incident procedure was rehearsed without
      natural data.

## 8. Offline pilot authorization

- [ ] Every preceding checkbox is complete and independently reviewed.
- [ ] The approved scope is only the small consented, manually de-identified,
      independently labeled frozen pilot.
- [ ] The authorization excludes anonymous/public execution, raw-source retention,
      model training reuse, publication of per-sample results, and any production-
      sandbox or human-code-accuracy claim.

Final decision and non-identifying rationale:

---

Any failed or uncertain item means `blocked`. Do not retry a failed check on natural
data. Follow the incident rule in `docs/DEDICATED_WORKER_HOST.md`.

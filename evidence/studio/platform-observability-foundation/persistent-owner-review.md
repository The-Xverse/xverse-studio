# Persistent public Maestro owner: primary-agent component review

Candidate: `1d13b7debd1657e575106607138edbe7501e8a31`.
Scope: Studio owner lifetime and original task/context/resource identity. This is
not independent milestone acceptance or full live Autoverse verification.

The native backend now retains the original public service; no public SDK private
entry point, reconstructed handle or imported executable callback was introduced.
An installed provider prepares a typed backend task; the actual process birth,
argv and task ID are recorded before activation. Run-state liveness additionally
requires its original live object, and a failed/missing task cannot borrow backend
PID liveness. Existing signed command/CAS and frozen-source checks remain in use.
Default child cwd is explicitly per run. Native commands and host grants remain
fixed in the installed provider, not selected by project metadata.

The runtime router selects original callback contexts by exact run ID. Public
service/root/runtime binding persists; every run receives its own prepared graph,
configuration, original clocks/observations, finite permit and acquired resources.
Successful release retires only exited original child handles; uncertainty retains
context and fences new starts. A prior-owner marker is a restart fence rather than
proof of recoverability. Shutdown cancels original tasks and closes only after
contexts settle. The generic task helper is included in both provider and actual
installation identity. Existing SDK claims/evidence remain unchanged.

Findings and repair evidence: initial actual HTTP handle-loss check failed because
the old startup grace retained preparing after handle loss. The grace was restricted
to an actual original live task; the successor passes. Review also identified a
possible contradictory release receipt: the final guard retains a live child/context
and reports cleanup unknown even if the original SDK recorded a false provider
release. Its adversarial owned-child check passes without rewriting original Argus.
Separate normal-run fixtures prove sequential Stop with actual public Core and owned
children, alongside cancellation, shutdown, failed-task, identity and restart fences.
Fresh final91 affected checks pass on the exact candidate, with no failures/errors/
skips. Their external demo/native substitutions remain explicit.

Open acceptance prerequisite: the existing real registration already lost its old
Core owner. This Studio change cannot restore it. ADR-0035 proposes additional public
recovery scope; until separately authorized and admitted, the real registration stays
fenced. Do not use fresh-root activation, claim deletion, fixtures or historical read
checks as full browser Start/Stop and driving/cruise acceptance.

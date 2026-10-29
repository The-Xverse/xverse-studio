# ADR-0003: recorded replay and freshly admitted reruns

Status: implemented for the owned executable reference provider. Date: 2026-10-25.
Requirement/task identities remain unchanged (FR-060/T091).

Observation/history/evidence reads re-present recorded data and do not create an execution. The
explicit `POST /api/v1/runs/{runId}/reruns` action accepts only an empty JSON object and requires an
idempotency key. Imported evidence has no owned Run identity and cannot confer this capability.
Unsupported physical/live providers remain blocked; this route does not bypass permits or expand
their authority.

The backend verifies the original source Run's exact snapshot binding, immutable file bytes, database
digest, original plan self-check and source semantic/plan identities. It recompiles the original
authored contributors through the current public compiler, checks identical semantics/plan and
effective configuration, verifies frozen profile locks and current native provider availability, and
prepares a fresh preflight. The current editable draft is never substituted for the selected original
inputs. Changed or incompatible original inputs reject before a child Run exists.

A new snapshot has a new ID, `parentSnapshotId`, `sourceSnapshotDigest` and `sourceRunId`. It preserves
the exact original execution input bytes and records current compiler/provider/capability admission.
Original snapshots, journals, annotations and evaluations remain unchanged. Invalid old observation
evidence does not itself prohibit a newly admitted execution of independently verified original
inputs; its old integrity status remains visible and is not repaired by rerunning.

The outer operation, new snapshot/preflight and private stable child-start key are committed before
delegating a runtime effect. Child `Runs.start(...allow_frozen=True)` occurs outside that transaction
and remains subject to its current capabilities, limits, immutable-file checks and effective-input
comparison. The frozen override is an internal admission path and cannot be supplied by a public
request. Outer completion means only that one durable new child Run was created; execution, cleanup,
evidence integrity and assertion outcomes remain separate.

Retries return the same outer operation and child identity. Restart reconciliation reads the child
start idempotency record and checks its fingerprint, snapshot, Run and operation correlation. It never
calls Start again. Missing/unverifiable dispatch evidence remains unknown with no automatic replay.
A proven child admission rejection is reported separately. New explicit user actions use new keys.

Verification exercises real owned reference execution, immutable originals despite changed drafts,
duplicate request keys, post-child acknowledgement loss, conservative restart, snapshot/database
tamper, incompatible current plans/providers, invalid old evidence, closed request bodies and imported
evidence authority boundaries. This does not establish native Windows, external simulator, physical
device or general determinism claims. Reference-model repeatability remains limited to its documented
model, inputs, clocks and admitted implementation.

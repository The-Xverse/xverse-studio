# Independent readiness review, findings before repair

Scope: read-only inspection of the new readiness service, `Runs.preflight` / `verify_snapshot` / `require_campaign_snapshot`, and campaign preview admission. All dynamic probes use isolated loop10 fixtures with process launch forbidden. No external providers, hardware, Windows work, or product implementation edits by this reviewer.

## READY-I01 — campaign replay runs new admission before durable idempotency (MEDIUM)

Confirmed before repair by `campaign_replay_probe.py` and `campaign-replay-before-repair.json`; all three recorded source hashes stayed unchanged during the probe. The first campaign request returns 202 and creates exactly one pending campaign. With its original snapshot file temporarily unavailable in the disposable fixture, the exact request/key replay returns 422 SNAPSHOT_INTEGRITY instead of the durable original operation; a changed-payload replay also returns that admission error instead of 409 IDEMPOTENCY_CONFLICT. Snapshot bytes are restored unchanged, no runs are created, and process launch is forbidden.

`new_campaign` invokes `campaign_preview` (which now performs filesystem-dependent admission) before `store.idempotent` gets a chance to resolve an existing key. Admission must remain mandatory for a new operation, while an accepted key resolves its existing result or payload conflict before revalidation. Repair must preserve atomic intent persistence and avoid nested SQLite connections/transactions when `require_campaign_snapshot` is called from the transaction callback.

## READY-I02 — advertised start scope/XDL compatibility not enforced (MEDIUM)

Confirmed before repair by `capability_scope_probe.py` and `capability-scope-before-repair.json`; preflight and Runs source hashes stayed unchanged. With an owned reference descriptor whose `start` capability targets `unadmitted-target` while its top-level `targetClasses` still includes `model-unit`, preflight reports ready/compatible and retains executable configuration. Separately, declaring only an unsupported XDL version in `supportedXdlVersions` produces the same ready result for current XDL. Process launch is forbidden and run count stays zero.

`reference_readiness` checks top-level target/realization and start legal state/authority, but does not match the operation's target class or the declared XDL versions to actual selected inputs. A current built-in implementation is not authorization to disregard its admitted capability descriptor. Block the affected capability/target with actionable diagnostics; do not change source data or invent compatibility.

The same descriptor boundary additionally accepts `available: "unknown"` and, separately, `hostCompatible: "unknown"` as true because it applies boolean truthiness. `capability-scope-additional-before-repair.json` confirms both cases independently return ready with executable configuration, source hashes unchanged, no runs. Unknown/nonboolean observations must not become native availability; require explicit true facts and keep unknown/unavailable visible.

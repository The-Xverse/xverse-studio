# M1 independent review: first findings

Reviewer: `/root/xdl_baseline`, separate from the author of runtime/recovery/API modules below.
Date: 2026-10-25. Findings recorded before the implementation author repairs them. This is an owned
reference-provider review, not Lite, CARLA, Argus, native X-COM or physical-device evidence.

| Reviewed module | SHA-256 |
|---|---|
| `api/app.py` | `61d3d50bf8116346ff0051ff956c9e51a4e7840db1c6c89d6edc02c7e6eb6961` |
| `runs/service.py` | `1ee6e95858c87b79c89e1fed8ea134a7d5743cf5e17d4eadaf24ccdec7678cdf` |
| `providers/worker.py` | `9f2fafae2954a999031c9d98077a499afb587fe1701872027a7faf83309edc9f` |
| `evidence/reader.py` | `444ed6629b0394404aeed232d1d3a26b4d7ee05971ad1904d1538671566dfa81` |

| ID | Severity | Finding and evidence | Required repair / verification |
|---|---|---|---|
| M1-R01 | High | Preflight and compilation routes accept `scenarioRef`/`deploymentRef` but do not pass the selection to the adapter. An actual HTTP preflight with a nonexistent selected scenario returned `200`, `status: ready`. The selected input intent is silently ignored. | Validate selected references against the supplied closed XDL set before readiness; reject unresolved/wrong-kind refs. Freeze actual selections in the snapshot and verify worker equality. Add HTTP negatives for nonexistent and mismatched deployment/scenario selections. |
| M1-R02 | High | Preflight reads files from the committed revision without checking stored source byte digests. An isolated committed Scenario was externally edited from gain 0.8 to 0.7; HTTP preflight for the unchanged revision returned `200`, `ready`. Snapshot bytes are exact, but its claimed committed revision did not contain those recorded bytes. | Detect external source changes before validation/compile/preflight/start/export, and require explicit conflict recovery before treating them as a committed revision. Verify a direct external edit blocks readiness while preserving both versions. |
| M1-R03 | High | `_dispatch` commits operation `delegated`, launches the child, then obtains PID creation time and persists the owner digest. A crash between launch and persistence loses recoverable ownership. Worse, a `psutil.Error` after successful launch takes the shared exception path and reports `LAUNCH_FAILED`/operation `failed` despite a potentially running workload. This finding is from source control-flow inspection. | Persist launch authority before delegation. Distinguish a proven spawn failure from lost postlaunch acknowledgement; uncertain dispatch remains `unknown` and is never blindly retried. Test crashes/inspection failure on both sides of Popen, and verify one child, truthful ownership, no process-name/PID-only cleanup. |
| M1-R04 | Medium | `Command.parameters` accepts arbitrary nested keys while stop/cancel dispatch ignores all parameters. Closed operation-specific parameter schemas are absent, so unsupported requested command options are silently discarded. Source inspection: API model generic dict; worker request contains only kind and operation ID. | Reject nonempty parameters for stop/cancel until a typed admitted schema supports them. Add direct API negative proving unsupported options reject before durable delegation. |

At-most-once start uses durable principal/route/key fingerprints before delegation, changed keys do not
deduplicate distinct requests, and browser reconnect performs reads rather than starting new work.
Run lifecycle, cleanup, evaluation and evidence statuses are represented separately. Worker-side
recompilation and explicit reference-template admission are present. SSE reads bounded batches from
canonical evidence and uses event IDs/cursors. Those observations do not close lost-ack, cleanup,
high-volume, native Windows, novice-task or external live integration acceptance.

Executed HTTP reproductions for M1-R01/R02 used a fresh local test application and only side-effect-free
preflight. No worker or hardware was started for those reproductions. Both returned ready on the
reviewed candidate, establishing the gaps independently of screenshots or mock runtime outcomes.

Status: findings open for the implementation author. Retain original findings; append successor
verification and source identities after repair.

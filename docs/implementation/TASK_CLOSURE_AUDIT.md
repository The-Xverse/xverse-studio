# Task closure audit — 2026-10-28

The count is **49 completed, 41 in progress and 10 blocked out of 100 tasks**.
It counts completed tasks, not percentage of implementation effort or product readiness.
No M0–M4 milestone is accepted. M5 remains deferred.

Recent work implemented reservation and connection-observation workflows, persistence and
recovery repairs, and coherent deployment comparison inside already open tasks. Those
changes are useful implementation progress; they did not satisfy every clause of those
tasks. Repeated suite counts must not stand in for task closure.

This audit checks the existing task wording and acceptance cases. The subsequent T026 closure amendment corrects the initial dependency-only keep-open conclusion under the existing component standard. Requirements, dependencies and acceptance environments remain unchanged. The native Windows hold remains in force.

| Task | Existing evidence / current implementation | Specific remaining obligation | Disposition |
|---|---|---|---|
| T025 | Lost Start/Stop acknowledgements, two tabs, browser departure, cursor expiry, resynchronization and failed-command views have actual Linux backend/browser evidence. | Repeat on both supported native backend/browser combinations. | Keep open; native Windows held. |
| T026 | All task implementation clauses pass33 backend and21 Playwright cases, with exact source identity and actual native execution distinguished from fixtures. | T023/T025 retain their broader native Windows conformance; AC-008/010 remain unaccepted. | Component complete under the existing task standard; acceptance gates remain open. |
| T027 | Clause review covers plan/Start, startup, signed durable controls, cleanup/evidence distinctions, frozen inputs and ordered ownership observations. Fresh1199 backend/80 affected browser/2 timeline/2 performance pass on377 identical inputs; source08d379c clean Linux package115 and6 UI assets match. | T021/T023/T025 native Windows and T033/T035 full fault/live lanes plus AC006/007/027 supported live tuning remain open. | Component complete under the existing T026 standard; no milestone acceptance. See M1-reference-optional-controls/task027-component-review.md and candidate-binding.json. |
| T033 | Fresh combined full1211 passes with379 unchanged inputs and no failures/errors/skips. Original1207/2, pre-late full1209 and late-ack native2red/2green remain retained. Historical receipts survive; live-denied controls stay blocked. Current affected browser86 and separate performance2 pass on the same379 inputs; source0bc939d clean Linux package115 and6 UI assets match. | Complete lifecycle fault matrix, including actual runtime cleanup-failure and supported live-tune fixtures. Windows/live acceptance stays separate. | Keep open; no component or milestone closure inferred. |
| T068 | Authoring, deployment, connection and negative API regressions exist. | Complete the task's migration-without-semantic-loss evidence and its T048 cross-platform exchange dependency; do not substitute aggregate test totals. | Keep open; closure evidence needs a clause-level mapping. |
| T073 | Registry, actual authenticated HTTP, concurrent claims, independent lease-scope grants, expiry, stale fences, repeated release and native interruption fixtures pass. | Physical-command API observation/stimulation/destructive-action conformance beyond reservation scopes. A stimulation lease alone is not a tested stimulation command. | Keep open; independent software work remains. |
| T074 | Typed host installation, durable reservation intent, pinned providers/assets, exact grants and same-fence reconciliation exist. | Integrate admitted active commands and ownership-loss/run policy; T073/T023 are incomplete. | Keep open; backend integration remains. |
| T075 | Inventory, bindings, reservation history and separately permitted observe-only connection tests have actual native fixture/browser evidence. | Complete the T074 prerequisite and verify the resulting integrated workflow. | Views implemented; keep integration gate open. |
| T077 | `recovery.py` and `time_quality.py` supply tested projections. Connection observations preserve source-clock facts separately from receipt time. | The disconnect/stop helpers have no production run-control caller. Implement provider-declared runtime loss/recovery/stop integration and retain actual observations. Physical acceptance additionally requires the admitted device/driver/permissions/clocks/stop environment. | Keep open; this is an implementation gap, not solely a hardware evidence gap. |
| T078 | The current uncommitted comparison uses one captured project revision and provider descriptor, shared System identity, declared mappings/targets, and explicit unmeasured/unknown physical outcomes. Focused 38 and affected 110 browser cases pass; those cohorts overlap. | T075/T077 integration and AC-023/024 actual compatible physical substitution, measured time quality and physical cleanup evidence. Static declarations cannot demonstrate those outcomes. | Partial implementation; keep open. |
| T082/T083 | Inert Scenario authoring and authoritative validation reject unsupported inputs. Only the admitted exact reference execution is executable. | Provider-specific scheduled effects, activation/recovery and intended-versus-observed matrices. | Keep open; supported-effect/provider integration remains. |

Primary records: [tasks](../../specs/001-industry-agnostic-studio/tasks.md),
[traceability](../../specs/001-industry-agnostic-studio/traceability.json),
[acceptance cases](../../specs/001-industry-agnostic-studio/acceptance.md),
[reservation interruption evidence](../../evidence/studio/M3-native-reservation-interruption/verification.json),
[last published observation verification](../../evidence/studio/M3-connection-observation-workspace/final/verification.json).

The last published source `974c783` has full Linux 1,146 backend / 562 browser /
2 performance and a clean 113-payload package record. Those results precede the new
comparison source. The comparison's full backend/browser/performance verification is
running separately; collection of 1,164 backend and 600 browser cases is not execution.

Published metadata commit `449fbd5` has mixed CI: push run `40704835751` succeeded;
PR run `40704849450` failed one reservation-options alert-focus assertion, with 561
browser cases passing and package steps skipped. The focus failure remains unresolved
at this audit checkpoint. It does not invalidate the separate locally recorded package
or establish a passing PR run.

Next work should close a concrete missing software clause, starting with the observed
reservation focus failure and then the physical-command authority/runtime integration
boundary. Additional static comparison polish cannot close T077 or physical acceptance.


Subsequent checkpoint: full1,164 backend passes with188 selected backend inputs unchanged.
The reservation focus repair passes its two controlled cases and all36 affected native journeys.
The original CI failure stays recorded; full602 browser verification is running separately.
No task status or acceptance gate changes follow from these results.


The exact dependency-ready set is T001, T023, T038, T048, T067 and T073.
Five retain native Windows obligations; T073 retains the command-authority software
and conformance gap. The [readiness record](../../evidence/studio/M3-coherent-deployment-comparison/task-readiness-audit.json)
retains the unchanged descriptions and dependencies. Further command work must follow
the admitted provider/Maestro boundary; adding a standalone device-action endpoint
solely to increase the task count would not satisfy it.


A fresh read-only [provider boundary review](../../evidence/studio/M3-coherent-deployment-comparison/provider-boundary-review.json)
confirms platform main still equals the selected7fab6a2 pin. The candidate trusted-host
RuntimeService and read-only admission checks require externally reviewed authorization
and facility facts; source presence and matching hashes do not supply those facts.
The complete src subtree and named files were checked after the initial whole-repository
recursive response was truncated. No runtime was imported/invoked or baseline changed.
T073/T074 integration must retain those boundaries; no physical action was authorized
by this source inspection.


T026 closure amendment: [clause/source review](../../evidence/studio/M1-session-component-closure/verification.json) corrects the initial accounting conclusion after all T026 clause verification passes. One status changes, T026 in_progress→completed; all task wording/dependencies/acceptance requirements remain. Current counts48/42/10, zero accepted milestones. T027 becomes dependency-ready for its own remaining view/failure verification; the earlier six-task readiness snapshot keeps its dated scope.

T027 closure amendment: primary-agent clause/source review and current1199/80/2/2 plus clean115-payload package evidence close its implementation component. Only T027 changes in_progress→completed; all task definitions/dependencies and acceptance requirements remain. Counts49/41/10, zero accepted milestones. Next independent work is the T033 owned-fixture vertical slice and complete lifecycle fault-matrix audit; the existing scattered tests do not automatically close that task.

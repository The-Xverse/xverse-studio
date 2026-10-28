# Task closure audit — 2026-10-28

The count is **47 completed, 43 in progress and 10 blocked out of 100 tasks**.
It counts completed tasks, not percentage of implementation effort or product readiness.
No M0–M4 milestone is accepted. M5 remains deferred.

Recent work implemented reservation and connection-observation workflows, persistence and
recovery repairs, and coherent deployment comparison inside already open tasks. Those
changes are useful implementation progress; they did not satisfy every clause of those
tasks. Repeated suite counts must not stand in for task closure.

This audit checks the existing task wording and acceptance cases. It changes no requirement,
dependency, acceptance environment or task status. The native Windows hold remains in force.

| Task | Existing evidence / current implementation | Specific remaining obligation | Disposition |
|---|---|---|---|
| T025 | Lost Start/Stop acknowledgements, two tabs, browser departure, cursor expiry, resynchronization and failed-command views have actual Linux backend/browser evidence. | Repeat on both supported native backend/browser combinations. | Keep open; native Windows held. |
| T026 | Proof-bound cursor replay, explicit gap/resync, bounded recovery and read-only reconnection are implemented. The current affected browser cohort includes the actual running replay-window expiry and reconnect journeys. | Its T023/T025 prerequisites include native Windows ownership/reconnection verification. | Implementation exists on Linux; keep dependency gate open. |
| T027 | Immutable input presentation, capability-gated Stop/Cancel, durable command receipts and separate cleanup/evidence/unknown outcomes exist. | Observed partial-start/cleanup-failure UI transitions, admitted optional-operation transitions, and the remaining AC-006/007/027 environment matrix. An unavailable button does not demonstrate a supported operation. | Keep open; software/provider work remains as well as environment gates. |
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

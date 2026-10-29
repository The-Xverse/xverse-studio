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
| T033 | Sourcecc65590 passes fresh1219 backend/88 affected browser/2 performance on identical380 inputs; clean Linux package115 and6 UI assets match. Actual temporary-resource release/identity faults, original failures and scoped phases remain retained. | Complete lifecycle fault matrix and supported live-tune fixtures. Native Windows/live/physical acceptance stays separate. | Keep open; no task or milestone closure inferred. |
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

Live-target focused amendment2026-10-29: uncommitted successor passes163 affected backend and4 native browser checks on387 identical inputs. This proves scoped owned Linux model changes and request recovery; full1239 regression, broader browser/performance/package and complete fault/lifecycle clauses remain pending. T033 stays open, counts49/41/10 unchanged. See evidence/studio/M1-fixture/live-target/. Prior af25449 push again failed the keyboard Undo expectation (622pass/1fail), while its PR passed623; the underlying key/focus cause remains unestablished.

Live-target full-failure amendment: first full1239 retains1237pass/2fail; original traces/test sources remain immutable. Reviewed test-only repair passes10, adding the real sixth-profile expectation and preserving actual native PID/birth/argv capture through a bounded owned-input gate, including a0.35-second real parent delay. All385 other inputs remain identical. Broader browser is running; fresh1240 full/performance/package pending. No task closure;49/41/10, zero milestones.

Finite-JSON successor: actual authenticated requests against a private copy of a completed native run reproduce500 for NaN/Infinity/overflow1e999 before fingerprint admission. Command body validation now rejects nonfinite nested values and unencodable strings as422 before lookup/ledger work, preserves valid opaque JSON and finite409, and leaves operations/snapshots unchanged. Nine contract negatives first fail; current40 affected checks pass on388 unchanged inputs. The1240 full run was intentionally interrupted after952passing cases for this concrete repair; it is not a full result. Fresh1250 full is running on the40-case map. Prior92browser/2performance are explicitly before this guard; fresh broader browser/performance/clean package remain pending. T033 stays in_progress,49/41/10, zero milestones. Evidence: evidence/studio/M1-fixture/live-target/finite-json/.

Verified live-target/finite-JSON source: fresh1250 backend/92 affected browser/2 separate standard performance pass on the same388 unchanged inputs, with0failures/errors/skips/flaky outcomes in applicable phases. Actual guided native journey, target changes, lost acknowledgements/review, input rejection and repaired native early-fault capture pass.629browser cases/61files are collected, not a current full browser execution. Clean native Linux package remains pending. Original failures/prefixes retain their scopes. T033 stays in_progress for complete lifecycle/fault/recovery review;49/41/10 and zero accepted milestones. Evidence: evidence/studio/M1-fixture/live-target/final-verification.json.

Live-target source/package binding: committed sourced67624a76af4f34138c5befcdb361d595307558f passes clean native Linux prepared-cache offline package116 with all manifest/archive/payload hashes and6 identical tested UI assets. Additional actual installed-model smoke verifies original native ownership, nonfinite1e999422 with no mutation, target1→2 with real control/next-state evolution, exact frozen/effective inputs, Stop/cleanup/evidencevalid and original worker exit. Fresh1250backend/92affectedbrowser/2performance use identical388 inputs. The initial extra-smoke receipt helper failed on a missing Start-receipt snapshotId after functional assertions; corrected helper rerun with fresh data passes, with original receipt/source retained.629/61 browser collection remains separate from full execution. T033 remains open for full lifecycle/fault/recovery clauses; nativeWindows/live/physical/human/AT/SADS/independent gates remain open.49/41/10, zero milestones. Evidence: evidence/studio/M1-fixture/live-target/candidate-binding.json.


2026-10-29 native terminal-boundary amendment: Native command-terminal verification adds10 actual owned Linux Stop/Cancel cases plus8 related existing regressions:18passed/0failures/errors/skips in75.21s on389 unchanged inputs. Actual final-poll/exit delivery, original-child interruption, recorded ownership loss/restoration and real reconciliation before delegation preserve exact receipts, immutable inputs and no replay/respawn; uncertainty staysunknown. All prior388 tested inputs and116 packaged payloads remain byte-identical to published91e81bd/productd67624a. Prior1250backend/92affectedbrowser/2performance and package116 retain original execution scope; no expanded full/browser/package rerun claimed. Native cleanup-interruption timing and complete T033 clause review remain open. No statuses/dependencies change;49/41/10, zero accepted milestones. Evidence: evidence/studio/M1-fixture/command-terminal/


Native cleanup-interruption successor:37 affected checks pass with0failures/errors/skips in181.28s on391 unchanged inputs. Three actual Linux x86-64 rmdir/SIGINT witnesses preserve known stopped lifecycle, unknown cleanup/resource identity and partial evidence. All three stronger log checks first fail because the original branch says workload failed; the worker now gives a cleanup-specific explanation. Two native active-workload SIGINT cases fail pending Stop/Cancel truthfully before application. Exact insertion inverse proves all other worker bytes unchanged; only its descriptive implementation digest changes. Prior389 inputs retain387 identical paths, two new tests are added, and114 prior package payloads/six UI assets are unchanged. Fresh full backend and affected browser are running; clean successor package not yet run. No task/milestone closure inferred;49/41/10, zero milestones. Evidence: evidence/studio/M1-fixture/cleanup-interruption/


Cleanup-interruption final checkpoint: sourcecb65206 passes37 affected native/contract checks and98 unique affected browser cases (92main+9supplemental−3overlap) on391 identical inputs; clean nativeLinux package116/all archive/payload hashes/6 UI assets passes. Full1265 retains1264passed/1failed,0errors/skips,1242.02s on391 unchanged inputs. Late-Stop operation read returned RUN_TERMINAL_BEFORE_COMMAND while canonical worker reported RUN_COMPLETED_BEFORE_COMMAND; later stored result matched the worker. Cause remains unestablished; original assertion/source/result retained. One initial and eight subsequently instrumented repeats pass but do not establish resolution; first repeated-node selection actually executed one case, and first supplemental browser selector executed zero. Two additional actual native backend-crash-before-launch cases pass on392 unchanged inputs with all prior391 hashes identical: durable receipts/immutable files survive, ownership staysunknown, controls409, no worker launch or blind dispatch. No expanded full execution after these2, new full browser or performance rerun is claimed. T033 staysin_progress;49/41/10, zero accepted milestones. Evidence: evidence/studio/M1-fixture/cleanup-interruption/candidate-binding.json.


Failure-retention successor: a fresh full1267 backend execution passes0failures/errors/skips in1302.20s on392 unchanged inputs with bounded read-only observations of the four original late-command cases. All four pass; zero trace omissions. Observer timing effects remain possible; the original1264pass/1fail and original temporary-data loss stayqualified, causeunestablished. Repository pytest now retains bounded allowlisted diagnostics for explicitly marked owned native failures before fixture teardown, outside disposable pytest data. Owner keys, signed mailboxes, requests, snapshots and auth DB are excluded; original failure survives capture-write errors. Current14 focused checks pass on394 unchanged inputs (ten original native functions/assertions unchanged plus four capture controls/safety cases). Initial2pass/1fixturefail retained; budget trigger and accidental child collection corrected. All116 product payloads/six UI assets remain identical; no expanded full/browser/performance/package rerun after this test-only change. Counts49/41/10 and zero milestones; T033 remainsin_progress. Evidence: evidence/studio/M1-fixture/failure-retention/candidate-binding.json.

Prior91e81bd push40809550411 and PR40809556858 CI are both terminalSUCCESS with actual1250backend/full629browser/package116 smoke from decoded logs. PR checkoutc7a66dcf1847bd38ae928f99a099b1e75cefaa56 and published91 have identical Git tree9775430403370c034c7958364658d2cd6a239d32 and environment sourceDigest. Artifact metadata retained without archive download/payload re-verification. These jobs predate ddc native terminal tests and later cleanup/recovery; they do not establish resolution or passing full current source. Evidence: evidence/studio/native-ci/ubuntu-24.04-91e81bd-runs.json.

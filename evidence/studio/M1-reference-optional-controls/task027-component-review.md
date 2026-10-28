# T027 component review candidate

The unchanged task is: “Implement run-plan/start/control views with startup,
stop, cleanup, evidence and optional-operation states, clearly identifying current
immutable inputs.” Its T020/T024/T026 dependencies are completed. This review
does not change its requirements, task description, dependencies or acceptance.
The [observed frontend merge defect](review-findings.md) is repaired: independently ordered backend observations update unknown/recovered ownership without changing worker CAS. Two actual native browser cases and one Node contract pass; 12 backend recovery/persistence checks and the broader 80-check affected cohort pass separately. Completion remains pending final verification and source/package binding.

| Task clause | Implementation and evidence | Scope boundary |
| --- | --- | --- |
| Plan and Start | Existing preflight review shows backend readiness dimensions and the compiled frozen selection. Actual startup and new keyboard-control journeys start one owned run through ordinary preflight. | Runtime admission is still unavailable for Lite and physical providers. |
| Ownership observations | `Runs.read` advances durable observation order only for changed metadata; `mergeRun` and control callbacks accept newer full observations and reject stale identities/versions. Actual browser polling loses and recovers observation of the original worker at both viewports, disables/re-enables controls, clears the stale reason, and retains the worker version and immutable inputs. Twelve native recovery/persistence checks include invalid/exhausted counter refusals and stable no-write reads. | The observation denial is injected in a closed fixture; this is actual owned Linux execution, not native Windows or physical integration. |
| Startup | `RunStartupStatus` distinguishes preparing, actual early rejection, recorded start, post-start failure and unresolved ownership. Existing startup cases repeat in the affected cohort. | Injected launch refusal is labelled; Windows startup is held. |
| Stop and control receipts | Signed, idempotent Stop/Cancel and Pause/Resume keep accepted, delegated, completed, failed and unknown operations separate. Actual native cases test terminal commands while paused, stale signed transitions, same-key retry and owned shutdown. Campaign cancellation also handles a paused child without freeing its slot early. | Lifecycle completion does not establish a functional verdict or a physical stop. |
| Cleanup | Current native startup, interruption and Stop cases observe complete or unknown cleanup independently. Existing labelled diagnostic projections render failed cleanup and actionable consequences. | A failed-cleanup presentation fixture does not prove an actual provider/device restore operation. |
| Evidence | Actual journals retain source simulation ticks, partial/complete coverage and integrity; a paused process creates no new simulation observations. Recorded same-version projections keep partial, invalid and unavailable evidence visible. | Physical/Argus and full fault-matrix acceptance remain separate. |
| Optional-operation states | Actual admitted nonphysical Pause/Resume have backend state/version/authority checks, durable browser receipts and current keyboard/reload journeys at both viewports. The finite cumulative pause budget does not reset on Resume. Missing/physical descriptor records and unsupported Step are refused. | Step/reset/rewind/live mutation remain unsupported. This is positive executed optional-control evidence, rather than completion based only on unavailable buttons. |
| Immutable input identity | Native cases retain canonical Project and snapshot bytes. The browser inspects the current frozen snapshot, plan and semantic identities while paused, then resumes the same run. Draft/run isolation and readiness cases repeat in the affected cohort. | AC-027's supported live parameter mutation is not claimed. |

The repository already distinguishes implementation-component completion from
broader native/live acceptance, including T026. If final checks establish this
complete view/control component, T027 can close under that existing standard.
T021/T023/T025, the complete T033/T035 fault/environment lanes, and AC-006/007/027
remain independently open. No M1 or other milestone is accepted by this review.
This is a primary-agent review, not independent milestone approval.

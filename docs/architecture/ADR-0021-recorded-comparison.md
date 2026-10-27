# ADR-0021 — Frozen comparison facts and original recorded windows

Status: implementation in progress; complete task and milestone acceptance unproven.
Date: 2026-10-27.

FR-059/FR-060 and T091 require visible model, deployment, parameter, artifact,
provider/capability and clock differences alongside results, with incompatible
quantities or incomplete evidence excluded from like-for-like interpretation.
The earlier API verified managed snapshot integrity but replaced the frozen provider
identity with a provider ID and invented a snapshot clock label. Its comparator
accepted missing or different complete window bounds. The browser rendered generic
JSON and could accept an older response after a newer baseline selection.

Keep both existing HTTP v1 comparison routes and request schemas. Add an explicit
comparisonVersion 1.0 report, retaining mode, compatibility, diagnostics, differences,
fields and the fresh-admission declaration. Derive configuration from protected
snapshots, contributing resource identities, compiled bindings/artifact references,
profile locks/provenance, provider descriptor, capability digest, compiler and
original clock declarations. Recorded observer identity, unit semantics and clock must
also agree with its compiled observer declaration. Do not substitute current draft or provider metadata.
A missing fact is unavailable, including when absent on both sides. Bound each
configuration value to 64 KiB, fields to 32 and canonical source acquisition to the
existing reader limits. Each configuration value also has depth 20, 8,192-node and
2,048-entry container bounds; malformed or excessive metadata is unavailable without
changing the stored snapshot. Unsupported field/source report sizes fail with a typed refusal.

Use the existing canonical reader integrity and unit-definition identities.
Comparison summarizes original numeric samples without resampling, interpolation,
new evaluation, arithmetic deltas or rewritten evidence. Preserve exact signed
source tick strings; never round them through browser numbers. The reference
projection detects changed units/clocks/resolution/uncertainty, non-monotonic or
invalid samples and explicit observation gaps. Show each side's recorded range,
last value, count and original sample/coverage bounds independently.

A positive pairing requires known frozen provenance/effective inputs, valid and
complete evidence, matching observers/quantity/unit definitions, verified complete
gap-free coverage and equal known windows. Clock references and frozen definitions
must agree; this component admits common simulation-clock definitions with known
zero source uncertainty and matching resolution. It applies no cross-clock mapping
or physical synchronization. Unsupported alignment stays blocked. Known configuration
differences remain reviewable and are not themselves a functional failure verdict.
Lifecycle, cleanup, evidence quality and assertion verdict remain independent.

Extract a dedicated comparison feature. Read workspace history in bounded pages,
validate report version and both submitted run/snapshot/project identities, serialize each read channel,
bound deadlines and guard selection/mount/focus intent. Changing a baseline clears
its previous report. Inspection and playback never create or replay a workload.
Playback opens the existing original-observation view; leaving it stops local
playback. Current-draft preflight and freshly admitted frozen-input rerun remain
explicit execution paths, each requiring its own authority and new identity.

Verify positive and negative backend contracts, actual owned runs with equal and
unequal complete windows, protected snapshot/journal immutability, unsupported
quantity/clock/gap cases and keyboard/browser interaction at both desktop widths.
Label injected transport/record fixtures. Native Windows, external/physical provider
admission, human/assistive-technology and full AC-029 remain distinct gates. No new
XDL/evaluator semantics, provider API, hardware authority or deterministic replay
claim is introduced.


Full-suite review amendment: after the added native-history cohort, actual `/runs`
requests exceeded their unchanged 15-second caller timeout and existing timeline
focus checks failed. The initial full run is retained as unsuccessful/interrupted,
not a complete pass. Run listing now filters/pages metadata before reconciling only
requested rows; the default 200/max 200 and all returned assessment facts remain.
Assessment admission caching uses exact frozen documents plus pinned compiler,
evaluator and schema identities after verifying the whole snapshot digest. It
retains the existing 64-entry bound. Per-run evaluation records are queried by run
and never shared, so equal definition inputs cannot borrow another run's verdict.
No validity check, caller deadline, benchmark or lifecycle authority is weakened.
Actual owned-run regressions first reproduced off-page reconciliation and repeated
admission for identical documents under different snapshot UUIDs; successors must
also preserve independent evaluation results, changed-input admission and invalid
snapshot refusal. A report limits sentence now explicitly retains each read's own
integrity verdict rather than implying that verification always succeeds.

Follow-on rerun acknowledgement amendment: an actual owned rerun completed while
its real HTTP acceptance response was deliberately held. Releasing that response
after the user selected Model caused the browser to select the child and return
to Results at both desktop widths. This is separate from recorded comparison and
does not invalidate the original immutable run or create another workload.

Bind rerun presentation to the mounted Results instance, source run/snapshot and
selected result tab. A completed request may select its verified child only while
that context and the initiating focus remain current and no newer dialog is open.
Settling an old receipt must not remove another tab's newer stored request key.
Guard repeated submissions synchronously. Apply the existing fifteen-second
acknowledgement budget to the initial HTTP request, operation reads and child read;
an aborted read does not cancel backend execution. Uncertain acknowledgement keeps
the same idempotency key for explicit retry and never authorizes another Start.

Before selecting a child, check the accepted operation ID, rerun kind, source run,
parent/new snapshot, child/start-operation IDs, project and owned-reference scope.
Malformed or mismatched replies remain unconfirmed. This consumes existing v1
response fields; no backend API, ownership, provider or XDL semantics change.
Verify normal rerun, newer views/annotations/focus/run selection, labelled response
identity faults and actual lost acknowledgements with same-key/no-duplicate retry.
Retain the original red and separate isolated proposal before main verification;
native Windows, broader provider admission and complete T091 acceptance remain open.


Frozen-input inspection amendment: a held actual HTTP200 snapshot read opened the
old run's dialog after selecting a newer recorded run at both desktop widths.
The old snapshots and canonical journals remained intact. Bind the inspection
control to run/snapshot/project/revision/digest and result-tab identity; unmounting
aborts its pending read. Returning to the same run cannot revive an earlier read.
Serialize pending reads synchronously and bound them to thirty seconds. Timeout
or a rejected response enables an explicit fresh read without creating a workload.

Require the existing backend integrity/read-only verdict, exact selected snapshot
and project identities, a well-formed snapshot digest and contributing source map,
and agreement with every known selected-run revision/plan/semantic digest. Optional
complete authored inputs may be unavailable; do not substitute contributing inputs
under that label. Display the run/project/snapshot provenance with read-only source
text. Preserve newer focus or dialogs, and render the Results dialog in the document
portal to avoid heading-specific presentation rules. The shared Model divergence
inspector keeps its existing optional-run interface and modal keyboard behavior.

Verify actual owned runs and immutable protected bytes, normal/duplicate reads,
newer run/view/tab/focus, run-selection round trips and superseding inspection.
Label HTTP/DTO faults separately, verify actual thirty-second timeout/fresh retry,
and wait for recorded-history options before keyboard selection in the harness.
The original red, TypeScript inference error and harness precondition/teardown
failures stay retained as failures. No backend API, execution authority, XDL,
provider admission or milestone acceptance changes.

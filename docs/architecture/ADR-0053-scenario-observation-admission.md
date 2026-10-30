# ADR-0053 — Scenario inspection and declared observation budgets

Date: 2026-10-30. Status: implementation candidate.

T082's literal test specification is complete. T083 still needs explicit selected-
provider observation cost checks and a coherent authoring inspection boundary.
This decision retains the existing XDL/compiler, provider configuration mapping,
full implementation plan and runtime/evidence ownership.

Add read-only Studio HTTP v1 `GET /projects/{id}/scenario-admission`, requiring the
current revision and selected provider, with optional explicit Scenario selection.
Capture one project/source set and one validated descriptor. Compile through the
existing contributor selector, then use the existing static configuration mapping.
No readiness probe, snapshot, permit, reservation or runtime operation is created.
Return supported/unsupported source mapping, original source identities, declared
steps/faults/observers and observation budget results. A positive static inspection
is always `preflight_required`; it is never live readiness or evidence of effects.
Unknown provider IDs refuse, stale revisions conflict, and unknown/duplicate query
fields refuse. Results bind project/revision/provider/selection/digests explicitly.

Providers may declare bounded `observationContracts` version1.0 metadata: at most32
unique observer IDs, each with at most8 nonnegative finite cost quantities and
optional inert intrusiveness/retention text; at most8 uniquely named unit budgets.
Quantities and budgets are bounded to1e15 and units use a closed safe identifier
syntax. Each selected observer must declare a cost in every budgeted dimension.
Sum only matching exact units; do not convert, estimate or assume a missing value
is zero. Unknown costs under a declared budget block admission. Unsupported or
ambiguous declarations and exceeded budgets also block. Undeclared dimensions
remain unknown. An optional integral `limits.maxObservers` is enforced separately.

Apply the same pure checks at the shared backend readiness boundary, before the
selected provider's readiness callback, including Start rechecks. Invalid, unknown
or exceeded budgets cannot dispatch. No imported project can supply a provider
contract, override a budget, install code or acquire authority through inspection.

Classic Autoverse declares its existing single observer as one `observer-slot`
against capacity one. This is a count budget, not a CPU/memory/latency estimate.
CPU, memory, retention policy and latency remain undeclared where unavailable.
Platform mode declares its existing four-observer count bound separately and does
not inherit classic observation cost declarations. Runtime behavior is unchanged.
Provider descriptors and frozen identities bind these declarations as usual.

Observation text is bounded and withheld when unsuitable for public metadata;
schema/sink references are never fetched. Invalid XDL remains an inspectable draft
with blocked inspection. Static support, liveness, measured effects and assertion
verdicts stay separate. Generic forms/timeline integration remains T084 work.

Verification uses the actual enrolled Autoverse providers: coherent selection,
count/cost/unknown/duplicate/malformed/unit-budget negatives, no provider readiness
contact or run allocation, exact source preservation, unavailable providers and
sanitized metadata. Native execution evidence is inherited only at its unchanged
runtime scope; metadata-only changes do not create a new live acceptance claim.

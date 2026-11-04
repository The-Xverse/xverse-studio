# ADR-0057 — Retrospective assessments of recorded bridge fault acknowledgements

Date:2026-11-04. Status: implementation and verification in progress.

Admit the existing bounded assessment Profile/AST for an explicit classic Autoverse
blueprint, through normal full XDL validation/compilation. Keep the original native
and browser examples unchanged. The added observer reads existing canonical fault
records after execution; it starts no subscription or physical operation. Its zero
additional subscription-slot cost is not a zero CPU/storage/latency claim. All
definitions, Profile identity, observer and source/plan digests remain frozen inputs.

Classic provider0.3.0 declares a version1.0 retrospective event mapping. Boolean
fields `activationObserved` and `recoveryObserved` contain one true sample for each
matching original bridge-lease acknowledgement. They are event series, not held
state, continuous lease coverage or vehicle/controller measurements. Source ticks
are the existing producer host-runtime microseconds since actual running; ordinary
telemetry retains no source clock. No receipt-time substitution or interpolation.

For the opted-in blueprint only, after closing the fault recorder the worker emits
one canonical coverage attestation: observer/contract/clock, half-open window,
per-field sample counts, preceding sequence/digest and complete/error facts. This
attests enumeration of successfully recorded acknowledgement events through cutoff,
not every underlying physical transition. Failed/partial recording or absent cutoff
does not establish coverage. Cleanup/lifecycle and assertion verdict remain separate.

An installed provider supplies a pure bounded context/projection through the common
assessment facade. Shared code has no industry dispatch. The context binds frozen
provider version/contract/source/plan and the actual canonical reader identity.
The projection verifies original producer/tick/payload/acknowledgement facts, coverage
prefix/counts/window and canonical integrity before supplying boolean event samples.
Observed dropped-frame identifiers must be positive safe integers from the admitted
driver interface. Recovery publication identifiers use the same range and must
follow the last dropped frame; boolean, fractional and out-of-range counters do not
establish coverage.
Empty required series, missing coverage, intervals beyond cutoff, incompatible clock,
unit/type errors and unknown context retain the existing indeterminate/error rules.
The evaluator/AST, half-open windows and dimensionless count semantics do not change.

Historical0.2 fault-clock decoding remains explicitly supported under its original
contract; old records gain no new assessment coverage. Existing source/unknown
payload refusal remains strict. No companion or original journal changes, private
runtime APIs, new hardware authority or physical-effect claim.

Verification must include exact source admission/refusals, actual complete demo,
real pass/fail/indeterminate/error/metric results and provenance, retry/immutability,
browser inspection at both sizes, original canonical/native ownership readback and
affected regressions. Synthetic/partial checks do not close T088 or live acceptance.

# Bounded evaluation implementation v1

The authoritative design remains the feature's `contracts/experiment-evaluation.md`.
`packages/contracts/assertions/evaluation-v1.schema.json` publishes the inert profile
payload; an identical packaged copy accompanies the backend. Its `$id` is
`https://schemas.xverse.io/studio/experiments/1.0/evaluation.schema.json`. It is loaded
from the installed package explicitly; no network schema resolution is permitted.

An XDL Profile declares namespace `io.xverse.studio.experiments`, profile version
`1.0.0`, the schema `$id`, and core-compatible API versions. A Scenario carries its
payload at root `extensions["io.xverse.studio.experiments"]`, with `version: "1.0"`
and `definitions`. Profile schema admission and validation are prerequisites; they
do not imply evaluation. The run's frozen profile/schema identities and definitions
must be checked again when the evaluation operation selects a definition. Opaque
expressions are never translated or executed implicitly.

The evaluator consumes verified canonical-reader projections, not chart samples.
A projection names snapshot/evidence identities, observer and exact field, original
clock domain, complete verified window coverage, original samples, and a field
schema. Numeric schema includes `unit`, semantic `quantity`, and the pinned
`unitDefinitionDigest`. Unit names alone confer no compatibility. Named pure
conversions come from the pinned profile and carry immutable identity, source/unit,
scale and offset. No implicit conversion is performed.

Implementation field allocation (within v1's existing semantics):

- Metric `evaluationRef` is `{evaluationId, version, definitionDigest}`. Available
  derived metric records must match all three, snapshot and exact evidence digests.
- Definition `maxUncertaintyTicks` is a nonnegative decimal integer string in the
  selected window domain. A cross-clock projection carries a backend-admitted
  `clockMapping` with mapping ID/digest, target domain, integer rational scale,
  integer offset and uncertainty. Unsupported or nonintegral mappings are
  indeterminate; no interpolation or receipt-time substitution occurs.
- A projection's `coverage` contains `verified`, `complete`, `startTick`, `endTick`
  and `gaps`. Failure of any requirement yields indeterminate. The provider/reader
  owns verification; an API caller cannot attest its own coverage.
- Samples have decimal-string `tick`, typed `value` and optional integer `sequence`.
  Duplicate ticks require explicit monotonic source ordering; identical duplicate
  delivery may be deduplicated. Conflicting unordered duplicates are indeterminate.

The evaluator enforces the contract's 128-node, depth-12, 32 signal/metric-reference,
1,000,000-sample and 64 MiB caps, plus cancellation and a configured wall-time budget
(default two seconds, not a performance acceptance result). Tighter caps may be
applied; callers cannot widen the hard caps. Definition errors are `error/null`;
missing/invalid evidence is `complete/indeterminate`; a missing admitted profile is
`unavailable/null`. Metric values never carry assertion verdicts. Evaluation outputs
are derived immutable records and do not modify original evidence or lifecycle.

This is owned evaluator conformance scope. Hardware, external simulator fidelity,
native Windows execution, performance targets and release acceptance need their
own retained evidence and remain unproven by these unit fixtures.

The HTTP facade validates the complete frozen definition graph (at most 32
entries), rejects missing targets, assertion-as-metric references, changed version
or definition-digest pins and dependency cycles, then evaluates the selected
closure in topological order. Every prerequisite metric is a separate durable
immutable evaluation job with its own operation, definition digest, exact canonical
evidence digests, evaluator implementation digest and dependency result links.
Prerequisite results are recorded before dependent evaluation. Each dependent
record pins the actual prerequisite evaluation ID and result digest; retries of the
same parent operation do not create new metric jobs. Interrupted running jobs
become explicit execution errors on restart and are never silently recomputed.

The admitted owned reference profile currently supplies only dimensionless unit
`1` and no conversion tables. Conversion nodes therefore remain explicitly
unsupported unless a separately admitted profile supplies their pinned pure
conversion; the backend never invents one from unit names. Missing/incomplete/
invalid metric inputs cannot become known scalars and propagate indeterminate
assertion results against the same frozen snapshot/evidence selection.

Run projections aggregate all frozen assertion definitions through a trusted
backend callback. Its bounded cache keys validated definitions by the actual
verified snapshot digest. It selects each definition's latest matching immutable
evaluation, retains execution status separately from verdict, and exposes missing
required definitions without inventing queued work. Empty or unattempted assessment
sets have no verdict; failure wins over unfinished jobs, otherwise unfinished/error/
unavailable required results are indeterminate, and all required passes yield pass.
Metric jobs expose values and execution/coverage states with no assertion verdict.
This projection changes neither provider lifecycle nor cleanup or original evidence.

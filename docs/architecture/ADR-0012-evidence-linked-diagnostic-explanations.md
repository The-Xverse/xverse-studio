# ADR-0012: Evidence-linked diagnostic explanations

Status: implemented owned components under verification; no M1 acceptance claim.

FR-019, FR-020 and NFR-011 require diagnostic explanations that keep observed facts, inferred
consequences, hypotheses and unknown causes distinct, with concrete next actions. Readiness records
and run state fields already carried codes and remediation, but nothing tied a statement to the
evidence that supports it or kept liveness, missing traffic and unconfirmed causes from being read
as failures.

Explanation contract 1.0 is an additive, read-only projection with two routes:
`GET /runs/{runId}/diagnostics` and `GET /projects/{projectId}/preflights/{preflightId}/diagnostics`.
Each finding has a stable `code`, a `class` from a closed registry, a severity and affected element
references. `facts` carry identifiers and bounded evidence references (canonical events, run fields,
operations, preflight dimensions, source diagnostics or named projections; at most eight, with an
omitted count). `consequences` must cite facts of the same finding. `hypotheses` are always
`unconfirmed`. `unknowns` state what the evidence does not establish. `nextActions` come from a closed
registry; the browser renders only actions it can perform as controls. The explanation's `rootCause`
is always `not_inferred`: a cause appears only when the workload itself reported it as a fact.

Run classes: process exit, lost ownership (`lost_connection`), cleanup, unavailable/invalid/partial
evidence, incompatible time mapping, declared telemetry gaps, observed faults with diverging
measurements, accepted commands that did not take effect, no-traffic ambiguity and liveness-only
health. Absence of observations from an expected observer is `info`, never failure, and is not
reported when evidence cannot be read. Liveness without observations states that functional health
is not observed. A requested fault alone is not evidence of a fault.

Preflight classes map only coded readiness records: invalid model (with source diagnostics), unsupported
capability or unavailable provider, missing artifact, clock mapping, resource limit and authority.
Codeless unknown dimensions are grouped as unestablished readiness rather than attributed to a specific
missing fact. A stale plan reports each changed assumption: expiry, project revision and capability
digest.

Compatibility: existing readiness, error and diagnostic fields are unchanged. Explanations add no
writes of their own and grant no execution authority; the run route performs the same ownership
reconciliation as `GET /runs/{runId}` before reading. Original evidence, preflights and operations are
never changed by an explanation. Affected elements come from the frozen snapshot configuration.
A run that never started is explained as producing no evidence; unreadable evidence of an active run is
information, not loss. Liveness-only findings require a verified running/stopping state and readable
evidence. A model whose readiness is invalid is explained with its authoritative source diagnostics;
dimensions that depend on a compiled plan are then unestablished. Target readiness is derived and is not
reported separately. Multiple observation clock domains are reported without inferring an admitted
mapping; a future admitted mapping contract must refine this rule. At most 64 findings
are returned with `findingCount` and `findingsComplete`.

Verification: `tests/contract/test_diagnostics.py` covers every class with shared invariants (every fact
cites evidence; consequences cite only their own facts; hypotheses unconfirmed; closed classes and
actions) plus API runs on owned and recorded evidence. `tests/e2e/diagnostics.spec.ts` covers the
browser views, keyboard action use and unchanged journal bytes. Live provider failures, Windows and
physical evidence remain separate gates.

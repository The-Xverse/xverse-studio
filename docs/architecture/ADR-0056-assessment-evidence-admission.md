# ADR-0056 — Explicit assessment evidence admission

Date: 2026-11-04. Status: implemented; scoped actual-recording verification, broader acceptance open.

The bounded evaluator's existing canonical measurement projection implements the
owned reference provider's field, dimensionless-unit and coverage contract. Other
providers can share a hash-chain envelope without sharing those semantics. Source
schema admission, journal integrity and timeline placement do not admit evaluation.

Expose read-only `GET /runs/{runId}/assessment-support`, version1.0, bound to the
protected project/run/snapshot/digest and original provider/reader/journal identity.
Its supported/unsupported result describes the installed evidence mapping only;
definitions, current evidence integrity/coverage and execution status remain separate.
The existing reference decoder requires matching owned reference provider/scope
identities and reference reader/journal identity. Its historical missing redundant
reader/journal metadata retains the established reference-only defaults.

No decoder is admitted for Autoverse's external-interface receipts. They remain
inspectable under their real provider-journal identity and generic hash-chain reader.
No clock, units, samples, continuity or coverage are inferred from their envelope,
receipt timestamps, timeline placement or reference-shaped payload fields.

After verifying a new request's protected snapshot, evaluation POST refuses an
unsupported mapping with `EVALUATION_EVIDENCE_UNSUPPORTED` before definition/evidence
projection, idempotency acceptance or operation/job creation. Already accepted exact
retries retain their immutable receipts; original results are never rewritten. The
private reference projection also enforces the gate to prevent accidental reuse.
The browser reads/validates the support report, shows the actual reader and reason,
and uses only an advertised supported evidence identity when submitting. Backend
enforcement remains authoritative.

This adds no runtime capability, profile execution, provider callback, unit mapping
or new expression language. A future provider mapping requires explicit reviewed
semantics and actual complete-demo evidence; this gate does not replace that work.
Verify actual Autoverse API refusal without new jobs, preserved canonical bytes,
cross-provider/reader counterexamples, browser availability and departed/cancelled
reads. Reference execution remains subject to the current user's test-target scope.
Affected traces: T087/T088/T095, FR-056/FR-057, AC-026 and SC-006. No task or milestone
completes merely from this prerequisite.

Verification:32 actual-recording Python projection/decoder checks and19 browser/
response checks passed on496 unchanged selected inputs and six private UI assets.
The browser verifies actual API refusal with no new run, operation, evaluation,
snapshot or idempotency receipt. Original/copy recording bytes and owned shutdown
are verified. One result-card case remains an explicitly synthetic display fixture.
See `evidence/studio/M4-assessment-evidence-admission/` for exact scope/failures.
No new complete-demo execution or actual Autoverse evaluator mapping is claimed.

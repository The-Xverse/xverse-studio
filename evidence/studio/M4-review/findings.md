# M4 read-only implementation review

Review date: 2026-10-25. Scope: evaluator, campaign state/scheduling, comparison,
annotation/retention facades, canonical evidence projection and their integration
with the root-owned Store/Runs services. This review was performed after 64 pure
service tests and three actual HTTP/native reference-provider tests passed, before
applying the repairs listed here. Those tests establish owned reference scope only.
Native Windows, physical hardware, external simulators, novice measurements and
performance acceptance remain NOT_RUN/BLOCKED as separately recorded.

| ID | Severity | Finding before repair | Affected verification |
|---|---|---|---|
| M4-R01 | High | A crash after durable evaluation acceptance but before result persistence leaves a running evaluation indefinitely. No startup reconciliation marks it interrupted. | Persist accepted evaluator job, recreate app, verify separate error execution/null verdict and no implicit reevaluation. |
| M4-R02 | High | Retention deletion currently occurs inside the idempotency callback before its transaction commits. A crash/rollback could lose intent/results after deleting files. | Verify durable accepted operation before deletion, per-item outcomes, interrupted apply remains unknown, retry never repeats effects. |
| M4-R03 | Medium | Campaign operations remain accepted after all children finish; cancellation followed by the final child stopping changes campaign status to complete rather than cancelled. | Native child runs finish with correct operation result; cancellation preserves child state and does not synthesize verdicts. |
| M4-R04 | Medium | Non-ASCII definition digest uses different JSON ASCII escaping between extraction and evaluator; stored result could disagree with selected immutable definition identity. | Unicode definition name has identical extraction/result digest. |
| M4-R05 | Medium | Clock coverage mapping uses floating arithmetic for decimal integer ticks; large ticks could lose precision. | Exact rational mapping/half-open boundaries at large tick values. |
| M4-R06 | Medium | Annotation update validates content shape but does not recheck evidence/model references against its original run. | Direct API rejects references belonging to another run and unknown model references on create/update. |
| M4-R07 | High | Snapshot definition extraction validates XDL but does not verify the stored snapshot digest. Canonical evidence projection also needs explicit requested/effective plan identity checks before claiming full evaluation coverage. | Tampered snapshot/effective-plan identities cannot yield pass, including literal assertions. |
| M4-R08 | Medium | Evaluator serializes a whole evidence record to count input bytes before enforcing sample count. This creates an avoidable unbounded serialization allocation relative to the job cap. | Count samples first; bounded incremental byte counting and budget checks stop at the declared cap. |

The identified findings require focused repairs and reruns. They do not justify
weakening any acceptance gate or declaring M4 complete. Root publication and final
candidate evidence are recorded separately; this report describes the pre-repair
working tree and is retained as review history.

## Evidence-exchange follow-up review (before implementation)

| ID | Severity | Finding before repair | Affected verification |
|---|---|---|---|
| M4-R09 | High | Run exports omit immutable derived evaluations and revisioned annotations/trace links. No inert evidence-bundle import/inspection route exists, so project archive import cannot satisfy evidence exchange. | Exact exported derived records, safe import/inspection without creating a run or provider effect, portable names and secret rejection. |
| M4-R10 | High | A manifest file hash alone cannot establish canonical evidence validity. Import must separately verify snapshot/plan identity and original journal digest/hash chain, retaining source-declared partial/invalid/unavailable status without promotion. | Missing/tampered files reject; recomputed archive manifest cannot conceal damaged original snapshot/journal identities; invalid/partial source evidence remains explicitly scoped. |

## Independent evidence-import follow-up (before repair)

The `xdl_baseline` agent independently inspected the new inert importer and
confirmed the numeric-overflow case without runtime/device effects.

| ID | Severity | Finding before repair | Affected verification |
|---|---|---|---|
| M4-R11 | Medium | Rejecting JSON NaN/Infinity constants does not reject `1e999`, which Python parses to infinity; a subsequent canonical digest could raise an untyped exception. | Reject floating numeric overflow and duplicate/nonfinite JSON as typed import errors. |
| M4-R12 | High | Conflicting original availability values only produce a diagnostic, while the result uses the report value. A source manifest declaring invalid must not be promoted to complete by a conflicting report. | Conflicting invalid/partial/unavailable declarations remain conservatively degraded or reject; preserve both original declarations. |
| M4-R13 | Medium | The original report's evidence-scope string is copied into the inspection scope. Imported producer claims need a distinct declared scope and must never confer provider/hardware admission through the reference reader. | Inspection scope identifies imported recorded evidence, source scope stays explicitly declared, unsupported provider readers remain unavailable. |

## Metric dependency admission follow-up (before implementation)

| ID | Severity | Finding before repair | Affected verification |
|---|---|---|---|
| M4-R14 | High | The pure evaluator supports pinned metric references, but the HTTP evaluation facade supplies no resolved metric results and snapshot extraction checks only individual definitions. Valid cross-definition dependencies are unusable; missing/pin-conflicting/cyclic definition sets are not checked as a complete bounded graph. | Admit a bounded acyclic frozen definition set, persist metric jobs before evaluation, evaluate in topological order against the same snapshot/canonical evidence, retain immutable dependency result identities, and test actual reference pass, unavailable evidence and rejected dependency pins/cycles. |

# Persist changed run observations without identical rewrites

Actual production reads on a private copy of recorded owned-reference runs perform
421 unchanged SQLite record writes for200 stable terminal reads. The successor
performs zero record writes for the same200 reads, preserving the previously
stored run bodies and all selected managed run files. The baseline records221
operation rewrites and200 run rewrites; no new observation was recorded by them.

The repair keeps ownership/PID/birth checks, worker observation, command
reconciliation, journal integrity and assessment computation. It compares the
existing canonical JSON representation before and after applying observations,
and skips only identical writes. New facts retain the original durable writes and
failure behavior. This is not an observation cache or a new execution capability.
See ADR-0026.

Four regressions fail before repair; the original changed-write failure control
passes. After repair, all five new cases and20 existing lifecycle/history/identity
cases pass. The new cases exercise actual short reference workers, an acknowledged
cancel, unchanged single-run/history reads, a controlled late cleanup observation,
journal corruption and injected changed-state storage failure. Controlled negative
observations are fixtures, not real physical cleanup/equipment evidence.

Cold verification remains about5.34seconds in both measurements. The stable phase
changes from about0.73 to0.64seconds. These observations establish write suppression,
not a general response-time target or the exact cause of the earlier trace-claims
browser failure. The original515/1 result remains failed and qualified separately.

The trace-claims test now attaches at most512 request metadata events, explicitly
counting omitted events. It records request identity, relative path, method,
timing, status and revision ETag; it captures no credentials, headers other than
ETag, request bodies or response bodies. Removing the added hooks restores the
exact original test. All workflow assertions and timeouts remain unchanged.

Current successor verification passes fresh1078 backend,73 affected browser,
full516 browser and performance2 with321 selected inputs unchanged across all
stages. Zero failures/errors/skips/flaky are recorded in those stages; the one
existing backend framework warning remains. Final reports, XML, logs and hashes
are retained under final/. The original515/1 and exact uncaptured request timing
remain qualified; a new passing cohort does not rewrite old outcomes.

Source is still a verified working-tree successor, with clean committed Linux
package binding pending. Counts47/43/10 and zero accepted milestones remain
unchanged; native Windows, actual hardware/provider evidence and independent
full acceptance are still open. Preliminary snapshots remain historical.

Public profiler excerpts redact their fixed isolated-fixture bootstrap value.
Exact executed programs remain private; source-redactions.json binds original
and sanitized hashes without retaining that credential publicly.

The final TypeScript/Vite rebuild also passes and reproduces all 321 selected
input hashes, including the six UI assets exercised by browser/performance checks.
See final/type-build-verification.json.

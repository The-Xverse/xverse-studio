# ADR-0004: bounded reuse of exact authoritative validation reports

Status: implemented; measured successor performance is recorded separately. Date: 2026-10-25.

The retained 200-element/400-connection browser workload failed the unchanged 3,000 ms p95 open and
validation target at 3,214.8 ms. An isolated diagnostic then measured five unchanged project reads at
4.7–10.2 ms and five unchanged authoritative validations at 1,554.2–1,979.4 ms. The original failure and
uncached diagnostic evidence remain in `evidence/studio/M2-review/performance-failure-before-repair/`.
No acceptance threshold or workload was relaxed.

The server-owned XDL adapter may reuse an exact read-only validation report. It still enforces source
count/name/byte limits before any lookup. The cache key covers every explicit source name and exact
authored byte, installed public validator source closure and package/dependency identity, packaged
core schemas and every admitted local profile-schema byte. Comments, path changes and formatting are
therefore distinct cache inputs even where executable semantics are equal. Schema/source identities
are checked before and after reading or generating a report; a changing/unavailable identity prevents
cache insertion. Public-library unavailable/error outcomes are never cached.

Each adapter has at most eight LRU entries, eight MiB of serialized reports and eight MiB of aggregate
contributing source bytes. A single source set over two MiB is not cached. Eviction is explicit and
bounded. Returned dictionaries are separate deep copies, so a consumer cannot mutate a future
authoritative result. Access is serialized across the adapter's report cache to avoid duplicate work
for simultaneous unchanged validation requests.

This is memoization of actual public-validator output, not another validator or executable model.
Compilation is never cached: every explicit compile, preflight admission, effective-input comparison,
ownership check and worker-side compilation continues through its normal current authoritative path.
Provider capability/authority and live readiness are not inferred from a validation-cache hit.

Focused tests ran red before implementation (five failed, one passed), then all six passed. They cover
actual public API invocation counts, source/comment/path/schema misses, returned-object isolation,
entry and result-byte eviction, source limits before lookup, unavailable reader failures and repeated
fresh public compilation. The full unchanged browser/performance workload must be repeated on the
successor candidate; these unit checks alone do not establish the performance gate or native Windows.

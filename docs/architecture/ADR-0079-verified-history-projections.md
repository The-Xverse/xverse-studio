# ADR-0079 — Retain bounded projections of verified terminal history

Date: 2026-11-05. Status: component verified; full live and finite repeats pending.
Traces: T096; NFR-007/008; AC-010/011/030. Windows remains frozen.

The contributor instrumented full Stop case on760970d passes, but is diagnostic
and does not replace uninstrumented Stop/Cancel repeats. During pressure, most
input operations take about0.04–0.07 seconds, with occasional metadata-lock waits
raising that to0.27–0.32 seconds; HTTP totals commonly take0.45–0.57 seconds. Owner
and mailbox atomic writes each take roughly0.004–0.014 seconds. Presentation and
request scheduling remain substantial costs outside input publication. These
measurements do not establish a complete single root cause.

Independent source-backed profiling shows each identical terminal50,000-record
history query rescanning facets and receipt/quality metadata over all records,
despite unchanged verified canonical bytes. The source-backed counterexample
retains three full scans for three identical requests. This is repeated derived
work, separate from canonical verification or authority.

Keep ordinary run reconciliation and current anchored journal verification on
every history request. Only after integrity is valid, the run is terminal and its
whole declared digest has been verified, retain the derived history projection.
Bind its key to run/snapshot, complete journal digest, last record digest, actual
record count, terminal state, evidence scope and the entire typed query. Current
invalid/unavailable/partial/running sources cannot use this cache. Nothing grants
provider authority or a new clock/quantity interpretation.

One application retains at most eight projections and4MiB of serialized JSON;
an entry is at most2MiB and32,768 traversal nodes. Conservatively bound UTF-8/JSON
escaping and pending nodes before serialization. Oversized projections preserve
the original response behavior and are not retained. Only cache lookup/insertion
holds its own short lock; projection, encoding and fresh JSON decoding occur
outside it and outside the lifecycle metadata lock. Concurrent misses may compute
independently. Return a fresh JSON observation so caller mutations cannot change
another result or cached canonical objects.

Source bytes/digests, unknown payloads, page counts, filters, clock uncertainty,
quality/gaps and public response shape remain unchanged. No source verification,
session/capability check, queue limit, lease or live workload is relaxed. Verify
same-count source changes, current corruption, query/scope separation, bounded
retention/oversized fallback and the actual full pressure/finite workloads before
claiming acceptance. Keep all earlier failed and instrumented results qualified.

Component evidence: the original six copied-source cases retain three full-scan/
retention failures and three passes. The successor passes34 focused cases, then
the combined210-case affected cohort including additional byte-budget eviction
and returned-object/canonical-capture isolation checks. Native contact attempts
are zero and selected source bytes remain unchanged. Actual current source
corruption still returns invalid; same-count valid content changes cannot reuse
old results. Oversized results retain their original behavior without caching.

A separate six-second offline concurrent reproduction on copied terminal sources
preserves original files and makes no native contact. Mean history request work
is0.009 seconds and mean observed-run read work0.015 seconds; initial maxima around
0.26–0.29 seconds remain retained. Earlier pre-successor means were0.241/0.186
seconds under that diagnostic workload. This is combined offline evidence, not an
isolated causal attribution, actual input latency or a new live/cold-start SLA.

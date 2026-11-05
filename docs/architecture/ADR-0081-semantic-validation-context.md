# ADR-0081 — Preserve the admitted validator context in semantic edits

Status: accepted for implementation; component verification required.
Date: 2026-11-05.

Semantic edits currently construct a default XDLAdapter even when their project
already has a configured adapter. This loses the selected local schema context
and discards its bounded exact-input validation cache. Function profiling also
identifies repeated public validation/YAML parsing in binding transactions; this
does not establish the cause of the earlier concurrent timeout failures.

Actual regression cases change an admitted schema after warming validation. The
configured public validator rejects the current authored bytes, while a fresh
default validator accepts them. A semantic HTTP edit then returns200; rebinding
advances its source revision before its incompatible follow-up list read fails.
Semantic editing already requires a valid authored source set. Explicit expert
source editing remains the route for preserving and repairing invalid drafts.

The semantic helper accepts an optional trusted adapter. Application semantic
edits, rebinding and generic campaign preparation pass their existing adapter;
standalone callers retain the existing default. This is an internal Python
dependency, never project/profile metadata, an HTTP option or execution authority.
Both before/after source validation use the supplied context. Unsupported schema
results refuse before source promotion. Installed-provider campaign preparation
continues through its separate admitted mapping.

The existing validation cache remains bounded and keyed by exact source/path,
validator closure and local schema bytes, with independent returned copies and
failure/invalidation checks. Its policy and quotas are unchanged. Compilation
remains a fresh authoritative public call; no compiler result or execution
permission is inferred from a cache hit. No provider/default descriptor fallback,
industry dispatch, canonical-evidence rewrite or device operation is introduced.

Affected traces: T042, T057–T059, T096 and T038/T097. Verification must retain the
actual failure/rollback cases, existing semantic/cache/refusal checks and actual
native binding journeys. Profiled CPU measurements and lightweight concurrent
timing are distinct. The earlier12/2 timing failures remain unresolved unless
stronger evidence establishes their cause. No task or milestone closes here;
Windows remains independently frozen and the full original goal stays active.

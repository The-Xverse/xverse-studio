# ADR-0051 — Composition uses the selected admitted provider

Date: 2026-10-30. Status: implemented; scoped Autoverse integration verified.

## Context

The native run facade discovers admitted installed providers, but connection and
deployment projections still use only the built-in registry. Actual Autoverse
connection, resolution and comparison queries fail404 after discovery succeeds.
The browser's Connections view also omits its selected execution provider.
Rebinding validates source against the reference configuration regardless of
the selected installed provider. These paths disagree with preflight.

## Decision

Inject the existing validated run-facade descriptor source into web composition.
Connection admission, resolution, comparison and rebinding use that same source;
unknown identities still refuse without fallback. Standalone deployment callers
retain their existing built-in defaults. Comparison captures one descriptor and
uses it for both sides, alongside one captured project revision/source set.

Rebinding uses the installed provider's existing static configuration mapping
after descriptor availability checks. It does not contact readiness resources,
resolve external bindings, acquire a runtime or create an execution permit.
Supported static intent remains `preflight_required`; unsupported source mappings
remain blocked. Preflight and Start retain all actual admission checks.

Pass the browser's selected provider through Connections. Bind both results and
errors to project/revision/provider and reject mismatched response context; abort
old requests when that context changes. Provider metadata supplies the semantics;
no industry branch or new platform API is introduced.

## Verification

Use actual enrolled classic/platform Autoverse declarations for combined API
regression, typed connection/coupling negatives, source/layout/history/conflict,
profile/parameter/placement and supported-copy migration. Retain the original
22fail/10pass result and the pre-test foreign ROS plugin-loading failure separately.
Exercise the browser composition views and a complete admitted actual demo before
claiming live integration. Static composition does not establish model fidelity,
physical access, another industry's execution or complete milestone acceptance.

Final verification: 54 actual classic/platform API cases and one complete native
browser/demo session pass on candidate `19084f8fb883757b5648863f3b2b107154ac36db`,458 committed inputs/six
new UI assets. Native cleanup and immutable-input readback agree. T068 complete;
full acceptance and milestone review remain open. See
[evidence review](../../evidence/studio/M2-integration/review.md).

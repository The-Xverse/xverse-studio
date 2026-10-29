# Independent scenario authoring review — findings before repair

2026-10-25, Linux. Reviewer did not author experiments/authoring.py or its scenario dispatch branch. Reviewed helper, generic edit dispatch, public Scenario schema and contract/HTTP tests. This review does not cover a native Windows lane.

## SCN-I01 — typed observer deletion can leave an admitted evaluation definition dangling (MEDIUM)

Concrete probe retained in independent-observer-reference-probe.json, including exact source digests. Starting from the owned reference project, add a second valid observer, point the admitted `io.xverse.studio.experiments` definition's signal.observerRef at it, and retain the original observer/metric. Public XDL validation and snapshot_definitions both accept this source. `remove_scenario_item(observer, other-observer)` then succeeds and public XDL validation reports valid, while the preserved evaluation payload still references other-observer and snapshot_definitions fails DEFINITION_REFERENCE_UNRESOLVED.

Execution is still blocked by reference-provider exact-topology admission, so this is authored reference integrity rather than a runtime authority bypass. The typed deletion should refuse when retained admitted/opaque references depend on the item, or require an explicit atomic reference repair before deletion. Do not silently remove evaluation definitions or rewrite their immutable identity. Add a regression proving transaction refusal preserves full original source and a positive atomic re-reference/remove transaction remains possible where supported.

Other reviewed boundaries: edit dispatch selects exactly one Scenario and checks qualified resource/item identity; public full-set validation runs after the transaction; helpers do not import a runtime or execute source payloads; nonfinite/oversized patch payloads and per-kind creation counts are bounded; merge updates preserve unselected opaque action data and comments supported by round-trip YAML. Existing tests cover these boundaries, but no independent test receipt is claimed here yet.

## SCN-I02 — deeply nested small payload escapes typed bounded rejection (MEDIUM)

Concrete helper probes in independent-depth-probe.json / independent-depth-probe-600.json. A 180-level initialConditions object is safely rejected by the public YAML parser. A 600-level object is only 7,234 JSON bytes (below the advertised 64 KiB edit cap) but passes json.dumps and then raises an unhandled RecursionError during mutation/deepcopy rather than XDLRejected. Original sources remain unchanged. Bound JSON depth/node count iteratively before copying/serialization, or catch recursion at the full semantic-edit boundary with a typed refusal; retain limits and reference integrity. The same generic deepcopy boundary should be assessed for other editable arbitrary properties, including logical-asset limits. This is a robustness/bounded diagnostic issue, not a proven execution or filesystem escape.

SCN-I02 HTTP confirmation: depth-600 edit returns 500 INTERNAL_ERROR; revision remains 1 and exact source unchanged. See http-depth-before-repair.json and reproducible http_depth_probe.py. Desired behavior is a bounded typed 422 rejection before recursion, with the same preservation guarantees.

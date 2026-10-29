# Composition implementation review

Date: 2026-10-25. This is an implementation self-review, not an independent milestone acceptance.
The initial service tests ran red for missing catalog/profile/deployment modules, then 12 tests passed
after implementation. HTTP selection, real owned variant execution and profile/catalog tests then
passed five cases. No external provider or Windows execution is claimed.

| ID | Finding before repair | Required correction |
|---|---|---|
| COMP-001 | Cloning a Scenario changes each assessment definition's `scenarioRef`, but named metric references still pin the source definition's digest. A new regression against actual snapshot admission failed `METRIC_IDENTITY_MISMATCH`. | Validate the original dependency graph/pins, then update only explicit cloned dependency pins in metric-first order after changing the authored clone's scenario identity; preserve original source definitions and actual new compiled identities. |
| COMP-002 | The pinned public XDL validator throws `AttributeError` for `metadata: []` before emitting schema diagnostics. One of seven invalid-draft cases failed before the adapter guard. | Return `XDL_PLATFORM_FAILURE` with validation unavailable, no executable plan and empty graph; retain exact source, without recreating semantic validation. The guard is implemented and expanded XDL/service regression passed 39 tests. |

Retain original observations above. Final affected verification and any independent review are
recorded separately; these findings do not mark M2 or its native/live gates complete.

Final affected verification: **55 passed** in 39.11 seconds, with all 12 captured source identities
unchanged throughout. `verification.json` records the exact commands, sanitized environment, outcomes,
hashes and limitations. COMP-001 is repaired by validating original metric pins and refreshing only
the cloned definitions' explicit pins in dependency order; snapshot admission now accepts the clone.
COMP-002 returns the explicit unavailable platform-failure diagnostic and preserves source. The suite
also includes a real HTTP-selected variant run proving its effective plan matches the selected
authoritative plan, mismatch rejection, profile lock concurrency, missing-profile resolution,
namespace/unsafe-field negatives and metadata-only artifact registration. Ruff checks passed for
owned modules/tests. Native Windows and independent external/live acceptance remain unfinished.

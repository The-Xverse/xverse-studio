# ADR-0018 — Read-only physical inventory and binding observations

Status: accepted for the owned T072 backend component; physical-provider admission remains blocked.
Date: 2026-10-26.

## Context

Canonical XDL already represents a binding through `logicalRef`, `targetId` and the target's
`externalAssetRef`. The isolated lab helper did not connect those declarations to the server-owned
inventory. Inventory dictionaries could contain private endpoint data, and a failed provider could
look indistinguishable from an empty inventory. T072 requires inspectable identity, metadata and
readiness without granting physical authority.

## Decision

Expose a bounded public inventory projection and a read-only physical-binding observation for one
selected authored Deployment. Authoritative validation precedes parsing and inventory resolution;
requirements come from the selected System's endpoint/interface declarations, not a request-supplied
contract. Bindings retain their existing logical references, target and asset references. Existing
source editing persists canonical declarations; no second binding store is introduced.

Public inventory uses an allowlisted shape. Endpoint credentials, private provider payloads and
unsupported metadata are not echoed. Supported observations retain their evidence scope; absent
identity, firmware, metadata, interface or provider evidence remains unknown or blocked. Provider
inventory failures and bounded/incomplete observations remain visible through stable diagnostics.

Identity resolution, interface compatibility, metadata availability, provider admission, availability
and active authority are separate facts. An inventory record's admission-looking label cannot confer
permission. The current physical activation/reservation APIs remain unadmitted, default inventory
remains empty and fixture observations cannot become live acceptance or active-operation readiness.
Resolution performs no reserve, command, probe, driver load or endpoint contact.

This extends inspection alongside ADR-0015. Its runtime admission remains unchanged: a read-only
inventory match does not resolve the missing admitted physical execution path, remove its blocking
compiler/provider diagnostics or validate behavioural equivalence. No secret handle is resolved.
Dedicated UI binding forms and controls remain T075.

## Compatibility and verification

The API addition is a GET under the selected project/deployment variant, tied to the current project
revision and selected document. Invalid or unreadable source cannot yield an apparently resolved
binding. Existing XDL, source bytes, semantic digests, project exports and active run snapshots are
unchanged by inspection.

Verify source save/reload and deployment selection, canonical interface mismatch, missing/malformed
inventory, unknown identity/firmware, provider failures, private-data omission, bounded results,
fixture scope and absence of delegated operations. Existing physical/hybrid contracts remain
regressions. These owned tests cannot pass AC-021–AC-024 live hardware cases; native Windows testing
remains held at user request.

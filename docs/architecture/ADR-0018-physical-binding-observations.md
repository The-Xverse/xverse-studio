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

## Inventory presentation amendment — 2026-10-27

The independent read-only portion of T075 now consumes the public inventory projection
in `features/lab/LabView.tsx`, preserving the existing application export. Provider
admission remains a separate, explicitly unavailable fact. A failed or incomplete
inventory observation cannot establish absence; successful empty pages state only
what that page returned. Loading, HTTP failure, malformed/unsupported responses,
provider diagnostics, truncation and further pages remain visible.

Identity and firmware/artifact observations, metadata coverage, declared interfaces,
provider OS declarations, fixture/evidence scope, availability, permission and active
readiness are displayed separately. An observed firmware revision uses the current
`firmware.status/version/digest` shape; an unobserved declaration remains unknown.
The public `physical: false` also covers a missing source declaration. It is shown
as not confirmed physical, without inventing a virtual or simulated realization;
an asserted physical flag is explicitly a declaration, separate from canonical XDL
realization and live-device admission.
Raw inspection uses only bounded public fields. Strings render inertly, including
metadata that resembles markup. Admission-looking flags cannot enable controls.
String bounds count Unicode code points consistently with the backend projection.
A bounded UTF-16 precheck avoids expanding oversized strings while preserving valid
supplementary characters at the public character limit.
Reservation and connection-test admission, durable ownership and actual-device cases
remain open under T074/T075/T080; this is no physical-provider integration claim.

Refresh starts a new observation at the first page. Each page is a separate current
GET, with at most 200 returned rows, forward cursors within the backend's 1,000-entry
bound and at most ten retained page positions for its default 100-row requests.
The UI does not merge pages into a supposedly frozen device inventory. A failed page
clears its current rows and offers explicit refresh. Reads have one active request,
an abortable 30-second client deadline and departure/generation guards. Pending native
resubmission cannot enqueue extra reads. Completion focuses the observation heading
or current error only after an explicit refresh/page action, while its origin or BODY
still owns focus and no modal has superseded it. Initial loading preserves navigation
focus; delayed completion cannot publish an error in a departed context.

Verification adds native keyboard journeys at both required viewports over the actual
empty/unadmitted API and labelled synthetic public-shape observations generated by
the real backend projection. Controlled HTTP/shape/page fixtures establish UI behavior,
not live hardware. Focused checks perform no mutation, reservation, probe, Start or
device operation; real inventory/project/run lists remain unchanged. Native Windows,
actual assistive technology and milestone acceptance require separate evidence.

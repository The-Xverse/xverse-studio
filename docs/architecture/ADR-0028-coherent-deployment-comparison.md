# ADR-0028 — Coherent deployment and hybrid declarations

Status: backend and browser implemented under verification; independent acceptance remains open.
Date: 2026-10-28.

## Context

T078 requires compatible substitution, shared logical topology, changed time/control/fidelity
capabilities and explicit physical/cleanup uncertainty. The existing variant comparison combines two
independent resolution responses. Their project revision is not checked by the browser, and the
resolution route previously ignored a requested revision. Equal System reference text alone cannot
establish that both responses describe the same captured authored state.

The selected platform can validate physical declarations while refusing their compilation or provider
realization. Its refusal stays authoritative. No actual device, admitted physical provider or measured
synchronization environment is available. Static comparison cannot close AC-023/AC-024.

## Decision

Add an authenticated read-only comparison route requiring two distinct Deployment document IDs, one
expected project revision and a selected provider descriptor. Read Project once, check the revision
and committed source integrity, and validate the complete captured source set through the selected XDL
adapter. Both resolutions consume that same source dictionary and one captured provider descriptor.
Refuse different or unresolved Systems instead of pairing unrelated element IDs.

Return the shared System document's exact source-byte digest as an inspection witness. It is not a
replacement XDL semantic digest or executable identity. Existing semantic/plan identities remain owned
by platform validation/compilation. This projection creates no XDL or durable Studio resource.

Separate authored target capability strings and Deployment/associated Scenario time mappings from
provider-declared operations, clock domains, native support, maturity and fidelity limitations.
Declared tolerances never become measured synchronization evidence; physical state and cleanup remain
unknown, fidelity unverified and fresh preflight required. No provider probe, reservation, command,
run or canonical edit occurs. Imported declarations never grant an operation.

The inspected selected `xverse-xdl` 0.4.0 Scenario schema uses `sourceTimeDomainId` and
`targetTimeDomainId`, with no mapping ID; Deployment uses qualified references and an ID.
Read-only normalization retains those distinct source shapes. Scenario mappings carry a null
`mappingId`, their Scenario owner and `/spec/timeMappings/{index}` pointer. It never adds an ID to
authored XDL. The existing resolver's incorrect Deployment-shape assumption is repaired alongside
comparison; clock-relation traversal keeps qualified System identities. The actual valid-Scenario
failure, schema digest and successful successor stay in the evidence history.

Existing single-resolution clients may omit revision for compatibility. A supplied revision is now
enforced, and committed-source integrity is required. Browser resolution reads supply and validate
their context. The comparison browser consumes only a coherent paired response, rejects mismatched
metadata, and suppresses replies after a newer context or navigation. Read completion does not move
focus away from subsequent user intent or a dialog.

Comparison bounds are advertised and enforced: 1,000 bindings, targets and combined declared mappings
per variant, 64 target capability strings and 2 MiB response bytes. Browser tables remain bounded.
Mapping collection stops after the limit plus one entry before refusing the comparison. Target and
mapping tables show 50 rows per page. The browser refuses unsupported metadata/value shapes rather
than claiming an empty or successful comparison.

## Verification and scope

Retain the initial fixture setup failures separately from the corrected published-baseline negatives.
Verify stale revisions, external source changes, invalid source, different Systems, missing documents,
provider changes, limits, one captured read and unchanged Project/run state. Browser journeys cover
actual authored differences, unsupported physical declarations, context/focus/storage-independent
reads, failures and malformed metadata at both required viewports. Labels distinguish controlled
transport observations from actual server outcomes. Repeat affected deployment/physical-placement and
shared application checks; retain exact candidate and clean package evidence.

T078 remains partial until its dependencies and actual physical substitution/time/stop evidence exist.
Native Windows, human/AT/SADS and independent milestone acceptance remain separate open gates.

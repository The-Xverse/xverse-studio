# ADR-0065 — Playback of original observation records

Date: 2026-11-04. Status: implemented and verified for the recorded Linux component.
Traces: T091, T097; FR-059, FR-060; AC-029, AC-031.

The completed Autoverse recording contains observation.available records with
external-interface receipt payloads. They have no admitted synchronized signal
projection. The existing plot correctly refuses them, but its empty state hides
the fact that original observation records remain available for inspection.

Add a generic read-only record browser in the Observations view when plot samples
are absent. It uses the existing authenticated, filtered history endpoint with
type=observation.available, at most20 records per page and bounded cursor history.
It displays the original selected record as JSON, including identity, payload,
source-time metadata and receipt metadata without reinterpretation. Large JSON
display is explicitly truncated at65536 characters; canonical bytes stay intact.

Playback advances through the current page at a declared display interval. It
does not recreate simulation timing, align clocks, convert quantities, infer
coverage, evaluate assertions or call a provider. Invalid/unavailable integrity
allows inspection with the original verdict and disables automatic playback.
Signal-field filters cannot be applied to opaque payloads; the UI requires that
filter to be cleared. Other original history selectors remain enforced server-side.

Run/snapshot/filter changes and leaving Observations invalidate requests and stop
playback. Late responses cannot reopen a departed view or replace newer context.
Reads have a15-second display deadline. Page completion restores the original
control or selected record only while the original focus intent remains current;
intervening focus, keyboard or pointer intent takes precedence.
Errors, page boundaries and records omitted from the current page stay explicit.
Controls support native keyboard operation and visible focus at both viewports.
No industry branch, backend API, ownership, execution or evidence format changes.

Verify actual copied Autoverse records against the original canonical journal at
both viewports, with native keyboard playback and paging. Retain separate labelled
transport-failure/integrity/shape fixtures and late-response checks. Preserve all
source journal/snapshot bytes and execution ledger counts. This work does not
close T091's real rerun prerequisite, Windows or complete milestone acceptance.

Final source9895675 passes22 actual/labelled native browser checks, the retained
comparison journey at both widths, and all original finite benchmark thresholds.
All541 selected inputs and six reproduced UI assets bind the final phases.
See evidence/studio/M4-original-observation-playback-20261104/. T091/T097 stay open;
counts71/19/10 and zero accepted milestones are unchanged.

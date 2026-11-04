# ADR-0062 — Protected export inputs and truthful inert dependency inspection

Date: 2026-11-04. Status: implementation and verification in progress.

Actual completed Autoverse 0.3/0.4 recording copies reproduce exports that ignore
changed/missing/linked protected snapshots or changed run-to-snapshot identities.
The evidence importer also overwrites a proven malformed-journal result with
`unavailable` when the source provider reader is unsupported. Internal hash
consistency does not establish provider interpretation or producer authentication,
but unsupported interpretation cannot erase a known integrity failure.

Before creating an evidence export operation or archive, verify the protected
snapshot's original bytes and digest using the existing native snapshot boundary.
Bind run/snapshot/project/revision/provider/semantic/plan identities. Preserve the
exact verified snapshot and captured journal; do not repair or normalize them.
A bad snapshot refuses `SNAPSHOT_INTEGRITY` before operation/idempotency publication.
Original source scope, evidence status, annotations and derived evaluations remain
separate. An intact unsupported journal stays unavailable to the source provider
reader; a known malformed envelope/hash chain stays invalid. Neither grants execution.

Add an optional versioned dependency summary to the existing report schema 1.0;
the manifest still hashes that exact report under evidence envelope 1.0. Its
`dependenciesVersion: 1.0` identifies the original snapshot digest and at most 256
frozen provider/compiler/profile/artifact identity declarations. External payloads
are `not_included`, or `unavailable` when their identity is missing, with
`contentIncluded: false`, `identityStatus: frozen_declaration`, and
`resolution: not_attempted`. This describes bundle content, not current-host
availability, redistribution permission, a package manager or runtime admission.
Portable project locks retain their original declared restrictions separately.
No path is inspected and no dependency is fetched, installed or executed.

Import verifies a supplied summary against the protected frozen metadata using
canonical typed identity; a rehashed availability claim cannot replace those
references. A legacy report without the summary stays inspectable, with a null
summary and `DEPENDENCY_SUMMARY_UNAVAILABLE`. Original reports remain immutable.
Imported inspection keeps its independent integrity/reader/availability verdict
and executionAllowed false. Unknown summary versions fail the versioned bundle
contract without rewriting the original archive. Existing file, credential,
profile and archive limits remain in effect.

Verify actual-recording regressions before fixes, then export/import across isolated
native Linux workspaces, including a clean target without the source integration.
Preserve portable model/plan identity, exact historical evidence, derived results,
annotation history and unavailable dependencies. Exclude private local bindings;
reject them in a portable archive. A separately moved private workspace must mark
its old declarations needs_review without changing model identity or granting
execution. Repeat browser import/inspection and source/root/owner readback.

Traces: T093; FR-061; NFR-004/NFR-009; AC-029. No task ID, original milestone scope,
platform entry point, provider/hardware permission or execution language changes.
Windows and full combined acceptance remain independently unverified.

Portable-request compatibility amendment: an actual-source project with controlled
inert supporting metadata produces a 7.18 MB export, below the old compressed and
expanded caps, but it cannot fit the unchanged 8 MiB base64 JSON request. Bound new
project/evidence exports to `requestBytes * 3 // 4 - 1024`, matching the existing
project uploader allowance (6 MiB minus 1 KiB). Refuse excess before publishing an
operation/download; retain original source/evidence. The 16 MiB expanded/capture
limits, 8 MiB request/decoder safety limits and legacy bounded download access stay
unchanged. No truncation, automatic partitioning, weaker limit or larger implicit
request is introduced. This corrects export/import interoperability; it does not
claim arbitrary-size package support.

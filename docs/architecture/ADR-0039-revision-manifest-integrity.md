# ADR-0039: Inspect the committed revision envelope with its source files

Status: implemented and verified for the revision-envelope boundary. Applies to T008's project metadata
and immutable revision ownership. IDs, dependencies and acceptance remain.

## Finding and decision

Each revision already writes project.studio.json and records its manifest in the
immutable revision ledger. Projects.read, execution admission and export currently
ignore that file. External edits, removal or unsafe replacement can be hidden by
the metadata copy, and source recovery does not preserve the changed envelope.

Inspect the bounded file through the existing secure managed reader. For recorded
revisions compare exact canonical bytes against the sealed manifest. Layout-only
updates remain outside executable identity: compare against the manifest sealed
with the source revision, rather than today's independently updated presentation
metadata. A prior project lacking a history record can compare its envelope's
canonical non-layout fields with existing durable metadata; it has no recorded
textual baseline. Retain its current separate layout behaviour without silently
adopting file content or claiming byte provenance that was never recorded.

Expose discrepancies through existing sourceIntegrity/sourceDiagnostics, with
specific observed missing/unsafe/oversize/modified facts and no file-content echo.
Block semantic edits, new current-draft compilation/preflight/dispatch and new project exports
before allocation while the revision envelope cannot be verified. A current
preflight is not permission to ignore a later external file change at Start.
Read-only inspection remains available. Existing completed receipts retain their
idempotent meaning; inspection does not revoke an already committed operation.

Include the envelope in the existing recovery observation as a sidecar. Preserve
readable changed bytes in the immutable private recovery backup before committing
an explicit recovery as a new forward revision. Never adopt an arbitrary external
manifest as resource/profile/provider/execution authority. Existing adopt_external
still adopts document text only; sidecars/envelope use recorded metadata. Missing
or unsafe files retain observed status without being followed. Restore uses an
already recorded revision. No existing revision, snapshot or canonical journal is
rewritten. Return the same typed revision conflict and existing recovery flow.

Malformed or mismatched history records cannot provide a new baseline; report
unverified observation instead of treating them as a foreign manifest grant.
This is reconciliation within Studio's existing file/metadata boundary, with no
new XDL schema/version, provider installation, command or runtime permit.

## Verification

First reproduce ignored changed/formatted/malformed/missing/unsafe/oversized
manifest files using authenticated APIs and forbid all process launch. Check new
edit/compile/preflight/export and stale-preflight Start refusal before allocation.
Verify readable original bytes remain untouched and recovery retains them exactly.
Repeat healthy layout-only revision identity, legacy-baseline compatibility,
metadata/commit failure, native reopen/migration/exchange and actual browser
recovery checks. Keep controlled corruption distinct from native process evidence.

Existing running work and explicitly re-admitted reruns of independently verified
original frozen snapshots remain separate from the current draft. A conflicting
current envelope never becomes their input or rewrites an accepted receipt.
Verify both cached-export retry and the existing closed frozen-rerun path rather
than expanding a draft conflict into unrelated process authority or termination.

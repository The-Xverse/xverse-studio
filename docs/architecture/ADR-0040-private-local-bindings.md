# ADR-0040: Private project-local environment binding declarations

Status: implemented; Linux storage component verified. Implements T008's missing binding
sidecars within the existing plan; T060 and provider admission remain separate.
No XDL resource family, industry dispatch or runtime entry point is added.

## Storage and authority

Add authenticated GET/PUT /projects/{projectId}/local-bindings. GET of an existing
project without declarations returns bindingRevision0 without allocation. PUT
requires If-Match for this independent binding revision; it never changes source
or presentation revisions. Bound32 entries/64KiB per complete sidecar. Closed
version1.0 records name bindingId, portable reference and providerId, plus one of:
artifact/absolute Linux path; asset/opaque assetId; credential/external secret
handle. Reject extra fields, duplicate IDs/reference-provider pairs, unsafe text,
inline credentials and unsupported versions before publication. Values remain
unvalidated data: do not stat/open a declared path, query inventory, resolve a
secret, install/probe a provider or grant execution/physical authority.

Persist immutable private JSON files under projects/<id>/local-bindings/ outside
authored revision/supportingFiles. Use anchored native secure exclusive writes,
flush/fsync and verified bytes before atomically publishing a SQLite head in the
existing root lock/transaction. Heads pin project/revision/path/digest. A failure before commit leaves the prior head usable. A lost acknowledgement
after a real commit leaves the new durable head observable by GET; never delete
committed files or replay a save to hide that uncertainty. Retain uncommitted unique prepared
files for inspection; use a new unique filename on retry, never overwrite or
remove an unrelated file. Committed sidecar/history membership is outside portable
exports and executable identity. Foreign private files in archives remain inert
and rejected by the existing documented project-kind allowlist.

Read the head and bounded regular sidecar securely; validate exact identities,
format and digest. Missing/corrupt/unsafe content gives a typed unavailable/conflict
state; unsupported versions remain preserved and blocked, never treated as empty
or silently downgraded. Inert private binding corruption does not rewrite XDL or
turn it into execution authority. Normal project edits/layout changes retain the
independent private head; imported/cloned projects get no host declarations.

## Context and movement

Store a server-derived context digest of canonical native data-root path, host
name, OS and architecture. This is a change-detection hint, not host attestation or
a security permit. Never print these context inputs in summaries. Private full
backup/restore and supported metadata copy migration preserve bytes. Another root
or changed context exposes needs_review, with validation still unverified and
executionAllowed false. An explicit new PUT can redeclare entries for the current
context; it cannot prove provider/device/artifact validity. Runtime consumers need
separate reviewed provider inspection/admission before any future active use.
Existing preflight must not consume these unvalidated declarations implicitly.

## Verification and compatibility

Use strict shared request models and generated API/TypeScript contracts. Keep the
new data separate from project/source/layout/snapshot identity and from provider
capabilities. Check real authenticated API authoring/reopen, absent/mismatched CAS,
concurrent writers, exact native persistence, unknown/corrupt heads/files, bounded
values and no contact/secret echo. Inject write/commit failures and test retry with
the old head intact. Verify export exclusion, inert foreign import, private
backup/copy migration, moved-root review and actual native restart. Fixtures and
storage declarations do not satisfy physical or runtime integration acceptance.

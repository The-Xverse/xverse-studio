# Studio project envelope v1

**Status**: planned persistence and interchange contract. XDL remains the system/execution language; the envelope stores references and editor metadata only.

## Layout

```text
project.studio.json
xdl/                       authored YAML/JSON resources
profiles/                  local pinned schemas and declarative presentation metadata
layout/                    presentation-only views keyed by stable XDL references
artifacts.lock.json        references and immutable identities, not embedded credentials
README.md                  human project description (optional)
```

Runs are stored in a separate managed run root, not silently included in project archives. A user may explicitly export an evidence bundle linked to exact project/snapshot identity. Downloadable artifacts are not fetched during project open/import.

ADR-0045 bounds compressed exchange/download capture and aggregate expanded output
to16MiB using anchored native regular-file acquisition. Run evidence verification
describes exactly the included capture, retaining original scope/status and bytes.
The legacy version1.0 `evidence/reference.jsonl` member name conveys no reference
execution claim. Imported detail checks original stored digests/manifest semantics;
local rehashing cannot replace the original report. Source `available` is distinct
from complete coverage, and an unsupported imported reader grants no authority.

## Manifest fields

| Field | Rule |
|---|---|
| `formatVersion` | Exact `1.0`; unsupported major versions open as inspect-only or reject without mutation. |
| `projectId` | Opaque UUID allocated by Studio; cloning/importing as new creates a new envelope identity, leaving XDL identity semantics unchanged. |
| `name` | Display label, string of 1–120 characters, matching project creation. |
| `resources` | Explicit relative file paths and source format for all XDL inputs. No implicit recursive discovery at execution time. |
| `profiles` | Namespace, version, relative schema path, schema digest, optional presentation path/digest. |
| `defaultSelection` | Optional existing System/Deployment/Scenario resource references; never an executable command. |
| `layoutFiles` | Explicit relative paths to sidecars. |
| `artifactLock` | Relative path to artifact-reference lock. |
| `provenance` | Origin/revision/maturity references with no secrets. |

`formatVersion` versioning is independent of XDL `apiVersion`. The envelope does not claim to validate an unknown XDL version. The manifest contains no copy of component topology or runtime plan.

## Authoring and round-trip

The backend retains authored bytes and a parser representation sufficient to make localized semantic edits. Preserve comments, formatting and unknown extension content where the parser supports this; when exact formatting cannot be retained, show the textual diff before committing a rewrite. Semantic preservation is mandatory for supported content even when formatting changes.

Unknown or incompatible profiles are retained as opaque source, visibly unresolved and blocked from semantic execution. Studio must not strip unknown fields or invent a normalized replacement to obtain a green validation result. The authoritative platform validator/normalizer decides semantic validity.

Stable references link canvas elements, properties, source locations and diagnostics. A layout-only save changes the sidecar/presentation revision, never XDL or the compiled plan digest. Changing a display label in XDL may legitimately alter the platform semantic digest; do not confuse it with moving a box.

Edits are transactional and optimistic: expected project revision plus staged file writes and an atomic committed manifest/revision update. Concurrent external file changes produce an explicit conflict. A failed multi-file edit leaves the preceding revision intact and recoverable.

ADR-0042 anchors native atomic writes and revision publication to acquired directory
descriptors. A prepared revision publishes without overwriting a late existing
destination; rollback removes only its recorded original directory identity.
Unknown/rebound names are preserved. Missing secure native publication support
refuses with503 rather than using a weaker fallback. Private atomic files use0600
and newly created directories0700; uncertain unpublished bytes remain outside the
committed revision and convey no execution authority.

## Layout sidecars

Each layout document has `formatVersion`, `viewId`, `systemRef`, positions keyed by ElementRef, collapsed group references, viewport and optional purely visual annotations. Hierarchical subsystem semantics remain in XDL/profile content; a visual group cannot silently become a subsystem. Invalid/dangling layout refs can be removed or remapped without changing model semantics.

## Private local binding sidecars (ADR-0040)

Host declarations live outside the portable envelope and authored revisions, at
`projects/<projectId>/local-bindings/<bindingRevision>-binding-<uuid>.json` in the
managed private root. Their independent version1.0 document contains project ID,
binding revision, a server-derived context digest and at most32 typed declarations
(64KiB total). The SQLite `project_local_bindings` head seals the project, revision,
relative sidecar path and byte digest; it contains no artifact path or secret handle.
Publication uses secure exclusive native writes, verified bytes and a transactional
revision-checked head. Prepared files stay private and do not become declarations
without a committed head. A lost acknowledgement requires reloading that head.

Each declaration has `bindingId`, a portable `reference`, `providerId`, and a kind:
`artifact` with an absolute Linux `path`; `asset` with an opaque `assetId`; or
`credential` with an external `secret://` or `urn:` handle in `credentialRef`.
Inline credentials, executable fields and unknown versions are rejected. These
are unverified declarations: saving/reading does not inspect a path, resolve a
secret, query inventory or grant execution. Project/source/presentation revisions,
XDL resources and compiled plan identities stay separate. Provider resolution and
runtime authority require their own admitted interfaces.

Portable export excludes all private sidecars; import rejects files of that kind
and allocates no host declarations for the new project. Private full backup/restore
and supported metadata copy migration preserve their exact files and head. A root
or host-context change reports `needs_review`, `environmentChanged=true`,
`validation=unverified`, `executionAllowed=false`. The digest is a change hint,
not attestation. Explicit redeclaration updates context without granting authority.
Corrupt/missing/unsafe/future state is preserved and refused, never treated as empty.
Project retirement fences new publications and removes its head with its metadata.

## Artifact and profile lock

Entries include kind, origin reference, immutable digest/revision, license/distribution restrictions when known, required platform/provider compatibility and availability. A mutable image tag alone is insufficient for a reproducible run. Missing immutable identity is a preflight diagnostic, not replaced by a guessed latest version.

Profile presentation may supply labels, descriptions, icons from packaged allowlisted assets, form grouping and help. It contains no JavaScript, Python, arbitrary HTML, executable URLs or shell hooks. Form validation is derived from declared schemas plus authoritative backend rules. Installing executable providers is a separate administrative workflow outside project import.

ADR-0046 recognizes known executable profile fields/URLs in the existing JSON
string security view and known bare/quoted YAML mapping keys before allocation.
It retains original bytes, ordinary documentation and opaque metadata; unknown
profile locks remain unresolved. Import never installs or dispatches a provider,
and execution still requires explicit admitted preflight/Start of exact inputs.

## Import/export safety

Accept only documented archive formats with bounded total expanded size, file count, compression ratio and path length. Reject traversal, absolute paths, symlink/hardlink escape, duplicate normalized names, executable auto-run hooks and files outside allowed project kinds. Extract into a fresh staged directory and validate before allocating the final project. Import never overwrites an existing project by display name.

Portable manifest/archive paths use normalized relative slash-separated names. Reject unsafe/ambiguous portable paths on Linux, including case-insensitive collisions, Windows reserved device names, alternate data streams, drive-relative/UNC roots and trailing-dot/space ambiguities. Native working roots may contain spaces and Unicode; safe containment checks must also account for Linux symlinks and inert foreign link/path metadata. No portable project file embeds a required Linux home path or Windows drive path. Atomic-save and migration tests run on the recorded Linux host with its actual file-lock/rename behaviour.

Malformed envelope roots, resource/profile/layout collection shapes, display names
and layout roots return `MANIFEST_INVALID` before project allocation. Unsupported
format versions retain `FORMAT_UNSUPPORTED`; unsafe paths and bounded-input failures
retain their specific diagnostics. Unknown envelope fields and opaque authored XDL
remain preserved. Importing an envelope never installs a provider or grants authority.

Exports include manifest, authored resources, declared schemas/layout, locks and explicitly selected documentation. Exclude credentials, session tokens, host-only secrets, caches, arbitrary home directories and run evidence unless explicitly selected. Preserve unavailable/restricted artifact references with their limitations rather than copying prohibited content.

ADR-0044 applies known inline authentication assignment/header recognition to
authored text, names, layouts, imports and portable output, including JSON string
escapes. Session/bootstrap/CSRF/refresh/ID tokens and Basic/Bearer headers are
rejected without echo or rewriting historical bytes. External credentialRef and
sessionTokenRef handles remain exact inert references; storing one never resolves
a secret, installs a provider or grants execution.

## Migration and verification

Migrations run on a copy, retain original manifest/bytes, produce a versioned migration report and textual/semantic diff, and require explicit application to replace the working revision. Failure leaves the original readable. Never migrate historical run snapshots in place.

Conformance checks: supported open/edit/save/reopen semantic equality; layout-only digest invariance; comments/unknown extension preservation; cross-profile conflict; concurrent edit rejection; unsafe archive rejection; export secret exclusion; missing artifact identity; and migration rollback.

ADR-0038 implements the existing SQLite metadata0-to-1 transition as an explicit
stopped-root copy migration. It does not introduce another envelope or XDL version.
Only the exact known unversioned records/idempotency schema is supported. Retain
original files and a verified private schema0 backup; produce a schema1 candidate
with a versioned textual/stored-identity diff. Browser sessions are invalidated;
all other metadata, authored/layout/binding files, original receipts and historical
snapshots/evidence retain their exact identities. The report does not reinterpret
unsupported semantics. Activation requires a separate explicit normal launch of
the new root after review. Unsupported versions and incomplete candidates refuse
startup; unknown metadata is not relabelled to obtain readiness.

ADR-0039 verifies the generated revision envelope against its already recorded
manifest before current-draft compilation, new execution or export. Readable
external envelope bytes are retained by explicit recovery as a sidecar; a new
forward revision uses recorded metadata, never arbitrary external declarations.
The sealed source revision is independent of later layout-only changes. Prior
metadata without a recorded textual seal compares known non-layout envelope
fields without inventing old byte provenance. Unreadable/malformed or foreign
history cannot supply a replacement baseline. Existing receipts and separately
verified original frozen rerun inputs retain their independent identities.

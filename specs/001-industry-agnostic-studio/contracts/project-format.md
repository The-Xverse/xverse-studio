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

## Manifest fields

| Field | Rule |
|---|---|
| `formatVersion` | Exact `1.0`; unsupported major versions open as inspect-only or reject without mutation. |
| `projectId` | Opaque UUID allocated by Studio; cloning/importing as new creates a new envelope identity, leaving XDL identity semantics unchanged. |
| `name` | Display label, bounded string. |
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

## Layout sidecars

Each layout document has `formatVersion`, `viewId`, `systemRef`, positions keyed by ElementRef, collapsed group references, viewport and optional purely visual annotations. Hierarchical subsystem semantics remain in XDL/profile content; a visual group cannot silently become a subsystem. Invalid/dangling layout refs can be removed or remapped without changing model semantics.

## Artifact and profile lock

Entries include kind, origin reference, immutable digest/revision, license/distribution restrictions when known, required platform/provider compatibility and availability. A mutable image tag alone is insufficient for a reproducible run. Missing immutable identity is a preflight diagnostic, not replaced by a guessed latest version.

Profile presentation may supply labels, descriptions, icons from packaged allowlisted assets, form grouping and help. It contains no JavaScript, Python, arbitrary HTML, executable URLs or shell hooks. Form validation is derived from declared schemas plus authoritative backend rules. Installing executable providers is a separate administrative workflow outside project import.

## Import/export safety

Accept only documented archive formats with bounded total expanded size, file count, compression ratio and path length. Reject traversal, absolute paths, symlink/hardlink escape, duplicate normalized names, executable auto-run hooks and files outside allowed project kinds. Extract into a fresh staged directory and validate before allocating the final project. Import never overwrites an existing project by display name.

Portable manifest/archive paths use normalized relative slash-separated names. Reject collisions under both supported native filesystem interpretations, including case-insensitive collisions, Windows reserved device names, alternate data streams, drive-relative/UNC roots and trailing-dot/space ambiguities. Native working roots may contain spaces and Unicode; safe containment checks must also account for Linux symlinks and Windows junction/reparse points. No portable project file embeds a required Linux home path or Windows drive path. Atomic-save and migration tests run on both operating systems with their actual file-lock/rename behaviour.

Exports include manifest, authored resources, declared schemas/layout, locks and explicitly selected documentation. Exclude credentials, session tokens, host-only secrets, caches, arbitrary home directories and run evidence unless explicitly selected. Preserve unavailable/restricted artifact references with their limitations rather than copying prohibited content.

## Migration and verification

Migrations run on a copy, retain original manifest/bytes, produce a versioned migration report and textual/semantic diff, and require explicit application to replace the working revision. Failure leaves the original readable. Never migrate historical run snapshots in place.

Conformance checks: supported open/edit/save/reopen semantic equality; layout-only digest invariance; comments/unknown extension preservation; cross-profile conflict; concurrent edit rejection; unsafe archive rejection; export secret exclusion; missing artifact identity; and migration rollback.

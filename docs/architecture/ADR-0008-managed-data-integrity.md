# ADR-0008: Managed reads, private recovery and explicit retirement

Status: implemented Linux component; final combined verification is recorded separately. Windows
installation/testing remains held, and native Windows secure acquisition is not yet implemented.

Path containment and a final-file nofollow flag are insufficient when an ancestor changes during
acquisition. Linux managed reads now walk directory descriptors from the filesystem root without
following links, check directory/leaf identity, require a regular singleton file and verify the held
descriptor before/after reading. Unsupported native primitives produce an explicit unavailable result;
there is no path-only fallback. The local OS account and selected private root remain administrative
trust boundaries; imported projects cannot supply executable commands or arbitrary deletion paths.

Project document reads enforce both one MiB per file and the complete 16 MiB project envelope before
allocation. Invalid UTF-8, unavailable files and unsafe links have typed failures; external bytes remain
untouched. Bounded modified bytes remain readable for inspection with `sourceIntegrity=modified` and
expected/actual digest diagnostics. They are not labelled committed source, and revision-checked
authoritative mutations/execution remain blocked. Derived inspection flags are not persisted as source.

Full private backup/restore holds anchored identities for selected input, reserved output and private
staging for the entire operation. SQLite receives a staged DB plus committed WAL acquired through
held handles, using public backup APIs and Linux directory-descriptor URIs. Source SQLite paths are
not reopened. Final naming checks occur inside restore marker finalization: late failures retain the
owned incomplete marker rather than report usable recovery. CLI maintenance passes lexical paths to
admission instead of resolving a rejected link into an admitted root. Canonical journals/snapshots are
unchanged; restored browser sessions are deliberately invalidated. Checksums prove integrity, not
authenticity. This does not establish native Windows backup support.

Retention separates preview from explicit fingerprint-checked apply. Project/run/artifact registration
IDs are the only selections; no external origin bytes are removed. Historical snapshots and shared
references protect dependencies. Bounded source/metadata proofs reject malformed or incomplete data
instead of interpreting it as absence of references. Project retirement persists intent, quarantines
owned files, transactionally retires metadata with a tombstone/audit, then purges. Uncommitted failures
restore known staged bytes; committed retirement is not reversed. Partial cleanup and explicit residue
retry remain visible. Canonical execution outcomes and assessment verdicts never become successful
because failed evidence was removed.

Compatibility: additive project inspection fields and Studio HTTP v1 retention selectors; no XDL,
provider or evaluator version change, stable task/requirement IDs and immutable historical bytes.
Native Windows secure I/O and held installation/tests, broad campaign/snapshot garbage collection and
full release acceptance remain open. Affected T005/T007/T008/T014/T022/T039/T092/T094/T098; NFR-004,
NFR-005, NFR-009, FR-003/FR-013/FR-063; AC-003/AC-009/AC-029/AC-032.

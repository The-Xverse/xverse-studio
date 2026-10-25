# Independent retention successor review

Original findings and before-repair receipts remain unchanged. The retention owner confirmed source freeze; independent inspection and fixture probes used the exact hashes in independent-successor-verification.json. No retention implementation writes by reviewer.

RET-I01 is repaired: retained collection/link shapes are checked before indexing or dependency iteration, including run-only plans. The exact malformed snapshot/campaign probes now refuse with RETENTION_DEPENDENCIES_UNRESOLVED. RET-I02 is repaired: null/scalar/sequence XDL and unsupported supporting suffixes refuse conservative artifact independence; current file bytes are read through bounded managed descriptors and compared with committed identities. RET-I03 is repaired: record/file byte budgets are reserved before materialization/read, directory discovery is bounded before listing growth, no retention call uses Projects.read/assert_intact/read_bytes/rglob, and growth is refused after the bounded descriptor read.

Actually executed independent checks:

- Five HTTP fixture probes pass: explicit project-only selection/idempotency, immutable snapshot protection, changed-filesystem 409 before effect, artifact metadata-only removal with origin sentinel preserved, and symlink target refusal. Popen was patched to forbid process creation; no provider starts occurred. Source hashes matched before and after.
- Four bounded I/O probes pass: oversized source and aggregate budget reject before os.read; tree proofs precharge bytes; a growing file is refused without reading beyond the reserved original size.
- Six exact malformed-dependency/source probes all return conservative typed ValueError instead of planning removal.
- Five focused failure/recovery tests pass in 1.26 s (four unrelated cases deselected, no skips): real SQLite before-/after-commit outcomes, partial purge plus explicit residue retry, interrupted quarantine restore without replay and conflict recovery without overwrite. Command and exact source/test identities are retained in the verification JSON and failure-tests-successor.txt.

Static ownership review confirms artifact deletion uses catalog records/tombstones and never opens originRef; projects quarantine before metadata retirement and restore on uncommitted failure; committed retirement is not reversed after lost acknowledgement; unresolved stages protect input/residue; partial cleanup reports remaining managed files and requires a new explicit plan. Durable idempotency intent precedes effects, restart marks interrupted application unknown rather than replaying deletion, and per-item checks repeat dependencies/filesystem identity.

No further concrete finding in this reviewed retention slice. This does not replace whole-candidate regression or native platform acceptance. Windows installation/testing remains blocked at user request.

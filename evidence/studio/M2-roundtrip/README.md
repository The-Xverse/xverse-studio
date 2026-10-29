# Round-trip, layout and conflict scenarios against the pinned XDL CLI (T048 Linux execution; task open)

`tests/integration/test_model_roundtrip.py` runs the corpus in `tests/fixtures/xdl/roundtrip/cases.py`
(the T041 corpus paths) through Studio's library adapter and the pinned `xdl` CLI. Each CLI call runs
as `python -I -m xverse_xdl` on the exact bytes at the same relative document paths, with the same explicit profile schemas Studio passes.

- **Admitted examples.** Both examples have equal validity, diagnostics, semantic digest and plan
  digest in Studio and the CLI.
- **Corpus.** Both tools agree on every case, and each case actually changes the authored bytes.
  - These keep identity: comments, reordered keys, CRLF line endings, YAML to JSON, a non-ASCII display
    label, and a non-ASCII document path with spaces.
  - A parameter value change alters both the semantic and plan digest.
  - An unresolved extension is rejected by both tools with `XDL-SEMANTIC-PROFILE-MISSING`.
- **HTTP.**
  - A layout-only save changes no source byte and no revision.
  - A semantic edit changes identity, with the HTTP compilation equal to the CLI.
  - A stale writer gets `412` with the bytes unchanged, and both tools still report the
    pre-conflict identity for the stored bytes.
  - A refused edit keeps the revision.
  - An invalid draft gets identical validity and diagnostic codes from both tools.
  - Restore recovers the exact earlier bytes as a new forward revision.
  - Export/import keeps the exact bytes.

`linux-identities.json` records the observed Studio and CLI identities for each case on this host.

T048 stays open: its bidirectional Linux-to-Windows and Windows-to-Linux exchange clause is blocked at
user request (native Windows), and Linux results are not claimed for Windows.

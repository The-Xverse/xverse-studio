# Component self-review — 2026-11-06

Six actual AT journeys pass on identical599source inputs and unchanged UI assets.
The shared helpers retain real XTest input, actual Orca SSIP output and actual
AT-SPI focus/text/tree observations. Text is bounded printable ASCII, with existing
XKB base/Shift mappings checked before any text is emitted. Modifier release is
paired and the key log stores counts/digests instead of form text. No host keymap
or physical keyboard is touched.

The conditions suite permits a narrow, independently checked copy-local mutation.
Every existing object/revision byte and every other original non-session record
must remain equal; exactly one new sealed revision and its expected files are
allowed. The actual selected XDL adapter validates the edit through the normal UI
endpoint. Read-only inventory/results suites keep the stronger whole-copy equality
guard. Original recordings, frozen inputs and execution ledgers remain unchanged.

The AT snapshot waiter is a bounded observation of a separate asynchronous channel;
it retains unsuccessful observations and fails on missing content or diagnostics.
No timeout threshold was extended. Source/asset hashes, original handles, capture
gaps and cleanup remain explicit. Historical probe failures are not promoted.
This is a component self-review, not complete or independent milestone acceptance.

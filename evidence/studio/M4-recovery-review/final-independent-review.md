# Independent frozen recovery regression review

Final reviewed source: managed_io.py f5c5798c, recovery.py cc3d4a71, test_recovery_safe_io.py ce7b0463. Full hashes and exact existing fixture selection are in final-independent-verification.json. This reviewer made no implementation edits.

Twelve existing repository file-fixture tests actually passed in 0.60 seconds, no failures or skips; stdout is retained in final-existing-fixtures.txt. All data was disposable loop10 state. No external system, network, physical equipment or production data was used; Windows installation/testing remains held.

The fixtures verify final named-output refusal, incomplete-marker recreation after both late input and late output namespace changes, source preservation after interruption, committed WAL preservation without source SQLite writes, original SQLite-path reopen prevention, actual descriptor acquisition through renamed source/output directories, and retention of active output anchors after private staging closes. Successful recovery preserves CRLF/non-ASCII fixture bytes and creates a fresh session context.

Read-only source inspection confirms:

- The helper walks the complete absolute directory chain with directory descriptors/NOFOLLOW and identity checks; ordinary file acquisition checks the opened inode and named entry. Descriptor writes/fchmod are confined to exclusively created files.
- Recovery keeps selected input, reserved output and private-stage anchors for the complete operation. Scope teardown removes only its own anchor, so non-LIFO staging closure cannot drop a live output anchor.
- SQLite receives private staged DB+WAL bytes through held originals and directory-descriptor paths, then validates the normalized image through a held immutable file descriptor. Original mutable SQLite names are not connected directly.
- Restore checks both input and output names before and after marker unlink. Late mismatch recreates the owned incomplete marker and raises. Restore input/output context cleanup has no additional fallible naming predicate after that marker flow. Backup has a final named-output gate before successful completion.

The recorded PRJ-IO-I01 and REC-IO-I02/I03/I04 repairs are supported by the retained before/successor probes and these final existing-fixture regressions. Projects source/link-reader successor had separately passed direct, authenticated in-process and sidecar acquisition probes with actual hook execution; those predecessor receipts remain explicitly source-pinned. No further concrete finding in this recovery regression scope. Whole-candidate verification/publication remains root-owned.

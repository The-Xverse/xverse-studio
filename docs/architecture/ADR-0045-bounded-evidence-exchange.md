# ADR-0045: Bounded native evidence exchange

Status: implementation under verification against Autoverse. T010 remains open.

Actual enrolled Autoverse project exports reproduce successful downloads through
file/ancestor symlinks and hardlinks, and unbounded acquisition before a size
refusal. A retained stopped complete-demo capture reproduces an inaccurate
`owned_reference` report and a journal verification/reopen race. Its original
`available` evidence status also reveals an export/import vocabulary mismatch.
Original recordings and failed observations are retained; no evidence is repaired.

Download and run-export acquisition uses the existing Linux directory-descriptor
walk and unchanged named regular-file check. A bounded capture refuses a file
already above its cap before reading, reads at most the cap plus one byte during
growth, and rejects changed acquisition. Compressed bundles and expanded output
are each bounded to16MiB. Missing downloads return404; missing run journals remain
unavailable, while unsafe sources refuse422, source changes409, excess bytes413
and unsupported secure native access503. No weaker path fallback is introduced.

The original journal verifier is shared with a pure captured-byte entry point.
Run exports verify exactly the capture they include, including original identity,
chain, sequence, prefix and terminal digest rules. The existing evidence reader's
cache/retry bounds remain. Export reports retain the source run's evidence scope
and evidence status instead of claiming reference execution. The version1.0
`evidence/reference.jsonl` archive member stays unchanged for compatibility; its
name is not an evidence-scope claim. Run exports also report their byte size.

Evidence imports preserve the existing source `available` vocabulary without
upgrading it to complete coverage. A reader unsupported for the original provider
continues to report unavailable integrity/coverage and no execution authority.
Detail acquisition anchors every ancestor, enforces per-file and16MiB aggregate
limits, and compares source digests and manifest semantics with the original
stored import. Rehashing a changed local report cannot replace the original
inspection. Lost/unsafe/changed files produce a separate degraded projection;
original reports, metadata and immutable journal bytes are preserved.

Verification uses actual enrolled classic/platform authoring and copies of an
explicitly nominated real stopped Autoverse recording for controlled read faults.
Positive live confirmation requires the complete demo, exact source/snapshot
export, inert import and original cleanup. This does not admit an imported Argus
reader, install a provider, authorize another execution or close all T010 clauses.

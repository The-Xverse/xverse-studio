# Retained-history workload review

The first actual 50,000-event recorded fixture run failed correctness: the reader's 16 MiB file cap
rejected the valid required workload, so fast empty pages did not satisfy the target. The raw 30-sample
record is `history-before.json`; `correctPages=false` and `passed=false` are preserved.

Repair: admit a bounded 64 MiB canonical journal and 100,000 records, retain pages of at most 200,
and cache only verified source projections keyed by file identity/size/change timestamps and the
expected final digest. Cache retention is bounded separately; source changes invalidate it. This
changes a resource bound to accommodate the existing specification workload, not its acceptance target.
The successor must prove 200 correct records and valid integrity on every measured page. Browser
presentation and native Windows remain separate verification lanes.

# Legacy delivery successor

The three added legacy cases pass, followed by the complete 25-case owned transport cohort on unchanged before/after source hashes. The original red receipt (two failures and one compatibility positive) is retained.

A legacy 1.0 consumer now receives all five consecutive original records even when their combined bytes exceed one pending batch. It receives no version 1.1 control frames and no silent omission. The bounded batches continue from their prior sequence; the independent canonical reader and original file bytes are unchanged. An oversized first 1.0 API frame is rejected with typed HTTP 413 STREAM_FRAME_TOO_LARGE before headers, rather than a successful empty body; no subscriber lease remains. A valid index-only cursor requires 410 STREAM_RESYNC_REQUIRED with LEGACY_CURSOR_WITHOUT_SOURCE_PROOF in 1.1, while the explicitly selected legacy 1.0 compatibility path resumes from that index without claiming source-generation proof.

Only new disposable fixture journals were used. No historical runtime evidence, provider implementation or broader reader cryptographic contract was modified by these test additions. Windows work remains held.

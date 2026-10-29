# Whole recovery response budget successor

The three new whole-response cases pass, followed by all 28 owned transport cases on unchanged before/after source hashes. The three original failures and independent finding remain retained.

The tests measure the complete canonical UTF-8 response, including run metadata, history, cursor, watermark, counts and URLs, against both 16 KiB and 1 MiB configured budgets. The returned original metadata remains present, omission counts equal source count minus returned history, and the watermark still identifies the exact last source record regardless of presentation omissions. A realistic 32-definition summary shape alone exceeding an 8 KiB budget is refused with typed HTTP-status 413 STREAM_RECOVERY_TOO_LARGE rather than returning an oversized recovery object.

The summary is synthetic metadata for a bounded serialization fixture, not a claim of actual32-definition project admission or execution. Each new journal remains independently valid and byte-identical through the recovery read. No product, provider or reader contract source was changed by this test author. Windows work remains held.

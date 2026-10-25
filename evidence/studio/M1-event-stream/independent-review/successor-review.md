# Independent successor review — event transport and browser session

The four recorded findings are repaired in the reviewed candidate. Original failing receipts remain alongside successful successors. No product, test, requirement, or traceability files were changed by this reviewer.

| Finding | Independent successor result |
| --- | --- |
| STREAM-I01 response-start disconnect admission leak | PASS: synthetic ASGI header OSError and cancellation through the actual API route/response both leave zero leases, including before iterator entry. |
| STREAM-I02 malformed event kind changes SSE framing | PASS: typed 422 `STREAM_ENVELOPE_UNSUPPORTED`; original reader integrity remains `valid` and original bytes remain unchanged. |
| STREAM-I03 live-prefix browser recovery rejection | PASS: actual production running-source resync is accepted by the current TypeScript gate with `verified_prefix` preserved. Gate also accepts valid and rejects invalid/unavailable. |
| STREAM-I04 unproven legacy index promoted into v1.1 proof | PASS: bare and run-qualified legacy v1.1 positions require 410 resync; v1.0 inspection remains available; the prior opaque proof still detects a real valid-chain replacement. |

The same semantic driver rechecked exact byte-pressure gap bounds, bounded frame/batch sizes, exact resync source watermark despite history omissions, valid-chain discontinuity with unknown loss count, and live unknown-state heartbeat/iterator-close release. All original fixture journal bytes remain unchanged by the inspected operations.

All four successful driver receipts have equal source-before/source-after hashes. Backend events source: `c018d66dcf4d6cc9858ac3bb5b4ce83cd94a28b4f6b1eb1098841a17988d403d`; API source: `682eb0ca1e9963a3e5b0df32ce6c467e2f592663a64d616234daa49d07d330a2`; session: `dc0e056bbce2a0b1bbf4309f2d36353a470cc844b19ba41aca58004ac179c624`; protocol: `f8b0229f58ebeaac0ab341d4dcce525f3ac3fefc203e8286ac5f0961e3ae3b2c`; App: `abe43d56124bf311c5eeda32b61af1a82a6b921551f4ca3d057261b5aabf0bf6`. Per-receipt exact hashes include the unchanged reader where applicable. The TypeScript probe records its separately observed transformed source hash.

Read-only browser source review confirms acknowledgement follows awaited consumer acceptance; canonical event identity/order/prefix checks precede acknowledgement; gap and expiry handling await state/history recovery before adopting its watermark; run-context disposal aborts stream/JSON readers; shared generation checks prevent stale poll/recovery responses from replacing current state. Reconnect issues read requests, never Start or runtime control. App bounds pending/visible presentation and preserves explicit reader-integrity scope and display omissions. No additional concrete correctness finding remains in this assigned scope.

Commands executed (each uses disposable repository-local scratch):

```sh
.venv/bin/python evidence/studio/M1-event-stream/independent-review/startup_disconnect_probe.py
.venv/bin/python evidence/studio/M1-event-stream/independent-review/semantics_probe.py
.venv/bin/python evidence/studio/M1-event-stream/independent-review/legacy_cursor_probe.py
.venv/bin/python evidence/studio/M1-event-stream/independent-review/running_recovery_probe.py | node evidence/studio/M1-event-stream/independent-review/running_recovery_probe.cjs
```

These are finite direct production-function and route/ASGI-lifecycle probes, not an independently executed native browser/server suite. Author-owned backend 22-test receipt is separately recorded under `../reviewed-final/`; frontend author browser receipts remain under `../../M1-session/`. Final expanded frontend browser lane was pending when this review was recorded. This supports the reviewed Linux implementation component; it does not close both-platform T025 browser obligations, physical/external-provider acceptance, native Windows hold, or M1 as a whole. Source review and fixture proof are identified separately from live acceptance.

## Follow-up scope audit and STREAM-I05 successor

A second literal-scope audit identified STREAM-I05 before repair; see the retained response-size failure and `literal-scope-and-results.md`. Its independent successor now passes. The same production response-size driver returns 1,042,871 encoded bytes within the browser's 1,048,576-byte limit, preserving the same 14,955-byte public run metadata and exact source watermark. It returns 184 display records and truthfully reports 16 omissions, versus the predecessor's oversized 187-record response. Reader integrity remains valid and source bytes remain unchanged. A separate configured 8 KiB run of that driver refuses the 14,955-byte metadata alone with 413 `STREAM_RECOVERY_TOO_LARGE` and retrieval routes. Exact stable before/after source hashes are in `recovery-size-successor.json`.

Read-only inspection confirms complete-response accounting before history selection, 4 KiB headroom for array/separator/count growth, and final bounded UTF-8 serialization. Metadata and each record retain their individual 10,000-node checks; the combined final node ceiling scales only with the bounded selected item count. Original evidence and metadata semantics are preserved. The earlier root-authored legacy repairs independently pass the contiguous-prefix and oversized-first/later-boundary checks in `legacy-bounds-successor.json`.

The browser's final typed-413 branch cancels the response body, reports `Recovery presentation limit reached — inspect paged retained history`, and stops automatic recovery before adopting a cursor. Source inspection found no new issue in this change. Its author-owned 14-case protocol receipt is under `M1-session/recovery-limit-green`; this reviewer did not rerun that lane. The separately inspected author 16-case receipt under `M1-session/expiry-green` demonstrates actual native replay expiry during a running owned reference execution and explicitly scopes the same-state-version Results negative as controlled HTTP metadata.

Final reviewed source hashes:

- events: `5ca8730a9065e3aac11c274bc39dba4c0de8d1233bd7a236d1653672ad260b4e`
- API: `682eb0ca1e9963a3e5b0df32ce6c467e2f592663a64d616234daa49d07d330a2`
- session: `83b7cb0cc09585f80c80dec7678acb91e7a4e728807d3574f139b3e2733a26df`
- protocol: `f8b0229f58ebeaac0ab341d4dcce525f3ac3fefc203e8286ac5f0961e3ae3b2c`
- App: `abe43d56124bf311c5eeda32b61af1a82a6b921551f4ca3d057261b5aabf0bf6`
- Results: `47008cf8dbcf1a395adb90c03a7aea22978d0306b5829adb0076b1ad710aaacf`

All five independently recorded findings are now repaired, with original failures preserved. No further concrete ready software gap remains in the reviewed T026/T028 components or the adjacent Results change. This is a component conclusion, not whole T025, AC-008/010/011, native Windows, external integration, or milestone acceptance. The earlier pending statements in this review are superseded by this follow-up.

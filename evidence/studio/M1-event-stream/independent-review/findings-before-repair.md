# Independent event transport review — findings before repair

Linux, disposable synthetic public-journal fixtures only. No runtime, equipment, Windows work or companion repository access. Product/tests/tracker files were not edited by this reviewer.

## STREAM-I01 — subscriber lease survives disconnect before iterator startup (medium)

Confirmed by `startup_disconnect_probe.py` against the real events API endpoint and its returned Starlette `StreamingResponse`, with an owned synthetic ASGI send that fails on `http.response.start`. Both `OSError` (converted to `ClientDisconnect`) and cancellation leave one admitted lease after the response exits. Explicit `aclose()` of the never-started iterator also leaves that lease. The response reserves admission before returning, while release exists only in `iterate`'s `finally`; a never-entered async generator cannot execute it. Repeated startup disconnects can occupy the per-run/global admission budget until service restart/close.

This is a finite route/response lifecycle repro, not a live browser/network test. The source journal remains byte-identical. Exact stable before/after product hashes and outcomes are in `startup-disconnect-before-repair.json`. A repair should own release around the complete ASGI response lifecycle as well as iterator completion, retaining idempotent release and no runtime controls.

## STREAM-I02 — malformed journal event kind injects SSE fields (medium)

Confirmed in `semantics_probe.py` on a newly allocated disposable journal. A record with `type = 'log.appended\ndata: {"injected":true}'`, correctly recomputed hash chain and declared digest, is accepted by the existing reader as `valid`. `_batch` interpolates this value into the raw SSE `event:` line and emits two separate `data:` fields. An SSE consumer therefore receives concatenated data that is not the original JSON envelope and fails parsing. This source is deliberately malformed relative to the contract's closed registered event kind; the finding is failure to reject malformed transport header text, not evidence of a legitimate provider producing it or of code execution. Original fixture bytes remain unchanged by reading/transport.

Exact stable hashes/results are in `semantics-before-repair.json`. Refuse unsupported/malformed event kinds with a typed error or explicit noncanonical stream error; do not mutate the journal or interpolate line breaks into SSE headers. The same probe verifies bounded Unicode byte pressure, truthful resync omission counts with exact source watermark, valid-chain prefix fork detection, and live unknown-state heartbeat/disposal.

## STREAM-I03 — browser refuses recovery from a live verified prefix (high)

Confirmed after frontend freeze using the actual production `EventStreams.resync` response for a newly created running fixture journal, then the current TypeScript `recoveryValue` function transformed in memory with the installed esbuild. The backend truthfully reports `history.integrity = verified_prefix` for a live journal without a terminal declared digest. The browser rejects this response with `Verified bounded recovery is unavailable` because its gate requires `valid` exclusively. Source hashes before/after match in `running-recovery-before-repair.json`; fixture bytes are unchanged.

The session's gap/410 path awaits `recover` before changing its cursor. Rejection therefore prevents that path from adopting the live source watermark; retrying the same stale/expired cursor cannot recover while this legitimate prefix status persists. This is an actual cross-module protocol repro with production functions, not a live network/browser exercise. Accept verified-prefix recovery while preserving and displaying that limited integrity scope, without treating it as complete/valid evidence. Continue rejecting unavailable/invalid sources. Add a live-prefix recovery regression; existing sealed fixture recovery alone misses this state.

## STREAM-I04 — v1.1 silently promotes a legacy position into current-generation proof (medium)

Confirmed by `legacy_cursor_probe.py`: allocate a new journal, retain its first record's opaque proof cursor and legacy numeric position, then replace only this disposable fixture with a newly recomputed valid chain under the same run/snapshot IDs. The original `st1` proof correctly rejects with `410 STREAM_RESYNC_REQUIRED`, but both bare `1` and `runId:1` with explicit `version=1.1` are accepted and return the new generation's digest. Thus a legacy acknowledgement can silently bypass the versioned prefix-continuity check. Legacy version1.0 inspection remains accepted, as intended.

The draft explicitly restricted legacy compatibility and prohibited treating it as cross-generation proof; root confirmed the intended restricted lane is version1.0. Exact stable source hashes/outcomes are in `legacy-cursor-before-repair.json`. Restrict non-proof cursors to the legacy stream version, preserving initial no-cursor v1.1 and proof-bearing resume. This is a direct production prepare repro, not a live browser/network test; source bytes are unchanged by inspection.

## STREAM-I05 — recovery budgets history but can exceed the browser's full-response cap (medium)

Confirmed in `recovery_size_probe.py` on the production resync method with a new valid 200-log journal and a synthetic run carrying the existing 32-definition assessment-summary shape. The response contains 187 retained items totaling 1,043,763 encoded bytes, plus 14,955 bytes of public run metadata and its envelope: 1,059,614 encoded response bytes. The browser's `readJson` rejects beyond 1,048,576 bytes. Reader integrity remains valid, source bytes remain unchanged, and source hashes before/after match in `recovery-size-before-repair.json`.

This is a direct production-response sizing repro using a realistic metadata shape, not a claim that a 32-definition project was admitted/executed in this probe. All records use the admitted `log.appended` kind and fit the transport's per-frame size. History alone fits the backend's pending-minus-control budget, but public run metadata/envelope are not charged to the browser recovery cap. Recovery for this bounded response therefore fails client-side instead of adopting a watermark. Bound the complete response (including run/envelope and any omission counters/cursors), conservatively dropping display items with truthful omission counts or returning an actionable typed refusal if metadata alone cannot fit; do not alter canonical source bytes or silently drop metadata semantics.

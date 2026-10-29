# T026 session findings before repair

- SESSION-001: api/client.subscribe advances its cursor before calling/awaiting event acceptance. Reconnect can acknowledge an event the consumer has not accepted.
- SESSION-002: HTTP410 clears the cursor and fires an unawaited callback. App reports resynchronization complete before the GET resolves and never obtains bounded history/watermark before reconnect.
- SESSION-003: Per-chunk CRLF normalization loses delimiters when CR/LF are split; parser ignores SSE event kinds and cannot separate noncanonical transport controls from canonical evidence.
- SESSION-004: App fabricates one omitted event for unknown cursor loss; resync GET replaces state without stateVersion gating. Unknown ownership is incorrectly treated as terminal, so reconnection/polling stop.
- SESSION-005: Retry sleep leaves abort listeners attached after successful timer expiry. Reader cleanup is not guaranteed on parse/transport errors.

Tests-first transport probes use explicit inert canonical-envelope/control fixtures. Native read-only reconnect checks follow actual backend transport1.1; no fixture claims external runtime evidence or native Windows acceptance.


First successor:10/13 checks passed. Unknown-state actual410/resync and bounded200-record tail succeeded. Two final reconnect assertions used setOffline, which did not cancel an already-established Chromium localhostSSE connection; use explicit test-only browser AbortSignal fault injection, retaining actual backend frames/resync responses and run ownership, rather than claiming an offline event disconnected transport. A separate test dynamic-import failed due the runner's ESM/CJS transform; use the already-supported static facade import. These are recorded as verification harness corrections, not repaired product defects.


STREAM-I03 (independent review) — Production active-run resync returns verified_prefix because the journal is not sealed. Requiring exclusively valid prevented live recovery. Independent actual-response probe and author prefix contract test both fail before repair (prefix-before-repair/). Accept exactly valid or verified_prefix when bounded event/chain/context/watermark checks pass; preserve original integrity in the completion notice. Invalid/unavailable recovery remains blocked. Replace Earlier display omissions with Display omissions because oversized omissions may be interspersed. Add native running-prefix assertion, not just terminal fixture coverage.


Final successor:15checks PASS23.5s, including real running verified-prefix recovery, invalid/unavailable rejection, accepted-tail ACK order, parser/resource cleanup, exact unknownloss, native ownedrunprogress during browser-only delivery faults, and refresh without anotherStart. Independent reviewer reproduced actual-response successor and valid/prefix/invalid/unavailable admission matrix; no remaining concrete frontend finding in owned scope. Raw receipts remain under ignored .studio-local/evidence-raw/session-fifteen-green; sanitized exact-source receipts under fifteen-green/. Windows remains NOT_RUN under userhold; these are not externalprovider/physical results or complete M1 acceptance.


Evidence facet successor regression: controlled HTTPmetadata keeps the same fixture lifecycle stateVersion while evidence changes partial→invalid→unavailable. Corrected baseline test fails specifically at invalid (card remains partial after8seconds), confirming stale card/cached-read gap. Fixture evidenceScope remains recorded_fixture; no journal/snapshot rewrite or runtime authority is introduced. Root owns Results correction; author owns this new browser regression only.


Native expiry strengthening first successor:15of16 checks passed; same-SV invalid/unavailable regression passed and native source progressed by more than1000 records, but no410 was observed before stop. The test fault helper threw every paused connection attempt, allowing exponential backoff to extend the intended12-second delivery pause past the16-second run. Correct the test-only helper to stall the actual pending SSE GET until explicit resume (old reader still aborted, cursor/options unchanged); release delivery before the diagnostic history request. Keep duration16s, timestep.01,12s pause, real HTTP410, active verified-prefix recovery and immutable-byte assertions unchanged. Retain first report as a failed strengthening attempt, not passing expiry evidence.


Strengthened native successor:16checks PASS40.5s. During the16-second/.01ownedreference run,12-second browser deliverypause allowed source records138→1385. The unchanged acknowledgedcursor145 produced actualHTTP410CURSOR_EXPIRED; subsequent realresync returned state running / integrity verified_prefix at watermark1398. Original170763-byte journal prefix and immutable snapshot hashes remained identical; final journal bytes matched backend journalDigest. Only one projectrun existed and reconnect/refresh sent no mutations. Same-SV metadata negative also passed partial→invalid→unavailable at version1 while backend evidence stayedpartial and sourcebytehashes remained unchanged. See expiry-green/ for exactreceipts/sourcehashes. Earlier failed strengthening remains retained, and no nativeWindows/externalprovider/physical acceptance is claimed.


STREAM-I05 frontend — Typed413 STREAM_RECOVERY_TOO_LARGE currently enters automatic retry after410; author contract probe observes4requests (events,resync,events,resync) within650ms instead of stopping after the first recovery refusal. The refused recovery must remain unacknowledged, release its response body and expose an actionable presentation-limit state directing inspection through paged retained history. Root owns corresponding backend whole-body metadata-budget repair. Red retained under recovery-limit-before/.


STREAM-I05 frontend successor:14pure protocol checks PASS9.2s; tsc/Vite build PASS. The typed413 refuses recovery without cursor acknowledgement or automatic retry, cancels the response body, and directs paged retained history inspection. The new probe waits650ms past the first failed recovery and sees only the original events/resync reads. Exact hashes/report are in recovery-limit-green/. Parent owns the final combined native/browser cohort; author did not rerun native jobs after this small limit branch.

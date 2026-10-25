# M2 implementation review findings


## WEB-001 — Run selection crossed project boundaries

- Severity: medium; observed during frontend review before repair (agent message retained in the implementation session).
- Finding: a globally selected run could remain visible when another project opened, causing the displayed snapshot context to refer to a different project. This did not mutate XDL, immutable snapshots, evidence, or backend lifecycle ownership.
- Repair: persist selected run references per project; reset to Model for a different project; retain same-project element selection; guard stale project loads and pending event/state refreshes so they cannot restore an unrelated run.
- Affected verification: real browser reload, second-project selection, keyboard create/validate/preflight/start/stop journey and final owned browser suite. Final result is recorded in the browser report; no Windows/native-provider acceptance is implied.

## WEB-002 — Malformed imported XDL could break a display projection

- Severity: medium; identified while reviewing untrusted source handling before hardening the projection.
- Finding: non-array `componentInstances` or `nodes`, or non-scalar presentation labels, could throw during rendering and obstruct source inspection.
- Repair: bound YAML aliases and normalize only display values, preserve authored bytes, retain opaque payloads and expose unprojectable structures. Executable validation and compilation remain entirely server/platform-owned.
- Verification: `tests/e2e/projection.spec.ts` contains malformed-source and opaque-extension preservation cases. Both passed in the first clean native browser suite; final report records the successor candidate.

## WEB-003 — Async preflight lost the keyboard return target

- Severity: medium; found by the true Tab/Enter-only journey before repair.
- Finding: disabling the focused Preflight button while awaiting readiness moved focus before the modal mounted. A generic modal return-focus capture therefore retained the body rather than the originating control. The final accessibility test failed at the explicit focus assertion; the failed command was `python scripts/test_browser.py --performance` with 2 passed / 1 failed at `toBeFocused`: expected focused, received inactive. This failed outcome is retained here; later browser output is successor verification.
- Required repair: give the asynchronous preflight dialog an explicit stable return target, retaining its focus trap and Escape behaviour. Repeat the keyboard journey and affected browser suite on the successor build.

## Successor verification

The final `python scripts/test_browser.py --performance` command passed all three tests on native Linux / Chromium 156.0.8078.4 with Node 24.22.1. The keyboard journey exercises Tab/Enter-only example creation, validation, preflight, Escape and return focus, admitted Start and owned Stop. Browser refresh retained the same run identity; selecting a second project used its own snapshot context. Both required desktop viewports exposed the structured graph alternative without horizontal page overflow. Malformed-source and unknown-extension presentation tests passed.

The valid 200-element / 400-flow authored fixture used one warm-up and 30 measured repetitions. Selection/inspector p95 was 27.7 ms against 150 ms; project open plus authoritative validation-result presentation p95 was 2729.9 ms against 3000 ms. See `../M2-operability/browser-performance-linux.json` for raw samples and `../M1-browser/summary-linux.json` for the exact frontend source digests and test limitations. No native Windows or live-provider acceptance is established.

## Retained-history successor verification

The next `python scripts/test_browser.py --performance` run passed all three tests in 2.0 minutes on native Linux / Chromium 156 with Node 24.22.1. A trusted test-only helper created a NEW terminal `recorded_fixture` run, with no process handle or runtime capabilities, tied to an authoritatively compiled reference snapshot. It wrote and verified 50,000 registered log events (38,877,438 bytes) using the full journal hash chain and final digest; no existing evidence was overwritten.

Results now reads explicit retained pages of at most 200 records through the history API, applies kind/severity/element filtering on the backend, exposes integrity and cursor navigation, and separates the bounded live buffer. Terminal historical runs do not drain the entire retained journal through SSE. Active UI pending/display buffers are each bounded to 200, with explicit omission counts, while canonical collection remains owned by the provider/backend.

The first 200 filtered source records rendered at p95 180.3 ms against the 2000 ms requirement over 30 repetitions after one warm-up. The test checked original event IDs/sequences 1–200, navigation to 201–400 and back, and unchanged source journal digest, integrity and record count after reading. This is recorded-fixture rendering evidence, not external runtime integration. Native Windows remains NOT_RUN. The same successor measured 200-element/400-flow selection p95 31.1 ms and open/validation presentation p95 2670.1 ms. Raw samples and successor source digests are in `../M2-operability/` and `../M1-browser/history-successor-summary-linux.json`; the preceding evidence files are retained.

## WEB-004 — Repeated authoritative validation exceeded the warmed browser target

- Severity: high performance gate failure; recorded before cache repair.
- The M2 composition successor passed its browser interactions, then failed the unchanged 200-element/400-flow open-plus-validation gate: p95 3214.8 ms against 3000 ms. Selection remained within target at p95 30.1 ms.
- Raw samples, failure screenshot and test error context are retained in `performance-failure-before-repair/`. Diagnostic HTTP timing against the same isolated valid project measured repeated project reads at 4.7–10.2 ms and repeated authoritative validations at 1554.2–1979.4 ms without changing source bytes or starting any provider. The reproducible diagnostic is `python tests/performance/profile_requests.py`.
- Repair assignment: XDL adapter owner will add only a bounded cache of actual authoritative validation results keyed by exact authored source bytes, actual installed validator identity and all admitted schema bytes. Compilation, execution admission and mutable capability facts must not be cached. Repeat invalidation/mutation tests and the same 30-repetition browser workload; the original failed gate remains recorded.

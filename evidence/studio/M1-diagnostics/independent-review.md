# Independent review — evidence-linked diagnostic explanations (2026-10-25)

A separate read-only reviewer inspected the first diagnostics candidate against FR-017–FR-022,
NFR-011, US4, AC-005/007/011, T031/T032 and the event contract, probing the pure module in memory.
All confirmed findings were repaired before the verified successor.

| # | Finding | Disposition |
|---|---|---|
| 1 | Real readiness records an invalid model without a code, so it was grouped as "unestablished" and never cited source diagnostics; tests invented a code and an unreal diagnostic shape. | `invalid_model` is keyed on the recorded status and cites real XDL `location`/`pointer`; dimensions downstream of an invalid model are unestablished. Contract test uses a real invalid Scenario through the API. |
| 2 | An active run's momentarily unreadable journal was an error "evidence" finding. | Active runs report `EVIDENCE_NOT_YET_READABLE` as information. |
| 3 | Liveness was asserted for unverified `preparing` and with unreadable evidence. | Limited to verified running/stopping with readable evidence. |
| 4 | Fault consequence asserted stale measurements without divergence and cited the requested fault. | Consequence only from observed fault plus diverging observations; otherwise an explicit unknown. The request is context only. |
| 5 | Affected elements were always empty for real runs. | Route passes the frozen configuration's element references. |
| 6 | A failed launch was described as an ended execution with refreshable evidence. | Not-started runs explain that no execution and no evidence occurred. |
| 7 | A previous run's explanation stayed visible after switching runs. | Explanations are bound to their subject URL. |
| 8 | Every streamed batch re-read the whole journal and scanned all operations; the key stalled at 200 events. | Re-reads keyed on the last sequence and coalesced (1 s); operations are queried by run. |
| 9 | "Refresh evidence" did not refresh the diagnosis; reconcile failures were silent. | Built-in refresh; action failures are shown. |

Speculative items addressed: `LIMITS_UNKNOWN` is unestablished rather than a resource limit; the
preflight panel is always shown; the browser assertion for grouped unknowns is unconditional; ADR
wording now states that the run route performs the same reconciliation as `GET /runs/{runId}`.

Retained limitations: cleanup `unknown` uses the `failed_cleanup` class name with an "unknown" title and
unknown statement; multiple clock domains are reported without consulting a future admitted mapping
contract; no red/green history exists for the first candidate module because it was never committed
(the reviewer's in-memory probes document its failures).

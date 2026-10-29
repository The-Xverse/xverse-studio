# Native reservation restart supplement

Two actual Linux backend crash/restart probes pass against the unchanged published
af45890 backend and owned physical-contract fixture. The branch has a separately
uncommitted UI recovery amendment; it is not part of these Python/HTTP semantics.
Exact backend/fixture/lock input equivalence is recorded, independently of the
currently running browser verification. This is not a fresh full backend suite.

Each probe starts the existing native fixture host on its own held loopback socket
and private Unicode data path. Real session, Origin, CSRF and idempotency handling
acquire one observe-scope reservation. One lane receives confirmed ownership; the
other deliberately loses the provider acknowledgement and receives unknown state.
Immediately before SIGKILL, the probe verifies the exact child's UID, parent,
argv and Linux birth identity. It restarts the same normal host and data root.

Both restored leases are unknown, retaining the original reservation, owner,
asset, scope, expiry and original fence (including unknown fence in the lost-ack
lane). Repeating the original key returns exactly the historical operation and
receipt without reacquisition. The historical confirmed receipt grants no current
ownership. Renewal is refused; explicit original-reservation reconciliation stays
unknown. The restarted provider's required shutdown record contains exactly three
inventory checks and one inspect callback, zero reserve/renew/release/stop calls,
zero new reservation identities and zero held provider dictionary entries. No run
is created and physical runtime admission remains unavailable.

The original in-process fixture provider dies with the backend, so these results
prove conservative handling of provider-state loss, not external device cleanup or
successful reconciliation of a still-owned external lease. The intentionally
killed host cannot write its normal lifespan-shutdown observation; no such missing
record is treated as a retained success. The restarted host exits normally and
its actual observation is mandatory. The original source and failed private
client/call-count explorations are retained in history; neither is an app failure
or a positive result. No production source, test threshold or existing assertion
changed to obtain these two passes.

T073/T074 remain in progress. Native Windows, in-flight delegation crashes,
external-provider persistence, active-run renewal/loss policy, actual hardware,
and full independent milestone gates remain open. No task or milestone is closed.

Permanent regression: `tests/integration/test_lab_native_restart.py` adds the same
two native scenarios, with real HTTP and process-identity guards, and passes both
in pytest (zero failures/skips). Its Linux-only process probe explicitly leaves
the held Windows lane separate. The original 1068-test backend suite is inherited
through 159 exact published backend/fixture/lock inputs; there is no new single
1070-test run. One new Python-only test file is outside the already frozen browser
selection and does not change browser collection or application runtime bytes.
All 315 browser inputs remain exact. Whitespace-only formatting after the two
pytest passes preserves the exact parsed AST; both source forms and hashes are
retained. The one existing framework deprecation warning is recorded.

Final-source follow-up: both permanent pytest scenarios pass again on the exact
formatted test source (zero failures/skips, one existing framework warning).
The fresh final XML, actual native process observations and source hash are
retained separately; the first two passes and formatting proof stay historical.
No fresh full1070 backend execution or broader acceptance is claimed.

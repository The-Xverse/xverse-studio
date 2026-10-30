# Autoverse command failure event review — 2026-10-30

Candidate `ed958f33a7111037f1babe911cad443922d07600` repairs a concrete T025 event gap and exposes the existing
command outcomes in the shared retained-history filter. **T025 remains in progress.**
Counts stay 61 complete / 29 in progress / 10 blocked; no milestone is accepted.

The actual initial browser test receives Start 202, then observes a failed Start
operation, failed lifecycle, complete cleanup and partial evidence. Its valid
canonical journal has no command.failed event. The executing classic worker now
writes that existing event kind for a Start that fails before reaching running,
using its original server-issued operation ID and actual bounded failure code.
The event precedes the canonical terminal lifecycle record. It changes neither
cleanup nor functional verdict, and never rewrites previous evidence or Argus.
The generic Results filter adds delegated/rejected/failed/unknown alongside the
existing accepted/completed command kinds; no industry dispatch is introduced.

Both final native Chromium cases pass with zero skips/flakes on 452 unchanged
committed inputs and 6 private built UI assets. One loses the actual original CARLA
child during startup and displays/filters the original failed-command event; its
terminal SSE and retained history preserve the same event identity/digest/sequence.
The other executes the complete actual demo through Android boot and observed
speed before original CARLA loss. Its Start operation remains completed and there
is no retroactive failed-Start event. Source clocks remain unmapped/absent and
functional verdict remains null. Independent source/resource/ledger readback
verifies canonical snapshots, effective plans, original request/operation IDs,
journal chains and terminal resource facts. Nineteen recorded component instances
and two workers exit, two backends/two browser drivers are absent, three exact
containers stop and both root locks release. All 6 original UI assets and 21 original
platform evidence files are unchanged. The operator is not restarted.

The initial red and subsequent test-locator error are retained and qualified in
phase-history.json. The latter occurred after successful backend/SSE assertions;
the tab's accessible name contains its count. It is not another product failure.
Final source is Git-bound; early uncommitted test hashes/raw reports remain private.
Typecheck, private build, Ruff, architecture, compatibility, spec and diff checks
pass. Existing build/Node warnings remain explicit. No new installed package,
Pygame, standalone Lite, whole-platform, physical or other-industry acceptance is
claimed. This is a self-review with separate readback, not independent milestone
acceptance. The T011 reference exception is not extended.

Continue the original T025 two-tab, UI-loss, delivery-order, expiry and resync cases.
The default replay window remains 1000; this work does not claim its expiry boundary
was exercised or lower that bound to obtain a passing check. T033 and the complete
remaining original M0–M4 scope stay open.

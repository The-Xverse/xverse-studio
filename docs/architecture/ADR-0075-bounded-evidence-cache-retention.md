# ADR-0075 — Retain costly verified captures within existing cache bounds

Date: 2026-11-05. Status: implementation; full live repeat pending.
Traces: T096; NFR-007/008; AC-010/011/030. No runtime authority change.

The actual full Autoverse pressure case reaches Android/APK and vehicle speed but
then receives CONTROL_LEASE_EXPIRED. Concurrent history/comparison reads take up
to5.47 seconds. The test's HTTP-client/capture setup also interrupts its driver
heartbeat. Cleanup completes and the failure remains retained; no lease extension
or weaker authority rule is justified by this result.

A separate read-only reproduction uses the actual two completed source journals
and the declared inert38MB/50,000-record history. Alternating the three sources
three times makes the two-slot LRU verify the large source three times. Its capture
is repeatedly displaced by the much smaller comparison inputs. Integrity parsing
also runs inside ordinary run observation's metadata lock, delaying unrelated
control work. Cache eviction policy is not a source-identity or admission rule.

Keep the existing two-entry and64MiB contributing-source-byte limits. On inserting
a verified capture, remove older fingerprints of its canonical path. When capacity
forces eviction, discard the smallest source capture, using existing LRU order for
equal sizes. Source bytes are a bounded cost proxy, not a promise of parse time or
decoded-object memory. Small inputs may be reverified more often, while expensive
large captures survive alternating small comparisons. No provider/industry-specific
key or dispatch is introduced.

Every hit still requires anchored opening and the complete current file/state
fingerprint. Canonical verification, source/change retries, limits, unknown/invalid
verdicts and returned records are unchanged. Invalid captures are never cached.
This does not move verification outside the observation lock, increase cache/queue
budgets, relax the driver lease or confer a new numeric evidence interpretation.

The live harness acquires a fresh public driver lease after its finite HTTP-client/
capture setup, then keeps the unchanged heartbeat during the measured pressure
phase. This separates preparation from active control and preserves the first
failure. Pressure sources, clients, duration, full renderer/sensors/Android and
canonical progress/control/cleanup assertions remain unchanged.

Verify the source-backed decode-count counterexample, changed-byte rejection and
unchanged byte/entry bounds, then repeat affected reader/stream/admission checks,
the complete actual Stop/Cancel cases and original finite measurements. Retain cold
setup and warm active-phase qualifications separately; no cold input-latency SLA,
native Windows, physical or full milestone acceptance follows. Windows stays frozen.

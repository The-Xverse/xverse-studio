# Stream recovery candidate — partial verification

T028 is component-complete after the full 493-test backend run and independent literal fixture review.
T026, T025 and T027 remain open. No M0–M4 milestone or Studio 1.0 release is accepted.

`candidate-verification.json` identifies the actual application-source digest and scope. The backend
receipt ran on unchanged source; all current backend/Python test files still match. Later changes
were frontend listener/parser fixes and browser test prerequisites/instrumentation, not unverified
backend substitutions. Native Windows installation/testing remains held; native secure I/O is still
unavailable there. Reference data is not evidence of a simulator or physical device.

Browser failures are retained, not counted as passing:

- `../../M1-session/full-before/`: first full run 35 passed/3 failed, unchanged source.
- `../../M1-modal-keyboard/before/`: deterministic asynchronous modal-input failure, with a passing
  synchronous control. The listener's layout-phase repair makes both successor cases pass.
- `../../M1-modal-keyboard/combined-after/`: focused 22 successor 18 passed/4 failed, unchanged source/dist.
  Both modal cases, known-gap recovery and all 15 protocol checks passed. Project creation remained
  pending; native expiry had sufficient source progress but no observed410 in its remaining window;
  screenshot and ordinary Apply input timed out. Their exact contexts remain available.

`host-io-pressure.json` records contemporaneous host-wide I/O stalls; it does not prove each failure's
cause, relax timeouts or replace required browser/performance results. Current full browser/performance
and clean-package successor verification is incomplete. Fresh-host CI/publication results are recorded
separately when available. Prior passing candidate metrics and packages remain historical evidence.

The unknown-lifecycle recorded fixture proves an initial SSE gap/resync with a known omission count.
The separate 16-second reference receipt under `../../M1-session/expiry-green/` captured genuine
HTTP 410 while running. See the scope erratum; historical raw receipts are retained. Later workload
changes must acquire their own native proof rather than inherit that result.
The current test-only successor requests 30 seconds at timestep 0.01 within the advertised 30-second/
3,000-sample provider bounds. It retains the 12-second delivery pause, source-progress, actual410,
running-prefix recovery and immutable-byte assertions, and rejects a shorter preset by checking all
3,000 observations and final tick. Its existing assertion timeouts remain; its native proof is pending.
Passive request/phase diagnostics are attached on failures without changing the acceptance checks.

Original findings, red/green successors and independent reviews are under `../../M1-event-stream/`
and `../../M1-session/`. Public copies normalize machine paths/display whitespace only; source hashes,
original journal/snapshot proofs, counts, timing and outcomes remain intact. Private raw originals stay
on loop10. The branch is `implement/studio-m0-m4`, with draft PR1; publication does not imply acceptance.

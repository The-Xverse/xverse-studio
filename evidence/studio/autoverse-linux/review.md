# Scoped native integration review

This is a scoped implementation self-review, not independent milestone acceptance.
The existing 100 task definitions and milestone gates remain unchanged.

Repaired findings:

- Initial native children lacked the admitted component user's HOME. Enrollment
  and the fixed child environment now retain the required graphical/user context.
- Telemetry envelopes and Android boot polling initially blocked readiness despite
  actual component progress. Their separate preparation states and bounded polling
  now use the actual interfaces.
- Asynchronous vehicle startup did not establish usable vehicle effects. The
  supported provider now chooses the existing public synchronous CLI option,
  checks its traffic-manager port, and records that execution choice. Actual
  CARLA velocity and applied control, cruise engagement and target changes passed.
- The publisher emits elapsed seconds while its metadata describes frame-delta
  milliseconds. The adapter retains this conflict without inventing a clock mapping.
- Storage failure could previously prevent cleanup. An actual owned-child test
  now confirms cleanup despite failed state persistence. A birth-identity mismatch
  leaves the unconfirmed process untouched and reports unknown cleanup.
- Three initial gear tests exposed backend forward-direction gating and gear
  reinitialization on driver reacquisition. Both directions are now gated; renewed
  driving retains gear desire while brake/expiry disengages cruise. All147 final
  contracts and the actual SDK transport check pass after repair.
- Android display checks sampled after the simulated vehicle had stopped. The
  corrected live check retains a moving screen and verifies positive application
  state updates, alongside actual backend/CARLA observations. No companion source
  or bundled APK was changed to satisfy the check.

Source and clean installed copies both passed the complete browser workflow and
terminal journal integrity. The installed copy has its own environment and separate
verification data. Its 96 copied implementation/UI payloads match the tested bytes.
Earlier failures remain qualified in verification.json and private diagnostics;
not every early diagnostic candidate had a complete source snapshot.

Residual scope: this is a trusted-host Linux prototype using existing Docker/GPU/VM
assets. Full-suite, broader failure conformance, independent review, native Windows,
physical integration, native X-COM and Argus admission are not established here.

# T008 private local binding storage review — 2026-10-30

Before implementation, all13 new API/concurrency/export cases fail at the missing
routes. ADR-0040 records the closed declaration model, independent CAS, secure
sidecar publication, bounds, context hint and absence of provider/path/secret
contact. The first implementation passes13/13. These are storage declarations;
provider admission, runtime resolution and physical authority are separate.

Review requires typed handling for malformed stored heads and unsafe stored paths,
write/commit/late-acknowledgement failures, private move/backup/import boundaries,
retention stage ownership and head cleanup. No unknown or corrupted state may be
reset to an empty declaration. No locator is opened or resolves a permit.

The expanded failure cohort reports15pass/4fail before repair: malformed JSON
heads escape decoding, unsafe stored paths use the request-path error rather than
a persisted-unavailable error, pending project retirement permits a new private
publication, and retirement leaves its private head row behind. Repair all four
while retaining the fifteen actual corruption/write/commit/late-ack controls.

All four are repaired. Affected41, expanded39 and movement46 cases pass in
separate retained phases. Final310 affected backend cases and12 actual native
browser journeys pass with420 unchanged source/config/test inputs and6 unchanged
UI assets. New process-boundary tests verify the original PID/birth/UID/argv/parent
before killing only that owned backend, then reopen through the stock launcher.
Private restore/copy-migration preserve bytes and plan while requiring context
review; portable exports exclude private declarations and imports reject that kind.
The complete T008 clause mapping is in
evidence/studio/M0-private-local-bindings/review.md. Clean package verification and
its candidate binding remain before the component completion decision.

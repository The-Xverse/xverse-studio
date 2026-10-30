# ADR-0048: Native Autoverse lifecycle conformance

Status: implemented and verified for the original T021 test scope. Three actual
native Autoverse cases pass on candidate f17b294; full clause audit and qualified
phase history are in evidence/studio/M1-native-autoverse-lifecycle/. No milestone
acceptance or new reference execution is claimed.

T021 requires lifecycle, immutable-input, idempotency, optional-control,
partial-start, cancellation and backend-restart conformance. Its originally
planned `tests/integration/test_run_recovery.py` does not exist. Existing reference
contract/native recovery tests retain their original implementation and historical
evidence. Current confirmation uses the user's Autoverse target instruction; the
separate T011 reference-provider exception does not extend to this task.

The explicit developer driver is
`tests/live/autoverse_lifecycle_conformance.py`. It starts the actual enrolled
classic complete-demo provider through the native launcher and public Studio API,
with a fresh private root for every case. The supported browser-input variant and
30-second active duration are authored through the same XDL source interface and
authoritative compilation as ordinary projects. No fixed model replaces submitted
inputs and no imported command or fault switch is introduced.

The complete-demo case tests concurrent initial Start requests and retries,
changed-payload conflicts, unsupported controls, an independent active draft,
uncertain ownership, actual backend process loss/restart, original worker survival
and natural completion of its frozen duration. Fresh enrollment can be unavailable
while the original demo resources are running; the recovered historical run and
its original ownership remain separate from fresh execution admission.

The ownership negative briefly suspends only the original worker while its new
test-owned mutable state report is obstructed by an incorrect owner digest. It
restores the exact original report bytes and resumes that same worker in a finally
block. This does not pause the simulator or implement a Pause capability. Canonical
evidence, owner keys, requests and immutable snapshots are not rewritten.

Two startup negatives cancel after actual router/CARLA acquisition or signal only
the original CARLA child before VCU/container acquisition. They are partial
executions of the real target, not complete-demo success. Lifecycle failure,
cleanup, evidence integrity/availability and functional verdict stay independent.

Provider-resource signals require original native Linux pidfds plus verified UID,
process birth, argv digest, original parent and run-owner witnesses. Original
backend subprocess handles are retained before acknowledgement checks across
stop/restart. If acknowledgement itself fails, only that fresh unreaped native
child may be terminated using its original Popen handle and parent/UID/birth
witnesses; this grants no provider or foreign-process authority.
No name, port, process group or guessed
PID supplies authority. Cleanup verifies the recorded process instances and exact
container configuration/start identities, canonical terminal resource facts,
unchanged snapshots and released root locks.

This amends the verification file allocation, not the application contract or
requirements: keep the existing reference contract/native recovery files and add
the explicit Autoverse driver in place of the missing proposed integration file.
T025 browser reconnection, T033's full fixture guided matrix, standalone Lite,
physical, independent review and full acceptance cases remain separately scoped.

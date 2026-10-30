# ADR-0043: Original-owner readback after uncertain container cleanup

Status: implemented and verified by165 enrolled-target checks,4 native browser
checks and3 complete installed Autoverse runs (nominal and both acknowledgement-loss
cases). T010/T033 and full milestone acceptance remain open. No companion API or
ownership grant is changed.

The previous complete installed Autoverse run ended with Android cleanup/Stop
receipt unknown. Later exact-container inspection found it stopped; its original
swallowed exception does not identify the precise cause. Preserve that observation.
A separate complete native baseline now pins a test Docker transport in its actual
enrollment. The transport runs the real original Android container Stop to exit0,
then withholds acknowledgement until the existing20s caller timeout. The original
worker records cleanup unknown because it skips readback after the CLI exception.
This reproduces the mechanism without fabricating a container or lifecycle result.

Container cleanup now separates optional Android shutdown, one container Stop
attempt, and final inspection. All ownership checks compare original container ID,
image/name/configuration identity and exact StartedAt. Recheck after optional
shutdown before any container Stop and again at final readback. An unavailable,
malformed, changed or still-running observation stays unknown. A command timeout
does not grant another Stop attempt or wider authority. A fresh verified original
container that is stopped establishes release despite a lost CLI acknowledgement.

Every resource retains the previous sum of maximum command/inspection durations:
70s for Android and50s for another container. An enclosing phase cleanup deadline
can only shorten that budget. Added inspections consume that same envelope; expiry
refuses further work and reports unknown. Individual existing15s inspection and20s
command caps remain. No broader timeout is introduced to make a test pass.

At most four unique constant diagnostic codes distinguish optional shutdown,
container command, ownership, readback and deadline uncertainty. Responses never
copy CLI output, exception text, private paths or credentials. Final canonical
`run.state_changed` retains the same actual per-resource outcomes/codes as native
state, using the existing event type and finalization I/O failure handling.
Historical unknown state, receipts and immutable journals are not rewritten.

Verification targets the actual enrolled Autoverse container for read-only claim,
inspection, changed final observation and expiry negatives. Complete native demo
verification separately exercises actual Stop acknowledgement loss and nominal
owned shutdown. Test transports are explicitly labelled and identity-pinned;
they do not substitute for original provider outcomes, full Maestro/Argus admission,
physical-device, another-industry or independent milestone acceptance.

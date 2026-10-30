# ADR-0049: Original Autoverse Start failure events

Status: scoped implementation verified by two actual native Autoverse/Chromium
cases on candidate ed958f3. T025 remains in progress for its remaining browser/
stream obligations. See evidence/studio/M1-autoverse-start-failure-events/.

T025 requires command-failure events and a visible distinction between command
acceptance and execution failure. An actual native browser case demonstrated
that Autoverse's accepted Start operation fails during CARLA startup, while its
canonical journal and SSE stream contain no `command.failed` event. The operation
ledger correctly reports failure; a lifecycle record alone does not fill that gap.
The shared Results event-kind filter also omits delegated, rejected, failed and
unknown command outcomes. It now offers all six existing command lifecycle kinds
through the same read-only retained-history interface, without industry dispatch.

After owned cleanup, the classic native worker now emits the existing v1
`command.failed` kind when execution failed before it ever reached running. The
event retains the original server-issued request operation ID, `kind: start`,
the actual bounded failure code, run/snapshot identity and original source clock
policy. It is written by the executing worker into its own hash-chain journal,
before its terminal lifecycle event. Evidence remains partial with its original
integrity; cleanup and functional verdict stay independent.

A failure after running cannot retroactively fail the completed Start operation.
Successful startup and cancellation do not synthesize a failed command. The change
adds no operation result to the private command-results map for Start, grants no
new capability and changes no past journal, Argus record or approval. Existing
provider implementation digests change normally; preflight/dispatch admission
continues to bind exact current bytes. The public platform provider uses its own
separate execution finalizer and is not relabelled by this classic-provider change.

Current confirmation uses the actual Autoverse target on native Linux. The scoped
browser failure case is partial startup, not complete-demo success. The rest of
T025's two-tab, delivery-loss, event-order, cursor-expiry and resynchronization
coverage remains open until separately verified; this amendment does not accept
a milestone or extend the T011 reference-provider exception.

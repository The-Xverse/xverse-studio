# ADR-0052 — Bounded Autoverse browser-input loss

Date: 2026-10-30. Status: implemented; scoped classic Autoverse live verification passed.

T082/T083 require positive scheduled fault activation/recovery and evidence of
actual effects. The admitted complete demo currently supports fixed startup and
browser input, including a bridge-owned 750 ms publication lease. Its vehicle
clock is unmapped. No generic physical fault or native X-COM fault API is implied.

Add a classic-provider contract `urn:xverse:studio:autoverse:input-loss:1.0`.
A native Scenario fault of kind `driver-input-loss` targets the existing `driver`
instance. Its opaque activation/recovery markers identify this contract; timing
comes exclusively from the installed public experiment-lite timed trigger and
duration. Compile the full XDL normally. Preserve the original quantities and
normalized plan nanoseconds; admit exact whole microseconds on the declared
`host-runtime` monotonic clock, relative to the actual transition to running.
This clock describes provider scheduling and bridge receipts, not simulation time.

The classic provider admits at most eight nonoverlapping half-open intervals.
Each starts at least two seconds after running, lasts between two and thirty
seconds, and ends at least two seconds before the run horizon. Adjacent intervals
are refused: recovery needs its own observation opportunity. Only the exact
existing browser-input blueprint may opt in; Pygame and platform mode refuse
these declarations until separately admitted. Other semantics remain exact.
The classic provider version advances to 0.2.0; historical 0.1.0 evidence is unchanged.

At activation, the worker inhibits forwarding fresh authenticated browser frames
to its original owned bridge. Dropped sequence numbers are consumed and never
replayed. The bridge continues its existing lease-expiry and neutral publication
policy; the external assets are unchanged. A fresh input is required after
recovery. Stop/Cancel retain priority and normal owned cleanup remains mandatory.

Record requested activation/recovery separately from observed effects. An
activation observation requires at least one suppressed fresh frame and a new
bridge report, produced after activation, showing its publication lease inactive.
A recovery observation requires a new post-recovery publication acknowledgement
and a new bridge report produced after recovery showing an active lease. These
facts attest the bridge publication lease only. Vehicle/controller telemetry
remains independent; no braking, physical safety or vehicle acknowledgement is
inferred. Missing input or bridge evidence leaves the effect unobserved, including
on early Stop. Record interrupted/unobserved outcomes explicitly at run end.

Bridge reports add their actual host monotonic production timestamp. Fault events
record actual host-relative microseconds and original scheduled positions. Existing
records without an admitted clock codec stay unplaced in the generic timeline;
this change grants no simulation/native-X-COM clock mapping or deterministic replay.
Queues, schedule counts and record volume remain bounded. The worker independently
recompiles frozen sources and compares the exact resulting configuration before
acquiring runtime resources. No imported command, URI, arbitrary callback or
companion repository mutation is introduced.

Verification must include full-source positive configuration and invalid target,
clock, unit/resolution, interval, count, overlap, unsupported-mode and payload
cases, then a complete native Autoverse run proving real suppression, lease expiry,
fresh recovery publication, immutable snapshots and exact owned shutdown. Until
that passes, this remains an implementation candidate, not a live capability or
a completed task/milestone.

Verification: 159 API regression checks, 10 causality/time-unit guards and one
complete actual native demo passed. Two intervals recover; Stop during a third
records interruption without an invented recovery observation. Source/plan/native
readback and original evidence preservation pass. Original failures and all
remaining scope are retained in the [component review](../../evidence/studio/M4-autoverse-input-loss/review.md).

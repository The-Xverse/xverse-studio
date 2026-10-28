Current source `08d379cc1687e7e0388a643ee62876aee2f99178` passes fresh **1,199 backend, 80 affected browser, two native frozen-intent timeline and two separate performance checks**, all on the same 377 unchanged inputs, with no skips or flaky results. Clean native Linux prepared-cache offline packaging passes all 115 payload/archive hashes and six tested UI assets. **T027 is complete as a view/control implementation component; counts 49/41/10, no accepted milestones.** The current 617-case/60-file full browser collection is not a local full execution. [Exact source/package binding](candidate-binding.json), [clause review](task027-component-review.md), [current checks and original failures](observation-ordering/).

# Owned reference optional controls

The owned reference provider implements cooperative Pause/Resume at model-step
boundaries. Its process stays alive, simulation observations stop advancing, and
Resume preserves the next model step. A cumulative 30-second wall-time pause
budget ends in an orderly stop with incomplete simulation coverage. Existing
signed command identities, state versions and immutable input bindings remain.

Four original native scenarios reject Pause before this implementation. The
first four successor scenarios pass. The expanded native phase initially ends
with 11 passes and three failures; the retained classification separates two
initial ownership-unknown observations from a timing assertion that included
terminal publication latency. Canonical timestamps prove the cumulative pause
budget was already working. The corrected serial phase passes all 14 cases.

The actual campaign regression first reports cancellation `not_requested` for
its paused child. Including paused among cancellable owned states makes that
regression pass, retaining its scheduler slot, pending-child cancellation,
immutable inputs and same-key deduplication. This is a separate successor phase.

The first two browser cases fail: one never observes an enabled initial Pause
within its unchanged expectation; the other reaches a completed Pause but
expects Results after reload defaults to Model. The explicit keyboard return to
Results passes both cases. Stronger current journeys also open the frozen-input
dialog while paused and verify the selected snapshot, plan and semantic IDs.
The earlier 58-case cohort passes before the campaign fix; final affected,
backend, performance and package checks remain separately tracked.

The changed reference descriptor is version 1.1.0. Its implementation identity
includes the shared control policy. Only its descriptive compatibility snapshot
changes; external pins and runtime admission stay unchanged. A scoped
nonphysical capability record is required, alongside a declared operation.
The unsupported-control negatives now request still-unsupported Step.

These are actual owned native model/API/browser results and explicitly labelled
private-mailbox or transport fixtures. They do not establish native Windows,
live Lite, physical pause, live parameter mutation or milestone acceptance.
T027 closes its implementation component under the existing component standard;
counts are 49 completed, 41 in progress and 10 blocked. Wider acceptance stays open.

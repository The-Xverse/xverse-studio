# ADR-0029: Bounded cooperative pause of the owned reference model

Status: implementation under verification. This amends the owned reference
provider's previously unsupported optional-control surface; it does not change
the requirements, task dependencies, physical permissions or platform admission.

The reference provider becomes version1.1.0 and admits Pause from running and
Resume from paused. They use the existing authenticated, CSRF-protected,
idempotent run-command route and owner-signed worker mailbox. The backend checks
frozen run capabilities, legal state, state version and unsettled operations.
The worker independently checks state and the signed expected version before
applying either optional transition. Existing runs retain their frozen controls.
New run controls intersect implemented operations with the frozen descriptor's
unique scoped capability records, legal states, empty parameter schema and exact
nonphysical authority. A declaration alone cannot add an implemented control.

Pause is cooperative at a model-step boundary. The process remains alive;
simulation ticks and observations stop advancing. Resume adjusts the pacing
origin by actual monotonic paused duration, retaining the next model step rather
than catching up the paused interval. This does not establish physical pause,
determinism, rewind, reset, step or live parameter mutation.

The cumulative pause budget is30 wall seconds per run, declared in the provider
descriptor, frozen with the snapshot and reported with new run controls. Resume
does not replenish it. Budget exhaustion performs an orderly owned-model stop,
reports `PAUSE_BUDGET_EXHAUSTED` and retains incomplete simulation coverage.
Lifecycle, cleanup, evidence integrity and assertion verdict remain independent.
Stop/Cancel remain usable while paused, including native launcher shutdown.
Campaign cancellation also delegates Cancel to its paused active child; the
paused child continues occupying its existing scheduler slot. The existing
campaign budget remains explicitly measured in declared simulated seconds,
separate from each child's bounded paused wall time.

Applied optional commands record one completion event immediately, along with
their lifecycle transition and original simulation tick; terminal finalization
does not repeat those completions. A stale optional command fails without its
effect. The final lifecycle tick reflects the actual completed model interval.

The provider implementation digest includes the shared control-policy module.
The schema1.0 receipt-seconds and simulation-microsecond codecs explicitly admit
reference versions1.0.0 and1.1.0, whose encodings remain identical. Recorded older
evidence remains unchanged; other versions/providers and unproven intent codecs
remain unresolved. This is a closed codec admission, not a version wildcard or a
generic clock-resolution conversion.
The descriptive compatibility snapshot must refresh only this owned provider's
changed descriptor fields; external source pins and runtime admission remain.
An older snapshot cannot silently acquire these controls. Existing unsupported
control regressions use still-unsupported Step after this deliberate capability
amendment, preserving their denial assertions. The declared-target comparison
negative uses Step for the same unsupported-authority distinction.

Verification requires actual native authenticated Pause/Resume, unchanged inputs,
stable observations while paused, consecutive source ticks after resume, same-key
retry, state/version refusals, Stop/Cancel while paused, finite cumulative budget,
native shutdown and browser keyboard/reload operation. Fixture results cannot
close native Windows, live provider or physical acceptance. Tasks and acceptance
remain open until their complete existing scope has evidence.

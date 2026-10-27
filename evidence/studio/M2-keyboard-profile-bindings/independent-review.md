# Profile-binding completion review

Existing read-only reviewer `/root/t076_hybrid_tests` identified the cross-slice
gap: the earlier Workspace interaction counter did not observe Environment's
profile checkboxes, so a held foreign recovery could replace a newer draft.
Root reproduced that defect with two failing native keyboard journeys, applied
the scoped interaction signal, and subsequently executed the integration tests.
The reviewer performed no edits or tests.

The existing agent's terminal review was re-read during final verification:

> The scoped `onIntent` change addresses the reproduced foreign-recovery gap.
>
> It advances only the interaction sequence, so pending foreign navigation becomes obsolete while profile acknowledgement guards remain valid. Newer readiness still has separate load/preflight guards. Programmatic retry focus does not trigger pointer, key or input captures.
>
> Multiple increments from one native action are harmless; only generation equality matters.
>
> Read-only source review PASS. The integration successor remains pending; the earlier four passing cases predate this patch. No edits or tests performed.

That last sentence describes the review's own checkpoint. Root's later six-case
and expanded 24-case results are retained separately; the final gates establish
their own exact inputs. This review does not establish Windows, actual assistive
technology, live provider support or milestone acceptance.

Root final source review confirms additive exact-identity binding, synchronous
pending protection, direct authoritative Project acknowledgement through the
shared current-project/load/newer-head guard, and separate visible completion.
Normal current success preserves the existing Workspace/exact-notice path.
New selection/focus and obsolete navigation preserve the current context. Current
refusal preserves selection; App restores error/source focus only while guarded
context and focus origin remain current. Discovery errors/malformed/incomplete
collections remain unknown; empty success is labelled as an observation. Abortable
retry has guarded focus. No backend contract or provider authority changed.

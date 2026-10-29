# Implementation review

This is the implementing agent's read-only source/criteria review, not independent
milestone acceptance. Task definitions, dependencies and acceptance cases remain
unchanged. See the [closure audit](../../../docs/implementation/TASK_CLOSURE_AUDIT.md).

The route reads Project once, checks the requested revision and committed source
integrity, validates the captured source dictionary, and deep-copies one provider
descriptor for both resolutions. It refuses different/unresolved Systems. The
before/after descriptor digest detects mutation of the captured descriptor. It
does not claim that a later provider installation or project edit cannot change.
Both sides remain facts about the captured read, and execution still needs preflight.

The projection excludes environment paths, external asset handles and arbitrary
provider/target payloads. Comparison bounds are backend enforced and advertised;
mapping collection stops after the limit plus one. Browser parsing validates context,
bounded values, binding/portable identity consistency and uncertainty fields. No
imported capability grants an operation. Tables show 50 declarations per page.

The mapping fix follows the actual selected public Scenario schema. It retains null
mapping identity and the original Scenario pointer, qualifies local clocks against
the owning System, and never writes normalized mappings into authored sources.
Actual valid-source failure and successful successor are retained. Compilation
continues to reject unsupported clock/model additions; inspection does not admit them.

Browser reads have abort/timeout/context guards, with parent keys preventing an old
context from flashing on reselection. Read completion does not move focus. Held
transport tests now settle cancelled requests using public Playwright fallback;
the exact source proof preserves all application assertions and deadlines.

Finding outside this comparison: the previous published reservation `useObservation`
scheduled focus immediately after a state update. A labelled delayed MessageChannel
control reproduces an alert existing later without focus at both viewports. The
successor schedules that focus from committed React state and retains generation,
lifetime, dialog and active-element guards. Verification is recorded separately.

No task closure follows from this review. T077 still has no production run-control
caller for its disconnect helpers; T073 command-level conformance and the actual
physical/native-platform environments remain unfinished.

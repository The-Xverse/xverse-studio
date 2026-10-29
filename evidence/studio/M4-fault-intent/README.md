# Owned fault intent compilation checkpoint

This implements an offline component toward T082/T083 and FR-053/054/055/057,
AC-025. It does not implement scheduled worker effects or complete either task.
Original dependencies, 49 completed / 41 in progress / 10 blocked and zero accepted
milestones remain unchanged. Native Windows remains held; M5 remains deferred.

The new closed Profile binds `measurement-hold` to the existing owned observer's
`measured` field. Timing uses the selected public experiment-lite `fault-intent`
trigger/duration, not a new timing language. The full source set is compiled through
the public XDL profile-schema argument. The pure compiler then verifies exact Profile,
clock, observer and native fault attachment identities; whole source microseconds;
sample-boundary alignment; nonempty half-open intervals; observable recovery before
the horizon; one to 32 unique faults; nonoverlap; and absence of a conflicting legacy
fault parameter. Original declared units and platform nanosecond/source microsecond
ticks are preserved separately with authoritative plan/semantic digests.

The result is always `compiled_intent`, `executionAllowed: false`. The schema is not
advertised by the default registry. Existing reference preflight still refuses these
declarations. No worker, provider descriptor/version, command or default blueprint is
changed. There is no scheduled effect or recovery observation yet. The next work is
explicit model/provider admission and independently validated frozen worker execution,
then native/browser activation, recovery and intended-versus-observed evidence.
ADR-0031 records compatibility and remaining verification.

## Recorded verification

The final affected run passes **127 cases**, zero failures/errors/skips, 67.09 seconds,
on **399 identical selected inputs**. This includes 56 new offline contract cases,
4 existing Scenario checks, 19 authoring checks, 27 XDL adapter checks, 19 Profile
checks and 2 authoring HTTP tests. CLI/library plan agreement executes the real
selected XDL CLI. The fixed source fragments are inserted into a complete canonical
owned XDL set; they are test inputs, not a standalone executable project.

These runs are successive overlapping candidates, never additive test totals:

| Run | Actual result | Scope / finding |
| --- | --- | --- |
| initial | 37 pass / 7 fail, 397 unchanged inputs | New test Profile omitted required provenance; early rejection meant passing negatives did not establish their intended semantic path. |
| profile-repair | 37 pass / 7 fail, 397 unchanged inputs | Exact public compiler rejected faults lacking experiment-lite trigger/duration. The earlier proposed schedule representation was abandoned. |
| existing-lite | 25 pass / 22 fail, 397 unchanged inputs | Full public compilation/CLI worked; new helper read the wrong plan key (`faults` rather than actual `faultSchedule`). |
| plan-binding | 47 pass, 397 unchanged inputs | Correct authoritative plan binding. |
| bounds-review | 125 pass, 398 unchanged inputs | Added 32/33-fault boundary, exact clocks/observer attachment checks and related compatibility tests. |
| final | 127 pass, 399 unchanged inputs | Fixed source fixture and affected HTTP tests included. |

Logs, actual JUnit, commands and before/after maps are retained for every run. Exact
three-file source copies for all failed candidates were captured before subsequent
edits and checked against their recorded input hashes. Public log/XML/command copies
replace contributor filesystem prefixes with placeholders and remove trailing whitespace; the original private
copies remain local. One existing Starlette/httpx deprecation warning remains.

F821, architecture boundaries, descriptive platform compatibility and structural
spec checks pass. Those checks establish neither runtime admission nor acceptance.
All 116 previously packaged product payloads, including six UI assets, still match
the prior clean Linux package. Two new product files are added; no fresh package,
full backend or browser execution is claimed for this checkpoint.

## Review and limits

Primary source review checked the actual selected compiler implementation and output,
exact bindings/attachments, bounds, digest retention, unsupported semantics, schema
inertness and current preflight refusal. Its findings were repaired and affected
verification repeated as recorded above. This is not an independent milestone review.
The intended measurement-hold runtime freezes the current measurement while state and
control evolve, then restores measurement; none of those effects is proven by this
compiler. The legacy fault is unchanged.

The original late-Stop mismatch and original lost temporary journal remain unresolved
under their previously recorded limitations. This checkpoint supplies no new causal
evidence or fix. Broader stimuli/observation-cost support, M0–M4 acceptance, Windows,
external Lite, physical permissions/hardware, human/AT/SADS and independent review
gates remain open. See `candidate-binding.json` for exact scope and installed baseline
hashes. No task status or task definition was rewritten.

# Independent review and closure audit: T056

First audit verdict: keep open. Confirmed defects and their repairs:

| Finding | Repair |
| --- | --- |
| Observations were attributed by bare flow id, across all Scenarios | Only observers of the run's selected Scenario count, matched by full System flow reference |
| An invalid or partial journal was shown as observed | Only `valid`/`verified_prefix` evidence counts; anything else is `unverified` |
| A missing or future `recordedAt` read as "live"; RFC3339 text crashed; unknown state could be "live"; an ended prefix read as "final" | Receipt times decoded with the evidence codec; `unknown` for missing, undecodable or future times and unknown states; `partial` for an ended verified prefix |
| No "not observed" state for an ended run | `not_observed` (expectation unmet) when an ended run with a valid journal has an observer but no sample |
| A missing snapshot fell back to the draft | `409 SNAPSHOT_UNAVAILABLE` |
| The UI never refreshed after the run state changed | Re-projects on run-state change and every 2 s while live |
| Adding `command-flow` to `elementRefs` attached state observations to it in evidence | Reverted; a separate `resolvedFlows` list drives resolution |

A re-audit confirmed items 1–7 in code and asked for regression tests for System attribution, the
route-level 409, the `elementRefs` separation, and a refresh while the view stays open. All were added
(the refresh test is red-checked). Following its optional suggestions, a run without a selected
Scenario is refused, and malformed record fields can no longer raise.

Remaining assumption, inherited from ConnectionsView: one System per project in the UI. The backend
attributes by full System reference.

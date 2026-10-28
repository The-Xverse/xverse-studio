# Owned-fixture lifecycle verification

T033 remains in progress. The first combined full backend run finished with
**1,207 passed /2 failed** out of 1,209, with no skips and 379 unchanged inputs.
Both failures were reproduced with controlled native interleavings; test-only
corrections then passed those same interleavings. The full successor then passed all 1,209 tests on 379 unchanged inputs. A later
late-acknowledgement repair now passes the complete **1,211-test backend suite**,
with no failures/errors/skips and379 unchanged inputs. The affected86 browser checks and two separate performance cases also pass on
the same379 inputs. Clean Linux packaging is pending.

The implementation repairs these failure paths:

| Boundary | Resulting behavior | Focused execution evidence |
| --- | --- | --- |
| Late parent acknowledgement | Confirmed Start receipts and verified same-child terminal facts remain; a denied live observation keeps ownership unknown and controls blocked. | Two actual native regressions fail before repair and pass afterward; combined full1211 includes both. |
| Private preparation before launch | The original accepted Start/run settles atomically as `PREPARATION_FAILED`; immutable inputs and retry identity remain. No worker launches. | Four preparation boundaries plus rollback and two native handoff cases pass among 19 backend checks; two browser viewport cases pass. |
| Journal creation before workload start | `EVIDENCE_OPEN_FAILED` reports trusted terminal identity without a workload start. Exclusive creation preserves an existing journal. | Directory and existing-file native faults pass; both browser viewports pass. |
| Evidence finalization after execution | Known stopped lifecycle and complete runtime cleanup remain; evidence becomes partial and carries a separate failure code. An unsafe canonical source stays invalid. | Native finalization obstruction preserves the original prefix/hash chain; both browser viewports pass. |

The 19-check preparation phase and its later 82-check affected browser cohort
precede the journal repair and retain their 378-input scope. The subsequent three
native journal cases and four browser journeys each retain their 379-input maps.
These separate phases do not add up to a new full pass. The [boundary matrix](matrix.json)
records incomplete cleanup-failure and supported live-tune fixture obligations.

The [original full result](full-original/verification.json) and its source hashes
remain unchanged. A private base-tree plus changed-file bundle reconstructs all
379 tested inputs. The [fixture source review](controls/fixture-repair-review.json)
proves that only two tests changed afterward; all production and compiled inputs,
ownership assertions and deadlines remain identical.

The capability counterexample waits for the actual model to finish after its
unsupported-operation denial. The old auxiliary Cancel then correctly receives
`STATE_CONFLICT` for its saved version. The corrected test verifies natural full
coverage with no command effects. The journal counterexample holds a genuine
preparing response until a real sample arrives. The corrected test requires both
running API metadata and a sample before delivering the filesystem fault. Exact
request timing from the original full run was not captured. Each controlled
before/after execution and witness is retained under [controls](controls/).

This is owned native Linux fixture evidence. The separately published baseline
`08d379c` does not verify this successor. The 623 cases across 60 browser
files are [collected](collection/verification.json), not fully executed locally.
Native Windows remains held. Live Lite, physical operations, supported live
mutation, human/AT/SADS and independent milestone acceptance remain open.
Counts remain **49 completed /41 in progress /10 blocked**, with zero accepted
milestones.

The [pre-late-ack full successor](full-before-late-ack/verification.json) passes all
1,209 checks. Subsequent source review and two reviewed native regressions expose
a parent lost-ack update that could undo a confirmed Start receipt and terminal
report. Both native successors pass after preserving those historical facts. An
observation denied while the worker is live still makes current ownership unknown
and rejects Pause. The separate [scope record](controls/late-ack-scope.json) retains
the initial test insertion mistake, corrected layout, reviewed red and passing
successor. The [combined full successor](full-after-late-ack/verification.json) passes all
1,211 backend cases on379 unchanged inputs. The [current verification](verification.json) records86 affected browser and2
performance cases on the same379 inputs. No local full623 execution or clean
package pass is inferred. The earlier results retain their exact source scopes.
T033 remains open.

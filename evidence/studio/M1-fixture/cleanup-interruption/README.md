# Native cleanup interruption and pending-command failure

The worker now explains an interrupted directory release accurately: the model
stopped, while cleanup remains unknown. Previously this branch logged “workload
failed” despite retaining known stopped state. The change adds only this log
explanation and updates the owned provider's implementation digest. Removing the
recorded insertion recovers every original worker byte.

**37 affected checks pass**, zero failures/errors/skips, in181.28 seconds on391
identical before/after inputs. This includes five new native cases:

| Actual boundary | Verified outcome |
| --- | --- |
| Natural completion, Stop and Cancel interrupted at directory release | The original child reaches its actual `rmdir` call. Its parent verifies the exact owned path/directory and process identity, queues SIGINT, observes signal delivery and detaches. Worker-owned state stays stopped; cleanup is unknown with an identified unresolved resource, evidence is partial, and the corrected log preserves these facts. |
| Stop and Cancel accepted before an active-workload interrupt | The original signed request is delivered while the verified worker sleeps after an actual sample. SIGINT reaches the execution exception path before command polling. Run and unapplied command fail with `REFERENCE_WORKER_ERROR`; no command application is invented, and cleanup stays unknown. |

The syscall fixture uses Linux x86-64 `ptrace` from the verified child's test
parent, with a bounded deadline and guaranteed detach on assertion failure. It
changes no register, return value, worker file, state file, executable arguments
or clock. Signal delivery follows the documented [Linux ptrace contract](https://man7.org/linux/man-pages/man2/ptrace.2.html).
This is contributor fault tooling, requiring kernel5.3+ and tracing permission;
it adds no application requirement and supplies no Windows result.

Frozen snapshot/request/project bytes, original-key receipts, journal hash-chain
or reader integrity, operation counts and absence of replay/respawn are checked.
The 37-case cohort also repeats native temporary-resource faults, evidence I/O,
terminal races and campaign failures, plus labelled existing command/event
fixtures. Fixture outcomes retain their original scope.

The [initial three native boundary passes](initial/verification.json) preceded
the stronger message assertion. All [three message checks then failed](message-red/verification.json)
on the original worker, retaining exact test/worker/config source. They overlap
the current37 and are not added as disjoint passes. The corrected successor is
recorded in [affected verification](affected/verification.json), [JUnit](affected/tests.junit.xml),
[command/output](affected/run.log), [environment](affected/environment.json) and
[five parsed native witnesses](native-witnesses.json).

The [scope record](scope.json) binds the391 inputs and exact diagnostic insertion.
Of the prior389 inputs,387 are unchanged; only worker text and its recorded digest
change. Two test files are added. Of the prior116 package payloads,114 and all six
compiled UI assets remain unchanged. The prior package therefore retains its
earlier source identity. The [clean successor package](package/candidate-binding.json) passes all116 payload/archive hashes and six identical UI assets. The [92-case main browser](browser/verification.json) and [nine-case evidence/diagnosis cohort](evidence-browser/verification.json) pass; three diagnoses overlap, giving98 unique cases. The initial anchored selector matched zero cases and is retained separately.

The [full1265 result](full-original/verification.json) ends1264passed/1failed, with zero errors/skips. The late-Stop operation read returned `RUN_TERMINAL_BEFORE_COMMAND`, while the actual worker recorded `RUN_COMPLETED_BEFORE_COMMAND`; its stored result later matched the worker. The original assertion and exact source remain. Read-only instrumentation subsequently observes one initial and eight repeated passing executions; this does not establish the original cause or resolution. Pytest deduplicated the first repeated-node selection to one case.

Two [additional native Start-acceptance crash cases](start-acceptance/verification.json) pass in7.17s on392 identical inputs. A labelled initial-backend gate holds actual durable Start before private preparation or immediately before launch; only that verified backend is killed. The ordinary native restart retains the original receipt and snapshot/private bytes, reports unknown ownership/cleanup, rejects controls and launches no worker. All prior391 hashes and116 package payloads remain identical; no expanded full suite was run after these added cases. [Current binding and qualifications](candidate-binding.json).

T033 remains open for complete clause/environment review. Native Windows is held;
external Lite, physical, human/AT/SADS and independent milestone gates remain open.
Counts remain49 completed/41 in progress/10 blocked, zero accepted milestones.

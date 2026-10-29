# Native failure retention and observed full verification

The earlier late-Stop code mismatch remains unresolved. A fresh full backend
execution passes **1,267 tests**, zero failures/errors/skips, in1302.20 seconds on
392 unchanged inputs. It includes read-only backend observations of the four
original late-command cases, with unchanged workers, clocks and outcomes. All four
pass; no trace records are omitted. Observer timing effects remain possible. This
passing execution does not establish the earlier failure's cause or resolution.
[Full result](full-observed/verification.json), [JUnit](full-observed/tests.junit.xml),
[trace](full-observed/trace.json), [exact probe](full-observed/probe.py).

The repository now captures bounded diagnostics for explicitly marked owned native
failures before teardown. The original command test functions and assertions are
unchanged; only their module marker is added. **14 focused checks pass** on394
unchanged inputs: the ten existing native command cases plus four capture checks.
All116 packaged payloads and six compiled UI assets remain identical. A full suite
after these test-harness changes, browser/performance reruns and package rebuild
were not performed. [Binding](candidate-binding.json),
[focused result](reviewed/verification.json), [JUnit](reviewed/tests.junit.xml).

The real native control completes every original workflow assertion and then
fails deliberately. The parent verifies one actual child test, retained data
before teardown, journal hash chain/terminal digest and exclusion of keys, signed
mailboxes, requests, snapshots and auth data. The [captured original bytes and manifest](controls/retained/manifest.json)
are retained for independent inspection. A second native control obstructs output
and verifies that the original failure survives with explicit capture-unavailable
reporting. The child failures are expected harness controls, never extra app
regressions or disjoint passing cases.

The [initial capture cohort](initial/verification.json) is2passed/1failed. Its
budget fixture exhausted bytes at its last copy, so no omitted copy was exercised;
the corrected fixture exhausts the budget before another read. A child import
alias also prevents four accidental extra collected tests. Exact original source
and results remain. A separate [private-probe capture control](private-probe-control/verification.json)
verifies the earlier diagnostic tool; its signed mailbox stays private and is not
exported. These controls overlap the native workflow and are not summed into the
full1,267 or focused14 counts.

See the [contributor guide](../../../../docs/implementation/native-test-failure-capture.md)
for opt-in scope, bounds and unsupported acquisition. Native Windows remains
held; no live Lite, physical, human/AT/SADS or independent acceptance is inferred.
T033 stays open,49 completed/41 in progress/10 blocked, zero accepted milestones.

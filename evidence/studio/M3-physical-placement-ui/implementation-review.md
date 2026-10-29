# Root implementation review — physical-placement inspection

This is the implementing agent's source and evidence review, not independent agent
review or milestone acceptance. No agents were delegated for this slice.

The report adapter consumes the existing ADR0018 endpoint and never joins inventory
in the browser. Closed admission/permission/readiness fields remain closed. Exact
project/document/revision and selected System/Deployment headers are checked. Public
shape limits preserve the backend's Unicode code-point bounds. The shared inventory
adapter extraction retains its original strict default diagnostic alphabet; only
placement/source validation accepts the authoritative hyphenated XDL codes.

Actual native invalid-source tests first reproduced disabled inspection because the
validated list is empty. Inspection-only fallback to the authored display identity
repaired that path without changing the validated variants used by execution or
authoring. Its first successor reached the report and reproduced the rejection of
XDL-PARSE-YAML. The public validator diagnostic was independently confirmed with the
actual XDLAdapter, then admitted by the placement adapter. Later actual invalid
source witnesses pass; an invalid report does not pretend to establish empty inventory.

The expanded browser cohort reproduced overflow at 1024 pixels. A separate unchanged
product diagnostic cohort showed document.scrollWidth=1382 and a resolution-table
right edge of 1381.875, while 1440 had no overflow. The inherited global nowrap on
table headers included a long explanatory sentence. A scoped normal-whitespace and
overflow-wrap rule retains complete text and semantics without clipping observations.

Request state has an explicit project/revision/document/selection key, generation,
abort controller and synchronous pending guard. React layout cleanup aborts and
invalidates old requests. Focus completion checks mounted/current intent, original
focus ownership and open dialogs. No read invokes canonical commit/reload or global
error handling. The deadline is 30 seconds; deadline implementation is source reviewed,
not yet a directly timed browser acceptance case.

Source review found that inspection fallback used the first display resource matching
the selected reference. Two invalid authored Deployments can share a reference. The
fallback now requires one matching authored document. A real public clone/source-save
fixture verifies that duplicate authored identities keep inspection unavailable. This
was a source-review finding with a new successor witness, not a prior reproduced red.

The expanded 100 cohort ended 98 passed/2 failed. Both failures were a test fixture
assumption: document IDs are local to a project and both origin and destination use
doc-3. The changed-project case now checks the exact destination GET and actual report
projectId plus the destination document identity. No product change addresses that
fixture mistake. All other 98 checks, including the scoped wrapping repair and positive
metadata, passed in that historical cohort; it is not claimed as a full passing cohort.

The maximum 1000-row fixture is explicitly a transport fixture; all rows are visited
in 50-row local pages with one read. Positive metadata fixtures cannot install a
provider or enable physical/reservation operations. Actual empty/invalid/stale/unreadable
API witnesses are distinguished from these fixtures in their attachments.

Backend and Python/contributor inputs are unchanged; inherited 851 backend checks
must retain the exact input proof and CI scheduling control. The new test file reads
only the existing inventory public projection fixture and owned browser roots. No
runtime payload, contract, backend fixture or companion repository changes are needed.

Final targeted successor: all 102 cases passed in 306.552s; all 276 source/compiled/fixed inputs unchanged, 6 compiled UI assets. Actual duplicate identity refusal and corrected changed-project witnesses pass at both viewports. 28 selected paint pairs pass, minimum 4.60580833:1. At that review checkpoint, full 339 and separate performance were still pending; the targeted result alone did not establish full acceptance.

The first full 339 subsequently ended 338 passed/one failed in 1141.401s. The failure
was before the deliberate-focus assertions, at holdPut.ready's default 10-second
setup observation wait. All original focus assertions therefore remain unverified
for that one failed invocation. Performance was not run. The complete failed cohort
is retained; it is never called a passing full run.

The actual owned project is selected by exact test/project name and creation timestamp
against the recorded test start, not directory ctime alone. An initial ctime-only
candidate was rejected because it did not contain the project. The correct root
e18b0a68a1604604bfa3c5331f234ae5 contains revision2 and the exact held-source marker.
Its revision file modification times extend to test-start+13.226s. These are filesystem
observations, not original per-request timings; the host-load cause is unproven.

Only the test helper changes: a bounded 30-second actual route.fetch and response
observation, at most 64 timing events, and a generic transport-error record that omits
authentication/header data. All bytes outside holdPut and every source/focus assertion
are preserved by exact prefix/suffix and SHA/diff control. No application deadline,
performance threshold, provider operation or backend code changes. The replacement
target 118 includes the 16 affected source journeys alongside the original 102. All 276
final inputs are frozen again for target 118/full 339/performance 2; new final results
are pending. The original 275 other inputs, including all application/compiled/runtime
bytes, match both the old passing 102 and failed full.

Replacement final targeted cohort: all 118 passed in 355.782s. All 16 affected source journeys have actual PUT observations (200 or expected 412), with unchanged focus/source assertions. The former failure passes at both viewports. 30 selected paint pairs pass, minimum 4.605808325148723:1. The replacement full and separate performance remain pending at this observation.

Replacement full suite: all 339 passed in 1093.070s, no failures/skips/flakes. All 276 source/compiled/fixed inputs match final 118 across and within both runs. All 16 actual source request observations are present; former failure passed. Separate performance remains in progress at this observation.

Final gates completed: targeted 118 PASS 355.782s, full 339 PASS 1093.070s and separate performance 2 PASS 173.841s. All 276 source/compiled/fixed inputs, including 6 compiled UI assets, are identical across and within all final stages. No failures, skips or flakes. Final input digest sha256:6bd1453314475a21039e72e0f1872863fafce79f4939104c395b3d5b9b188cc4. Thirty selected paint pairs pass, minimum 4.605808325148723:1. Earlier full 338/1 remains failed; host-load cause remains unproven. Native Windows/AT/physical admission and milestone acceptance remain open; this is root implementation review only.

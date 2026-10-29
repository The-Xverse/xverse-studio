# Combined successor outcome

The modal mount/Escape repair is verified in the actual native Chromium lane. Both the synchronous New dialog and asynchronous Preflight dialog handled the observer-dispatched earliest post-mount Escape, closed, and restored focus. Both recorded events were prevented. Before the repair, the asynchronous dialog remained mounted and its Escape was not prevented. The original failing receipt and screenshot remain in ../before.

The broader combined lane is not passing: 18 passed and four failed in 500646.382 ms (8.3 minutes), with all listed source and distribution hashes unchanged throughout. All 15 session protocol contract cases and the unknown recorded-state native read-only recovery case passed.

The four retained failures are:

1. Neutral asset workflow: after native keyboard project creation, the expected project heading was absent while the page still showed Creating project and the New dialog's disabled submit button. This occurred before asset creation.
2. Native owned replay-window expiry: after the test's >1000-record precondition, no 410 response was observed within its four-second assertion window. This is not recorded evidence of duplicate Start.
3. Same-lifecycle metadata fixture: screenshot capture exceeded 15 seconds after fonts loaded; a response-disposed error also occurred during teardown. The receipt does not establish a failed metadata-value assertion.
4. Owned reference workflow: native Apply click exceeded 15 seconds after Playwright reported the control visible, enabled and stable and began the click action.

Full sanitized browser report, native output, all four failure contexts, available screenshots and both modal observations are retained here. The complete raw report/artifacts remain outside Git in .studio-local/evidence-raw/modal-combined-after. The recorded load and parent-reported I/O pressure are environmental context; they do not prove every failure was caused by I/O and do not waive any check. No assertion, timeout, source file or distribution was changed during this run. No additional heavy browser run was started.

This receipt makes no native Windows, performance, physical-provider or milestone-completion claim.

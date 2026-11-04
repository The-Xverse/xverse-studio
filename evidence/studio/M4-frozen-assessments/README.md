# Frozen assessment inspection — T088 progress

Product source: `d3d82e3`; full identity and 494 SHA-256 input hashes are retained in
`verification.json` and `source-inputs.json`. **T088 remains in progress; no milestone
or new live-evaluator acceptance is claimed.**

The Assertions view previously retained definitions/results between run selections,
accepted late responses and silently treated failed reads as empty lists. It now
mounts per project/run/snapshot, verifies protected frozen inputs, cancels obsolete
and sibling reads, distinguishes unavailable from empty, and pages at most100
results with at most32 definitions. Definition, clock/window, schema, evaluator and
evidence provenance are visible. Runtime state, evaluation execution, assertion
verdict and metric value remain separate. Numeric metrics carry no verdict; a
completed evaluation is no longer labelled Not evaluated. The existing evaluation
request remains backend-authorized; in-memory duplicate submission/retry handling
is not a claim of durable cross-navigation recovery.

Final verification: **14 passed, zero unexpected/skipped/flaky**. Five browser
journeys inspect a private copy of an actual completed Autoverse recording, including
1024×768/1440×900, failed read/retry, departed responses and sibling cancellation.
One explicitly labelled synthetic display fixture checks metric/indeterminate/error
presentation at both sizes; eight counterexamples exercise display identity/bounds
and incomplete-evidence guards. Synthetic rows are never submitted to the evaluator
or presented as authentic recorded results. The actual recording has no admitted
assessment definitions or results. This does not prove live evaluation admission.

The native driver verifies unchanged original/copy run and snapshot bytes, no new
run/operation/evaluation/snapshot, original backend/browser exit and root release.
494 selected source/lock/config/test inputs and six private UI files are unchanged
during the final run, and all selected sources match the committed product bytes.
TypeScript/private Vite build, architecture, compatibility, specification, Ruff and
diff checks pass.136 predecessor backend/contract/config/script/lock inputs remain
identical. No fresh full backend/browser/performance/package result is inferred.

`history/` retains all phases: an initial HTTP-client helper error, old-UI failures,
the specific swallowed-read-error regression, intermediate12/13 successes, the
sibling cancellation failure, aborted-route helper error and cleanup timeout, the
isolated repaired helper and final14. The helper repair isolates the explicit
assessment refresh from the application's independent header snapshot read and
awaits only its own handler. It preserves the actual request-abort assertion and
test/application time bounds. Historical outcomes have not been relabelled.

Reproduce using the pinned backend Python and Node, a completed private Autoverse
recording, the existing enrollment receipt and a privately built UI:

```text
<backend-python> -I tests/live/autoverse_assessments_browser.py
  --recording <completed-autoverse-recording>
  --receipt <private-enrollment-receipt> --output <new-private-output>
  --static-dir <private-ui> --node <pinned-node>
  --playwright-cli <installed-playwright-cli> --browser-cache <prepared-cache>
```

Arguments above belong on one command line. The driver copies only a settled owned
root, creates a fresh private session and never starts a workload. Public paths are
normalized; commands/cookies and original raw artifacts remain private.

Remaining work: actual admitted frozen assessment definitions/results and evaluator
provenance in the current complete-demo lane; real pass/fail/indeterminate/unsupported
clock cases, result pagination and mutation-acknowledgement/context tests; broader
accessibility/performance/package and independent acceptance. The selected Autoverse
adapter currently compares its complete resource set with its admitted template and
has no assessment-profile execution mapping; inspect/amend that boundary explicitly
before a positive claim. Existing immutable recordings must remain unchanged.

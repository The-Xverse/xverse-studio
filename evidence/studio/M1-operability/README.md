# T038 / T067 — native Linux operability and performance, 2026-10-26

Both focused browser journeys passed against the real isolated native Linux backend in Chromium
156.0.8078.4, with application/test source unchanged during the run. Each viewport exercises native
Tab/Enter controls, keyboard parameter entry, table-based element selection, polite textual validation
status, modal Tab containment, Escape/focus restoration, visible focus outline, actual Start-response
run identity and textual running/stopped states. Page overflow is checked after the run and both
large workloads. This covers the selected workflow; it is not a complete accessibility assessment.

Each workload excludes one warm-up and retains 30 measured repetitions. Raw distributions, units,
thresholds, browser identity and scope are under each viewport directory. Both model fixtures reported
**authoritative validation passed**, retained in `model-validation-outcome.json`.

| Viewport | Selection / inspector p95 | Open / validation presentation p95 | 200-row history page p95 |
| --- | ---: | ---: | ---: |
| 1024×768 | 29.3 ms | 1,652.7 ms | 446.3 ms |
| 1440×900 | 28.6 ms | 1,660.2 ms | 446.2 ms |
| Limit | 150 ms | 3,000 ms | 2,000 ms |

Canvas workload: 200 elements and 400 logical connections, measuring programmatic local button
selection and browser/authoritative-validation presentation. History workload: actual hash-verified
synthetic retained journal with 50,000 events, server filters, 200-record pages, exact row identities,
paging and unchanged source digest. These are authored/recorded fixtures, not runtime capacity,
simulator fidelity or physical-device observations.

Command: `.venv/bin/python -I scripts/test_browser.py --performance --grep 'operability:'`.
The wrapper launches/terminates only its own isolated backend on a dynamically allocated port.
`verification.json` and `application-source-hashes.json` identify this exact successor candidate.
All source covered by the earlier full 776-backend / 75-browser cohort is unchanged; only
`tests/e2e/accessibility.spec.ts` was added. The two new checks are a separate focused run, not a
claim that a 77-check full suite was rerun. Native environment/package/tool identities are in
`../M3-physical-contracts/environment.json`.

Initial attempts are retained: an anchored grep selected no full Playwright titles; then the test
read project identity before asynchronous example creation completed. The successor reads it after
validation and verifies the exact run returned by Start. Original test source and failure logs are
retained; neither was an application failure or a passing acceptance attempt.

The independent audit's first findings and successor verdict are in `independent-review.md`.
T038 and T067 remain **in progress**: Windows installation/testing is held at user request; no
screen-reader or other browser-engine assessment is supplied, and full diagnostic/accessibility
acceptance remains open. No milestone or live provider acceptance is claimed.

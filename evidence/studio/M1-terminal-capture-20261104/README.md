# Terminal observation fault-injection repair

The final 57 affected checks pass on `baac6a705ab279d5a2c88985c3dab00fcf100ca4`.
Before the test repair, the same cases produced 16 failures and 41 passes. This
is T033 verification progress: counts remain **71 completed / 19 in progress /
10 blocked**, with zero accepted milestones.

The secure report reader now acquires bounded bytes through anchored native file
descriptors. Three test files still patched `Path.read_text`, which that reader
does not call. Their delayed snapshots, exit observations and identity faults
therefore never reached the intended production boundary. Existing read-count and
state assertions expose the drift; no assertions were weakened to obtain a pass.

The tests now wrap `runs.service.read_bounded`. Every wrapped call first performs
the real anchored acquisition, then returns the explicitly controlled captured
observation. Production decoding, identity checks, monotonic lifecycle checks,
producer completion and final receipt reconciliation still execute normally.
Original BackendTask reporter threads use their own handles and completion
barriers; their finally blocks join them. Other process observations are labelled
fixtures, with process launch and control forbidden.

Only three contributor test files change. All 83 original assertion ASTs match,
and the other 533 selected inputs, including the entire production runtime and
frontend, remain identical. All 536 final hashes match committed Git and remain
unchanged during the final run. The separate pre-repair cohorts contain exactly
the same 57 case identities as the final cohort. No errors or skips occur.

[Verification](verification.json), [source binding](source-binding.json), the
original failed reports, final report and logs retain the results. Hostnames and
operator paths are replaced and trailing whitespace trimmed in public report copies; original private files
remain retained. [Static checks](static-checks.json) pass for the specification,
architecture, descriptive platform baseline, changed-file lint and whitespace.

This does not reconstruct the missing original late-Stop interleaving, execute
the complete lifecycle matrix, or establish a fresh full regression, browser,
Windows or provider result. The older `test_owned_state_handoff.py` also patches
the former seam; its executable reference case remains unrun and unrepaired in
this scope. No simulator, reference model workload, physical operation or new
Autoverse run was launched. The original prepared environment was untouched.

The existing producer-completion repair in commit `15e6b73` remains separate from
this contributor-test repair and from the historical failure's unproven cause.
T033 and the complete M0–M4 goal remain open.

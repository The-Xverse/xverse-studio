# Component self-review — 2026-11-06

Two product findings were repaired with direct counterexamples: inaccessible
retained-run selection without a browser preference, and stale list metadata
replacing the selected projection's current status. The 16 final selector cases,
unchanged six diagnostic and 22 playback cases, and actual Orca journeys at both
sizes pass. This is a component self-review, not independent milestone acceptance.

The picker uses the existing project filter and page limit, validates identity and
shape, bounds each read and its retained page, aborts departed reads and presents
failures explicitly. Current selection and page buttons preserve focus. Responses
cannot change a departed workspace. React renders metadata as text; no imported
command is executed. Backend capability and provider enforcement remain unchanged.
The actual backend, compiler, evidence writer and provider code are byte-identical
to the inherited baseline. No production dependency or industry dispatch was added.

The AT harness verifies its namespace before importing AT libraries or launching a
browser, creates an authenticated private display and private session bus, and uses
real Orca/eSpeak NG with an ALSA null sink. Original subprocess/pidfd handles govern
cleanup. Event count, snapshots, tree queue/depth, key sequence, duration and debug
output are bounded; missing/truncated observations fail the final journey. Sampled
process capture gaps are counted. Source/UI hashes and original/copy data guards
are checked after cleanup. No human auditory or broader accessibility claim follows.

Residual work remains the original T038/T097 complete critical-flow matrix,
required-host/Windows freeze, human studies, external admission and milestone review.
Historical timing failures and all exploratory harness failures remain retained.

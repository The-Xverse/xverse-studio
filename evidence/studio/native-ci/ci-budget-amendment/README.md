# Native CI job budget amendment — 2026-10-26

The source-editor predecessor jobs exhausted the total 25-minute job limit during browser
checks, after setup/backend/browser installation used roughly 13 minutes. All four GitHub
annotations explicitly report that limit. Their logs reached 161/170/162/165 passing browser
cases, with no assertion-failure lines before cancellation, and never completed the cohort
or package stages. Preserve cancelled outcomes; partial progress is not a CI pass.

The native Ubuntu24 job budget is now 45 minutes. Only jobs.native.timeout-minutes changes
in the parsed workflow. Actions/pins, commands, environment, matrix, test repetitions and
per-test deadlines are unchanged. Windows remains held. This gives the measured setup,
growing 209-case browser cohort and package/artifact stages room within a finite job deadline;
it does not hide test failures or establish a fresh-host result.

The recovery UI candidate completed its 209 local browser checks and separate performance
run with the old CI 25 input frozen. This amendment follows those checks as a declared
non-runtime input change. verification.json retains 264 unchanged source/compiled/fixed inputs
and the sole changed workflow's before/after digests and YAML control. For backend 851
inheritance, 163 inputs are byte-identical; the changed CI input has identical test commands.
The verified clean 100-file packaged payload is also byte-identical, and never includes
this workflow. Candidate CI under 45 minutes remains a separate observed gate.

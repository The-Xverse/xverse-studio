# Verification history

The original five admission failures, two clock/model negatives and independent READY-I01/I02
findings are retained before repair. Six permanent scope/availability/host negatives also failed
before their repair (`scope-before.txt`), then all 15 current preflight cases passed in 14.63 seconds
(`backend-successor.txt`). Four additional immediate pre-Start cases cover expiry, changed provider,
exhausted capacity and changed canonical snapshot bytes.

An attempted combined command initially named nonexistent `test_advanced.py`; collection exited 4
without running tests. The actual repository file is `test_advanced_api.py`. This invocation was not
counted as verification.

The first capacity test used intentionally synthetic occupied-run rows without a runtime operation.
Real reconciliation rejected that invalid fixture (`backend-fixture-before.txt`). Its first correction
made admission pass, but monkeypatch teardown restored reconciliation before application shutdown,
leaving one teardown error (`backend-focused.txt`, 30 passed and one error). The fixture now isolates
reconciliation and explicitly retires synthetic rows before teardown. Four pre-Start cases then passed
without errors in 7.55 seconds (`readmission-successor.txt`). This is admission failure coverage, not
evidence of four running processes.

A full run was interrupted after 100 passes while the fixture correction was being verified. Its
source hashes changed, so it is not candidate evidence. Raw interrupted receipt/log are retained
privately on loop10 under `.studio-local/evidence-raw/readiness-claims/interrupted-full/`.
The restarted full candidate suite has its own receipt under
`evidence/studio/release/linux-readiness-claims-2026-10-25/`; only its actual result is authoritative.

Four API/capability contract checks passed after additive contract-version discovery and generated
request schema refresh. Ruff passed for the changed readiness/runtime/annotation modules and tests.
Native Windows installation/testing remain blocked at user request; external providers, hardware and
full milestone acceptance are outside these owned Linux test results.

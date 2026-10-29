# Retaining an owned native test failure

An explicitly marked test with the `client` fixture can use
`@pytest.mark.capture_owned_native_failure`. The pytest report hook captures its
diagnostics after failure and before fixture teardown, without reconciling,
commanding, signalling or changing the run. The original assertion remains the
failure even if diagnostic output cannot be written.

Default output is `test-results/native-failures/<session>/<capture>/`, outside
pytest's disposable temporary directory. Existing CI artifact upload already
includes `test-results/`. Contributor runs may set `--owned-failure-dir PATH`.
The marker is for reviewed Studio-owned reference fixtures, not arbitrary
providers, imported projects or user environments.

Only `state.json` and `evidence.jsonl` are copied. Run/operation metadata uses a
closed field allowlist. Owner keys, signed command mailboxes, requests, snapshots,
bootstrap/session files and SQLite databases are excluded. Original fixture files
are never modified. Raw diagnostic files remain test artifacts; review and sanitize
them before committing evidence.

Limits per pytest session are eight failed cases, four run records and eight
operation records per case,64KiB per metadata row,4MiB per copied file and16MiB
of copied source bytes. Metadata has separate row/count bounds. Partial copies,
changed sources, unavailable files and exhausted budgets remain explicit in the
manifest. A copied byte hash is not an assertion of canonical journal integrity.

Source acquisition uses the existing anchored reader. Linux links and unsafe
paths are refused. Unsupported secure acquisition produces an explicit code;
there is no insecure fallback or native Windows acceptance claim. Capture output
failure is reported in the original test report.

The integration control executes the original owned native workflow, then raises
a deliberate assertion. It verifies retention before teardown, exact captured
journal chain/terminal digest and exclusion of private files. A separate output
obstruction verifies that capture errors preserve the original failure. These
induced child failures are harness controls, not application regressions. Safety
fixtures cover linked files and byte/case exhaustion.

The earlier full-run temporary-data loss remains documented. This tooling does
not reconstruct those deleted files or establish the cause of the late-Stop
operation-code mismatch. See [current evidence](../../evidence/studio/M1-fixture/failure-retention/README.md).

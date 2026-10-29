# Scenario authoring gap review

2026-10-25, base commit ba5ef0a33c8d161096420cad4b868205830ba1fd plus the separately identified neutral-asset successor.

SCENARIO-001: Experiments displays existing schedules/observers but offers only source editing. There is no transactional typed operation for initial conditions, steps, fault intent, observers or metrics.

SCENARIO-002: existing provider-scenario helpers are isolated fixtures, not an admitted interpreter. Do not make adding a form imply arbitrary action/fault execution. Keep the reference provider's exact supported-source/configuration admission and reject unsupported execution.

Tests first: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 TMPDIR=<loop10-cache>/tmp .venv/bin/python -I -m pytest tests/contract/test_scenario_authoring.py --basetemp=.studio-local/scenario-first -q --tb=short`: **4 failed, 9 passed**, 4.93 seconds. Positive authoring operations are unsupported; the helper module is absent. Negative passes at this stage establish only rejection, not implemented authoring.

The inspected normative source is the installed public XDL v1alpha1 `scenario.schema.json` at pinned platform commit 7fab6a290c3731533c2b88517158055c768b9d4e. Action objects and fault activation/recovery strings remain data; no new schedule language or provider privilege is introduced. Windows installation/testing stays blocked.

SCENARIO-003: adversarial selector probes before repair found unhashable list/object values in `kind`, `documentId` or `elementRef` raise TypeError rather than a typed rejection. Four focused probes failed in 2.01 seconds (`-k malformed_selectors`, `.studio-local/scenario-malformed-first`). Add selector type checks before dictionary/set membership; no source transaction or runtime effect occurred.

Verification setup corrections: the first combined run had a duplicate pytest module basename (collection stopped), corrected by naming the HTTP test `test_scenario_authoring_http.py`. The next combined run passed 53 checks and failed the new HTTP test's assumed document path; corrected to select the actual Scenario document by authoritative kind. Its focused HTTP successor passed. These are test setup failures, not passing product acceptance.

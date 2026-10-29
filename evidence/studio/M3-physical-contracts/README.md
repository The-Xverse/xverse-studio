# Physical-provider contract fixtures — T070

This task adds an in-memory provider and synthetic asset corpus under
`tests/fixtures/providers/physical/`, with contract tests in
`tests/contract/test_physical_provider.py`. It contacts no hardware, loads no driver and registers
no application provider. `physical: true` describes the binding under test; every asset and lease
retains `evidenceScope: fixture`, which cannot establish active-operation readiness.

The suite covers observed/unknown metadata, unresolved and absent assets, inventory-copy isolation,
exclusive reservations without a second delegation, lease bounds/renewal/expiry, observe-only
permissions, current stimulation grants and removed capabilities, destructive-operation denial,
durable unknown intent on lost acknowledgements, disconnect/reconciliation, unknown release and
independent stop acknowledgement, observed state and cleanup outcomes. The production inventory
remains empty and reports the physical provider unavailable.

The focused run includes the pre-existing reservation and hybrid-time integration cases. Six
isolated-process source mutations are each detected by the new contract tests: bypassed fixture
admission, exclusivity delegation, observe-scope widening, expiry, uncertain release and stop
acknowledgement interpreted as observed state. Mutation source is evaluated only in child-process
memory; repository application files are untouched. See `red-checks.json` and `red-*.txt`.

Initial harness attempts failed because the pytest base-temp parent was absent and then because the
new production-inventory assertion used the wrong route. Creating the local parent and using the
existing `/api/v1/assets` route resolved them; no application repair was required.

Commands, exact source hashes, native environment, results and independent review are retained in
this directory. Command paths in portable evidence are repository-relative; scratch files, tool
caches, browser data and artifacts were stored on the user's loop filesystem.

Only T070 can close on this fixture evidence. T073, T076 and the other downstream tasks retain their
own clauses. AC-021/022/023, M3 physical acceptance and all milestone gates remain open. No actual
device/provider, driver, permission scope or physical safe/stop state is claimed. Native Windows
installation/testing remains blocked at user request. No companion repository was modified.

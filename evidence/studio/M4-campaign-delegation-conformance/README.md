# Permanent native campaign delegation-recovery conformance

The four native recovery cases are now in
`tests/platform/test_campaign_delegation_recovery.py`. The initial backend has an
explicit bounded test-only pause after real Start returns and before campaign
acknowledgement. The durable child remains dispatching without its run ID while
the actual Start receipt and unchanged native worker exist. The test verifies
PID/birth, exact argv, owner and snapshot relations before killing only its owned
backend. Restart uses the ordinary native launcher. No provider descriptor, worker
code/argv, stored record, owner file or canonical evidence is rewritten.

Four Linux cases restart while the original worker is running, after its normal
completion, or after its own failure under continue and stop_on_failure. The
failed lanes verify the actual kernel sleep point and owner/PID/birth/argv before
SIGINT to only the original worker after the backend crash. Continue retains the
failed child and starts one pending successor. Stop on failure cancels pending
work without allocating another run. Repeated same-key retries preserve identities
and no duplicate run appears. Canonical base/child snapshots, Project and terminal
journal bytes remain unchanged. Partial prefix-verified evidence, unknown cleanup
and null verdict stay distinct from completed campaign coordination.

The complete backend baseline passed938 tests with zero failures/errors/skips.
Root review then found that final PID/birth assertions were conditional on worker
failure. The existing assertion was moved to the successful common path after all
retries, so all four modes explicitly verify the retained original worker identity.
Every existing assertion node and the exact embedded fault-fixture string remain.
Only this test source changed after the full baseline; runtime and all other934
test cases remain byte-identical. The final affected four cases pass separately.
This is baseline938 plus final4 coverage, not a single full938 run on the final
test source. Both exact source maps, commands, JUnit records and amendment are retained.

Fresh final format, undefined-name, architecture, compatibility and structural spec
checks pass. The existing Starlette/httpx deprecation warning is retained for both stages;
dependencies are unchanged. Passing JUnit hostname attributes are removed while
all testcase attributes and outcomes remain intact. Four original final-test
worker journals are copied byte-identically after credential/path screening, and
their complete sequence/previous-digest/canonical-digest chains are independently
verified. Raw auth/data roots, owner keys and raw CI logs remain private.

Application, service, browser-test and compiled UI bytes match the published focus
repair. Among its298 inputs,297 are unchanged and only non-executable ADR20 differs;
one native backend test is added. Prior48 affected/full474/performance2 and clean104-file
package belong to product5736276 plus equivalent metadatab2897ee. Those browser and
performance results are inherited through that exact comparison; no new execution
is claimed. All299 final selected inputs remain unchanged during final verification.

This is the implementation agent's root review, not independent milestone acceptance.
The labelled initial pause and Linux kernel/process fault boundary do not establish
arbitrary interruption points, mid-journal writes, native Windows, live external or
physical providers, actual AT/human measurements or complete campaign acceptance.
The full M0–M4 objective remains; M5 is deferred. Task states remain47 complete/43 in
progress/10 blocked with zero accepted milestones.

Clean committed successor package verification is retained below.

Clean candidate `be4d7e12d7554a39718f666d03036b972c3070fc` passed offline native Linux package provisioning from the prepared cache, startup/UI, Unicode persistence, public compilation and owned shutdown. All 104 manifest/archive/file hashes and six tested UI assets are verified; candidate-binding.json checks 293 committed source/fixed inputs plus six compiled assets. Native Windows remains held.

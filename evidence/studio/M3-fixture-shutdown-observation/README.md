# Required native fixture shutdown observations

The original two native journeys pass their application assertions but fail once
missing shutdown observations become mandatory. Pinned Uvicorn0.41.0 restores and
replays SIGTERM after serving/lifespan shutdown, so recording only in an outer
Server.run finally can be terminated before the record is written.

The fixture now wraps and preserves the actual application's original ASGI lifespan,
then records its counts after original shutdown and before signal replay. Actual
routes and the production application are unchanged. The Node helper requires a
closed, bounded observation after a host that became ready. Setup failures still
propagate without a return from finally; the labelled invalid-scenario control is
an expected negative and never runs its body. No timeout/assertion is weakened.

All34 configured native browser journeys pass with34 required raw fixture records.
Only two test-harness files differ from the1068/117/performance2 UI candidate. All110
customer payloads, production Python, backend pytest inputs, compiled UI,83 default
journeys and performance case source are unchanged. Their previous evidence and
clean f921 package are inherited by exact bytes; no new full508 or full-backend run
is claimed for this test-only change. Raw dictionary entries and fixture preparation
seconds do not establish physical state, safety, hardware clocks or device support.

The older a12 PR recovery failure is retained under related-ci/. Its exact two
current native cases pass unchanged; that does not explain the original CI event.
No source recovery fix or relaxed threshold is claimed. Root cause remains open.
Earlier absent-trace results remain absent-trace results; these fresh records are
new evidence, never a reconstruction of the old in-memory provider state.

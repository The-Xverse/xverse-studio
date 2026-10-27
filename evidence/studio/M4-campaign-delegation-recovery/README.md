# Campaign recovery after durable Start delegation

These two supplemental probes exercise a specific crash boundary in an actual isolated
native Linux backend. A labelled test-only wrapper pauses CampaignState.mark_started
after the real runs.start returns. The durable campaign child remains dispatching with
no runId, while the real Start idempotency receipt and the unchanged native worker exist.
The fixture verifies PID, process birth, exact unmodified argv, owner digest and snapshot
relations before killing only the backend Popen process it launched. It rewrites no
campaign, run, ownership or canonical evidence record. The initial backend is instrumented;
this is not an uninstrumented observation of naturally occurring timing.

The successor uses the ordinary unmodified native launcher. In one lane the original
worker is still running; in the other it has already written stopped/complete cleanup
and complete evidence. Startup turns the interrupted claim unknown, and normal polling
looks up its durable Start receipt to recover the existing run identity. Both lanes
finish the original child and schedule only the pending second child. The same-key
campaign retry returns the original accepted identity. Exactly two distinct runs exist,
with the original child keys, matrix values and first run identity preserved. No blind
Start replay or worker respawn is observed. A separate read-only SQLite/native-state
review confirms the original worker PID/birth in both final states.

Canonical project and active snapshot bytes/identities remain unchanged. In the terminal
lane all retained top-level worker files except the private owner key are hashed before
restart and compared afterward, including the canonical evidence journal. The running
lane does not claim a pre-restart terminal-file comparison. All 298 selected application,
test, configuration, lock, ADR, guide and compiled UI inputs remain unchanged.

Both lanes pass separately (17.391 s and17.563 s). They are supplemental native subprocess
probes, not two extra pytest passes in the existing934 backend result. The parameter-focus
full browser/performance pipeline was still running when this evidence was retained;
these probes do not establish that pipeline's outcome. The first fixture attempt correctly
received PARAMETER_UNRESOLVED for the mistakenly named time_step before any campaign or
worker allocation. The successor uses the existing timestep field; the failed attempt,
its exact source and unchanged-input maps are retained separately.

This is the implementation agent's root review, not independent milestone acceptance.
The first two probes do not cover worker failure; the additional lanes below exercise
a specific failed-worker boundary. Arbitrary interruption points, mid-journal writes,
the complete campaign matrix, native Windows and external/physical providers retain separate gates. No hardware,
companion repository or unrelated process was accessed. Raw authentication and owned data
roots remain private; only allowlisted credential-free observations are retained.

Counts remain47 complete/43 in progress/10 blocked with zero accepted milestones.

## Additional failed-worker recovery lanes

After killing the same exact owned, fixture-paused backend, the probe verifies the
original worker's PID/birth, unchanged argv, owner and actual kernel sleep point before
sending SIGINT only to that worker. The worker's own exception path writes failed state,
unknown cleanup and partial evidence. It is not replaced, and neither canonical records
nor its launch arguments are rewritten. The normal native launcher then restarts.

Both policy lanes pass with all298 selected inputs unchanged. Continue retains the
failed first run and starts exactly one pending successor, which stops normally.
Stop on failure retains the failed run and cancels the pending child without allocating
a second run. Both recover the durable original Start receipt and child key, retain
the original worker PID/birth, preserve the canonical Project and active snapshot, and
create no duplicate run. Campaign coordination completes independently of the first
run's failed/unknown/partial facts and null functional verdict.

The actual observations reader reports verified_prefix. An independent journal pass
checks every sequence, previous digest and canonical record digest, including the actual
worker error event. Terminal worker files and journal bytes stay identical across restart.
The failed-continue lane first passed12.781s before the extra reader/hash-chain assertions;
that exact source/result is historical. The final continue successor passes14.462s with
those assertions, and the stop-policy lane passes6.668s. These are two additional native
subprocess cases, not new passes added to the934 pytest tally. All four final cases use
the labelled initial backend pause and unmodified native launcher restart. They do not
establish arbitrary failure timing, interruption inside a journal write, Windows or
external/physical-provider admission.

Four credential-free original worker journals are retained as unmodified byte-identical copies. An independently executed verifier compares each with its actual private terminal journal and checks all sequence/digest links. Owner keys, request files and raw authentication/data roots are excluded. See original-worker-journal-verification.json.

# Compare recorded runs

Open **Results → Compare** for the run you want to inspect. **Refresh recorded runs**
reads workspace history in pages of 20. Choose a **Baseline run** and select
**Inspect compatibility**. Each side keeps its original project, revision, run and
protected snapshot identity; current draft edits do not replace recorded inputs.

The configuration table shows model and plan digests, resources, deployment/bindings,
Scenario, parameters, artifacts, profiles, provider, capabilities, clocks and compiler.
Expand an input to inspect its frozen values. Missing facts are **unavailable**, even
when absent on both sides. A configuration difference is not an assertion failure.

The recorded-results table retains each side's quantities, units, exact source ticks,
coverage and numeric summary. **Pairing blocked** lists the missing or incompatible
checks. Different windows, units or clock definitions, gaps, uncertain timing and
unverified/incomplete evidence cannot be presented as a valid like-for-like result.
No interpolation, cross-clock conversion or invented numeric difference is applied.
Reports inspect at most 32 fields and bounded metadata. For an unsupported report size,
inspect the individual run evidence; original data is retained.
Run state, cleanup, evidence integrity and functional assertion outcomes stay separate.

Changing the baseline clears its old report. Retry inspection after a failed read;
refreshing or reopening does not execute a workload. Inspection does not modify
protected snapshots or canonical evidence.

**Open recorded playback** returns to the selected run's original observations.
**Replay observations** only changes their local presentation; leaving that tab stops
local playback. It neither runs the model nor establishes determinism or physical replay.

**Preflight a new run** checks the current draft and creates a new frozen input snapshot;
Start requires separate acceptance. **Rerun frozen inputs** instead requests fresh
backend admission for the historical inputs and creates a new run/snapshot identity.
Neither path guarantees reproducibility or admits an unsupported provider or physical
operation. Native Windows and live-provider support require their own evidence.

A rerun can continue on the backend after you leave Results. Its acknowledgement
preserves a newer view, selected run, annotation draft or deliberate focus. Return
to Results and use **Recorded run** to inspect the retained child independently.
If acknowledgement is uncertain, repeating **Rerun frozen inputs** retries the same
stored request key. A read timeout does not cancel the experiment or request a
second Start. An incompatible operation or child reply stays unconfirmed until a
matching response can be read.


Use **Frozen inputs** to inspect the selected recorded run's verified sources and
run/project/snapshot identities. **Compiled contributing inputs** and **Complete
authored revision** are distinct input sets. If the complete revision was not
recorded, its option is unavailable. Sources are read-only.

Changing the selected run, view or results tab dismisses the earlier inspection.
A delayed read preserves newer focus and dialogs. After a failed or timed-out
read, select **Frozen inputs** again to retry. Inspection starts no workload and
does not modify the original snapshot or recorded evidence.

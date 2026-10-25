# Scenario intent and execution

Scenario steps, faults, observers and metrics are authored XDL. Studio's semantic edits use the
pinned public Scenario schema and validate the complete source transaction before committing.
They preserve resource/item identity and unedited payloads. Invalid references, negative schedule
times, stale revisions, removal of required last entries and incompatible source fail without saving
a partial revision.

Steps declare a target, clock, nonnegative time/unit and an inert action object. Faults declare a
target, kind, maturity and opaque activation/recovery intent. Observers declare target/clock,
sampling intent, payload schema, units and evidence sink. Metrics declare observer IDs, calculation
reference, units and acceptance intent. Neither a schema URI nor evidence-sink URI is fetched by
authoring. A calculation reference is not executable code; use the separate admitted bounded
assertion workflow to evaluate immutable evidence.

The typed authoring bounds are 64 steps, 32 faults, 32 observers, 64 metrics and 64 KiB per edit
payload. They are advertised by `/api/v1/capabilities`. Advanced source edits remain subject to
the one MiB document and complete-project limits. Execution admission is separate from source validity.

The owned reference provider executes its exact admitted first-order model and parameter set.
Additional topology, schedule, observer, fault-intent or extension changes remain authored but block
its preflight. Studio never executes a preset after silently dropping those changes. To exercise
the supported owned fault, set the declared `fault` parameter to `stuck-sensor`: it activates halfway
through that bounded reference run and records requested and observed activation separately.
General fault activation/recovery text has no admitted interpreter in this provider. This is reference
model evidence, not evidence of an external simulator or physical device.

Windows installation/testing remains blocked at user request. Authoring and browser evidence are
recorded for the actual Linux candidate; they do not establish native Windows acceptance.

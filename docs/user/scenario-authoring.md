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

In **Experiments → Scenario**, the authored timeline shows the current draft's steps,
faults, observers and metric intentions. Choose an **Authoring clock** and **Authoring
schedule unit** to inspect step markers in their original units. Other clocks, observer
sampling and opaque fault schedules stay unplaced. **Edit intent** opens the same typed
form used by the item controls. Saving creates a canonical revision; a later acknowledgement
does not close a newer draft or removal dialog. A stale-revision refusal preserves the
form so you can compare it with the current project before retrying.

In **Experiments → Timeline**, use **Inspect selected run timeline** to read the selected
run's verified frozen inputs, canonical recorded events and existing evaluations. The
snapshot identity, executed revision, Scenario and Deployment identify the actual inputs.
Later project edits remain separate and produce a draft/run difference notice. The view
does not evaluate definitions or issue runtime commands.

Open **Inspect frozen definitions** to review typed declarations before evaluation.
The list includes each definition's original expression, clock/window, declared
coverage policy and definition/profile/schema identities. These are declarations,
not verdicts. An unavailable resolver is labelled unknown; it does not establish
that no definitions exist. Current draft definitions cannot replace this frozen list.

**Timeline clock** selects the original source clock; inspect again after changing it.
Only admitted clock/unit encodings receive markers. Exact tick strings, original timing
metadata and independent receipt UTC remain available in **Timeline records**. Fault
requests and fault observations have separate event identities. The frozen reference
fault parameter appears as a configuration intention with no invented authored timestamp.
Same-axis placement is not proof of causality or a physical fault effect.

Evaluation ranges use half-open windows: `[start, end)`. Execution status, assertion
verdict, metric value, coverage, reason codes and evidence/definition digests are separate.
A numeric metric has no pass/fail verdict. Expand **Inspect exact data** for a row's
provenance, including evaluator identity. A historical result whose evidence no longer
matches is labelled rather than treated as an assessment of current evidence.
An unfinished or interrupted evaluation can show unknown coverage and partial state.
It has no assertion verdict; recorded evidence remains independently inspectable.

The browser reads 100 rows per page and draws at most 100 placed markers from that page;
the table retains every returned row, including unplaced observations. Use the named
scrollable table region for keyboard inspection. The backend considers at most 50,000
records, 1,000 intentions and 200 recent evaluation records. Completeness, gaps and
missing/unsupported timestamps stay visible. Use Results' retained-history pages to
inspect evidence outside the timeline's processing window. A changed-input cursor,
unavailable read or malformed response requires a new first-page inspection; it never
turns missing observations into a known empty result.

Native Linux is the current delivery target. Windows delivery is outside the release
scope under ADR-0036; historical Windows results remain evidence, not current gates.

## Autoverse browser-input loss

Classic Autoverse provider 0.2.0 admits a bounded `driver-input-loss` fault for an
already-supported `studio-browser` project. Pygame and platform-mode projects
refuse this fault. Changing only a Pygame Scenario's input-surface field does not
create the complete supported browser variant. Guided fault presets remain pending.

Add this item under the Scenario's `spec.faults`, keeping the rest of its supported
source unchanged. The existing experiment-lite Profile supplies typed timing.

```yaml
- id: input-loss
  targetRef:
    apiVersion: xverse.io/xdl/v1alpha1
    kind: System
    namespace: org.xverse.studio.autoverse
    name: autoverse-demo
    element: driver
  faultKind: driver-input-loss
  activation: urn:xverse:studio:autoverse:input-loss:1.0:activation
  recovery: urn:xverse:studio:autoverse:input-loss:1.0:recovery
  maturity: prototype
  extensions:
    io.xverse.experiment:
      schemaVersion: '0.1'
      kind: fault-intent
      target:
        apiVersion: xverse.io/xdl/v1alpha1
        kind: Scenario
        namespace: org.xverse.studio.autoverse
        name: interactive-drive
        element: input-loss
      trigger: {kind: time, at: 5, unit: s}
      duration: {value: 3, unit: s}
      timeDomainId: host-runtime
```

Timing starts when the actual demo reaches running, after preparation. The worker
suppresses fresh browser frames during the interval; suppressed sequences are
consumed and never replayed. The bridge's existing 750 ms lease expires normally.
Recovery requires fresh input. This affects the bridge's publication lease; it
does not assert a vehicle response or physical safety outcome.

At most eight faults are admitted. Activation must be at least two seconds after
running, duration 2–30 seconds, recovery at least two seconds before the horizon,
and the next activation at least two seconds after the previous recovery. Only
whole-microsecond positions normalized by the public compiler are admitted.

Inspect separate `fault.activation_requested`, `fault.activation_observed`,
`fault.recovery_requested` and `fault.recovery_observed` records in retained history.
An observed activation requires suppressed input and a fresh inactive bridge lease
report; observed recovery requires a fresh publication acknowledgement and active
lease report. No input or missing bridge evidence leaves effects unobserved. Stop
during an interval records interruption without inventing recovery.

Fault records carry a declared host-relative microsecond clock. Vehicle telemetry
remains unmapped, and generic timeline marker placement for this new codec is still
unsupported. The actual fixed input rate limit remains 25 requests/second. No native
X-COM fault, simulation clock mapping or deterministic replay is claimed.

## Inspect source support and observation budgets

The read-only Scenario admission API accepts the current project revision, chosen
execution provider and optional Scenario reference. It reports declared stimuli,
faults, observer source/clock/sampling/units and known provider cost budgets. Its
positive result says **preflight required**: it does not contact runtime resources
or create a run. A fresh preflight and Start are still required.

Classic Autoverse declares one observer slot against capacity one. CPU, memory,
latency and retention policy are not measured or inferred from that slot count.
Platform mode exposes four existing observer declarations with undeclared costs.
Missing costs under an explicitly declared budget block execution; mismatched
units are not converted. Invalid source keeps counts/costs unavailable rather
than appearing as a zero-cost configuration.

Open **Experiments → Scenario** and select **Inspect scenario support** to see
these declarations for the chosen provider and current draft. Editing the draft
clears the old result. A mismatched or unsupported response is unavailable, never
a positive admission. Guided fault timing and further clock timeline integration
remain separate work.

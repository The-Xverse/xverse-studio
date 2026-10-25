# Acceptance and Verification Plan

**Feature:** `001-industry-agnostic-studio`\
**Status:** planned. Every case below is **NOT_RUN**; no runtime, hardware or usability result is asserted.\
**Authority:** [spec.md](spec.md) defines requirements and success thresholds. [traceability.json](traceability.json) maps exact requirements, task IDs, cases and success criteria. [tasks.md](tasks.md) schedules implementation and verification.

## How to record a result

Use `NOT_RUN`, `BLOCKED`, `PASS` or `FAIL` for acceptance-case status. Record outcome per lane when a case has fixture and real-provider variants; fixture PASS never promotes a blocked real lane. Assertion verdicts inside a run are separately `pass`, `fail`, or `indeterminate`. A case testing an expected rejection passes only when the documented rejection and lack of effects are observed.

For each executed case retain: candidate revision and dirty-state/diff identity, case and lane, exact model/artifact/provider/profile versions and hashes, procedure or command, sanitized host/browser/runtime identity, start/end and clock interpretation, exit status, assertions, bounded observations/logs, evidence hash/location, limitations and reviewer findings. The release gate consumes exact-candidate evidence; stale or mismatched evidence remains informative but cannot satisfy acceptance.

Cases start at their first applicable milestone and are retained through subsequent milestones. Later requirement extensions in a retained case are tested when that requirement enters scope. All physical and live-negative operations remain bounded by the selected provider's actual admission and authority. Evidence collection must use supported observation contracts; private streams are not bypassed.

## Reference environment and thresholds

M0 records reproducible native Linux and native Windows reference hosts with at least four CPU cores, 8 GiB RAM, local SSD and exact supported distribution/edition/release, architecture, browser and language-runtime versions. This defines supported combinations and does not promise every Linux or Windows release. Provider/simulator overhead and provider OS/driver availability are separate from the Studio application and isolated reference measurements.

- SC-008 M1 platform gate: AC-032 must pass independently on both native hosts for install/start/browser access, import/save/reopen, validation, owned-reference run/cancel, results, reconnection, backend recovery and clean stop. A Windows browser using a Linux backend or WSL cannot satisfy the Windows lane. Core operation has no undeclared Bash/VM/container/remote-Linux dependency. Optional OS service registration is assessed only if offered.
- M2 and later: repeat applicable authoring, bidirectional portable-project exchange, accessibility and performance cases on the native support matrix. Preserve platform-specific results. Live simulator/hardware cases identify the actually admitted host and remain blocked on unsupported hosts; a correct unavailable-provider diagnostic is a core capability test, not proof of that provider's execution.

- SC-001: at least 4 of 5 first-time X-Verse users complete the prepared example/change/run/result/failure task within 15 minutes without terminal commands or facilitator intervention. Record setup separately and retain failures in the denominator.
- NFR-007: 200 visible elements and 400 logical connections; local selection/inspector update at p95 ≤150 ms and open/validation-result presentation at p95 ≤3 s; 30 repetitions after one documented warm-up.
- NFR-008: 50,000 local evidence events; first filtered page of at most 200 events at p95 ≤2 s over 30 repetitions. Record memory/queue bounds, omitted-display counts and authoritative evidence independence.
- NFR-006: critical workflows at 1024×768 and 1440×900, including keyboard-only structured graph alternatives, focus, labels and non-colour status.

Use the actual measurements. The targets above are not benchmark results, a simulator timing guarantee, or hardware capacity claims.

## Cases

### AC-001 — Baseline, contracts and capability discovery

**Milestone:** M0; retained through M4. **Status:** NOT_RUN.\
**Environment:** owned fixtures; selected installed platform.\
**Requirements:** FR-006, FR-007, NFR-001, NFR-002, NFR-009, NFR-010, NFR-003, NFR-012.\
**Success criteria:** Supports the stated requirements directly.\
**Tasks:** T001, T002, T003, T004, T011, T012, T013, T014, T099, T100.

**Given:** An exact platform/profile/package set and owned provider fixtures with supported, unsupported and incompatible capabilities. The selected Linux and Windows native support matrix records distribution/edition/release, architecture, browser and language-runtime versions.

**Procedure:** Inspect version/capability responses; change a provider or profile version; request an unsupported operation directly through the API. Inspect Studio-host capability and provider OS/driver capability independently on each native host.

**Expected:** Record immutable baseline identities and admitted limits; incompatible semantics remain unresolved; unsupported operations fail in the backend before effects. No generic runtime service is inferred from private Lite classes. Core Studio capability does not disappear because a simulator is unsupported on that OS; provider operations correctly remain unavailable and their platform limits are explicit.

### AC-002 — Authoritative XDL import and semantic identity

**Milestone:** M0; retained through M4. **Status:** NOT_RUN.\
**Environment:** owned XDL fixtures; installed validator/compiler.\
**Requirements:** FR-001, FR-003, NFR-002, NFR-009.\
**Success criteria:** SC-002.\
**Tasks:** T005, T006, T007, T008, T014, T015, T016, T099, T100.

**Given:** Valid YAML/JSON representations of one system and equivalent CLI compiler inputs.

**Procedure:** Import, validate, compile, save and reopen; vary comments, file ordering and source formatting; compare canonical semantics and plan identity using the platform rules. Repeat native validation and persistence on Linux and Windows and exchange supported portable inputs in both directions.

**Expected:** Equivalent declared inputs produce equivalent plans. Source and semantic identity are distinguished; no second graph configuration overrides XDL; required profile files and references are explicit. Path and line-ending differences do not create unintended executable semantic changes; host-local bindings are resolved separately.

### AC-003 — Untrusted project/package input remains inert

**Milestone:** M0; retained through M4. **Status:** NOT_RUN.\
**Environment:** hostile owned import fixtures.\
**Requirements:** FR-003, FR-004, NFR-004.\
**Success criteria:** Supports the stated requirements directly.\
**Tasks:** T009, T010, T014, T015, T016, T039, T099, T100.

**Given:** Archives containing traversal, symlink escapes, oversized inputs, duplicate entries, unknown extensions, credentials and command-like content. Inputs also include Windows drive/UNC/device paths, reserved names, case collisions, junction escapes, spaces and non-ASCII names.

**Procedure:** Attempt import and project export within an allowlisted workspace, including direct API requests. Run the hostile-input and file-boundary suite natively on both OS families.

**Expected:** Unsafe paths and limits are rejected; imports never run scripts or providers; unknown extension content is preserved but cannot become executable valid content; credentials are rejected/redacted according to the project contract and never appear in exports or diagnostics. Platform-specific path/locking behaviour cannot escape the project root or bypass admission; portable and host-local path meanings remain distinct.

### AC-004 — Prepared example and actionable onboarding

**Milestone:** M1; retained through M4. **Status:** NOT_RUN.\
**Environment:** owned blueprint fixture; admitted live blueprint for live claim.\
**Requirements:** FR-002, FR-005, NFR-012, NFR-003.\
**Success criteria:** SC-001.\
**Tasks:** T015, T016, T017, T036, T040, T100.

**Given:** A prepared example, an offline environment and a separately prepared admitted live environment.

**Procedure:** Open the example, inspect purpose/interfaces, edit an allowed parameter and follow environment diagnostics. Run the prepared reference example through a native Linux backend and a native Windows backend in their supported browsers.

**Expected:** Useful project/evidence views work offline; prerequisites identify exact remediation and unsupported operations. An admitted owned executable reference provider offers Run with explicit reference scope. Only an admitted live provider can claim live integration; unavailable live providers remain disabled, and previews or replayed/mock outputs are never reported as live execution. Required settings have units, bounds and defaults with provenance. The core workflow works without WSL, VM, container or remote-Linux prerequisites. An unavailable live provider has an actionable OS-specific message; reference execution is labelled with its actual scope.

### AC-005 — Preflight binds the exact execution request

**Milestone:** M1; retained through M4. **Status:** NOT_RUN.\
**Environment:** owned runtime fixture; admitted wrapper for live lane.\
**Requirements:** FR-008, FR-009, FR-010, NFR-011, FR-006.\
**Success criteria:** SC-008.\
**Tasks:** T018, T019, T020, T031, T032, T033, T035, T040, T100.

**Given:** A valid project with known artifact identities, resource limits, target health and a preflight result.

**Procedure:** Change model, deployment, artifact, capability version or resource availability before Start; exceed admitted unit/time limits; retry with unchanged admissible inputs. Exercise a fixed workflow that generates its own XDL and ignores a requested parameter/model edit. Request the Linux-only historical shell-wrapper candidate from native Windows, and separately exercise a supported native reference provider.

**Expected:** Preflight is invalidated or refreshed on relevant changes and Start verifies the same snapshot. Model-valid, artifacts-available, target-ready and permits are separate facts. Limits block execution before acquiring or starting resources. The adapter exposes its effective normalized inputs/plan for comparison before Start. Unsupported edits are rejected until a compatible config-input integration exists; unchanged fixed workflows remain explicitly scoped. Studio/backend availability and runtime/provider compatibility are separate findings; the unsupported shell wrapper is rejected without starting WSL, a remote host or another unrequested execution environment.

### AC-006 — Normal lifecycle and evidence closure

**Milestone:** M1; retained through M4. **Status:** NOT_RUN.\
**Environment:** owned runtime fixture and admitted real Lite lane.\
**Requirements:** FR-011, FR-014, FR-015, FR-020, FR-022.\
**Success criteria:** SC-003.\
**Tasks:** T021, T022, T027, T033, T034, T035, T040, T099, T100.

**Given:** An admitted supported experiment with explicit ownership and observers.

**Procedure:** Start, observe startup, finish normally, request stop where supported and read the final run. Repeat owned reference-runtime start/finish/stop and evidence readback on both native platforms; run live variants only on their admitted OS.

**Expected:** One run ID anchors state/events and immutable inputs. Startup respects dependencies. Completion, cleanup and evidence-integrity states are independent; a completed process does not assert functional success. The real lane records actual provider and scope. The actual effective generated XDL/plan recorded by the adapter equals the requested admitted immutable snapshot; a wrapper ignoring input edits cannot pass this case.

### AC-007 — Partial start, cancellation and cleanup failure

**Milestone:** M1; retained through M4. **Status:** NOT_RUN.\
**Environment:** faultable owned runtime fixture; supported live negatives.\
**Requirements:** FR-011, FR-014, FR-020, NFR-005, NFR-011.\
**Success criteria:** SC-003.\
**Tasks:** T021, T023, T027, T031, T032, T033, T034, T035, T040, T099, T100.

**Given:** A run with failure points during prepare, startup, active operation, stop and evidence finalization.

**Procedure:** Inject failures at each boundary; repeat cancellation; fail cleanup or evidence collection. Exercise platform-specific process termination/cleanup using verified owned resources on native Linux and Windows.

**Expected:** Only owned resources are stopped; commands are idempotent; bounded stop policy is respected. Cleanup uncertainty/failure remains visible and actionable, evidence gaps remain visible, and no state is promoted to a success merely to close the UI. No POSIX-only signal or process-group assumption is required for native Windows run ownership and cleanup.

### AC-008 — Browser reconnection and duplicate command handling

**Milestone:** M1; retained through M4. **Status:** NOT_RUN.\
**Environment:** owned runtime fixture; browser automation.\
**Requirements:** FR-012, FR-013, FR-021, NFR-005.\
**Success criteria:** SC-003.\
**Tasks:** T021, T022, T023, T025, T026, T033, T035, T040, T099, T100.

**Given:** An active run and two browser sessions sharing one project.

**Procedure:** Double-click Start; retry identical command after response loss; refresh/close/reopen the browser; reconnect with old, valid and expired event cursors. Repeat with each supported browser/native backend combination and include a failed accepted command event.

**Expected:** One accepted command creates one run; payload-changing reuse of an idempotency key is rejected. Browser loss does not transfer ownership or restart a run. Reconnection reconstructs state; an expired cursor produces explicit resynchronization and gap information. command.failed remains an execution failure, not a successful mutation or invented lifecycle outcome.

### AC-009 — Backend restart and uncertain ownership

**Milestone:** M1; retained through M4. **Status:** NOT_RUN.\
**Environment:** owned process/provider fixture.\
**Requirements:** FR-012, FR-013, FR-014, NFR-005, NFR-009.\
**Success criteria:** SC-003.\
**Tasks:** T021, T023, T033, T039, T040, T099, T100.

**Given:** Persisted runs with known owned handles, an external resource and an uncertain in-flight command.

**Procedure:** Restart or kill/relaunch the control service at lifecycle boundaries, then reconcile. Repeat native backend stop/restart on both OS families, including held files and stale process identities/handles.

**Expected:** Runs are reconciled against recorded ownership and provider facts. Unknown outcomes remain unknown pending reconciliation; no blind respawn, process-name kill or port-based ownership inference occurs; duplicate starts remain prevented across restart. Windows handle/locking differences and Linux process semantics are covered explicitly; only validated ownership permits mutation after restart.

### AC-010 — Bounded event and log delivery

**Milestone:** M1; retained through M4. **Status:** NOT_RUN.\
**Environment:** owned high-volume event fixture.\
**Requirements:** FR-017, FR-021, FR-022, NFR-008.\
**Success criteria:** SC-008.\
**Tasks:** T025, T026, T028, T029, T030, T033, T038, T040, T096, T099, T100.

**Given:** A fast producer, slow/disconnected browser and finite retention/queue budgets.

**Procedure:** Flood logs and signals, reconnect after retention expires and compare persisted evidence with UI delivery.

**Expected:** Backend memory and queues remain bounded; rendering/transport sampling never silently alters retained evidence. Dropped or unavailable UI records are labelled with gaps/cursors; control and cancellation remain responsive within declared budgets.

### AC-011 — Signals, clocks and factual diagnosis

**Milestone:** M1; retained through M4. **Status:** NOT_RUN.\
**Environment:** owned evidence with clock uncertainty and missing intervals.\
**Requirements:** FR-017, FR-018, FR-019, FR-020, FR-022, NFR-011.\
**Success criteria:** SC-008.\
**Tasks:** T028, T029, T030, T031, T032, T033, T038, T040, T096, T099, T100.

**Given:** Observed events, diagnostic hypotheses, live-only process liveness, differing time domains and incomplete records.

**Procedure:** Select a component, flow and time interval; align signals/logs; inspect the explanation panel.

**Expected:** The view traces each fact to evidence and marks hypotheses/unknowns. Unsynchronized times are not combined into false causal order or latency. Liveness is distinct from functional health; absence of traffic alone is not automatically failure.

### AC-012 — First-time prepared-example study

**Milestone:** M1; retained through M4. **Status:** NOT_RUN.\
**Environment:** prepared workstation; representative novice users.\
**Requirements:** FR-002, FR-005, NFR-012.\
**Success criteria:** SC-001.\
**Tasks:** T036, T037, T040, T100.

**Given:** The prepared environment and participants who have not previously operated X-Verse; technical experiment literacy may be present.

**Procedure:** Use the scripted study in spec.md: open the prepared example, change one permitted parameter, run it, locate its result and identify the injected supported failure. Record assistance, time, errors and completion.

**Expected:** Apply the specified success threshold without coaching or excluding failed participants. Record setup separately, anonymize participant records and disclose sample size. No simulated user result or developer self-test substitutes for this case.

### AC-013 — Graph/source synchronization and layout isolation

**Milestone:** M2; retained through M4. **Status:** NOT_RUN.\
**Environment:** owned project fixtures; browser automation.\
**Requirements:** FR-001, FR-023, FR-024, FR-025, FR-027, NFR-002, NFR-009.\
**Success criteria:** SC-002.\
**Tasks:** T041, T042, T043, T044, T048, T068, T069, T099, T100.

**Given:** A valid project with stable IDs, multiple subsystems and a saved layout sidecar.

**Procedure:** Edit through graph, inspector and XDL source; move/recolour/group nodes; save/reopen; compare platform semantic/plan identities. Round-trip portable projects from Linux to Windows and back with supported source names and line endings.

**Expected:** Semantic edits agree across views and compiler; presentation-only edits leave executable semantics unchanged. Identity survives labels and layout. Source extensions are not dropped; invalid source keeps a clear draft state and cannot execute. Host-specific paths remain outside portable semantic identity and valid project content survives both directions.

### AC-014 — Undo, autosave and external-edit conflicts

**Milestone:** M2; retained through M4. **Status:** NOT_RUN.\
**Environment:** owned filesystem/projects; browser automation.\
**Requirements:** FR-026, FR-028, NFR-009.\
**Success criteria:** SC-002.\
**Tasks:** T045, T046, T047, T048, T068, T069, T099, T100.

**Given:** Two editors or sessions and a project with unsaved valid/invalid changes.

**Procedure:** Undo/redo add-connect-delete operations, interrupt autosave, change files externally and save with a stale revision. Exercise each platform's file-locking, atomic replacement and case/name collision rules.

**Expected:** Operations preserve reference integrity; atomic saves do not corrupt the last saved revision; stale writes return a conflict and preserve both recoverable versions. Autosave never rewrites the active run snapshot. An unsupported portable name or conflicting path is reported before data loss; neither platform silently aliases distinct project resources.

### AC-015 — Catalog and role-realization-placement wizard

**Milestone:** M2; retained through M4. **Status:** NOT_RUN.\
**Environment:** owned catalog/provider/profile fixtures.\
**Requirements:** FR-029, FR-030, FR-031, FR-032, FR-033, NFR-004.\
**Success criteria:** Supports the stated requirements directly.\
**Tasks:** T049, T050, T051, T052, T068, T069, T100.

**Given:** Components with independent roles, realizations, requirements, versions and provider capabilities.

**Procedure:** Instantiate a template, import an existing implementation and register a logical device. Change role filter, realization and placement.

**Expected:** The wizard produces existing XDL kinds with stable component/device identities. It distinguishes reusable definition from instance, artifact requirement from chosen artifact, physical asset from logical device, and definition creation from firmware/build completion.

### AC-016 — Typed communication and feedback loops

**Milestone:** M2; retained through M4. **Status:** NOT_RUN.\
**Environment:** owned interface and connection fixtures.\
**Requirements:** FR-034, FR-035, FR-038.\
**Success criteria:** Supports the stated requirements directly.\
**Tasks:** T053, T054, T055, T068, T069, T100.

**Given:** Compatible and incompatible directions, types, units, versions, coordinate frames, rates and clock assumptions; a valid feedback loop.

**Procedure:** Connect ports, inspect suggested compatible targets, request an explicit supported conversion and create valid/invalid feedback configurations.

**Expected:** Each accepted edge has defined semantics; incompatible links and unavailable converters are diagnosed. Valid control feedback is admitted under its time/causality contract; cycles are not universally prohibited and unsupported causal assumptions are not inferred.

### AC-017 — Connection kinds and X-COM evidence scope

**Milestone:** M2; retained through M4. **Status:** NOT_RUN.\
**Environment:** owned communication/model-coupling fixtures.\
**Requirements:** FR-036, FR-037.\
**Success criteria:** Supports the stated requirements directly.\
**Tasks:** T053, T055, T056, T068, T069, T100.

**Given:** Declared flows, resolved provider routes, observed traffic, deployment and traceability relationships, plus an unavailable physical-model coupling provider.

**Procedure:** Switch perspectives; inspect source/provider/evidence labels; attempt the unsupported coupling.

**Expected:** Declared/resolved/observed states remain distinct. Lite evidence is identified as Lite, not activated native X-COM. Communication, physical coupling, placement and traceability cannot be connected interchangeably; unsupported physical solver semantics block execution.

### AC-018 — Deployment variants and capability-aware controls

**Milestone:** M2; retained through M4. **Status:** NOT_RUN.\
**Environment:** owned multi-deployment fixtures.\
**Requirements:** FR-016, FR-039, FR-040, FR-041, FR-042, NFR-004.\
**Success criteria:** Supports the stated requirements directly.\
**Tasks:** T024, T057, T058, T059, T068, T069, T100.

**Given:** One logical system with compatible software/emulated/physical declarations and varied operation capabilities.

**Procedure:** Change selected realization and placement, alter resource/time/network bindings, compare variants and invoke a disabled operation through the API.

**Expected:** Logical identity/topology survives compatible rebinding; target/artifact/resource constraints and clock mappings are revalidated. Pause, step, reset, live tune and faults require explicit backend capability; a preserved identity does not assert behavioural equivalence.

### AC-019 — Profiles compose without domain branches

**Milestone:** M2; retained through M4. **Status:** NOT_RUN.\
**Environment:** owned profile packages with conflicting and compatible namespaces.\
**Requirements:** FR-043, FR-044, FR-045, FR-047, NFR-001, NFR-009.\
**Success criteria:** Supports the stated requirements directly.\
**Tasks:** T013, T060, T061, T062, T063, T068, T069, T099, T100.

**Given:** Automotive and process-control profiles plus a mixed-domain project and incompatible profile revisions.

**Procedure:** Load compatible profiles together; inspect vocabulary/forms; introduce namespace/schema conflicts and unresolved bindings.

**Expected:** Compatible profiles share core objects and workflows; profile content supplies vocabulary/validation/presentation without executable hooks. Conflicts and unknown semantics are surfaced and blocked. No industry switch replaces core runtime or identity rules.

### AC-020 — Two-domain executable blueprint proof

**Milestone:** M2; retained through M4. **Status:** NOT_RUN.\
**Environment:** admitted vehicle-loop and process-control model providers.\
**Requirements:** FR-046, FR-047, NFR-001.\
**Success criteria:** SC-004.\
**Tasks:** T013, T064, T065, T066, T069, T099, T100.

**Given:** Two independently meaningful blueprints: a vehicle loop and a small process-control system, each with declared model fidelity and expected observations.

**Procedure:** Compose/edit/save/reopen/execute both through the same Studio workflow, collect evidence and inspect core changes needed for the second.

**Expected:** Both satisfy their own declared observations; the second is not a renamed vehicle diagram. Domain content lives in profiles/blueprints/providers; the core requires no domain conditionals. Fixture-only evidence is labelled and does not claim either live provider works.

### AC-021 — Physical inventory and asset binding

**Milestone:** M3; retained through M4. **Status:** NOT_RUN.\
**Environment:** one actual supported device/provider; owned inventory fixture.\
**Requirements:** FR-048.\
**Success criteria:** SC-005.\
**Tasks:** T070, T071, T072, T075, T079, T080, T081, T099, T100.

**Given:** A real asset with recorded identifier, supported interfaces and observable firmware/provider versions.

**Procedure:** Register a logical device, discover or enter its permitted external binding, probe supported metadata and bind it to a deployment.

**Expected:** Physical identity/availability is resolved before readiness; endpoint details stay out of logical IDs and public exports. Unsupported metadata remains unknown. Missing hardware leaves the real case not run/blocked, never passed by its fixture. The inventory reports the actual provider OS/architecture/driver support; a device supported only on one platform is not advertised as universally operable.

### AC-022 — Reservations and observation/stimulation separation

**Milestone:** M3; retained through M4. **Status:** NOT_RUN.\
**Environment:** actual supported asset; reservation fixture.\
**Requirements:** FR-049, FR-050.\
**Success criteria:** SC-005.\
**Tasks:** T070, T073, T074, T075, T079, T080, T081, T099, T100.

**Given:** Two competing clients, read-only access and explicitly authorized supported stimulation.

**Procedure:** Attempt concurrent exclusive reservations, unauthorized stimulation, stale-lease use and allowed observation; retry reservation/release commands.

**Expected:** Backend enforces exclusivity and capability/authority checks; no UI bypass grants stimulation. Lease expiry and uncertain release are visible; observation and actuation privileges are distinct and audit records identify actual operations.

### AC-023 — Hardware disconnect and cleanup boundaries

**Milestone:** M3; retained through M4. **Status:** NOT_RUN.\
**Environment:** actual supported asset with nonhazardous test setup.\
**Requirements:** FR-049, FR-050, FR-051.\
**Success criteria:** SC-005.\
**Tasks:** T070, T073, T074, T076, T077, T078, T079, T080, T081, T099, T100.

**Given:** A supported bounded operation and documented provider-specific stop/restore behaviour.

**Procedure:** Disconnect the asset or provider during run; fail a supported stop/restore action; reconnect and inspect reconciliation.

**Expected:** Studio stops issuing unsupported commands, preserves ownership/evidence and reports unknown physical state where appropriate. UI Stop does not claim a physical safe state without provider evidence. Recovery follows the explicit adapter contract.

### AC-024 — Virtual-to-physical substitution and time quality

**Milestone:** M3; retained through M4. **Status:** NOT_RUN.\
**Environment:** compatible virtual and real provider pair.\
**Requirements:** FR-040, FR-051, FR-052.\
**Success criteria:** SC-005.\
**Tasks:** T071, T076, T077, T078, T079, T080, T081, T099, T100.

**Given:** The same logical device and compatible interfaces with distinct clock/control/fidelity capabilities.

**Procedure:** Rebind the device, rerun the supported scenario, inspect unchanged logical connections and changed capabilities/time mappings.

**Expected:** Topology is retained where contracts agree; incompatible bindings are rejected. Physical pause/rewind/determinism are never assumed; measured synchronization quality/uncertainty and fidelity differences are visible in comparison. Physical acceptance identifies its host OS/driver; native Studio support on the other OS does not imply availability of this physical provider.

### AC-025 — Scenario, stimulus and supported fault schedules

**Milestone:** M4; retained through M4. **Status:** NOT_RUN.\
**Environment:** owned deterministic model/provider; permitted live fault subset.\
**Requirements:** FR-053, FR-054, FR-055, FR-057.\
**Success criteria:** SC-006.\
**Tasks:** T082, T083, T084, T088, T095, T099, T100.

**Given:** Scenario initial conditions, typed stimuli, time mappings, observation requirements and a supported/unsupported fault vocabulary.

**Procedure:** Author schedules with activation/recovery, invalid time references and conflicting operations; compile and execute the supported subset.

**Expected:** Only admitted semantics execute. Fault timing and recovery are recorded against their actual clocks; unsupported targets/operations fail preflight. Determinism is claimed only for the evidenced provider/configuration envelope.

### AC-026 — Bounded assertion evaluator and missing evidence

**Milestone:** M4; retained through M4. **Status:** NOT_RUN.\
**Environment:** owned evaluator fixtures; no arbitrary code execution.\
**Requirements:** FR-056, NFR-004.\
**Success criteria:** SC-006.\
**Tasks:** T085, T086, T087, T088, T095, T099, T100.

**Given:** Versioned typed predicates, valid/invalid units, gaps, missing inputs, unsynchronized clocks and adversarial expressions.

**Procedure:** Evaluate true/false/indeterminate examples, apply time windows, reject unknown operators and exercise resource limits.

**Expected:** The defined bounded language produces pass/fail/indeterminate as specified. Missing data never yields a pass; unit/time incompatibility is diagnosed. No eval, arbitrary imports, filesystem/network access or silent execution of opaque XDL strings occurs.

### AC-027 — Immutable runs and recorded live parameter changes

**Milestone:** M1; retained through M4. **Status:** NOT_RUN.\
**Environment:** owned snapshot and live-tune-capable fixtures.\
**Requirements:** FR-015, FR-016, FR-028.\
**Success criteria:** Supports the stated requirements directly.\
**Tasks:** T021, T022, T024, T027, T033, T040, T047, T095, T099, T100.

**Given:** A running snapshot and a separately editable project draft, with both mutable and immutable parameter declarations.

**Procedure:** Edit project/source/deployment during a run; request unsupported live changes; apply an explicitly supported live change.

**Expected:** The existing run retains exact inputs; edits form the next draft. Supported live changes record command, old/new values, time, authority and outcome; immutable/unsupported changes are rejected without side effects.

### AC-028 — Campaign bounds, cancellation and restart

**Milestone:** M4; retained through M4. **Status:** NOT_RUN.\
**Environment:** owned campaign runtime; admitted provider for live scope.\
**Requirements:** FR-058.\
**Success criteria:** SC-006.\
**Tasks:** T089, T090, T095, T099, T100.

**Given:** A finite parameter matrix, explicit seeds, budgets, hardware exclusivity and accepted per-run limits.

**Procedure:** Preview cardinality; exceed budgets; execute, cancel and restart/reconcile the campaign across a failed run.

**Expected:** Expansion is bounded before execution; each run has immutable inputs and identity. Cancellation/recovery do not duplicate runs or violate reservations. Failed/indeterminate runs remain in results; physical repetition is not advertised as deterministic replay.

### AC-029 — Baseline comparison, replay and exchange

**Milestone:** M4; retained through M4. **Status:** NOT_RUN.\
**Environment:** owned runs with matching/mismatching identities and tampered exports.\
**Requirements:** FR-059, FR-060, FR-061, FR-062, FR-063, NFR-004, NFR-009.\
**Success criteria:** SC-007.\
**Tasks:** T091, T092, T093, T094, T095, T098, T099, T100.

**Given:** Runs with different configurations, clocks, observations and integrity states; a portable project/evidence package.

**Procedure:** Compare baselines, replay observations, request a real rerun, export/import and tamper with referenced evidence. Export/import the supported portable package in both native Linux/Windows directions, test stale annotation revisions, and revalidate retention dry-run plans before apply.

**Expected:** Comparison exposes configuration and time differences. Replay only re-presents recorded data; rerun requires fresh admission. Export includes provenance and hashes, excludes secrets, reports missing/restricted artifacts and detects integrity problems without rewriting original evidence. A stale annotation or changed retention dependency is rejected; platform-local bindings cannot leak into or silently reinterpret a portable package.

### AC-030 — Performance and retention envelope

**Milestone:** M2; retained through M4. **Status:** NOT_RUN.\
**Environment:** recorded reference hardware; repeatable load fixtures.\
**Requirements:** NFR-007, NFR-008, NFR-003.\
**Success criteria:** SC-008.\
**Tasks:** T067, T069, T096, T099, T100.

**Given:** The exact reference environment, workload sizes, warm/cold conditions and thresholds defined by spec.md.

**Procedure:** Run declared canvas, API, streaming/backpressure and history workloads; record distributions, resource consumption, dropped-display counts and evidence retention. Execute the workload on both recorded native Linux and Windows reference environments and retain each result independently.

**Expected:** Apply every specified threshold to measured results; failures remain failures. Report capacity/provider limitations and test command/configuration hashes. Do not extrapolate fixture throughput to simulator or hardware capacity. Every platform meets its applicable threshold; aggregate averages cannot conceal a failed native-platform result.

### AC-031 — Keyboard access and accessible diagnostics

**Milestone:** M1; retained through M4. **Status:** NOT_RUN.\
**Environment:** supported browsers; keyboard and assistive-technology checks.\
**Requirements:** FR-027, NFR-006, NFR-003.\
**Success criteria:** SC-008.\
**Tasks:** T017, T038, T040, T043, T067, T069, T097, T099, T100.

**Given:** The model, forms, errors, operation controls, diagnostics and results views.

**Procedure:** Complete critical flows without a pointing device; inspect focus, labels, contrast, non-colour status, dynamic announcements and resizing at the specified viewports. Repeat the declared supported browser/accessibility matrix against native Linux and Windows backends.

**Expected:** Critical operations and validation findings remain usable through an accessible alternative to drag-only canvas interaction. Focus and error locations are meaningful; no essential state depends only on colour, hover or animation.

### AC-032 — Offline packaging, migration and release evidence

**Milestone:** M1; retained through M4. **Status:** NOT_RUN.\
**Environment:** clean recorded native Linux and native Windows hosts; supported browsers; owned reference provider; previous/current project fixtures.\
**Requirements:** NFR-003, NFR-004, NFR-009, NFR-010, NFR-012, FR-006, FR-008, NFR-005, NFR-006.\
**Success criteria:** SC-008.\
**Tasks:** T002, T009, T010, T036, T039, T040, T092, T098, T099, T100.

**Given:** A packaged candidate with pinned dependencies, documented install/start/backup/recovery steps and locally available admitted artifacts. There is one clean supported native Linux host and one clean supported native Windows host; neither Windows browser access to Linux nor WSL substitutes for the Windows host.

**Procedure:** Install/start in the documented offline envelope, migrate/restore projects, run compatibility/regression checks and audit the release manifest. On each OS install the package, start the native backend, open its browser UI, import/save/reopen XDL, validate, run/cancel the owned reference provider, inspect results, reconnect the browser, restart/reconcile the backend, and stop cleanly. Exercise documented update/recovery and portable exchange paths. Verify optional service-manager registration only if offered.

**Expected:** Core operation requires no cloud or AI service; absent dependencies produce actionable errors. Migrations preserve originals and identities. Evidence binds commands, versions, sanitized environment, exit status, hashes and limitations to the exact candidate; incomplete external lanes remain explicit. Both native core smoke lanes pass independently without undeclared Bash/WSL/VM/Docker/remote-Linux dependencies. Foreground or launcher-managed background operation is documented. Provider-specific live limitations remain visible and are not misreported as native runtime support.

## Release interpretation

M0 evidence establishes contracts and declared compatibility. M1 adds guided execution for its admitted runtime scope. M2 requires the independent two-domain demonstration and semantic/performance evidence. M3 requires an actual identified physical device and permitted operations. M4 requires the scenario/assertion/campaign/exchange behaviour and retained earlier obligations. A user-interface screenshot, parsed schema, fixture run or unexecuted test file cannot substitute for these distinct claims.

A blocker does not erase independent successful work. Report the exact supported release scope, pending task/case IDs and remaining dependency. Keep release acceptance separate from checking task boxes and from the application asserting that an experiment passed.

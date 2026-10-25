# Feature Specification: Industry-Agnostic X-Verse Studio

**Feature**: `001-industry-agnostic-studio`\
**Created**: 2026-10-25\
**Status**: Implementation specification; application implementation and acceptance are pending\
**Input**: Provide a friendly, model-based workspace to compose, configure, connect, execute, and inspect X-Verse systems across simulated and physical environments. ECU is an automotive specialization, not a platform concept.

## Product outcome and scope

X-Verse Studio lets a person who understands the experiment operate X-Verse without needing its internal command sequence. A system model connects design intent, realization choices, runtime operations, observations, and evidence. The product is industry agnostic: automotive, industrial automation, robotics, energy, and other vocabularies enter through compatible profiles, providers, and blueprints.

Studio is a web-based application: its user interface runs in a supported desktop browser, and its backend must install and run natively on both Linux and Windows. Native Windows operation must not silently require WSL, a Linux virtual machine, Docker, or a remote Linux backend. Individual simulators, device drivers, and runtime providers can have narrower OS support; Studio must expose those constraints separately from the application's own cross-platform support.

Studio edits and consumes the existing XDL resource families (`Component`, `System`, `Deployment`, `Scenario`, `Profile`). It does not introduce a competing executable model. “Element” is an approachable UI umbrella; persisted entities retain their precise XDL types. Role, realization, and placement are independent dimensions. A controller is a role; a software process, emulator, or physical device is a realization; a host or laboratory asset is placement.

The scope is a complete phased product plan through Studio 1.0. A milestone is accepted only for its demonstrated capability set. Draft specifications, mocks, fixture evidence, and live evidence have distinct labels. The specification does not claim that the current Lite baseline supplies every required API or provider.

| Milestone | Product increment | Required outcome |
|---|---|---|
| M0 | Foundation | Versioned integration contracts, pinned compatibility baseline, project ownership and persistence, and recorded native Linux and Windows validation environments. |
| M1 | Studio 0.1: guided operation | Install and operate native Studio on Linux and Windows; open a supported blueprint, inspect/edit permitted parameters, preflight, run/cancel, reconnect, and understand evidence, with provider support reported per environment. |
| M2 | Studio 0.2: visual composition | Compose systems, edit XDL coherently, choose deployments, validate connections, and demonstrate two industries through the shared core. |
| M3 | Studio 0.3: hybrid laboratory | Bind and operate one admitted physical-device provider, including reservation, explicit capabilities, and mixed-time observations. |
| M4 | Studio 1.0: experiment management | Author scenarios and bounded fault schedules, evaluate supported assertions, execute bounded campaigns, compare runs, and export traceable evidence. |

Beyond-1.0 work is roadmap material, not a substitute for the M0–M4 acceptance gates: distributed execution, native X-COM core integration, broad external-model import/export, AI assistance, real-time collaborative editing, a public plugin marketplace, and advanced physical-coupling solvers. The core must leave explicit extension boundaries for this work, without claiming it is implemented.

## User Scenarios & Testing

Each story is independently demonstrable using its declared prerequisites. P1 stories establish the guided vertical slice; P2 stories establish authoring and cross-industry use; P3 stories add admitted hardware and experiment management. Story priority does not waive dependencies or the evidence needed for a milestone claim.

### US1 — Open a project and complete a guided example (Priority: P1; M0/M1)

As a new user, I want to open a working example or an existing XDL project and understand its purpose before editing it.

**Independent test**: Use the packaged reference example in a prepared environment, without opening a terminal.

**Acceptance scenarios**:
1. **Given** a prepared installation and a packaged blueprint, **when** the user chooses “Explore an example,” **then** Studio identifies the system, expected observations, prerequisites, maturity, and available next action.
2. **Given** an existing supported XDL resource set, **when** it is imported, **then** the project lists its resources and validation results without executing referenced artifacts.
3. **Given** an unsupported profile extension, **when** its project is opened, **then** its content is preserved for inspection, the unresolved dependency is explained, and execution remains unavailable.
4. **Given** each recorded native Linux and Windows reference environment, **when** the user installs and starts Studio through its documented native path, **then** the browser workspace and backend operate without an undeclared WSL, container, virtual-machine, or remote-host prerequisite.

**Requirements**: FR-001–FR-005.

### US2 — Determine what the environment can actually run (Priority: P1; M0/M1)

As an operator, I want an actionable preflight that distinguishes model validity from executable readiness.

**Independent test**: Run preflight against a fixture adapter with supported, missing, stale, and incompatible capabilities; use the admitted Lite adapter for the live claim.

**Acceptance scenarios**:
1. **Given** a valid model and a missing required artifact, **when** preflight runs, **then** validation remains valid while readiness is blocked with the affected element and remediation.
2. **Given** a scenario exceeding an advertised runtime limit, **when** it is checked, **then** Studio rejects execution and explains the limit before creating a live run.
3. **Given** changed capabilities after preflight, **when** Start is requested, **then** the backend rechecks the relevant admission facts and rejects a stale plan rather than relying on an earlier green badge.
4. **Given** a working native Windows Studio installation and a provider available only on Linux, **when** the user selects that provider, **then** Studio explains the provider-specific OS limitation and available configured alternatives without claiming that the provider ran or that Windows Studio itself is unsupported.

**Requirements**: FR-006–FR-010.

### US3 — Start, stop, and reconnect to an owned experiment (Priority: P1; M1)

As an operator, I want reliable run control that survives UI refresh and does not leave ambiguous ownership.

**Independent test**: Execute lifecycle conformance cases with an owned fixture, then exercise the admitted Lite workflow with pinned inputs.

**Acceptance scenarios**:
1. **Given** an admitted plan, **when** Start is retried with the same idempotency key and request identity, **then** exactly one run is created and the same run ID is returned.
2. **Given** a running experiment, **when** the browser disconnects and reconnects, **then** the backend retains ownership and returns current state and the available event continuation without starting another experiment.
3. **Given** a stop request whose cleanup fails, **when** termination is reported, **then** the run exposes the cleanup failure and unresolved owned resources instead of reporting successful cleanup.
4. **Given** a provider without pause capability, **when** a user or API client requests pause, **then** the backend rejects it and the UI explains why the operation is unavailable.

**Requirements**: FR-011–FR-016.

### US4 — Understand a run and diagnose a failure (Priority: P1; M1)

As an operator, I want logs, observations, and explanations tied to the component or connection that I selected.

**Independent test**: Load an evidence fixture containing normal, missing, stale, conflicting, and failed observations; repeat an admitted live failure case where available.

**Acceptance scenarios**:
1. **Given** a selected element and run, **when** the user opens Results, **then** its available logs, events, signals, and associated connections are navigable by time and source.
2. **Given** evidence of a process exit but no confirmed cause, **when** the explanation is shown, **then** it identifies the observed exit, its affected elements, and an investigation step while leaving the cause unconfirmed.
3. **Given** a telemetry gap or incompatible clock mapping, **when** signals are correlated, **then** the gap or uncertainty is visible and no false continuous line or precise latency is inferred.

**Requirements**: FR-017–FR-022.

### US5 — Edit the system graph and XDL coherently (Priority: P2; M2)

As an author, I want visual and source editing to describe the same executable system.

**Independent test**: Import, edit, save, reload, and compile a corpus of supported XDL resources using both Studio and the pinned platform tools.

**Acceptance scenarios**:
1. **Given** supported XDL, **when** the author changes only layout and reloads the project, **then** the platform semantic digest remains unchanged and the layout is retained.
2. **Given** an inspector edit, **when** it is saved, **then** the XDL source and graph reflect the same value and the pinned platform validator supplies the authoritative diagnostics.
3. **Given** a conflicting external edit, **when** Studio attempts to save an older revision, **then** the conflict is detected and neither version is silently overwritten.
4. **Given** unsupported extension content, **when** an otherwise supported field is edited, **then** that extension is preserved or the edit is refused explicitly; it is never silently dropped.

**Requirements**: FR-023–FR-028.

### US6 — Compose a system from reusable elements (Priority: P2; M2)

As an author, I want to find compatible capabilities and instantiate them with understandable configuration.

**Independent test**: Create a system with a controller, device, model, stimulus, and observer from local catalog entries.

**Acceptance scenarios**:
1. **Given** a catalog component, **when** the author adds it, **then** Studio creates a distinct instance with stable identity while retaining the reusable definition reference.
2. **Given** a sensor role, **when** realization choices are displayed, **then** supported simulated, software, emulated, or physical choices come from compatible providers rather than being inferred from the role.
3. **Given** an imported implementation artifact, **when** it is registered, **then** Studio records provenance and compatibility information without executing, building, flashing, or declaring equivalence automatically.

**Requirements**: FR-029–FR-033.

### US7 — Connect interfaces with explicit semantics (Priority: P2; M2)

As an author, I want connections that express valid interactions and make their implementation visible.

**Independent test**: Exercise compatible/incompatible ports, unit mismatches, explicit converters, clock mismatches, valid feedback, and unavailable transport cases.

**Acceptance scenarios**:
1. **Given** incompatible endpoint contracts, **when** a connection is proposed, **then** Studio explains the mismatch and offers only declared compatible conversion options.
2. **Given** a valid feedback loop with supported time semantics, **when** it is connected, **then** the graph is not rejected merely because it contains a cycle.
3. **Given** a declared flow and available observations, **when** the connection is inspected, **then** declared topology, resolved route, and observed behaviour are distinguishable.
4. **Given** a physical-model coupling with no admitted coupling provider, **when** execution is requested, **then** Studio reports an unsupported coupling rather than reinterpreting it as an ordinary X-COM message.

**Requirements**: FR-034–FR-038.

### US8 — Choose deployments without rebuilding the system (Priority: P2; M2)

As an author, I want alternative realizations and placements for a stable logical system.

**Independent test**: Create two compatible software/model deployments and one unresolved physical binding for the same logical system.

**Acceptance scenarios**:
1. **Given** compatible realization candidates, **when** the author changes deployment, **then** logical identities and valid interfaces remain stable while bindings and readiness are recomputed.
2. **Given** an incompatible candidate, **when** the author selects it, **then** affected contracts are identified and execution is blocked until explicitly resolved.
3. **Given** layered parameter values, **when** the effective configuration is inspected, **then** each value's source and override are visible using the platform's declared precedence rules.

**Requirements**: FR-039–FR-042.

### US9 — Use multiple industries through the shared core (Priority: P2; M2)

As an author, I want familiar domain terminology while retaining a common system workflow and interoperable elements.

**Independent test**: Complete the same author/validate/deploy/run/inspect workflow with an automotive blueprint and a simple process-control blueprint using admitted implementations.

**Acceptance scenarios**:
1. **Given** the two blueprints, **when** both are exercised, **then** the shared frontend and backend need no industry-specific core branch to handle their roles, fields, or lifecycle.
2. **Given** compatible namespaced profiles, **when** both are selected, **then** their validated extensions can coexist without redefining core concepts.
3. **Given** conflicting profile definitions or an unsupported version, **when** the project is validated, **then** the conflict or unresolved dependency is explicit and affected execution is blocked.

**Requirements**: FR-043–FR-047.

### US10 — Bind and operate a physical device (Priority: P3; M3)

As a lab operator, I want to bind a logical device to an identified physical asset with supported controls and visible ownership.

**Independent test**: Use one nominated physical device and admitted provider, with recorded environment and operator authorization; fixture tests alone do not satisfy the physical claim.

**Acceptance scenarios**:
1. **Given** a resolvable physical asset, **when** it is bound, **then** its identity, capabilities, relevant firmware/artifact information, and readiness are recorded separately from the logical device.
2. **Given** an exclusively reserved resource, **when** a second run tries to claim it, **then** the request is rejected before stimulation begins.
3. **Given** observe-only access, **when** stimulation or a destructive device action is requested, **then** it is rejected unless the corresponding declared capability and current authorization exist.
4. **Given** a lost device connection, **when** the run's declared recovery/stop policy is applied, **then** Studio records the actions and uncertain physical state rather than assuming the device stopped.

**Requirements**: FR-048–FR-052.

### US11 — Design and assess an experiment (Priority: P3; M4)

As an experiment author, I want typed stimuli, supported faults, observations, and evaluation rules tied to the system.

**Independent test**: Author and execute a bounded reference scenario with one supported fault and assertions covering pass, fail, and indeterminate outcomes.

**Acceptance scenarios**:
1. **Given** a system and deployment, **when** a scenario is authored, **then** schedule, target references, clock domains, parameters, and declared limits are validated before execution.
2. **Given** an unsupported fault or target, **when** it is scheduled, **then** Studio rejects execution and identifies the missing capability.
3. **Given** an assertion with missing required observations, **when** it is evaluated, **then** its result is indeterminate with the missing-input reason, not passed.
4. **Given** an opaque XDL expression without a compatible evaluator, **when** it is imported, **then** Studio preserves its declaration but does not invent executable semantics.

**Requirements**: FR-053–FR-057.

### US12 — Compare, repeat, and share experiment evidence (Priority: P3; M4)

As an experiment author, I want bounded campaigns and reviewable comparisons tied to exact inputs.

**Independent test**: Execute a small parameter campaign, interrupt/resume according to policy, compare compatible runs, and export/reimport a sanitized project/evidence bundle.

**Acceptance scenarios**:
1. **Given** a campaign matrix and budget, **when** execution starts, **then** each child run has an immutable input snapshot and the scheduler respects declared concurrency and resource limits.
2. **Given** two runs, **when** they are compared, **then** model, artifact, parameter, capability, and clock differences are available before interpreting result differences.
3. **Given** a run with incomplete or invalid evidence, **when** a report is exported, **then** its evidence status and missing observations remain visible.
4. **Given** a bundle containing a reference to an unavailable artifact, **when** it is imported elsewhere, **then** Studio reports the gap without executing or silently retrieving that artifact.

**Requirements**: FR-058–FR-063.

## Requirements

“SHALL” identifies a release obligation in its assigned milestone. Later milestones retain earlier obligations. “Supported” means advertised by the selected, version-compatible adapter/provider and admitted for the requested operation; it is not inferred from a label, mock, or catalog entry. Acceptance requires both frontend behaviour and backend enforcement where applicable.

### Functional requirements

#### US1 — Projects and onboarding

- **FR-001** **[M0]** Studio SHALL use the platform's five XDL resource families as the authoritative executable description and retain stable resource/element references across its model, connections, deployment, experiment, and results views.
- **FR-002** **[M1]** Studio SHALL provide project creation, opening, recent-project navigation, a curated example path, and guided prerequisites that identify what a selected blueprint demonstrates and what remains unavailable.
- **FR-003** **[M1]** Studio SHALL import supported local XDL resources, resolve their explicitly supplied dependencies, and return authoritative platform diagnostics without executing referenced code or accessing undeclared remote resources.
- **FR-004** **[M1]** Studio SHALL preserve unsupported profile/extension source content for inspection, identify it as unresolved, and prevent affected execution; no import or save path may silently discard it.
- **FR-005** **[M1]** Studio SHALL expose guided parameter forms with descriptions, type, units or categorical domain, default/source, constraints, and actionable errors, while allowing an advanced read-only XDL view before source authoring is delivered in M2.

#### US2 — Capabilities and preflight

- **FR-006** **[M0]** Studio SHALL define and negotiate a versioned runtime/provider capability contract covering operation support, applicable targets, host/provider OS and architecture compatibility, runtime limits, clock behaviour, evidence scope, version identity, and declared maturity; provider OS support SHALL be represented separately from Studio application OS support.
- **FR-007** **[M0]** Studio SHALL use a versioned backend integration boundary for validation, compilation, admission, lifecycle requests, state, and evidence; browser clients SHALL NOT invoke private platform classes or arbitrary host commands.
- **FR-008** **[M1]** Studio SHALL present separate preflight results for Studio/backend availability, provider/driver OS and architecture compatibility, model validity, artifact availability, capability compatibility, target readiness, resource/ownership availability, clock mappings, and execution authority; an unavailable provider SHALL yield an actionable limitation without being reported as a supported live integration.
- **FR-009** **[M1]** Studio SHALL enforce advertised unit, duration, resource, concurrency, collection, and other applicable limits before execution, and identify unknown limits that prevent reliable admission rather than substituting guessed defaults.
- **FR-010** **[M1]** Studio SHALL bind an execution-plan preview to its input identity and revalidate mutable admission facts immediately before Start, rejecting stale or changed dependencies with actionable diagnostics.

#### US3 — Lifecycle ownership

- **FR-011** **[M1]** Studio SHALL submit only explicitly supported, admitted workflows through the runtime adapter and return a persistent run identifier, plan identity, ownership context, and lifecycle status.
- **FR-012** **[M1]** Studio SHALL make lifecycle mutations idempotent for a scoped request key and request fingerprint: identical retries return the original result, while reusing the key for a different request is rejected.
- **FR-013** **[M1]** Studio SHALL retain backend run ownership across browser disconnection, support cursor-based event resumption and state reconciliation, and default to continuing an admitted run during UI disconnection unless its recorded run policy specifies otherwise.
- **FR-014** **[M1]** Studio SHALL expose stop/cancel progress, terminal outcome, cleanup outcome, and unresolved owned resources separately; cleanup operations SHALL use verified ownership handles and SHALL NOT target unrelated resources by guessed name or port.
- **FR-015** **[M1]** Studio SHALL capture an immutable run snapshot before execution, including XDL/plan identities, selected deployment, artifact/provider/runtime identities, parameters, time mappings, seed where applicable, observer configuration, and admitted limits; subsequent project edits SHALL create a separate draft.
- **FR-016** **[M1]** Studio SHALL enable pause, step, reset, restart, live parameter mutation, and other optional controls only when supported and admitted; the backend SHALL reject unsupported requests and record any permitted live mutation in the run evidence.

#### US4 — Observation and diagnosis

- **FR-017** **[M1]** Studio SHALL correlate available logs, events, signals, and flow observations with stable model elements and run IDs, supporting selection, source/severity/time filtering, and navigation between evidence and the relevant model object.
- **FR-018** **[M1]** Studio SHALL retain source clock domains, timestamp provenance, mapping uncertainty, and data-quality states in displayed observations; missing, stale, conflicting, or unavailable data SHALL be distinguishable from a measured zero or false value.
- **FR-019** **[M1]** Studio SHALL provide evidence-linked diagnostic explanations that distinguish observed facts, inferred consequences, hypotheses, and unknown causes, with a concrete next action when one is supported by the diagnostic contract.
- **FR-020** **[M1]** Studio SHALL separately report model validity, target readiness, process liveness, observed communication/data availability, experiment outcome, and evidence completeness/integrity; none SHALL be promoted to a stronger claim without supporting evidence.
- **FR-021** **[M1]** Studio SHALL bound UI event buffering and signal rendering, report omitted or unavailable intervals explicitly, and resume from a declared cursor or require a resynchronization when retention no longer covers that cursor.
- **FR-022** **[M1]** Studio SHALL consume only evidence and log streams exposed by the admitted observation contract, preserving integrity/read limitations and redaction rules; private provider streams SHALL NOT be collected through an undocumented bypass.

#### US5 — Model authoring and persistence

- **FR-023** **[M2]** Studio SHALL support graphical and XDL source editing through one authoritative model service, with source locations for diagnostics and equivalent semantic output for equivalent edits.
- **FR-024** **[M2]** Studio SHALL store positions, view state, collapsed groups, and other presentation-only data separately from executable XDL content; presentation-only changes SHALL preserve platform resource/input semantic digests.
- **FR-025** **[M2]** Studio SHALL round-trip the supported XDL corpus without unintended semantic change, preserve untouched unknown extension content or refuse the operation, and disclose formatting/comment normalization when exact source preservation is unavailable.
- **FR-026** **[M2]** Studio SHALL provide undo/redo, explicit save state, bounded autosave/recovery, and revision-checked writes that surface external-edit conflicts instead of silently overwriting another revision.
- **FR-027** **[M2]** Studio SHALL provide subsystem navigation, grouping, named ports, selection, search, zoom, automatic layout, and a keyboard-operable structured alternative to graph-only editing; visual grouping SHALL NOT invent unsupported executable containment semantics.
- **FR-028** **[M2]** Studio SHALL identify the draft revision and selected run snapshot in every combined authoring/runtime view so changes to a draft cannot be mistaken for changes to the running system.

#### US6 — Catalog and element creation

- **FR-029** **[M2]** Studio SHALL provide a local catalog searchable/filterable by capability, industry/profile, interface compatibility, realization support, version, and maturity, with provenance, requirements, and limitations for each entry.
- **FR-030** **[M2]** Studio SHALL instantiate reusable component definitions with distinct stable instance identities and explicit references, exposing role, realization, and placement as separate choices rather than inferring one from another.
- **FR-031** **[M2]** Studio SHALL support registering implementation artifacts and their immutable identities, requirements, provenance, and compatible providers without automatically executing, compiling, flashing, or granting them authority.
- **FR-032** **[M2]** Studio SHALL support creating and editing logical devices, model references, sensors, actuators, services/controllers, gateways, stimuli, and observers through the applicable XDL/profile semantics; industry labels SHALL remain profile presentation rather than new hard-coded core types.
- **FR-033** **[M2]** Studio SHALL expose configuration schemas and forms for admitted catalog/provider entries with defaults, typed constraints, units, documentation, and supported lifecycle operations; invalid or unavailable entry versions SHALL remain inspectable but unexecutable.

#### US7 — Connections

- **FR-034** **[M2]** Studio SHALL validate logical connections against endpoint direction, interface/schema/version, units and declared semantics, multiplicity, relevant rate/QoS assumptions, time mappings, and compatible realization/provider capabilities.
- **FR-035** **[M2]** Studio SHALL require explicit, inspectable mappings for converters or bridges, including limitations; it SHALL NOT silently change units, discard fields, fabricate a protocol bridge, or infer unsupported semantics.
- **FR-036** **[M2]** Studio SHALL expose declared flows, resolved routes/providers, and observed communication as distinct projections, with each observation's source, scope, freshness, and limitations visible.
- **FR-037** **[M2]** Studio SHALL distinguish data/service flows, physical-model couplings, deployment relationships, and traceability links; unsupported coupling semantics SHALL block affected execution, and X-COM communication SHALL NOT be presented as a general physical solver.
- **FR-038** **[M2]** Studio SHALL allow feedback cycles when their declared timing/causality contracts are supported, diagnose invalid cycles according to those contracts, and avoid treating either graph acyclicity or the presence of a drawn edge as proof of executable correctness.

#### US8 — Deployment

- **FR-039** **[M2]** Studio SHALL author multiple named deployment variants for a logical system, binding artifacts, targets, resources, networks, and time mappings while preserving logical identities.
- **FR-040** **[M2]** Studio SHALL check compatibility when changing realization, preserve compatible logical links, and identify incompatible interfaces/requirements; logical substitutability SHALL NOT imply unverified behavioural equivalence or fidelity.
- **FR-041** **[M2]** Studio SHALL show effective parameter values and their source/override chain using authoritative platform/profile precedence, and reject ambiguity where no precedence is defined.
- **FR-042** **[M2]** Studio SHALL separate portable deployment intent from environment-specific addresses, asset handles, and secret references, and report unresolved bindings before admitting execution.

#### US9 — Domain extension and cross-industry validation

- **FR-043** **[M2]** Studio SHALL treat profiles, providers, and blueprints as distinct extension responsibilities: profiles define semantics/presentation; providers implement integration; blueprints compose reusable systems and experiments.
- **FR-044** **[M2]** Studio SHALL admit profile versions and namespaces explicitly, permit compatible mixed-profile systems, and reject collisions or attempts to redefine core identity, ownership, validation, or realization semantics.
- **FR-045** **[M2]** Studio SHALL let compatible profiles customize terminology, catalog categories, forms, icons, and documentation while preserving the shared create/model/connect/deploy/experiment/results workflow.
- **FR-046** **[M2]** Studio SHALL demonstrate the same author/validate/deploy/run/inspect workflow with an automotive blueprint and an independent simple process-control blueprint, using admitted providers and without industry-specific conditional logic in the shared core.
- **FR-047** **[M2]** Studio SHALL preserve declared evidence maturity and limitations for every blueprint, model, and provider, clearly separating fixture demonstrations, supported live integrations, unresolved targets, and proposed future capabilities.

#### US10 — Physical integration

- **FR-048** **[M3]** Studio SHALL register and bind a logical device to an explicitly identified physical asset, recording available identity, firmware/artifact revision, interfaces, capability/permission scope, and readiness evidence; unresolved identity SHALL prevent affected active operation.
- **FR-049** **[M3]** Studio SHALL acquire, renew, release, and reconcile exclusive reservations where required by the physical provider, rejecting conflicting claims before stimulation and reporting uncertain ownership after interruption.
- **FR-050** **[M3]** Studio SHALL distinguish observe-only access from active stimulation and separately capability-gated destructive actions; no generic physical-device workflow SHALL silently imply permission to flash firmware, reset hardware, or change a production asset.
- **FR-051** **[M3]** Studio SHALL record physical/simulation clock relationships, supported synchronization quality, connection loss, and declared stop/recovery policy, exposing uncertain physical state when cleanup or device acknowledgment is unavailable.
- **FR-052** **[M3]** Studio SHALL demonstrate at least one admitted physical-device provider and a compatible virtual-to-physical realization change without recreating the logical topology; fixture success alone SHALL NOT satisfy this requirement.

#### US11 — Scenario authoring and assessment

- **FR-053** **[M4]** Studio SHALL author scenarios with initial conditions, typed stimuli, selected deployment, bounded duration, parameter sets, dependencies, observers, and time-domain interpretation through a form/timeline and corresponding XDL.
- **FR-054** **[M4]** Studio SHALL author activation and recovery schedules only for supported fault/target combinations, enforce declared authority and resource/time limits, and record intended versus observed fault effects separately.
- **FR-055** **[M4]** Studio SHALL expose observation configuration including source, sampling/trigger intent, retention, units, intrusiveness, and resource cost where declared, validating it against the selected provider before a run.
- **FR-056** **[M4]** Studio SHALL evaluate only assertions with a compatible versioned evaluator and defined typed/temporal semantics, producing pass, fail, or indeterminate with input provenance, clock assumptions, and reasons; opaque imported expressions SHALL remain unevaluated until such an evaluator exists.
- **FR-057** **[M4]** Studio SHALL show scenario intent, actual events, fault markers, measurements, and assertion outcomes on a correlated timeline while preserving gaps, timing uncertainty, and unsupported observations.

#### US12 — Campaigns, comparison, and exchange

- **FR-058** **[M4]** Studio SHALL define bounded parameter/seed campaigns with an explicit run matrix, budget, resource/concurrency limits, stop policy, and immutable child-run snapshots; duplicate scheduling SHALL be prevented during retries or recovery.
- **FR-059** **[M4]** Studio SHALL compare runs with model, deployment, parameter, artifact, capability, and clock differences visible alongside results, and prevent incompatible quantities or incomplete evidence from being presented as a valid like-for-like comparison.
- **FR-060** **[M4]** Studio SHALL distinguish replaying recorded observations from rerunning an experiment, declare reproducibility limits, and avoid promising deterministic behaviour for unsupported or physical realizations.
- **FR-061** **[M4]** Studio SHALL export/import project bundles and export evidence/report packages with a manifest of exact identities, dependency availability, schema versions, provenance, integrity status, limitations, and selected sanitized content; imports SHALL NOT auto-execute or silently fetch dependencies.
- **FR-062** **[M4]** Studio SHALL associate model elements, scenarios, assertions, and run evidence with optional external requirement/test references, preserving their referenced revision and claim status without treating a link as proof that the referenced requirement passed.
- **FR-063** **[M4]** Studio SHALL preserve historical evidence as read-only, keep user annotations and derived reports separate, and provide explicit retention/deletion operations that identify dependencies and never silently rewrite a prior run's evidence.

### Non-functional requirements

The performance profile below is a target for isolated Studio fixtures, not a claim about simulator performance or an admitted live system's scale. M0 records reproducible native Linux and Windows reference environments, each with at least 4 CPU cores, 8 GiB RAM, local SSD, a supported desktop browser, and exact distribution/edition/release, architecture, browser, and runtime versions. The support matrix names the tested OS and browser versions; it does not imply every Linux distribution or Windows release is supported. The exact machine identities are retained with results. External simulator/provider load is measured separately and does not waive correctness. Application conformance is tested with an owned cross-platform reference provider; live provider compatibility requires separate evidence for each claimed host environment.

- **NFR-001** **[M0 onward]** Studio SHALL keep domain semantics in profiles/blueprints/providers and prevent reverse dependencies from shared core modules to industry packages, verified by an architecture-boundary check and the M2 two-industry demonstration.
- **NFR-002** **[M0 onward]** Studio SHALL reuse the pinned platform validator/compiler and document all cross-language/versioned boundaries; equivalent supported inputs SHALL produce equivalent platform semantic/plan identities through CLI and Studio.
- **NFR-003** **[M1 onward]** Studio SHALL deliver a browser-based UI and a backend that installs, starts, operates, and stops natively on both recorded Linux and Windows environments, without an undeclared WSL, Linux VM, Docker, or remote Linux prerequisite. Core workflows SHALL support offline operation after provisioning. The backend SHALL bind to local interfaces by default and reject untrusted origins and unauthorized mutation requests; remote multi-user exposure is outside the initial release envelope.
- **NFR-004** **[M1 onward]** Studio SHALL exclude credentials and private environment material from portable XDL, ordinary logs, and exported bundles; protect project-bound file operations against path traversal and symbolic-link escape; and treat imported artifacts and profile presentation content as untrusted data.
- **NFR-005** **[M1 onward]** Studio SHALL recover committed project/run metadata after a controlled backend restart and report uncertain live ownership for reconciliation before further mutations; it SHALL NOT blindly restart, duplicate, or kill a process whose ownership cannot be established.
- **NFR-006** **[M1 onward]** Studio SHALL support keyboard operation, visible focus, labelled controls, text alternatives for status colours, and a structured alternative to pointer-only graph actions; critical workflows SHALL be tested in the recorded supported browser matrix on both native Linux and Windows at 1024×768 and 1440×900 desktop viewports without inaccessible clipped actions.
- **NFR-007** **[M2 onward]** On the recorded reference fixture of 200 visible elements and 400 logical connections, selection and local inspector updates SHALL complete within 150 ms at p95, and project open/validation-result presentation within 3 s at p95, over 30 measured repetitions after one documented warm-up; provider/network execution is measured separately.
- **NFR-008** **[M1 onward]** On a local evidence fixture of 50,000 events, the first page of at most 200 filtered events SHALL display within 2 s at p95 over 30 repetitions; browser buffering SHALL be bounded and UI backpressure SHALL NOT block the runtime's authoritative evidence collection.
- **NFR-009** **[M0 onward]** Studio SHALL record protocol/schema and native OS/browser compatibility explicitly, reject unsupported incompatible versions, and test supported upgrade/migration paths with preserved source backups and visible failures rather than silent data loss. Portable projects SHALL survive Linux-to-Windows and Windows-to-Linux exchange; environment-specific bindings SHALL be revalidated. Filesystem and persistence tests SHALL cover spaces/non-ASCII names, platform path syntax, case differences, locking/replacement behaviour, and line endings without changing executable semantics.
- **NFR-010** **[M0 onward]** Studio SHALL maintain requirement-to-design/task/verification traceability, meaningful negative and failure-path coverage, exact dependency locks, and reproducible verification commands; a passing document/fixture check SHALL NOT be reported as a live integration result.
- **NFR-011** **[M1 onward]** Studio SHALL provide actionable diagnostics for unsupported capability, missing artifact, invalid model, stale plan, lost connection, failed cleanup, incompatible time mapping, and unavailable evidence, with machine-readable codes and human-readable explanations.
- **NFR-012** **[M1 onward]** Studio SHALL document native Linux and Windows installation, startup, shutdown, update, recovery, prepared-example operation, compatibility limits, project/evidence retention, and provider extension responsibilities, with OS-appropriate commands or launchers. Any optional WSL/container/remote provider path SHALL be labelled explicitly and SHALL NOT replace native Studio support. Its guided-example usability acceptance SHALL be measured with first-time users under SC-001.

## Key Entities

These are semantic responsibilities, not new substitutes for platform XDL types. API representation and persistence details are specified in `data-model.md` and `contracts/`.

| Entity | Ownership and relationships |
|---|---|
| Project | Studio workspace referencing authored XDL, presentation metadata, selected dependency versions, and local environment bindings; does not redefine executable semantics. |
| System / subsystem | Logical composition and boundary. Supported containment semantics follow XDL; additional visual groups remain presentation-only. |
| Component definition / instance | Reusable capability contract and a distinct occurrence of it in a system. |
| Device | Logical cyber-physical identity that can survive compatible simulated, virtual, physical, or hybrid realization. |
| Model | Declared behaviour/physics/structure/control representation with input/output contracts, fidelity, provenance, and limitations. |
| Interface / endpoint / flow | Interaction contract, owned interaction point, and logical transfer. Protocol/route realization remains explicit. |
| Deployment / target / resource | Binding of logical entities to artifacts, execution places/mechanisms, capacity, networks, and time mappings. |
| Profile / provider / blueprint | Semantic extension; executable integration; composed example/experiment. They have distinct ownership and admission contracts. |
| Scenario / fault / observer / metric | Experiment intent, perturbation, evidence collection, and evaluation semantics. |
| Run / immutable snapshot | One execution identity referencing exact authored/compiled inputs and an admitted lifecycle; UI session is not its owner. |
| Evidence / diagnostic / annotation | Authoritative recorded observations; evidence-linked explanations; separately stored user commentary. |
| Physical asset / reservation | Environment-specific device identity and exclusive ownership where required, independent of logical identity. |
| Campaign | Bounded orchestration of separately identified runs with explicit scheduling and recovery policy. |

## Edge Cases and Failure Semantics

- Missing or incompatible profile: retain authored content; mark unresolved; block affected execution. An unknown plugin is never downloaded or executed merely to open a project.
- Invalid source edit: retain an editable draft and diagnostics; do not corrupt the last valid saved project or the active run snapshot.
- External file edit/save race: fail the revision check and offer explicit comparison/resolution. A refreshed view is not permission to overwrite.
- Alias, symlink, or archive path escape: reject the import/file operation and leave files outside the project unchanged.
- Catalog entry has an artifact but no provider: allow inspection/authoring, expose the missing realization capability, and keep execution unavailable.
- Preflight succeeds but the target changes: re-admit immediately before Start; reject stale facts. Readiness is not a permanent grant.
- Two tabs issue Start: use request identity/idempotency and ownership rules. Independent intentional starts still obey resource constraints.
- Browser reconnect cursor is older than retained events: return a resynchronization indication and visible missing range; do not invent events.
- Backend restarts while a run is live: reconstruct committed state, reconcile admitted ownership, and report uncertainty until resolved. Never silently relaunch.
- Provider exits during startup or cleanup: record the stage and known owned resources; lifecycle termination and successful cleanup are separate facts.
- Clock is paused, drifts, or cannot be mapped: apply only provider-supported operations, retain original timestamps, and report timing limitations.
- Configured flow has no observations: distinguish “not observed,” “not collected,” and an actual expectation violation. Silence alone is not a universal fault.
- Observation writer or storage fails: surface incomplete evidence and apply the declared bounded run policy; no synthetic replacement evidence.
- Physical device disconnects or reservation expires: follow the provider's admitted policy and report unknown physical/ownership state where acknowledgment is absent.
- A physical realization lacks pause/rewind/fault support: expose the limitation and reject both UI and API requests for those operations.
- Assertion inputs are missing, stale, or outside the supported clock semantics: return indeterminate with reasons, unless an explicitly defined assertion semantics specifies a different valid outcome.
- Campaign is interrupted: reconcile child run identities before scheduling; resume only pending admissible work, with already completed evidence unchanged.
- Mixed profiles disagree on quantities, units, or namespaces: require an explicit compatible mapping or reject; no implicit merge of conflicting semantics.
- A graph contains a feedback loop or a physical coupling: use its declared provider/time/solver contract. A graphical connection alone creates no numerical solver or causal guarantee.
- Export includes restricted or unavailable inputs: preserve references and declared gaps, exclude credentials, and disclose omitted content in the manifest.
- Studio supports the host OS but a selected provider does not: preserve modelling and inspection workflows, give an actionable provider capability diagnostic, and never auto-launch WSL, a container, a VM, or a remote host to conceal the gap.
- Project moves between Linux and Windows: preserve portable semantic identities, revalidate local bindings, and explicitly resolve path/case or filename conflicts; no silent reinterpretation of a portable artifact reference as a host command.
- A platform-specific process/locking mechanism is unavailable: fail the affected capability explicitly or use its tested native implementation; native Windows acceptance cannot be established solely by passing a WSL test.

## Assumptions, Dependencies, and Boundaries

1. The initial product is a locally operated web application: a supported browser UI and native backend on Linux or Windows. Both application environments are mandatory; WSL is not an implicit dependency. Simulator, emulator, runtime, and hardware-driver availability is provider-specific and separately advertised/tested. The product is not initially an internet-exposed multi-tenant service. Offline core workflows are required after provisioning.
2. XDL is authoritative. The approved domain-neutral metamodel and the accepted resource/compiler contracts take precedence over Studio convenience abstractions. Contract drift requires a documented compatibility decision.
3. The inspected Lite rc.1 release record dated 2026-10-24 is historical evidence for the limitations below. Newer repository heads and later completion evidence may differ; M0 must inspect, resolve, and pin an admitted compatible successor before writing an adapter rather than assuming the rc.1 limitations still describe it. See `sources.md` for the inspected source identities, evidence, and scope.
4. The documented Lite execution path is a trusted-host workflow, not evidence of an admitted generic public Run API. A reviewed adapter boundary is required; source visibility does not authorize private API bypass or broader execution.
5. Lite flow evidence does not establish activation of the C++ X-COM core. Studio's M1/M2 communication view must identify the actual evidence source and limitations.
6. Runtime unit/time/resource limits are negotiated and checked. Historical Lite limits must not be generalized into permanent product limits, and an attractive canvas must not imply arbitrary execution scale.
7. Opaque XDL metric/assertion expressions do not establish an evaluator. M4 must define supported semantics and implement/test an evaluator or consume an explicitly compatible one.
8. A physical asset and provider must be nominated for M3. Until available, offline contracts and fixtures can progress, but physical acceptance remains blocked and visibly unclaimed.
9. Required changes to companion repositories are identified as external dependency work with exact contracts and acceptance evidence; this feature does not silently authorize modifying or executing existing production assets.
10. The process-control example must use an admitted implementation and explicit model fidelity. A toy/reference model can demonstrate platform generality but cannot claim industrial process accuracy or physical equivalence.
11. Schema/profile metadata can supply forms and documentation but is untrusted input. Adding a catalog item never grants execution authority.
12. Advanced physical-coupling solvers, universal firmware generation, universal protocol conversion, and unrestricted code execution are outside Studio 1.0. Unsupported interactions remain explicitly represented or rejected rather than simulated by UI animation.

## Success Criteria

All criteria below are acceptance targets, not reported measurements. Record candidate revision, environment, commands/procedure, inputs, outcomes, and evidence locations. A failed or missing criterion cannot be silently treated as passed.

- **SC-001 — Guided usability (M1)**: At least 4 of 5 first-time X-Verse users complete the prepared guided example, change one permitted parameter, run it, locate its result, and identify an injected supported failure within 15 minutes without terminal commands or facilitator intervention. Record preparation time separately and retain task observations; exclude simulator download/install time from this prepared-environment test.
- **SC-002 — Semantic integrity (M2)**: All supported round-trip corpus cases preserve expected semantic identity; layout-only edits change no executable semantic digest; Studio and the pinned CLI produce equivalent plan identities for equivalent supported inputs. Include unresolved-extension and conflicting-write negative cases.
- **SC-003 — Lifecycle reliability (M1)**: The lifecycle conformance suite demonstrates no duplicate starts under identical retries, correct reconnection/resynchronization, explicit uncertain ownership after restart, and separate cleanup failure reporting. Repeat applicable cases through the admitted Lite adapter before claiming live integration.
- **SC-004 — Cross-industry reuse (M2)**: An automotive blueprint and an independent process-control blueprint complete the shared author/validate/deploy/run/inspect workflow with documented provider evidence and no domain-specific conditional logic in shared core modules.
- **SC-005 — Physical substitution (M3)**: One identified physical device is operated through an admitted provider, reservation conflicts are rejected, and a compatible virtual-to-physical deployment change retains logical identity/topology. Record permission scope, clock limitations, shutdown outcome, and unverified fidelity claims.
- **SC-006 — Experiment validity (M4)**: A supported fault scenario and a bounded campaign produce traceable child runs, explicit intended/observed effects, and correct assertion pass/fail/indeterminate outcomes under missing-data and incompatible-time negative cases.
- **SC-007 — Reviewable exchange (M4)**: An exported project and evidence package can be inspected/reimported in a clean prepared environment with exact identity manifests, visible missing dependencies, preserved evidence status, no credential leakage, and no import-triggered execution.
- **SC-008 — Native platform operability and performance (M1 platform gate; M2 performance/authoring gate; retained through M4)**: On both recorded native Linux and Windows environments, demonstrate installation/startup, browser connection, XDL import and save/reopen, validation, an owned reference-provider run/cancel, result inspection, browser reconnect, backend recovery, and clean shutdown without WSL or another undeclared execution layer. Record unsupported live providers as capability limitations; reference-provider success does not prove their support. At M2, also demonstrate cross-OS project exchange, the relevant authoring workflow, and NFR-006–NFR-008 on the declared reference fixtures. The diagnostic matrix covers NFR-011 failures with codes, affected elements, and supported next actions. Results must distinguish Studio overhead from simulator/provider performance.

## Release Claim Rules

The implementation report must list completed milestones, tested providers/profiles, exact compatibility set, measured criteria, unresolved dependencies, and known limits. Incomplete hardware access, unsupported X-COM core integration, missing assertion evaluators, or unverified cleanup are material gaps and must remain visible. No milestone is inferred from the existence of UI controls, source code, a schema, or this plan.

The Studio 1.0 claim requires M0–M4 obligations and retained earlier acceptance evidence. Useful earlier releases are permitted under their narrower milestone names and demonstrated capabilities.

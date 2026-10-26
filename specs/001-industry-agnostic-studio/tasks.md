# Implementation Tasks: Industry-Agnostic X-Verse Studio

**Feature:** `001-industry-agnostic-studio`\
**Status:** implementation in progress. Checked tasks have the component evidence recorded in traceability.json; milestone acceptance and unverified native/live lanes remain open.\
**Inputs:** [specification](spec.md), [architecture plan](plan.md), [data model](data-model.md), [contracts](contracts/studio-api.md), [acceptance cases](acceptance.md), [roadmap](roadmap.md), [machine-readable traceability](traceability.json).

## Execution rules

- Read the repository engineering rules and constitution first. Follow these tasks in dependency order; task numbering is a convenient ordering, not an excuse to ignore dependencies.
- `[P]` identifies work that can run in parallel only after its dependencies pass and when file ownership does not overlap. Tests establish behaviour and failure cases before the corresponding implementation. A path below is an intended implementation/evidence artifact, not a claim that it already exists.
- Implement M0–M4; M5 is an explicitly excluded successor backlog. Do not expand scope to fill an unavailable backend capability with fake UI behaviour.
- The product is a browser UI with a backend that installs and operates natively on both Linux and Windows. M0 records supported distro/edition/releases, architectures, browsers and runtime versions. M1 must pass both native core smoke lanes; WSL, a Windows browser pointed at Linux, containers or remote Linux do not substitute. Optional Spec Kit Bash helpers are development tooling and must not become an undeclared product dependency. Provider OS/driver support remains explicitly negotiated and may be narrower than Studio support.
- A task is complete only when its described work and appropriate verification are recorded. Check its task box and update its `status` to `completed` in `traceability.json` together; keep intermediate work `in_progress` with an unchecked box. Do not mark live/device work complete from fixture success.
- Record missing dependencies with exact operation/provider/version, evidence, affected tasks and next technical action. T012, T034–T035, T064–T066 and T071/T080 have genuine external/environment prerequisites. Continue independent work rather than blocking the entire program. Milestone release claims still require their applicable gates.
- The runtime adapter must use an admitted supported contract; neither the browser nor Studio handlers may bypass it through private Lite classes, arbitrary commands or weakened permits. Existing repositories remain read-only unless separately authorized for the exact change.
- Acceptance in [acceptance.md](acceptance.md) is execution evidence, not a pre-implementation checklist gate. All cases begin **NOT_RUN**. A missing physical asset or live adapter is **BLOCKED** for that lane, never PASS.
- Retain commands/procedures, candidate and input identities, tool/environment versions, exit status, bounded sanitized output and hashes under the planned evidence path or a stable referenced evidence bundle. Re-run affected checks after repairs; do not repeatedly run unrelated suites without a changed risk.
- Use [traceability.json](traceability.json) for the complete dependency graph and bidirectional requirement/task/acceptance mapping. User-derived requirements can proceed despite unavailable normative SADS text; keep source dispositions accurate.

## Independent work branches

After M0 owned contracts pass, guided operation (T015–T033), visual authoring (T041–T063), and documented dependency preparation can progress according to their actual task dependencies. The M2 release review retains M1 gates, but authoring implementation does not need to wait for a missing live host. Physical-provider fixture work similarly precedes actual hardware admission. Final release verification depends on actual completed earlier obligations.

## M0 — Foundation and integration contracts

- [ ] T001 [SETUP] Inspect and pin the actual platform/compat/blueprints revisions, API/profile surface, dependency identities, runtime limits and execution boundary; record missing supported-wrapper work without importing private classes. Record applicability and source dispositions for public SADS allocations XVE-SYS-0159–0178; absent normative text is an evidence gap, not permission to invent detailed matches or a blocker to user-derived requirements. Establish the native platform-support matrix: exact supported Linux distribution/release and Windows edition/release, architecture, browser and Python/Node versions. Separate Studio backend support from each provider/driver/runtime OS capability. Paths: `docs/implementation/baseline.md`, `docs/implementation/dependencies.md`, `docs/implementation/sads-dispositions.md`, `docs/implementation/platform-support.md`. Depends on: none. (FR-006; FR-007; NFR-002; NFR-009; NFR-010; NFR-003; NFR-012; AC-001)
- [ ] T002 [P] [SETUP] Create the planned frontend/backend workspace and exact dependency locks; select supported versions from verified package sources and record the reference environment rather than inventing version pins. Make dependency resolution, build tooling and CI run on both native Linux and Windows; do not make Bash, WSL, a VM, Docker or a remote Linux machine an undeclared core dependency. Paths: `apps/studio-web/package.json`, `services/studio-api/pyproject.toml`, `package-lock.json`, `uv.lock`, `.github/workflows/ci.yml`. Depends on: T001. (NFR-001; NFR-003; NFR-010; NFR-009; AC-001; AC-032)
- [x] T003 [P] [SETUP] Specify failing contract tests for capability/version negotiation, unsupported operations, error envelopes and frontend/backend schema compatibility. Paths: `tests/contract/test_capabilities.py`, `tests/contract/test_api_versions.py`. Depends on: T001. (FR-006; FR-007; NFR-009; AC-001)
- [ ] T004 [SETUP] Implement versioned API models, capability registry and generated frontend contracts; preserve ownership boundaries and reject incompatible providers before operations. Advertise host OS/architecture and provider-specific OS support separately; unsupported simulator/device providers remain unavailable without disabling the native Studio application. Paths: `services/studio-api/src/xverse_studio/api/`, `services/studio-api/src/xverse_studio/providers/`, `packages/contracts/`. Depends on: T002, T003. (FR-006; FR-007; NFR-009; FR-008; AC-001)
- [ ] T005 [P] [SETUP] Build the minimal supported XDL corpus and CLI/library equivalence tests, including explicit dependencies, invalid inputs and semantic/source identity distinctions. Run authoritative validation/compilation fixtures through the selected native platform-library installation on both supported operating systems. Paths: `tests/contract/test_xdl_adapter.py`, `tests/fixtures/xdl/`. Depends on: T001. (FR-001; NFR-002; NFR-009; AC-002)
- [x] T006 [SETUP] Implement the pinned platform validation/normalization/compilation adapter and source-location diagnostics without recreating XDL rules in the frontend. Paths: `services/studio-api/src/xverse_studio/xdl/`. Depends on: T002, T005. (FR-001; FR-007; NFR-002; AC-002)
- [ ] T007 [P] [SETUP] Specify project revision, atomic persistence, stable references and backup-preserving migration tests using isolated project roots. Cover spaces/non-ASCII paths, drive/UNC paths, case collisions, reserved names, locks, replacement semantics and line endings; portable project identity must survive bidirectional Linux/Windows exchange. Paths: `tests/integration/test_project_store.py`, `tests/fixtures/projects/`. Depends on: T001. (FR-001; NFR-009; AC-002)
- [ ] T008 [SETUP] Implement project metadata storage, XDL resource ownership and separate layout/binding sidecars, with atomic revision-checked writes and explicit migration versions. Use host-correct atomic/locking behaviour and a portable path representation for project data; preserve environment-specific paths only in the appropriate local binding. Paths: `services/studio-api/src/xverse_studio/projects/`, `services/studio-api/src/xverse_studio/storage/`. Depends on: T002, T006, T007. (FR-001; NFR-009; AC-002)
- [ ] T009 [P] [SETUP] Add negative API/import tests for untrusted origins, unauthorized mutations, traversal, symlink escapes, unsafe archives, oversized input, secrets and script-like profile content. Exercise Windows drive/UNC/device-path and junction escapes, case collisions and reserved-name attacks as well as Linux path/symlink cases. Paths: `tests/contract/test_security_boundary.py`, `tests/fixtures/imports/`. Depends on: T001. (FR-007; NFR-003; NFR-004; AC-003; AC-032)
- [ ] T010 [SETUP] Implement local binding/session/origin controls, bounded project-file access, inert import and redaction; only installed admitted provider operations can cross the execution boundary. Enforce these boundaries on both native platforms using OS-aware path APIs rather than POSIX-only assumptions. Paths: `services/studio-api/src/xverse_studio/security/`, `services/studio-api/src/xverse_studio/imports/`. Depends on: T004, T008, T009. (FR-007; NFR-003; NFR-004; AC-003; AC-032)
- [ ] T011 [P] [SETUP] Create an owned executable reference provider plus separate fake-provider and recorded-evidence fixtures, with deterministic lifecycle failure points, clocks, capability versions and explicit scope labels. The executable reference must produce its own observations under native Linux and Windows ownership; replayed/mock data cannot substitute for executing that reference. Paths: `tests/fixtures/providers/`, `tests/fixtures/runs/`. Depends on: T004. (FR-006; FR-007; NFR-010; AC-001)
- [ ] T012 [SETUP] Define and implement the supported Lite-wrapper binding only when its public contract/admission is established; otherwise record the exact blocked external dependency and keep the binding unavailable. For a wrapper that generates XDL internally, expose and compare the effective generated model/plan to the requested immutable inputs before admission; reject unsupported edits instead of claiming a fixed harness executed them. Paths: `services/studio-api/src/xverse_studio/integrations/lite/`, `docs/implementation/dependencies.md`. Depends on: T001, T004. (FR-006; FR-007; NFR-002; NFR-009; AC-001)
- [x] T013 [P] [SETUP] Add architecture-boundary checks preventing core imports or industry branches on profile/provider/blueprint packages while allowing declared extension contracts. Paths: `tests/contract/test_architecture_boundaries.py`, `scripts/check_architecture.py`. Depends on: T002. (NFR-001; NFR-010; AC-001; AC-019; AC-020)
- [ ] T014 [SETUP] Run M0 contract/security/project checks, record candidate/environment identities, and classify the real Lite binding as available or blocked; fixture completion must not imply T012/live completion. Paths: `evidence/studio/M0/`, `docs/implementation/dependencies.md`. Depends on: T004, T006, T008, T010, T011, T013. (FR-001; FR-006; FR-007; NFR-001; NFR-002; NFR-009; NFR-010; AC-001; AC-002; AC-003)

## M1 — Guided operation / Studio 0.1

- [x] T015 [P] [US1] Add prepared-example onboarding, import, unknown-extension preservation and parameter-validation scenarios before UI implementation. Paths: `tests/e2e/project-onboarding.spec.ts`, `tests/integration/test_project_import.py`. Depends on: T014. (FR-002; FR-003; FR-004; FR-005; AC-002; AC-003; AC-004)
- [x] T016 [US1] Implement create/open/recent/example journeys, explicit dependency import and unresolved-content inspection with clearly scoped example claims. Paths: `apps/studio-web/src/features/projects/`, `services/studio-api/src/xverse_studio/projects/`. Depends on: T015. (FR-002; FR-003; FR-004; AC-002; AC-003; AC-004)
- [x] T017 [P] [US1] Implement guided schema-backed parameter forms, units/constraints/provenance, actionable errors and advanced read-only XDL display with accessible controls. Paths: `apps/studio-web/src/features/inspector/`, `apps/studio-web/src/features/source/`. Depends on: T015. (FR-005; NFR-006; AC-004; AC-031)
- [x] T018 [P] [US2] Add admission tests for stale inputs/capabilities, missing artifacts, unknown limits, exceeded budgets, missing clock mappings and ownership conflicts. Paths: `tests/integration/test_preflight.py`. Depends on: T014. (FR-008; FR-009; FR-010; NFR-011; AC-005)
- [x] T019 [US2] Implement digest-bound plan previews and immediate pre-Start re-admission of mutable target/capability/resource/authority facts. Require the adapter to confirm its effective configuration/plan matches the selected snapshot; unavailable input injection leaves unsupported authoring changes unexecutable. Paths: `services/studio-api/src/xverse_studio/preflight/`. Depends on: T018, T006, T004. (FR-008; FR-009; FR-010; AC-005)
- [x] T020 [US2] Implement separate readiness dimensions, exact blocked elements, advertised limits and supported remediation without a misleading aggregate health badge. Paths: `apps/studio-web/src/features/preflight/`. Depends on: T019, T016. (FR-008; FR-009; FR-010; NFR-011; AC-005)
- [ ] T021 [P] [US3] Add lifecycle, immutable-snapshot, idempotency, optional-control, partial-start, cancellation and backend-restart conformance tests against the owned provider. Run owned-process lifecycle and service-restart cases on native Linux and Windows; process ownership and termination must not assume POSIX signals or process groups. Paths: `tests/contract/test_runtime_lifecycle.py`, `tests/integration/test_run_recovery.py`. Depends on: T014. (FR-011; FR-012; FR-013; FR-014; FR-015; FR-016; NFR-005; AC-006; AC-007; AC-008; AC-009; AC-027)
- [x] T022 [US3] Implement persistent immutable run snapshots, scoped request fingerprints and durable idempotent dispatch through admitted provider bindings. Bind dispatch to the adapter-confirmed effective input/plan identity, not merely the requested GUI document. Paths: `services/studio-api/src/xverse_studio/runs/`, `services/studio-api/src/xverse_studio/commands/`. Depends on: T021, T019. (FR-011; FR-012; FR-015; AC-006; AC-008; AC-027)
- [ ] T023 [US3] Implement restart reconciliation and ownership-verified cleanup; keep uncertain ownership and cleanup outcome separate from run termination and never blindly respawn. Reconcile platform-specific owned process handles/identities on Windows and Linux, including PID reuse and lost handles; uncertain ownership stays blocked instead of inferring a process match. Paths: `services/studio-api/src/xverse_studio/runs/reconcile.py`, `services/studio-api/src/xverse_studio/runs/cleanup.py`. Depends on: T022. (FR-013; FR-014; NFR-005; AC-007; AC-008; AC-009)
- [x] T024 [US3] Enforce optional-operation capability/authority checks in the API and record permitted live mutations with original/new value and outcome provenance. Paths: `services/studio-api/src/xverse_studio/runs/controls.py`. Depends on: T022. (FR-016; AC-018; AC-027)
- [ ] T025 [P] [US3] Add duplicate-Start, two-tab retry, UI-disconnect, event-order, cursor-expiry and resynchronization tests; test changed-payload idempotency conflicts. Verify command.failed events, command acceptance versus execution failure, and browser reconnection on both supported native backend/browser combinations. Paths: `tests/e2e/run-reconnect.spec.ts`, `tests/contract/test_run_events.py`. Depends on: T021. (FR-012; FR-013; FR-021; AC-008; AC-010)
- [ ] T026 [US3] Implement resumable cursor events, explicit gap/resync responses and session reconnection independent of backend run ownership. Paths: `services/studio-api/src/xverse_studio/events/`, `apps/studio-web/src/features/runs/session.ts`. Depends on: T022, T023, T025. (FR-013; FR-021; AC-008; AC-010)
- [ ] T027 [US3] Implement run-plan/start/control views with startup, stop, cleanup, evidence and optional-operation states, clearly identifying current immutable inputs. Paths: `apps/studio-web/src/features/runs/`. Depends on: T020, T024, T026. (FR-011; FR-014; FR-015; FR-016; FR-020; AC-006; AC-007; AC-027)
- [x] T028 [P] [US4] Add verified-prefix/read-only evidence fixtures with gaps, redaction restrictions, differing clocks, measured zero versus missing data and a slow UI consumer. Paths: `tests/integration/test_evidence_projection.py`, `tests/fixtures/evidence/`. Depends on: T014. (FR-017; FR-018; FR-020; FR-021; FR-022; NFR-008; AC-010; AC-011)
- [x] T029 [US4] Implement admitted Argus/evidence projections, bounded filtering/pagination and cursor delivery without reading private provider streams or changing authoritative evidence. Paths: `services/studio-api/src/xverse_studio/evidence/`. Depends on: T028. (FR-017; FR-018; FR-021; FR-022; NFR-008; AC-010; AC-011)
- [x] T030 [US4] Implement selected-element logs/signals/events, source/severity/time filters, clock/quality markers and explicit display gaps with bounded rendering. Paths: `apps/studio-web/src/features/results/`. Depends on: T029, T026. (FR-017; FR-018; FR-020; FR-021; AC-010; AC-011)
- [x] T031 [P] [US4] Specify evidence-linked explanation tests for every required diagnostic class, facts versus hypotheses, no-traffic ambiguity and liveness-only health. Paths: `tests/contract/test_diagnostics.py`, `tests/e2e/diagnostics.spec.ts`. Depends on: T028. (FR-019; FR-020; NFR-011; AC-005; AC-007; AC-011)
- [x] T032 [US4] Implement structured diagnostic codes, affected references, evidence sources and supported next actions; root causes remain unknown unless evidenced. Paths: `services/studio-api/src/xverse_studio/diagnostics/`, `apps/studio-web/src/features/diagnostics/`. Depends on: T031, T029. (FR-019; FR-020; NFR-011; AC-005; AC-007; AC-011)
- [ ] T033 [SETUP] Run the owned-fixture guided vertical slice and lifecycle fault matrix; keep fixture results explicitly separate from the live integration lane. Paths: `evidence/studio/M1-fixture/`. Depends on: T016, T017, T020, T027, T030, T032. (FR-011; FR-012; FR-013; FR-014; FR-015; FR-016; FR-017; FR-018; FR-019; FR-020; FR-021; FR-022; NFR-005; NFR-011; AC-005; AC-006; AC-007; AC-008; AC-009; AC-010; AC-011; AC-027)
- [ ] T034 [US3] Prepare actual installed-wrapper conformance and permitted nominal/failure scenarios using pinned environment inputs; record blocked state if T012 or the runtime environment is unavailable. Include a fixed-wrapper negative that ignores a requested edit and must be rejected, plus a supported edit whose actual generated XDL/plan equals the requested snapshot. Treat the historical run-live.sh candidate as Linux-only unless separately verified otherwise. On native Windows verify explicit unavailable-provider responses; never substitute WSL or report that rejection test as Windows simulator execution. Paths: `tests/integration/test_lite_live_adapter.py`, `docs/implementation/live-lane.md`. Depends on: T012, T021, T033. (FR-011; FR-014; FR-022; AC-006; AC-007)
- [ ] T035 [US3] Execute only the admitted Lite live scenarios and retain exact provider/input/evidence identities; do not count fixture or dry-run output as live evidence. Record the actual host OS for every live provider and test a native Windows live lane only when that provider has separate compatible admission; core Windows support is established by its owned reference-runtime lane. Paths: `evidence/studio/M1-live/`. Depends on: T034. (FR-008; FR-009; FR-010; FR-011; FR-012; FR-013; FR-014; FR-020; FR-022; NFR-010; AC-005; AC-006; AC-007; AC-008)
- [x] T036 [P] [US1] Write prepared-example setup/operation/recovery documentation and the scripted first-time-user study with explicit prerequisites, prompts and assistance accounting. Paths: `docs/user/getting-started.md`, `docs/user/troubleshooting.md`, `docs/user/recovery.md`. Depends on: T016, T017, T027, T032. (FR-002; FR-005; NFR-012; AC-004; AC-012; AC-032)
- [ ] T037 [US1] Run SC-001 with five first-time users on the prepared environment and retain anonymized timing/completion/assistance records; address failures and rerun affected checks. Record each participant's native platform; the five-user usability cohort is distinct from the mandatory automated Linux/Windows platform smoke matrix. Paths: `evidence/studio/M1-usability/`. Depends on: T035, T036. (FR-002; FR-005; NFR-012; AC-012)
- [ ] T038 [P] [SETUP] Verify keyboard/focus/status alternatives at 1024×768 and 1440×900 and measure the 50,000-event/200-row workload over the specified repetitions. Execute the supported browser/accessibility and event-query matrix on both native Linux and Windows, retaining each platform's results independently. Paths: `tests/e2e/accessibility.spec.ts`, `tests/performance/evidence-query.spec.ts`, `evidence/studio/M1-operability/`. Depends on: T030, T032. (NFR-006; NFR-008; NFR-011; NFR-003; AC-010; AC-011; AC-031)
- [ ] T039 [P] [SETUP] Add native launcher/install/start/stop/restart tests first, then package the web UI and local backend for Linux and Windows with a cross-platform launcher and documented offline, backup, migration and retention procedures. Support foreground or launcher-managed background operation without requiring WSL, a VM, Docker or a remote Linux host. OS service-manager registration/autostart is optional, explicit and separately tested if offered. Execute AC-032 natively on both platforms and report provider-specific limits separately. Paths: `docs/user/installation.md`, `docs/user/retention.md`, `scripts/package_studio.py`, `services/studio-api/src/xverse_studio/launcher.py`, `tests/integration/test_native_launcher.py`. Depends on: T010, T023, T036. (NFR-003; NFR-004; NFR-009; NFR-012; AC-003; AC-009; AC-032)
- [ ] T040 [SETUP] Review M1 against its requirements and actual fixture/live/usability evidence; record gaps and accurate release scope instead of marking unavailable lanes passed. Require SC-008 native platform smoke evidence for both Linux and Windows; a Windows browser pointed at Linux, WSL or a fixture-only provider claim is not evidence of a native Windows backend install. Paths: `evidence/studio/M1-review/`. Depends on: T033, T035, T037, T038, T039. (NFR-010; NFR-012; AC-004; AC-005; AC-006; AC-007; AC-008; AC-009; AC-010; AC-011; AC-012; AC-027; AC-031; AC-032)

## M2 — Visual composition / Studio 0.2

- [x] T041 [P] [US5] Extend the supported XDL corpus with graph/source-equivalent edits, layout-only changes, unknown payload preservation and explicit comment/format normalization disclosure. Paths: `tests/integration/test_model_roundtrip.py`, `tests/fixtures/xdl/roundtrip/`. Depends on: T014. (FR-023; FR-024; FR-025; NFR-002; AC-013)
- [x] T042 [US5] Implement typed model edits through the authoritative XDL service and separate stable-ID layout updates; validate before promoting an executable revision. Paths: `services/studio-api/src/xverse_studio/models/`. Depends on: T041, T008. (FR-023; FR-024; FR-025; AC-013)
- [x] T043 [US5] Build the system canvas and structured keyboard editor with named ports, subsystem navigation, search, grouping, zoom and automatic layout mapped to supported XDL semantics. Paths: `apps/studio-web/src/features/model/`, `apps/studio-web/src/features/model/tree/`. Depends on: T042, T017. (FR-023; FR-027; NFR-006; AC-013; AC-031)
- [x] T044 [US5] Enable source authoring and synchronized selection/diagnostics; retain invalid drafts and unsupported extension content without dropping data or overwriting active run inputs. Paths: `apps/studio-web/src/features/source/`, `apps/studio-web/src/features/inspector/`. Depends on: T042, T043. (FR-023; FR-025; AC-013)
- [x] T045 [P] [US5] Add external-write races, interrupted saves, undo/redo reference integrity and simultaneous draft/run inspection cases. Paths: `tests/integration/test_edit_conflicts.py`, `tests/e2e/draft-run-isolation.spec.ts`. Depends on: T041. (FR-026; FR-028; NFR-009; AC-014)
- [x] T046 [US5] Implement bounded autosave/recovery, undo/redo transactions and revision conflict resolution with recoverable source backups. Paths: `services/studio-api/src/xverse_studio/projects/revisions.py`, `apps/studio-web/src/features/model/history.ts`. Depends on: T042, T045. (FR-026; NFR-009; AC-014)
- [x] T047 [US5] Show the editable draft revision and immutable selected run snapshot distinctly, including divergence badges and evidence navigation to snapshot identities. Paths: `apps/studio-web/src/features/model/run-overlay.tsx`. Depends on: T027, T044, T046. (FR-028; FR-015; AC-014; AC-027)
- [ ] T048 [US5] Execute round-trip/layout/conflict scenarios against the pinned CLI/library and inspect resulting source/digest differences, including failed-edit recovery. Execute bidirectional Linux-to-Windows and Windows-to-Linux project exchange with spaces, non-ASCII names, line-ending changes and host-specific bindings, preserving executable semantic identity. Paths: `evidence/studio/M2-roundtrip/`. Depends on: T043, T044, T046, T047. (FR-023; FR-024; FR-025; FR-026; FR-027; FR-028; NFR-002; NFR-009; AC-013; AC-014)
- [x] T049 [P] [US6] Specify catalog/wizard contract tests for versions, role-realization-placement independence, definition/instance identity, inert artifacts and untrusted form metadata. Paths: `tests/contract/test_catalog.py`, `tests/fixtures/catalog/`. Depends on: T014. (FR-029; FR-030; FR-031; FR-032; FR-033; NFR-004; AC-015)
- [x] T050 [US6] Implement local catalog admission/filtering with immutable artifact references, schema/provenance/maturity records and explicit unavailable versions. Expose admitted catalog discovery through the specified API so the UI and external contract tests consume the same versioned entries. Paths: `services/studio-api/src/xverse_studio/catalog/`. Depends on: T049, T004, T008. (FR-029; FR-031; FR-033; AC-015)
- [x] T051 [US6] Build Add element and instance wizards for generic roles/devices/model references, separate realization/placement and schema-backed configuration without hard-coded ECU core entities. Paths: `apps/studio-web/src/features/catalog/`, `apps/studio-web/src/features/elements/`. Depends on: T050, T043. (FR-030; FR-032; FR-033; AC-015)
- [x] T052 [US6] Verify representative controller/sensor/actuator/service/model/observer creation, invalid versions and implementation registration without build/flash/execute side effects. Paths: `tests/e2e/catalog-wizard.spec.ts`, `evidence/studio/M2-catalog/`. Depends on: T051. (FR-029; FR-030; FR-031; FR-032; FR-033; NFR-004; AC-015)
- [x] T053 [P] [US7] Add compatible/mismatched port, explicit converter, multiplicity, timing/QoS, physical-coupling and valid/invalid feedback fixtures with declared expected semantics. Paths: `tests/contract/test_connections.py`, `tests/fixtures/connections/`. Depends on: T014. (FR-034; FR-035; FR-037; FR-038; AC-016; AC-017)
- [x] T054 [US7] Implement connection admission using platform/profile/provider contracts; require explicit conversions and validate supported feedback causality without a universal acyclic-graph rule. Paths: `services/studio-api/src/xverse_studio/connections/`. Depends on: T053, T042, T050. (FR-034; FR-035; FR-038; AC-016)
- [x] T055 [US7] Implement compatible-target guidance, inspectable mapping forms and distinct relation styles/actions for communication, model coupling, deployment and traceability. Paths: `apps/studio-web/src/features/connections/`. Depends on: T054, T043. (FR-034; FR-035; FR-037; FR-038; AC-016; AC-017)
- [x] T056 [US7] Implement declared/resolved/observed communication projections with provider scope, freshness and limitation labels; preserve Lite/native X-COM distinction. Paths: `services/studio-api/src/xverse_studio/connections/projections.py`, `apps/studio-web/src/features/connections/projections.tsx`. Depends on: T055, T030. (FR-036; FR-037; AC-017)
- [x] T057 [P] [US8] Add compatible/incompatible rebinding, logical identity preservation, resource/time/network constraints, effective-value precedence and portable/private binding tests. Paths: `tests/integration/test_deployment_variants.py`. Depends on: T014. (FR-039; FR-040; FR-041; FR-042; AC-018)
- [x] T058 [US8] Implement named deployment variants and authoritative compatibility/effective-value resolution; reject undefined override precedence and keep environment addresses/secret handles separate. Resolve host-specific paths/resources against the selected provider OS contract while keeping portable deployment intent and secret references separate. Paths: `services/studio-api/src/xverse_studio/deployments/`. Depends on: T057, T042, T054. (FR-039; FR-040; FR-041; FR-042; AC-018)
- [x] T059 [US8] Build realization/placement comparison, binding and resource/time forms with visible provenance/fidelity limits and provider-supported controls. Paths: `apps/studio-web/src/features/deployments/`. Depends on: T058, T051. (FR-039; FR-040; FR-041; FR-042; FR-016; AC-018)
- [x] T060 [P] [US9] Add compatible mixed-profile, namespace collision, core-semantic redefinition, malicious presentation and unsupported-version cases. Paths: `tests/contract/test_profiles.py`, `tests/fixtures/profiles/`. Depends on: T014. (FR-043; FR-044; FR-045; FR-047; NFR-001; NFR-009; AC-019)
- [x] T061 [US9] Implement profile admission and composition independently from provider execution and blueprint composition; retain exact namespace/version/maturity/limitation metadata. Expose admitted profile discovery through the versioned API; OS compatibility comes from provider bindings rather than from the industry name. Paths: `services/studio-api/src/xverse_studio/profiles/`. Depends on: T060, T050. (FR-043; FR-044; FR-047; NFR-001; NFR-009; AC-019)
- [x] T062 [US9] Render sanitized profile-provided terminology/forms/icons/documentation through shared workflows and allow compatible cross-industry selections. Paths: `apps/studio-web/src/features/profiles/`. Depends on: T061, T051, T059. (FR-045; NFR-004; AC-019)
- [x] T063 [US9] Run profile conflict/security/architecture checks and inspect dependency direction; reject domain conditionals or executable presentation hooks in core modules. Paths: `evidence/studio/M2-profiles/`. Depends on: T062, T013. (FR-043; FR-044; FR-045; FR-047; NFR-001; NFR-009; AC-019)
- [ ] T064 [US9] Nominate exact automotive and independent process-control blueprint/provider artifacts; prepare a minimal reference process model and contract fixtures, and record any missing companion capability as external work before real admission. Paths: `docs/implementation/blueprint-admission.md`, `tests/fixtures/blueprints/process-control/`. Depends on: T001, T004, T061. (FR-046; FR-047; NFR-001; AC-020)
- [ ] T065 [US9] Integrate the admitted example bundles and their declared observations/fidelity into the catalog; fixtures may demonstrate only their explicit scope and cannot masquerade as unavailable live providers. Paths: `tests/fixtures/blueprints/automotive/`, `tests/fixtures/blueprints/process-control/`, `apps/studio-web/src/features/projects/examples.ts`. Depends on: T064, T059, T062. (FR-046; FR-047; AC-020)
- [ ] T066 [US9] Execute author/validate/deploy/run/inspect for both independent blueprints using their admitted implementations, recording provider scope and proving the core needs no domain-specific branch. Paths: `tests/e2e/cross-industry.spec.ts`, `evidence/studio/M2-domains/`. Depends on: T065, T035, T048, T052, T056. (FR-046; FR-047; NFR-001; AC-020)
- [ ] T067 [P] [SETUP] Measure the 200-element/400-connection workload and retained evidence-query target over 30 repetitions after one warm-up; verify keyboard alternatives and the required viewports. Run the declared reference workloads and keyboard/browser checks on both supported native platform environments; retain per-OS measurements rather than averaging platforms together. Paths: `tests/performance/model-canvas.spec.ts`, `tests/e2e/accessibility.spec.ts`, `evidence/studio/M2-operability/`. Depends on: T043, T044, T059, T062. (FR-027; NFR-006; NFR-007; NFR-008; NFR-011; NFR-003; NFR-009; AC-030; AC-031)
- [ ] T068 [SETUP] Run combined authoring/deployment/connection regression and direct API negatives, including unsupported physical coupling and version migration without semantic loss. Paths: `evidence/studio/M2-integration/`. Depends on: T048, T052, T056, T059, T063. (FR-034; FR-035; FR-036; FR-037; FR-038; FR-039; FR-040; FR-041; FR-042; NFR-002; NFR-009; AC-013; AC-014; AC-015; AC-016; AC-017; AC-018; AC-019)
- [ ] T069 [SETUP] Review M2 and retained M1 evidence, record measured SC-002/SC-004/SC-008 and publish only the demonstrated profile/provider compatibility envelope. Paths: `evidence/studio/M2-review/`. Depends on: T040, T066, T067, T068. (NFR-001; NFR-010; AC-013; AC-014; AC-015; AC-016; AC-017; AC-018; AC-019; AC-020; AC-030; AC-031)

## M3 — Hybrid laboratory / Studio 0.3

- [x] T070 [P] [US10] Add physical-provider fixtures for identity/metadata, unresolved assets, exclusivity, leases, observe-only access, denied stimulation, disconnect and unknown cleanup. Paths: `tests/contract/test_physical_provider.py`, `tests/fixtures/providers/physical/`. Depends on: T063. (FR-048; FR-049; FR-050; FR-051; AC-021; AC-022; AC-023)
- [ ] T071 [US10] Nominate one actual device/provider, exact identities, permitted nonhazardous test actions, reservation/clock/stop contract and required external capability work; record unavailable inputs as blockers. Record the provider's supported native OS/architecture and driver requirements; a provider verified only on Linux remains explicitly unavailable on Windows. Paths: `docs/implementation/physical-provider-admission.md`. Depends on: T001, T070. (FR-048; FR-050; FR-052; AC-021; AC-024)
- [x] T072 [US10] Implement lab inventory and logical-device-to-asset binding with explicit identity, metadata availability and active-operation readiness checks. Paths: `services/studio-api/src/xverse_studio/lab/assets.py`, `services/studio-api/src/xverse_studio/lab/bindings.py`. Depends on: T070, T058, T061. (FR-048; AC-021)
- [ ] T073 [P] [US10] Exercise concurrent claims, lease renewal/expiry, stale handles, interruption and repeated release; verify API-level observe/stimulate/destructive-action distinctions. Paths: `tests/integration/test_lab_reservations.py`. Depends on: T070. (FR-049; FR-050; NFR-005; AC-022; AC-023)
- [ ] T074 [US10] Implement provider-backed reservations/reconciliation and action authority checks; expired or uncertain ownership cannot enable active commands. Paths: `services/studio-api/src/xverse_studio/lab/reservations.py`, `services/studio-api/src/xverse_studio/lab/authority.py`. Depends on: T073, T072, T023. (FR-049; FR-050; AC-022; AC-023)
- [ ] T075 [US10] Build inventory, binding, reservation and connection-test views with simulation/hardware indication, observe-only default and explicit unsupported-operation explanations. Paths: `apps/studio-web/src/features/lab/`. Depends on: T072, T074, T059. (FR-048; FR-049; FR-050; AC-021; AC-022)
- [x] T076 [P] [US10] Specify virtual/physical substitution, mismatched interfaces, missing clock evidence, unplug, refused stop and failed restore outcomes without assuming physical pause or rewind. Paths: `tests/integration/test_hybrid_time_and_loss.py`. Depends on: T070. (FR-051; FR-052; FR-040; AC-023; AC-024)
- [ ] T077 [US10] Implement provider-declared disconnect/recovery/stop integration and expose physical-state uncertainty and original timestamp/synchronization evidence. Paths: `services/studio-api/src/xverse_studio/lab/recovery.py`, `services/studio-api/src/xverse_studio/lab/time_quality.py`. Depends on: T076, T029, T074. (FR-051; AC-023; AC-024)
- [ ] T078 [US10] Show compatible substitution, unchanged logical topology, changed time/control/fidelity capabilities and uncertain physical/cleanup outcomes. Paths: `apps/studio-web/src/features/lab/hybrid-inspector.tsx`, `apps/studio-web/src/features/results/`. Depends on: T075, T077, T030. (FR-051; FR-052; FR-040; AC-023; AC-024)
- [ ] T079 [US10] Run physical contract and failure-path fixtures, label results as fixtures and confirm that absent device access cannot pass the actual hardware case. Paths: `evidence/studio/M3-fixture/`. Depends on: T075, T077, T078. (FR-048; FR-049; FR-050; FR-051; NFR-005; AC-021; AC-022; AC-023; AC-024)
- [ ] T080 [US10] Execute the admitted physical inventory/reservation/substitution/loss cases on the identified device, retaining permission scope, clocks, actions and actual shutdown outcomes. Bind physical evidence to the actual supported host OS and driver. Missing Windows hardware-provider support must not be advertised as universal device support, nor treated as failure of the separately verified native Studio core. Paths: `evidence/studio/M3-physical/`. Depends on: T071, T079. (FR-048; FR-049; FR-050; FR-051; FR-052; AC-021; AC-022; AC-023; AC-024)
- [ ] T081 [SETUP] Document the demonstrated physical provider and limits, review SC-005 and retain explicit gaps; do not release a hardware-support claim from fixture-only results. Paths: `docs/user/hybrid-lab.md`, `evidence/studio/M3-review/`. Depends on: T069, T080. (FR-052; NFR-010; NFR-012; AC-021; AC-022; AC-023; AC-024)

## M4 — Experiment management / Studio 1.0

- [ ] T082 [P] [US11] Specify scenario/observer/fault tests for target references, typed time/stimuli, bounds, conflicting schedules, unsupported operations and intended versus observed effects. Paths: `tests/contract/test_scenarios.py`, `tests/fixtures/scenarios/`. Depends on: T068. (FR-053; FR-054; FR-055; FR-057; AC-025)
- [ ] T083 [US11] Implement scenario authoring/compilation using admitted XDL/profile semantics and provider checks for stimuli, observation cost and activation/recovery schedules. Paths: `services/studio-api/src/xverse_studio/experiments/`. Depends on: T082, T042, T019. (FR-053; FR-054; FR-055; AC-025)
- [ ] T084 [US11] Build scenario/stimulus/fault/observer forms and timeline with explicit clock selection, intent/observation markers and unavailable-capability explanations. Paths: `apps/studio-web/src/features/experiments/`. Depends on: T083, T044, T030. (FR-053; FR-054; FR-055; FR-057; AC-025)
- [x] T085 [P] [US11] Refine the existing contracts/experiment-evaluation.md bounded typed/temporal JSON-AST contract into implementation schemas and detailed design, preserving its versioned operators, half-open run-relative windows, full-data coverage, resource caps, units/time rules and pass/fail/indeterminate outcomes. Record a versioned contract decision before any necessary semantic change; define the admitted XDL/profile mapping without inventing a competing language. Paths: `docs/architecture/assertion-language.md`, `packages/contracts/assertions/`. Depends on: T082. (FR-056; NFR-004; AC-026)
- [x] T086 [US11] Add evaluator examples and adversarial negatives for missing/gapped/stale inputs, clock incompatibility, unit errors, unknown operators, nested limits and attempted arbitrary execution. Paths: `tests/contract/test_assertions.py`, `tests/fixtures/assertions/`. Depends on: T085. (FR-056; NFR-004; AC-026)
- [x] T087 [US11] Implement or integrate the compatible bounded evaluator and explicit expression-to-contract mapping; preserve opaque unsupported expressions unevaluated and never call eval or execute arbitrary code. Implement the contract's evaluation create/result operations with separate evaluation-execution status and assertion verdict. Paths: `services/studio-api/src/xverse_studio/assertions/`. Depends on: T086, T083. (FR-056; AC-026)
- [ ] T088 [US11] Display assertion definitions/results with input provenance, clock assumptions, indeterminate reasons and correlated scenario/fault markers. Paths: `apps/studio-web/src/features/experiments/assertions.tsx`, `apps/studio-web/src/features/results/`. Depends on: T087, T084. (FR-056; FR-057; AC-025; AC-026)
- [ ] T089 [P] [US12] Specify bounded matrix/cardinality, per-run snapshots, reservations/concurrency, retry deduplication, cancellation and crash/reconciliation cases. Paths: `tests/integration/test_campaigns.py`. Depends on: T023, T027. (FR-058; AC-028)
- [ ] T090 [US12] Implement finite campaign preview/scheduling/history with explicit budgets, immutable child identities and pending-only recovery under current admission limits. Paths: `services/studio-api/src/xverse_studio/campaigns/`, `apps/studio-web/src/features/campaigns/`. Depends on: T089, T083, T022, T023. (FR-058; AC-028)
- [ ] T091 [US12] Add incompatible-quantity, gap, clock and replay/rerun regression cases first, then implement baseline comparison with configuration/clock/quantity compatibility and distinguish recorded observation playback from freshly admitted rerun. Paths: `tests/integration/test_comparison.py`, `services/studio-api/src/xverse_studio/comparison/`, `apps/studio-web/src/features/comparison/`. Depends on: T030, T059, T088. (FR-059; FR-060; AC-029)
- [x] T092 [P] [US12] Add export/import integrity, missing/restricted dependency, malicious archive, credentials, revisioned trace links, annotation separation and dependency-aware retention tests. Paths: `tests/integration/test_exchange_and_retention.py`, `tests/fixtures/bundles/`. Depends on: T068. (FR-061; FR-062; FR-063; NFR-004; AC-029; AC-032)
- [ ] T093 [US12] Implement sanitized manifests and project/evidence/report exchange with exact identities, unavailable references and integrity status; imports remain inert and local by explicit selection. Test portable package import/export in both native directions and refuse incompatible host-local bindings without rewriting portable model identity. Paths: `services/studio-api/src/xverse_studio/exchange/`, `apps/studio-web/src/features/exchange/`. Depends on: T092, T008, T029. (FR-061; NFR-004; NFR-009; AC-029)
- [x] T094 [US12] Implement revisioned external requirement/test references, separate annotations/derived reports and explicit dependency-aware retention/deletion without rewriting historical evidence. Enforce revision-checked annotation updates and the contract's retention dry-run/apply sequence, rechecking dependencies before a destructive retention action. Paths: `services/studio-api/src/xverse_studio/annotations/`, `services/studio-api/src/xverse_studio/retention/`, `apps/studio-web/src/features/results/`. Depends on: T092, T029, T091. (FR-062; FR-063; AC-029)
- [ ] T095 [SETUP] Run positive/negative assertion and supported fault cases, bounded campaign recovery, baseline comparison and clean-environment exchange; record actual provider scope and SC-006/SC-007. Run owned experiment/campaign/exchange lanes on native Linux and Windows; record live-provider lanes separately by actual OS support. Paths: `tests/e2e/experiment-campaign.spec.ts`, `evidence/studio/M4-experiments/`. Depends on: T088, T090, T091, T093, T094, T035. (FR-053; FR-054; FR-055; FR-056; FR-057; FR-058; FR-059; FR-060; FR-061; FR-062; FR-063; NFR-004; NFR-003; NFR-009; AC-025; AC-026; AC-027; AC-028; AC-029)
- [ ] T096 [P] [SETUP] Repeat declared canvas/history/event workloads with campaign/analysis features enabled, preserving bounded queues and meaningful control responsiveness evidence. Retain separate native Linux and Windows reference measurements and verify that queue/control behaviour is independent of POSIX-specific process assumptions. Paths: `tests/performance/`, `evidence/studio/M4-performance/`. Depends on: T090, T091, T093, T094. (NFR-007; NFR-008; NFR-011; NFR-003; AC-010; AC-011; AC-030)
- [ ] T097 [P] [SETUP] Verify all added authoring/lab/campaign/export flows with keyboard, focus, labelled diagnostics, status alternatives and both required desktop viewports. Use the declared supported browser matrix on both native Linux and Windows backends. Paths: `tests/e2e/accessibility.spec.ts`, `evidence/studio/M4-accessibility/`. Depends on: T084, T088, T090, T091, T093, T094. (NFR-006; NFR-012; AC-031)
- [ ] T098 [SETUP] Complete clean-host packaging, upgrade/backup/retention/provider guides and release compatibility/evidence manifest; preserve unsupported/M5 limitations and exact dependency identities. Document and smoke-test native installation, start, browser connection, stop, update, backup and recovery on both supported OS families. Declare optional systemd/Windows-service installation separately; package the native launcher and explain OS-specific provider gaps without silently recommending WSL as required. Paths: `docs/user/`, `docs/providers/`, `docs/releases/studio-1.0.md`, `scripts/package_studio.py`. Depends on: T095, T096, T097, T081. (NFR-003; NFR-004; NFR-009; NFR-010; NFR-012; AC-029; AC-032)
- [ ] T099 [SETUP] Perform a separate read-only architecture/requirements/security/evidence review; record findings before repairs, then retest only affected behaviour and dependencies on the successor candidate. Audit the native Linux/Windows evidence matrix, platform path/process/security cases, package locks and provider-specific OS claims. Paths: `evidence/studio/M4-review/`. Depends on: T098. (NFR-001; NFR-002; NFR-003; NFR-004; NFR-005; NFR-006; NFR-007; NFR-008; NFR-009; NFR-010; NFR-011; NFR-012; AC-001; AC-002; AC-003; AC-006; AC-007; AC-008; AC-009; AC-010; AC-011; AC-013; AC-014; AC-019; AC-020; AC-021; AC-022; AC-023; AC-024; AC-025; AC-026; AC-027; AC-028; AC-029; AC-030; AC-031; AC-032)
- [ ] T100 [SETUP] Assemble the exact-candidate M0–M4 acceptance dossier with all measured success criteria, tasks/evidence traceability and remaining dependencies; report truthful completion and release scope for review. Require both native-platform core smoke/packaging results and explicit per-OS provider availability in the release dossier; browser-only Windows access or WSL execution cannot satisfy native Windows backend support. Paths: `evidence/studio/release/`, `docs/releases/studio-1.0.md`. Depends on: T040, T069, T081, T095, T096, T097, T098, T099. (NFR-010; NFR-012; AC-001; AC-002; AC-003; AC-004; AC-005; AC-006; AC-007; AC-008; AC-009; AC-010; AC-011; AC-012; AC-013; AC-014; AC-015; AC-016; AC-017; AC-018; AC-019; AC-020; AC-021; AC-022; AC-023; AC-024; AC-025; AC-026; AC-027; AC-028; AC-029; AC-030; AC-031; AC-032)

## Completion and handoff

Run the repository specification validator whenever IDs, mappings or dependencies change. At the end of each implementation session, record completed task IDs, exact changed files, executed verification, actual outcomes, pending dependencies and the next ready task. Preserve the complete plan rather than regenerating a new specification from a shortened prompt.

The final task assembles a reviewable release dossier; it does not authorize unsupported hardware actions, publish a service, mutate another repository or claim external standards compliance. The existing user-authorized scope and actual provider permissions determine permitted actions.

## Current implementation evidence

See [current status](../../docs/implementation/STATUS.md) and each task’s `implementation_evidence` / `implementation_note` in traceability.json. Component completion does not imply a milestone release. Hardware, live providers, native Windows and first-time-user measurements retain their own gates.

Windows installation and test obligations are explicitly **BLOCKED at user request**. The Linux lane continues; original Windows install failure evidence is retained and the CI matrix excludes Windows until resumed.

T039/T098 progress: private stopped-root full backup/verify/restore preserves original source, snapshots
and journals, refuses unsettled execution/corruption/overwrite, and invalidates restored sessions.
Twenty-three Linux component/native subprocess checks passed; see
`evidence/studio/M0-full-recovery/focused-verification.json` and ADR-0006. Independent review and final
candidate checks remain open. Both task checkboxes remain unchecked; this does not close AC-032.

T044 reopened after the selected-resource navigation review finding: source inspection exists, but the
selected declaration is not yet opened reliably. Repair and browser verification are in progress; see
`evidence/studio/M2-neutral-assets/root-review.md`.

Further Linux component progress (checkboxes retain their full task scope): T049/T051/T052 now have
neutral Device/Sensor/Actuator/Model source and browser authoring evidence; T082/T083/T084 include
typed Scenario conditions/steps/fault intent/observers/metrics with independent profile-reference and
deep-input repairs. T092/T094 include explicit project/run/artifact-registration retention: 50 focused
tests and separate dependency/bounded-I/O/commit/recovery probes passed. Exact evidence paths and
remaining gates are recorded in traceability.json. Shared secure file acquisition is under repair after
the full-backup and project-reader ancestor-race findings; full candidate verification is pending.

Current cohort verification: 350 backend tests and nine Playwright checks passed, including 30-repetition
performance workloads. Prepared-cache offline fresh-package provisioning/start/persistence/compiler
smoke passed. T022 and T092 are component-complete after independent literal-scope audits; T044
review repairs are verified and its checkbox is restored. T094 remains open for FR-062 claim-status
preservation, not optional campaign/snapshot garbage collection. All M0–M4 acceptance gates retain
their unmet native/live/hardware/usability obligations. See `evidence/studio/release/linux-cohort-2026-10-25/`.

T020 component completion: readiness 1.0 now renders independent dimensions, exact affected refs,
limits and remediation plus frozen compiled-plan inspection. Four final native Linux browser/display
checks passed after the visual disclosure repair; see `evidence/studio/M1-readiness/final/verification.json`.
T018/T019 retain explicit remaining admission-matrix and integration gates in traceability.json.

T094 component completion: annotation sidecar 1.1 preserves reported claim status and exact frozen
subjects without changing the assertion v1 contract. Twenty-nine focused backend checks, native
trace exchange and the two-check context-switch/delayed-refresh successor passed. The snapshot display
route now reuses bounded canonical acquisition (13 reader/rerun checks plus independent successor).
Retention evidence remains applicable. Full M4 and native/live acceptance remain open; see
`evidence/studio/M4-trace-claims/` and traceability.json.

Final readiness/claim candidate 180d026: 393 backend tests and 15 combined browser checks passed
on unchanged source, with 30-repetition performance checks and a clean committed-package offline
installation/startup/persistence/compilation smoke. Seventeen task components are complete; all five
milestone acceptance gates remain open. See `evidence/studio/release/linux-readiness-claims-2026-10-25/cohort-summary.json`.

T018/T019 component completion: the complete owned admission file passed 30 checks after the partial
artifact-binding fact repair. Independent literal review confirms the specified matrix and immediate
effective-input readmission. Evidence: `evidence/studio/M1-readiness/T018-successor/`. This raises
component completion to 19/100; Windows, admitted live integrations and all milestone gates stay open.

T029/T030 owned components are complete after the 466-test backend and 21-check browser/performance
cohort on unchanged source, with independent reader/UI review. Component completion is 21/100.
T028 remains open for explicit restriction/private-log and advancing-producer/slow-consumer gap
fixtures; T026 expired-cursor resynchronization remains open. These concrete software obligations
are not hidden behind Windows/hardware blockers. See `evidence/studio/release/linux-evidence-query-2026-10-25/`.

Clean product candidate 829d428 additionally passed prepared-cache offline package installation,
startup, browser-index serving, Unicode persistence and public compilation. Its 86-file clean manifest
and archive digest are retained with the final466/21 cohort; publication/CI outcomes are separate.

T028 owned fixture component is complete after explicit private-log exclusion and advancing-producer/
slow-consumer evidence, 28 focused stream cases and 493 full backend tests on unchanged backend source,
with independent literal review. Component completion is 22/100. T026 remains open: current focused
browser successor is 18 passed/4 failed; the full browser/performance gate has not passed. Both early
modal-input cases and reserved-control-slot boundaries have successor proof; creation/input/screenshot
latencies and the native expiry timing window remain recorded failures under observed host I/O stalls.
T025/T027 retain their concrete pending receipt/control-operation/failure-view obligations. See
`evidence/studio/release/linux-stream-recovery-2026-10-25/candidate-verification.json`. No milestone
or Windows/physical/live-provider acceptance is claimed.

Control receipts successor: fresh-host push CI for fb8ddb6 failed the native expiry check because one
history read raced a journal append; bounded reader re-acquisition repairs it. Durable Start/Stop/Cancel
receipts, two-tab/lost-ack/close-reopen browser cases, a canonical accepted-command `command.failed`
producer, capability-aware controls and operation/ownership views are implemented with independent
review. 499 backend tests and the 44-check Linux browser/performance gate pass. T025/T026/T027 stay
open (both-native repetition, T025 dependency, AC environment clauses); completion remains 22/100. See
`evidence/studio/M1-control-receipts/`.

T031/T032 owned components are complete: evidence-linked explanation 1.0 for runs and preflights keeps
facts, consequences, unconfirmed hypotheses, unknowns and closed next actions separate, with no-traffic
ambiguity and liveness-only health. Independent review found nine defects, all repaired; 531 backend
tests and 47 browser/performance checks pass on an unchanged candidate. Component completion is 24/100.
Live failure repetition, communication-link loss from an admitted provider and AC environment clauses
remain open. See `evidence/studio/M1-diagnostics/`.

T045/T046 owned components are complete: revision records with verified content copies, graph undo/redo
as continuity-checked restore transactions, explicit recovery that preserves changed or unreadable
sources and sidecars first, and bounded per-tab autosave. Independent review found six defects, all
repaired; 547 backend tests and 51 browser/performance checks pass on an unchanged candidate. Component
completion is 26/100. Per-platform locking/case behavior and Windows exchange remain T048. See
`evidence/studio/M2-revisions/`.

T043 owned component is complete: node-placement grouping as a keyboard tree, presentation-only canvas
frames and node-aware layout, named ports, and System › node › element › definition drill-down.
Independent review found eight defects and the first full run two browser regressions, all repaired;
547 backend tests and 54 browser/performance checks pass. Component completion is 27/100. See
`evidence/studio/M2-structure/`.

T051 owned component is complete: an instance wizard keeps definition, identity, role/placement, typed
configuration and realization separate and commits existing XDL kinds atomically through `add_element`
and the new `add_binding` edit. Independent review found seven defects, all repaired; 567 backend tests
and 56 browser/performance checks pass. Component completion is 28/100. See `evidence/studio/M2-wizard/`.

T052 owned verification is complete: representative controller, neutral service, device/sensor/
actuator/model and observer creation; malformed artifact versions and non-admitted XDL versions; and
inert implementation registration without build, flash, execution, file changes or origin requests.
Four silently ignored HTML input patterns were repaired with a guard test. 575 backend tests and 60
browser/performance checks pass. Component completion is 29/100. See `evidence/studio/M2-catalog/`.

T047 owned component is complete: the draft revision and the selected run's immutable snapshot are
shown together with a divergence comparison of the executed run inputs, navigation to elements, draft
sources and verified frozen inputs, and canvas badges. Independent review found six defects, all
repaired; 575 backend tests and 64 browser/performance checks pass. Component completion is 30/100.
See `evidence/studio/M2-run-overlay/`.

T053 is complete: connection fixtures with declared expected semantics and contract tests. Connection
admission 1.0 (ADR-0014) and the Connections view progress T054/T055, which stay open because no
provider or profile admits converter, causality or coupling contracts. 599 backend tests and 66
browser/performance checks pass. Component completion is 31/100. See `evidence/studio/M2-connections/`.

Later completions (2026-10-26):
- **T015, T061:** onboarding/import/parameter scenarios and exact profile discovery
  (`evidence/studio/M1-onboarding/`).
- **T016:** project dependency and unresolved-content inspection (`evidence/studio/M1-projects/`).
- **T057:** deployment resolution 1.0 (ADR-0015; `evidence/studio/M2-deployments/`).
- **T054:** owned connection contracts with real execution (ADR-0016;
  `evidence/studio/M2-connection-contracts/`). This supersedes the T053 note above: the reference
  provider now admits a declared linear converter and unit-delay causality that it executes. Coupling
  contracts stay unadmitted.
- **T058, T059:** closed after T054 (`evidence/studio/M2-deployments/`,
  `evidence/studio/M2-deployment-forms/`).
- **T055:** flow-contract form and relations by kind (`evidence/studio/M2-relations/`).
- **T056:** declared, resolved and observed communication projections
  (`evidence/studio/M2-communication/`).
- **T062:** owned inert domain presentation (ADR-0017; `evidence/studio/M2-profile-presentation/`).
- **T063:** profile and architecture checks with dependency direction (`evidence/studio/M2-profiles/`).
- **T070:** physical-provider contract fixtures, independently audited with six detected mutations
  and passing controls (`evidence/studio/M3-physical-contracts/`); 776 backend and 75 browser/performance
  checks pass. Fixture task complete; live physical acceptance remains blocked.

The current count is in `traceability.json`.

T049 and T060 are complete: catalog/wizard and profile contract cases with fixtures. Review found
several first-draft tests passing for unrelated reasons; they were rewritten, and preflight now
reports unadmitted (`PROFILE_UNRESOLVED`) and redefined (`PROFILE_CONFLICT`) authored profiles.
618 backend tests and 66 browser/performance checks pass. Component completion is 33/100. See
`evidence/studio/M2-profiles-catalog/`.

Linux-only partial checkpoint (2026-10-26): T038/T067 now retain separate 1024×768 and 1440×900
keyboard/focus/status journeys and passing 30-repetition canvas/history distributions
(`evidence/studio/M1-operability/`, `M2-operability/`). T023's executed Linux recovery cases and
remaining direct regression gaps are mapped in `M1-linux-reconciliation/`; T001's installed XDL
checksums match the selected baseline (`M0-linux-baseline/`). All four tasks stay unchecked; native
Windows remains held and no acceptance gate is inferred from these partial results.

M3 owned successor (2026-10-26): T072's read-only canonical inventory/binding observations
(ADR-0018) and T076's hybrid substitution/loss fixtures are complete. Independent reviews,
mutation controls and the unchanged 851-backend / 77-browser-performance cohort are retained in
`evidence/studio/M3-assets/`, `M3-hybrid-contracts/`. T073 has stronger registry failure/restart
fixtures but stays open for positive HTTP authority; T074 is behind Windows-held T023. T023's
three direct identity/shutdown fixture gaps are repaired, with native Windows still open.
Both CI failures on abd5acc are retained: duplicate project names exposed a retention-test selector
assumption; the successor scopes actions by exact project ID and passes the full regression.
Component completion is 47/100; no milestone is accepted.

Committed b2cf71a passed both native Ubuntu 24.04 CI jobs and a clean local package extraction smoke.
The latter uses resolved physical cache/tool/temp paths; failed logical-symlink-path attempts and
successful controls with both Python interpreter choices are retained in `M3-assets/package/`.

Linux diagnostic operability successor (2026-10-26): T038/T067 remain unchecked. Eight native
Tab/Enter journeys at both required viewports now verify real source-error recovery, recorded
clock/gap/partial-evidence diagnostics, actual stale-plan Recheck and held-response navigation;
artifact/lost-ownership/failed-cleanup transport fixtures are explicitly labeled. Repaired contrast,
lost diagnostic focus, stale Start/Recheck and obsolete readiness response handling. All 26 selected
text pairs pass the scoped 4.5:1 check (minimum 4.5919), and the final full 85-check browser successor
passes with unchanged source. Backend/services/scripts/Python tests are byte-identical to the passing
851-test b2cf71a cohort, not rerun here. Separate final-source viewport performance refresh and
independent review are retained in `evidence/studio/M1-accessible-diagnostics/`. Native Windows,
assistive-technology and complete accessibility acceptance remain open; component count stays 47/100.
Clean product commit e6c9de0 passed a fresh offline Linux package extraction with the tested frontend,
native startup/UI, Unicode persistence and authoritative compilation; receipt and clean 98-file
manifest are under `M1-accessible-diagnostics/package/`. Fresh-host CI remains a separate outcome.

Linux shell operability successor (2026-10-26): T038/T067 stay unchecked. Four native keyboard
journeys at both required viewports verify actual login HTTP 401 feedback/association and edit recovery,
all navigation destinations/current state, labelled project creation/Escape focus return and real
busy-response observation. Fixed 18/24 initial selected text contrast failures, navigation semantics,
login descriptions/invalid state and a real layout defect that pushed focused Settings below the
viewport on tall Environment content. All 24 selected shell text pairs pass (minimum 4.5204), and the
full 89-check browser successor passes unchanged source. Independent review and original failures
are retained in `evidence/studio/M1-shell-operability/`. Backend 851 is inherited byte-identically,
not rerun here. Windows, actual assistive-technology and full accessibility acceptance remain open.
Final shell-source performance refresh passed: 30 repetitions after one warm-up per viewport,
selection p95 27.9/27.1 ms, open-validation 1679.4/1780.1 ms and history 446.6/447.1 ms. Raw distributions
and authoritative model validation outcomes are retained separately. Both earlier e6c9de0 product
CI jobs and c4e31f6 metadata CI jobs passed; they predate this shell source.
Clean shell product 944a875 passed fresh offline native Linux package extraction, startup/UI, Unicode
persistence, authoritative compilation and owned shutdown; receipt/clean 98-file manifest and tested
frontend byte comparison are in `M1-shell-operability/package/`. Fresh-host CI is recorded separately.

T001 descriptive baseline successor (2026-10-26): added the plan-required
`config/platform-compatibility.json`, with selected immutable source/package/schema/lock identities,
actual limits and separate descriptor/native-host evidence. The live compatibility set stays null;
Windows is held, its owned I/O gap is source-inspected, and SADS allocation claims no satisfaction.
The contributor gate now checks recorded facts against fixed installed/source/evidence inputs without
provider operations or runtime authority. Independent review's missing/failed-receipt guard was repaired;
18 controlled rejections and 18 restored controls pass. Evidence: `M0-compatibility-manifest/`. T001
remains unchecked and component completion remains 47/100, with no milestone accepted.
The fresh unchanged-source contributor gate passed 851 backend tests plus baseline consistency,
architecture and spec structure. Prior 89 browser checks and compiled UI bytes remain applicable by
exact unchanged-source comparison; no browser rerun is claimed for this descriptive artifact.
Clean 13ff409 passed fresh offline native Linux package extraction, startup/UI, Unicode persistence,
authoritative compilation and owned shutdown. Its clean 100-file manifest includes the descriptive
baseline and checker; archive hashes and tested UI bytes were verified. See the dossier's package/.

Linux wizard/history successor (2026-10-26): T038/T067 stay unchecked. Eight native keyboard
journeys at both viewports verify definition/identity/placement/realization choices, one atomic
instance+binding transaction, unchanged reusable definition bytes, exact source Undo/Redo through
Enter and toolbar shortcuts, and authoritative validation without a run. Repaired focus loss and
late history completion reopening a departed project or replacing a newer tab head; counterchecks
retain deliberately moved focus and a newer same-project edit. ADR-0013 documents the client
completion amendment. All 97 full browser checks and the separate final-source performance refresh
pass unchanged source; 851 backend tests are inherited through exact unchanged-source comparison,
not rerun here. Raw results/reviews/failures are in `evidence/studio/M2-keyboard-instance/`. Native
Windows and complete accessibility/assistive-technology acceptance remain open; count stays 47/100.
Clean 70a13a1 passed the fresh offline native Linux package smoke: startup/UI, Unicode persistence,
public compilation and owned shutdown. All archive/file hashes, clean 100-file manifest and tested
frontend bytes are verified under `M2-keyboard-instance/package/`. Fresh-host CI remains separate.

Linux keyboard connection successor (2026-10-26): T038/T067 stay unchecked. Two keyboard journeys
at both required viewports reproduce and repair browser/backend flow-ID grammar drift, with
associated instructions/native constraint focus, independent backend HTTP 422 rejection, exact
successful edit/revision, complete topology and other-document preservation, authoritative
validation and unchanged project run set. Full 99 browser checks pass unchanged runtime; the
review-added complete-flow assertion passes both final focused checks, with exact test-only
equivalence proof. Final-source two-viewport performance refresh passes. Windows, actual
assistive-technology assessment and full acceptance stay open.
Evidence: `evidence/studio/M2-keyboard-connections/`; component count 47/100, no milestone accepted.
Clean e76b969 package smoke also passes; clean 100-file manifest, archive/file hashes and tested UI
bytes are verified under `M2-keyboard-connections/package/`. Native Windows remains held.

Linux keyboard deployment successor (2026-10-26): T038/T067 stay unchecked. Eighteen keyboard
journeys at both viewports verify clone/resource/time-mapping authoring and removal, exact four
successful revisions/requests, complete intended clone spec and unchanged original document
bytes, authoritative validation and no new run. Repairs stop late Home reopening/selection
replacement, restore removal focus and preserve newer heads, moved focus and changed variants.
Review-reproduced explicit-selection fallback and same-revision readiness dismissal are repaired.
Final 117 browser checks and separate performance refresh pass unchanged source; backend 851 is
inherited by exact unchanged-input proof. Extra declaration fixtures establish no runtime,
reservation or clock-accuracy support; the ready lane uses the exact admitted reference. Windows,
actual assistive-technology assessment and full acceptance remain open.
Evidence: `evidence/studio/M2-keyboard-deployment/`; count 47/100, no milestone accepted.
T057/T058/T059 component traces also retain the ADR-0015 client-completion amendment and final
regression; their completed component status is unchanged.
Clean 1c8e937 package smoke passes; clean 100-file manifest, archive/file hashes and tested UI
bytes are verified under `M2-keyboard-deployment/package/`. Native Windows remains held.

Linux parameter completion successor (2026-10-26): T038/T067 stay unchecked. Twenty-eight keyboard
checks at both required viewports verify native range recovery, typed authoritative save,
current acknowledgement/focus, newer/reverted/other-field draft preservation, current/departed
real stale failures, same-value numeric normalization, project isolation, delayed presentation
regrouping/focus, exact newer readiness ID and unchanged newer history. Full 145-check browser
and separate performance pass unchanged application/test source. ADR-0013 records generic
completion and field generations. Backend 851 is inherited by exact unchanged-input proof.
No live mutation/Start; Windows, actual assistive-technology and full acceptance remain open.
Evidence: `evidence/studio/M1-keyboard-parameters/`; count 47/100, no milestone accepted.
T015/T017/T042/T045/T062 component traces retain the ADR-0013 amendment without changing their
completed statuses.

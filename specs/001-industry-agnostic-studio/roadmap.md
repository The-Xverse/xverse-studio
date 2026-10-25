# Delivery roadmap

**Feature:** `001-industry-agnostic-studio`\
**Status:** planned; no runtime or user-study evidence is supplied by this package.\
**Scope:** M0–M4 are the implementation baseline. M5 is a separately scoped future backlog.

Milestones are dependency and acceptance boundaries, not calendar estimates. Implement the next ready task, retain the outcome and continue independent work when an external dependency blocks one path. A mock provider can validate a Studio contract; it cannot satisfy a live-provider, hardware, or cross-industry execution claim.

## M0 — Foundation and contracts

Establish a browser-based application and local control service that run natively on both Linux and Windows, authoritative XDL integration, capability negotiation, project persistence, security boundaries, and an explicit Lite compatibility adapter contract. Record exact supported Linux distribution/release, Windows edition/release, architecture, browser and language-runtime versions in the platform-support matrix. Record platform, compatibility and blueprint revisions, package identities, supported profiles, runtime limits and integration authority. Studio's OS support and each simulator/device/provider's OS support are separate capabilities.

The inspected rc.1 record's trusted-host execution path does not establish a public generic Studio service. Inspect the actual selected successor baseline and determine whether an admitted supported wrapper exists. If absent, record the missing contract and the required owner/repository change as an external dependency. Implement and verify the Studio-facing contract with owned fixtures while the real integration remains unavailable. A wrapper that generates its own XDL must expose its effective inputs/plan for comparison with the requested immutable snapshot; unsupported edits stay unexecutable until a compatible configuration-input contract exists. Do not import private runtime internals, broaden permits, or modify another repository to make a green demo.

**Exit:** project data and UI layout remain separate; native Linux and Windows dependency/build/contract lanes are established; validation/compilation agrees with the selected platform library; capability and security contracts pass; a dependency register states exactly which provider operations can be exercised on each selected host. Native core support must not silently require Bash, WSL, a VM, Docker or a remote Linux machine.

## M1 — Guided operation / Studio 0.1

Deliver the first complete prepared-example journey: open/import a project, inspect and edit supported parameters, check readiness, start an admitted run, observe its state, stop and inspect cleanup, reconnect, explain failures and examine recorded evidence. Provide useful offline authoring and evidence browsing when no runtime is attached.

The product can be evaluated with an owned reference provider before live integration is available, but the release must identify that scope. M1 requires a native install/start/browser/import/save/reopen/validate/reference-run/cancel/results/reconnect/backend-recovery/clean-stop smoke lane on both Linux and Windows. The backend can be a foreground or launcher-managed background process. OS service-manager registration/autostart is optional and separately verified when offered. The live guided-run acceptance case requires the admitted wrapper and prepared Lite environment; the historical shell-wrapper candidate is Linux-only unless separately verified otherwise. A first-time user study distinguishes setup prerequisite problems from problems operating the prepared example.

**Exit:** both native Studio core smoke lanes pass; successful and deliberately failing supported experiments are interpretable without terminal commands; duplicate requests and refresh do not duplicate runs; failure or missing evidence is never displayed as success. Windows browser access to Linux or execution inside WSL cannot satisfy the native Windows backend lane. An unavailable simulator/provider remains explicitly unavailable on its unsupported OS.

## M2 — Visual composition / Studio 0.2

Add a schema-backed model canvas, source/graph synchronization, catalog, element wizard, typed communication, explicit deployment variants and compatible profile composition. Roles, realizations and placement remain independent. Preserve unknown profile content while blocking unsupported validation/execution.

Demonstrate two independent domains through the same editor and execution contracts. Use the vehicle-loop blueprint plus a deliberately small process-control blueprint with a suitable explicitly admitted provider. Neither an automotive rename nor a second static diagram establishes cross-industry support. A simple reference model is acceptable if its actual implemented scope and fidelity are recorded. New external blueprint/provider changes require their own repository-owned specification and authorization; Studio-owned fixtures can proceed independently.

**Exit:** users can compose, save, reopen and execute supported systems; moving nodes leaves execution semantics unchanged; portable projects exchange in both native Linux/Windows directions without unintended semantic changes; both domain blueprints pass their declared checks without domain branches in the Studio core. Record each live provider's actual host support and retain separate native reference/performance results.

## M3 — Hybrid laboratory / Studio 0.3

Add device inventory and explicit binding to a physical asset, capability-aware operation, reservations where required, observation/stimulation separation, clock quality and disconnect handling. Deliver one real supported device/provider combination, identified by actual hardware and firmware evidence.

**Exit:** a compatible physical realization replaces a virtual realization without rebuilding logical topology; operation bounds and exclusive ownership are enforced in the backend; unplug, reservation conflict and cleanup failure produce truthful outcomes. Device/provider admission identifies its supported host OS, architecture and drivers. Missing hardware leaves the hardware cases blocked or not run and prevents a hardware-support claim; a provider supported only on Linux is not thereby advertised on Windows.

## M4 — Experiment management / Studio 1.0

Deliver scenario/stimulus/fault authoring, a bounded and defined assertion evaluator, immutable experiment snapshots, baseline comparison, bounded parameter campaigns, export/import and evidence review. Existing opaque XDL expression strings do not count as an evaluator. New semantics require a versioned Studio experiment contract and an admitted XDL/profile representation.

Complete performance, accessibility, operational packaging, migrations, documentation and recovery verification against both native reference environments selected in M0. Use a cross-platform packager and launcher, with OS-aware paths, file locking/replacement, process ownership and stop/recovery behaviour. Document native install/start/stop/update procedures and optional service-manager hooks independently. Release claims identify supported Studio OS versions separately from provider/driver support, capacity and timing envelope, unresolved limitations and exact evidence identities.

**Exit:** the acceptance matrix for M0–M4 is satisfied for the declared release scope; all exceptions remain explicit. Evidence replay and live rerun are separately labelled operations. An implementation task being checked off does not itself accept a release.

## M5 — Future backlog; excluded from the M0–M4 baseline

| ID | Candidate capability | Prerequisite and admission question |
| --- | --- | --- |
| FUT-001 | Distributed execution and remote laboratory access | Durable remote ownership, authentication, transport security, time mapping, partitions and resource arbitration. |
| FUT-002 | Native C++ X-COM tool-gateway inspection and stimulation | Separately admitted core activation/provider and backend IPC bridge; Lite flow evidence is not equivalent. |
| FUT-003 | FMI/FMUs and SSP exchange | Supported versions and model kinds, artifact admission, solver/time contracts, explicit import/export loss report. |
| FUT-004 | SysML, ARXML, DBC and other domain imports | Per-format semantic mapping, supported subset, licenses, unresolved content and round-trip limits. |
| FUT-005 | Continuous physical-model coupling | Provider-owned numerical solver, causality, units, stability/convergence conditions, clocks and capability evidence. Data-flow wires alone do not implement physical coupling. |
| FUT-006 | AI-assisted explanations and model edits | Optional provider, clear provenance, suggested patches, ordinary validation and no independent execution authority. Core workflows remain usable without AI. |
| FUT-007 | Real-time multi-user editing | Conflict model, actor identity, access control, immutable runs and compatible file/external-editor semantics. |
| FUT-008 | Firmware/build pipeline integration | Artifact provenance, trusted builders, target admission and explicit separation between creating a definition and producing an executable. |
| FUT-009 | Large-system federation and advanced analytics | Measured workload demand beyond M4 targets, partitioned views, storage/retention design and query limits. |
| FUT-010 | Shared catalog or public plugin marketplace | Package provenance, trust and admission policy, dependency resolution, distribution permissions and revocation; discovery never grants execution authority. |

Do not silently pull M5 into implementation to resolve a dependency. Open a successor feature proposal with its own acceptance scope instead. Conversely, do not advertise an M5 feature because a menu, stub, imported library or mock exists.

## Dependency register to establish in M0

| Dependency | Initial state | Work that remains possible |
| --- | --- | --- |
| Native Linux and Windows build/test hosts and supported toolchain matrix | To establish and record in M0 | Shared contracts and implementation; missing native evidence blocks the corresponding OS-support claim. |
| Exact installed XDL/library and profile compatibility set | To verify against selected revisions | Contract fixtures, UI design and plan review. |
| Supported live-run wrapper and runtime execution permits per provider OS | Not established by this plan; historical shell candidate is Linux-only | Native owned reference provider, offline validation and run-history reader on both supported Studio OS families. |
| CARLA/legacy vehicle blueprint environment | Host-specific; availability not established here | Prepared fixtures and domain-neutral composition. |
| Process-control model/provider and blueprint | New implementation required | Specification and owned reference fixture. |
| Physical device/provider, reservation and allowed stimulation | Not selected; no physical execution authorized by planning | Inventory UI, provider conformance fixtures, negative tests. |
| Executable assertion semantics and XDL/profile mapping | New implementation required | Editor design and evaluator contract tests. |

The implementation agent records an owner only when actually known. It records blocking evidence, next technical action and affected task IDs instead of inferring a person, approval or availability.

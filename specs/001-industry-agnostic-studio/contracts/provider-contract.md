# Studio provider facade contract v1

**Status**: planned integration boundary. It adapts admitted platform/provider contracts; it does not confer execution authority or replace Maestro.

## Descriptor and admission

Each provider publishes an immutable descriptor with `providerId`, `providerVersion`, `contractVersion`, implementation identity/digest, provenance, supported XDL/profile versions, realization classes, target classes, supported host OS/architectures, external dependencies, capabilities, limits and evidence scope. An adapter's descriptor names the underlying runtime identity and compatibility-set digest. Studio runs natively on Linux and Windows; provider support is admitted separately for each host combination. Unsupported combinations return a diagnostic, never silently install/use WSL or a container.

Capabilities are scoped records, not a single boolean list. Each operation specifies target class, legal lifecycle states, typed parameters, authority requirements, maximum duration, observable completion, failure semantics and whether it can affect the physical environment. Time capabilities state clock domains, ownership of advancement, pause/step availability, synchronization requirements and uncertainty reporting. Observation capabilities state schema, retention/throughput bounds, possible perturbation and canonical evidence support.

Admission verifies descriptor/schema compatibility, pinned implementation identity, explicit installation, required dependencies and conformance evidence. A project/profile may reference a provider but may not install or execute it. Imported endpoints remain uncontacted until an admitted, explicitly scoped probe is requested.

## Operations

| Operation | Contract |
|---|---|
| `describe()` | Return descriptor and current availability; no workload start. |
| `validate_binding(binding, snapshot)` | Static contract check; no external side effect. |
| `probe(binding, scope, deadline)` | Bounded admitted readiness observation; declares contacted resources and observation scope. |
| `reserve(asset, scope, owner, deadline)` | Return unique lease/fencing identity or typed conflict; does not imply start authority. |
| `renew(reservation_ref, expected_fencing_identity, requested_deadline, authority)` | Backend-owned bounded renewal within the existing scope; reject stale/expired/unknown authority, and never silently reacquire an asset or widen permission. |
| `inspect_reservation(reservation_ref)` | ADR-0024 amendment: bounded ownership observation for the original installed provider/asset/owner/fence; missing acknowledgement remains unknown and never authorizes reacquisition. |
| `prepare(run_id, operation_id, snapshot, authority)` | Prepare through existing ownership/permit mechanisms; return typed ownership reference and evidence. |
| `start(run_id, operation_id, prepared_ref)` | Start at most once for that operation; return acknowledged state or unknown, never invented success. |
| `command(run_id, operation_id, expected_state, command)` | Apply only supported operation with current authority; preserve cancellation/cleanup semantics. |
| `inspect(run_id, ownership_ref)` | Return observed lifecycle/ownership, raw provider state and timestamps; missing evidence is unknown. |
| `reconcile(run_id, operation_id, ownership_ref)` | Resolve accepted/delegated operations after backend restart without blindly repeating actions. |
| `read_events(run_id, cursor)` | Bounded incremental stream with source identity, sequence/gaps and canonical evidence refs. |
| `read_evidence(run_id, scope)` | Read original evidence through its authoritative reader; retain integrity verdict. |
| `release(reservation_ref, authority)` | Release only owned resources, reporting remaining or unknown state explicitly. |

These are conceptual callable contracts; implementation may use in-process calls or protected local IPC with a tested implementation for the host OS. A remote transport or Unix-domain socket on Windows is not implied. No API accepts arbitrary command-line strings, executable paths from the browser, unrestricted environment overrides or unrestricted process identifiers. Launchers use argument vectors, explicit working directories and declared environment variables through native host adapters. Process groups/signals on Linux and ownership/termination handles on Windows are tested independently; a PID alone is not authority.

## Integration classes

- **Owned fixture provider:** portable deterministic small workloads and controlled failures for native Linux/Windows conformance tests. Display `fixture` evidence scope. It cannot establish legacy, simulator or physical-device integration claims.
- **Lite runtime adapter:** on its supported Linux host, the first integration candidate is a fixed-argv wrapper of the documented `automotive/thesis-lite-carla-closed-loop/run-live.sh` harness, using a pinned executable path, closed case enum and backend-owned output directory. An admitted successor platform service is an alternative. A native Windows provider requires its own admitted launcher/contract; the Bash harness is not assumed portable. Neither exposes arbitrary shell commands. The inspected rc.1 trusted-host/private runtime path is not a generic public API; no web handler imports it. If an admitted wrapper/API is absent, this provider remains unavailable for that host and DEP-RUN is recorded.
- **Physical asset provider:** binds logical devices to identified assets. Observe-only and stimulation scopes are separate. Requires declared ownership, firmware/version observations where supported, connection-loss policy and shutdown/cleanup semantics.
- **Model provider:** declares model format, input/output contracts, fidelity, step/time behaviour and supported coupling semantics. It does not imply a general-purpose solver.

Native X-COM integration requires its own adapter admission. Browser callers never connect directly to its protected gateway or bypass communication activation plans.

### Effective-input identity for the Lite candidate

The inspected harness constructs XDL internally with `build_documents`. A fixed preset launch cannot claim to execute arbitrary GUI XDL or changed parameters. Before admission, the adapter must expose the effective generated inputs/compiled plan without launching the workload and prove equality with the requested snapshot's semantic and plan identities. After launch it records the actual effective identities and rejects/flags any disagreement; a post-run mismatch cannot retroactively validate the run.

Only explicitly mapped, schema-validated configuration fields may reach a launcher. Unsupported changes reject before launch. If the current harness cannot expose effective inputs safely before launch or cannot consume selected configuration, record DEP-RUN-CONFIG and require an admitted successor input contract. M1 edited-parameter/live acceptance remains blocked; a nominal fixed preset or owned fixture does not close that requirement. Newer repository heads must be inspected before choosing the actual integration, rather than assuming rc.1 limitations still apply.

## Ownership and restart invariants

The provider/runtime remains the authority for processes, simulator tick ownership, device access and controlled stimulation. Studio persists references and reconciles them; it does not infer ownership from an address. One exclusive resource cannot be held by two incompatible reservations. Stale fencing tokens reject control.

The backend schedules renewals from provider-declared lease timing and persists outcomes. Browser disconnect does not stop renewal for an active backend-owned run. Renewal failure/expiry/unknown state immediately disables new active commands and invokes only the previously admitted ownership-loss policy. Renewal cannot extend beyond permitted scope or a run's authority budget; a new wider reservation requires a new explicit operation. Reconciliation never silently reacquires an expired reservation.

Browser disconnect leaves the backend-owned run active unless the frozen run policy explicitly states another supported behaviour. Backend restart first marks affected run projections `reconciling`; it queries actual authority and recorded operation IDs. Unknown state remains `unknown`. Automatic restart/recovery may only follow a provider capability and a previously declared policy, with observable evidence.

After stop/cancel, report each resource's release state. A run may be terminal with `cleanup=failed|unknown`; hide neither orphan processes nor attached physical assets. Releasing an expired reservation must not modify another owner's newer reservation.

## Error and maturity envelope

Every failure returns stable `code`, `retryable`, `operationId`, target reference, observed state, evidence references, and a safe user explanation. Retryability describes the operation's documented semantics; it does not authorize an automatic retry with a new operation ID. Preserve the underlying diagnostic code in `providerDetails` after redaction.

Supported maturity values distinguish `fixture`, `prototype`, `admitted_integration`, and `unavailable`; evidence references qualify their scope. `admitted_integration` is a Studio compatibility status, not a safety certification or proof of domain fidelity.

## Conformance suite

Test static validation without side effects; unauthorized/unsupported operations; at-most-once start; duplicate and conflicting operation IDs; stale state/lease tokens; partial prepare/start; readiness timeout; lost acknowledgement; browser loss; backend crash and reconciliation; event gaps; capability changes invalidating preflight; stop with incomplete cleanup; device disappearance/replacement; and evidence reader failure. Tests use the owned fixture on native Linux and Windows first, including paths with spaces/Unicode and OS-specific child ownership/termination. Real integrations repeat applicable cases on their exact admitted environment and record untestable cases explicitly.

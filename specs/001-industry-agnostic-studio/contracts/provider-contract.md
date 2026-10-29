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

ADR-0027 adds an explicit observe-only Studio facade for the existing conceptual
probe operation. A separate native installation and exact observation permission
are mandatory; neither a reservation scope nor method presence authorizes contact.
Its result remains an observation, separate from readiness/admission, ownership
and physical commands. Original lease installation descriptors are unchanged.
See [observation-service.md](../../../docs/providers/observation-service.md) for the
closed callback projection, original clock metadata and bounds. This amendment
does not admit a physical provider or establish actual hardware acceptance.

## Integration classes

- **Owned fixture provider:** portable deterministic small workloads and controlled failures for native Linux/Windows conformance tests. Display `fixture` evidence scope. It cannot establish legacy, simulator or physical-device integration claims.
- **Lite runtime adapter:** on its supported Linux host, the first integration candidate is a fixed-argv wrapper of the documented `automotive/thesis-lite-carla-closed-loop/run-live.sh` harness, using a pinned executable path, closed case enum and backend-owned output directory. An admitted successor platform service is an alternative. A native Windows provider requires its own admitted launcher/contract; the Bash harness is not assumed portable. Neither exposes arbitrary shell commands. The inspected rc.1 trusted-host/private runtime path is not a generic public API; no web handler imports it. If an admitted wrapper/API is absent, this provider remains unavailable for that host and DEP-RUN is recorded.
- **Physical asset provider:** binds logical devices to identified assets. Observe-only and stimulation scopes are separate. Requires declared ownership, firmware/version observations where supported, connection-loss policy and shutdown/cleanup semantics.
- **Model provider:** declares model format, input/output contracts, fidelity, step/time behaviour and supported coupling semantics. It does not imply a general-purpose solver.

Native X-COM integration requires its own adapter admission. Browser callers never connect directly to its protected gateway or bypass communication activation plans.

### Owned live target input (ADR-0030 amendment)

Owned reference 1.2.0 adds the conditional nonphysical `set_parameter` capability
for the exact `io.xverse.studio.reference-controls` 1.0 Profile declaration and
corresponding installed model artifact. Binding the schema alone admits no input.
The input is initialized from the frozen configuration; the XDL parameter and
snapshot are never rewritten. Constant initialization and other inputs reject.
The native XDL mutability enum remains `constant|configuration|scenario`.

The closed parameters object is `{inputId: "target", expectedValue, value}`.
Both numbers must be finite, dimensionless and within [-100,100]. Current owned
authority, running/paused state, expected state version, old-value CAS and one
unsettled command are enforced before dispatch and independently by the signed
worker mailbox. Its maximum is 32 applied changes per run. Application advances
the worker state version at a model-step boundary without changing lifecycle.
Old/new values, time, authority and outcome remain in the durable operation and
canonical completion record. Same-key retry cannot reapply a mutation.
Provider/schema discovery grants no physical effects or external runtime admission.

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

## Native external demo amendment (ADR-0033)

An explicitly enrolled native installation can supply a trusted provider adapter to
Studio's existing run service. Provider registration remains host administration;
XDL/profile/imported metadata never selects Python modules, commands or installation
paths. The Autoverse prototype maps an exact supported canonical blueprint through
public component CLIs and APIs, with independent source/plan revalidation before effects.
It is separate from the unavailable Lite adapter and confers no Maestro, native
X-COM, Argus, physical-device or Windows integration claim.

The adapter binds actual implementation/installation digests, exact container IDs,
image/configuration identities and mounted artifacts. It acquires an exclusive
installation lock, checks stopped/unoccupied resources and records process birth/argv
and container-start identities. Stop/Cancel release only those resources. Canonical
hash-chain evidence remains distinct from native component logs and from functional
observations. Failure to persist state or evidence cannot prevent owned cleanup.
The normalized browser input surface is described in the Studio API amendment;
it cannot pause/reset the external simulator or execute arbitrary project commands.

## Installed backend-owned task lifecycle — ADR-0034

An installed host provider may prepare a native `BackendTask` instead of a new
per-run worker process. Preparation creates no runtime workload. Studio records
its actual backend process birth/argv identity and unique `ownerTaskId` before
starting the callback. `executionKind: backend-task` distinguishes this scope;
the private PID is not a claim that a separate worker process exists. Browser or
profile data cannot nominate this callback or a process identity.

A live backend PID is insufficient: active observations require the original
registered task handle, matching task ID and a nonterminal task result. A missing
or dead task leaves active state/cleanup unknown, including during the startup
grace interval. Historical terminal reports remain historical receipts. Backend
restart never reconstructs task or provider resource handles from a PID or file.
Existing signed command, capability and expected-state-version checks still apply.

The installed platform owner keeps one original public Maestro service for the
backend lifetime and dispatches callbacks by exact run ID. Frozen configurations,
phase attempts, native bridges, observations, permits and resources stay per run.
Its public service ceiling is2700seconds; each permit limits actual execution to
requested driving duration plus900seconds, with60seconds cleanup. Ordinary child
commands retain their run directory as cwd without changing the backend cwd.

Only observed released cleanup plus absence of the original owned child processes
retires a run's callback context and closes its exited stdio handles. Unknown or
contradictory release retains context, reports uncertainty and blocks acquisition.
The SDK's original records are not rewritten if a Studio observation contradicts
a provider receipt. At most128 runs are admitted by an owner; no capacity condition
allocates a fresh root. Shutdown requests existing signed cancellation, waits the
installed provider's bounded budget and closes the service only after original tasks
and contexts settle. It never signals the backend PID as if it were a worker.

A private owner-lifetime marker fences a preceding owner, including re-creation in
the same process. It is diagnostic metadata, not an ownership/recovery receipt.
Existing SDK durable claims remain authoritative fences even if no marker predates
them. `AUTOVERSE_PLATFORM_OWNER_RECOVERY_REQUIRED` explains that retained historical
views remain readable and public recovery is required before another Start. The
ADR-0035 recovery proposal is not an admitted interface. Native Windows support
for Studio core does not imply support for this Linux simulation provider.

# ADR-0015: Deployment resolution over declared requirements

Status: implemented owned components under verification; no M2 acceptance claim.

## Context

FR-039 to FR-042 require four things of deployment variants:

- They are rebound without changing logical identity.
- Compatibility is checked when realization changes.
- Effective parameter values are shown with their source chain, and ambiguity is rejected where no
  precedence is defined.
- Portable intent is kept separate from environment addresses and secret references, and unresolved
  bindings are reported before execution.

The pinned XDL validator checks reference integrity: targets, artifacts, resources, networks and time
domains exist, and a physical binding has an `externalAssetRef`. It does not do the following:

- It treats `parameterValues` on System instances and Deployment bindings as opaque, and defines no
  precedence between them.
- It does not compare Component `artifactRequirements` or `resourceRequirements` with what a binding
  provides.
- It keeps realization class and target class as independent dimensions.

## Decision

Deployment resolution 1.0 (`deployments/resolution.py`) evaluates one selected Deployment of a
structurally valid source set. It is exposed in three places:

- `GET /projects/{projectId}/deployment-variants/{documentId}/resolution?providerId=` (an invalid or
  unparseable source set returns `sourceValid: false` with validator diagnostics);
- the `PATCH` rebinding response, whose `compatibility` includes resolution diagnostics;
- blocking preflight diagnostics.

It only evaluates what declarations state. An undecidable requirement is `unknown`
(`COMPATIBILITY_UNKNOWN`) and blocks execution; it is never a pass. Studio defines no rule the schema
lacks:

- Realization class and target class are `declared` when no provider is selected.
- When a provider is selected, they are checked against that provider's descriptor. Its declared
  `realizationClasses` and `targetClasses` either `pass` or are `unsupported`
  (`CAPABILITY_UNSUPPORTED`). The report carries the provider's maturity and fidelity limitations.
- A hard limit is not compared with capacity.

The route and the rebinding `PATCH` take `providerId`, defaulting to `studio.reference`; preflight
uses the selected provider. An unknown `providerId` returns `404 PROVIDER_UNAVAILABLE`.

Connection compatibility also depends on the provider's declared connection contracts (ADR-0016). The
report therefore carries a `connections` summary for the selected provider:

- the blocking count;
- the admitted contracts;
- the flows that are not admitted;
- the verdict on each cycle.

Rebinding shows those consequences without double-counting preflight's own connection diagnostics.

### Bindings

Each binding gets per-check results:

- **Placement.** Every bound resource must be in the target's `offeredResourceIds`
  (`RESOURCE_NOT_OFFERED`). If the target declares no offered resources, placement is `unknown`.
- **Artifact requirements.** A requirement needs a bound artifact of its `artifactKind`
  (`ARTIFACT_REQUIREMENT_UNMET`).
  - A `versionConstraint` of `*`, or an exact version that is bound, passes.
  - An exact semantic version that is not bound fails.
  - Any other constraint syntax has no admitted evaluator and is `unknown`.
- **Resource requirements.** A requirement needs a bound resource of its `resourceClass`.
  - It passes if any bound capacity in the same unit meets the minimum.
  - If none does and some capacity is in another unit, the result is `unknown`: no unit conversion is
    admitted.
  - Otherwise it fails.

### Time-mapping edit

Deployment time mappings are authored with the `set_time_mapping` semantic edit (a contract
amendment). It adds a mapping, replaces one by its id, or removes one. The authoritative validator
checks the referenced domains.

### Client completion and selection amendment (2026-10-26)

Variant cloning and binding updates already return the full committed Project alongside their
reports; time-mapping edits return that Project directly. The browser applies this authoritative
result without starting another project load from a request's captured navigation closure. It checks
the initiating project/load generation and requires a strictly newer revision than the latest
accepted Project. All Project state assignments update that known head synchronously, including
loads, history and readiness refreshes. An acknowledgement for an already-current revision does not
clear a newer preflight or overwrite its selection. A fresh accepted revision reconciles the tab's
graph history and invalidates earlier readiness; it does not change existing run snapshots.

Completion may update variant selection or local feedback only while the originating mounted
project/variant/provider/Scenario context and selection intent remain current. Late errors from a
departed context are suppressed. Conditional form clearing preserves text entered while a save was
pending. An explicit Deployment selection never falls back to a different sole cached variant while
its metadata is loading; the loading state is announced and its authoring forms wait for the matching
variant. No executable resource identity is inferred from the old selection.

Removing a mapping restores focus to Mapping identifier after the item disappears, provided the
authoring context is unchanged, no modal is active, and focus remains on the initiating button or
BODY. Deliberately moved focus is preserved. This is client completion handling: the mutation,
optimistic-concurrency, validation, resolution and provider-admission contracts above are unchanged.
Authoring a resource binding or clock relation establishes neither reservation nor clock accuracy.

### Deployment constraints

- **Exclusive resources.** An exclusive resource bound by more than one binding fails
  (`RESOURCE_CONFLICT`).
- **Time.**
  - The reference clock is the System default time domain, or its only time domain.
  - A simulator in another domain needs a mapping path to the reference clock, through this
    Deployment's or a matching Scenario's `timeMappings` (`CLOCK_MAPPING_MISSING`).
  - Without a reference clock, an unmapped simulator domain is `unknown`.
  - Mappings are `declared`, since their accuracy is not evaluated; a negative tolerance fails
    (`CLOCK_MAPPING_INVALID`).
- **Networks.** More than one binding for a logical network fails (`NETWORK_BINDING_CONFLICT`). An
  unbound network is `declared`.

### Effective values

For every Component instance, and every bound element that carries values, the chain lists the
definition `default`, the System instance value and the Deployment binding value. Each entry carries its
document and JSON pointer.

- XDL `default` applies only when no value is authored. That is the only ordering Studio applies.
- A single authored value is `overridden` (or `authored` when there is no default).
- Two or more authored values are `ambiguous` (`PRECEDENCE_UNDEFINED`) even when they agree.
- Values follow JSON Schema semantics: an integral number is an `integer`, and `1` equals `1.0`.
  - A mismatched type reports `PARAMETER_INVALID`.
  - Replacing a `constant` default with a different value reports `PARAMETER_IMMUTABLE`.
- A key no definition declares, including any value on a bound non-component element, is
  `unsupported` (`PARAMETER_UNDECLARED`).
- A value with no default and no authored value is `unset` and does not block.
- Scenario parameters of the owned reference profile follow that profile's declared rule: a Scenario
  value replaces the admitted parameter default.

### Portable and private

`portableIntent` lists targets, bindings, resources, time mappings and network bindings. It never
contains asset references, secret references or binding values.

- Every `externalAssetRef` and `secretRefs` entry is listed under `environment` as `unresolved`
  (`BINDING_UNRESOLVED`). Studio admits no environment-binding store and never stores secret values.
- Credential material fails (`SECRET_INLINE`) and is never echoed. It is always redacted wherever it
  is authored: secret references, asset references, and the values in parameter chains. It covers:
  - URI user information (with or without a password);
  - secret-like query or fragment parameters;
  - connection strings such as `password=...`.
- Host-specific paths in artifact `sourceRef`, binding values and target extensions are resolved
  against the backend host OS and the selected provider's `supportedHostOS`. A mismatch fails
  (`HOST_PATH_INCOMPATIBLE`); a match is `declared` as environment-specific. Network shares are
  `declared`.
  - Host paths are Windows drive or UNC paths, `file:` URIs, and absolute POSIX paths under
    conventional filesystem roots. Other slash-separated names, such as topics, are not host paths.

## Consequences

- Studio never reorders values, converts units, rewrites sources or resolves secrets.
- The owned reference provider still refuses any changed placement or topology independently.
- A preserved logical identity never implies behavioural equivalence or fidelity.
- The reference blueprints declare none of these layers, so their readiness is unchanged.

Verification: `tests/integration/test_deployment_variants.py` and `tests/e2e/deployment-resolution.spec.ts`.
The resolution panel, variant comparison and resource/time forms (T059) live in
`apps/studio-web/src/features/deployments/`. The T054 converter/causality contracts and the native Windows host remain open.

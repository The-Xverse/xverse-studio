# Deployment variants: rebinding, constraints, effective values and portable/private bindings (T057; T058 component)

Deployment resolution 1.0 (ADR-0015, `services/studio-api/src/xverse_studio/deployments/resolution.py`)
is exposed in three places:

- `GET /projects/{projectId}/deployment-variants/{documentId}/resolution`;
- the rebinding `PATCH` response;
- blocking preflight diagnostics.

T057: `tests/integration/test_deployment_variants.py`, with the cases added after the existing variant
tests.

- **Compatible rebinding.** Rebinding the plant to an emulator target keeps the System bytes, element
  references and connection references identical. Declared artifact requirements (exact and `*`), the
  resource minimum and placement pass. Readiness is recomputed: the owned reference provider refuses
  the changed placement with its own diagnostic.
- **Incompatible rebinding.** It commits as a draft that names the unmet requirement. Missing artifacts,
  exact-version mismatches and insufficient capacity fail. Range constraints and mixed units are
  `unknown` and block execution; they never pass. Unaffected bindings stay compatible. Realization and
  target class are recorded, not ruled on.
- **Constraints.**
  - Exclusive resources shared by two bindings fail; quota limits are declared.
  - Resources a target doesn't offer fail; a target that declares none is `unknown`.
  - A simulator clock needs a mapping path to the reference clock (transitive mappings accepted).
    Negative tolerances fail, and a missing reference clock is `unknown`.
  - Two bindings for one network conflict.
- **Effective values.** The value chain covers definition default, System instance and Deployment
  binding, each with its document and pointer.
  - A single authored value overrides the default.
  - Two authored values are `PRECEDENCE_UNDEFINED`, even when equal.
  - JSON Schema typing applies, including integral integers and `1 == 1.0` for constants.
  - Undeclared keys, including binding values on non-component elements, are reported.
  - Ambiguity blocks preflight over HTTP.
- **Portable and private.**
  - Portable intent never contains asset references, secret references or binding values.
  - Asset references and secret handles are listed as unresolved environment bindings.
  - Credential material is redacted and fails, wherever it appears: URI user information, secret
    query or fragment parameters, and connection strings in secret references, asset references or
    values.
  - Host paths resolve against Linux, Windows and Darwin hosts and the provider's `supportedHostOS`.
    MQTT-style topics are not treated as paths, and network shares are declared.

T058 remains open. Its declared dependency T054 (admitted converter/causality contracts) is still in
progress, and variant comparison and forms belong to T059. Native Windows is blocked at user request.

## Closure (after T054)

T054 closed with the owned connection contracts (ADR-0016). The resolution report now carries the
selected provider's connection verdicts: blocking count, admitted contracts, flows that are not
admitted, and cycle verdicts. Rebinding therefore shows what a provider change does to the loop and
the converter; `test_resolution_reports_connection_compatibility_for_the_selected_provider` checks it
under both the reference and Lite providers. An unknown provider returns 404. A closure audit found
every T058 clause met. T058 is complete; the current run is recorded in `closure-verification.json`.

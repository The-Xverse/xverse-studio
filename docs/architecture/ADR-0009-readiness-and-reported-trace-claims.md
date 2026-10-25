# ADR-0009: Independent admission facts and reported trace claims

Status: implemented components under focused verification; milestone acceptance remains open.

Preflight previously exposed coarse dimension strings without the facts needed to explain admission.
The additive `readinessVersion: "1.0"` envelope records backend, provider, model, artifacts,
capabilities, target, resources, ownership, clocks and authority independently. Each fact has a status,
message, affected element references, diagnostic codes and remediation. Missing facts remain unknown.
Provider availability requires explicit true observations and actual native OS/architecture matching;
operation scope and declared XDL versions must admit the requested model. Preflight never acquires
equipment, starts a process or asserts runtime health. Limits come from the selected descriptor.

A read-only declared-intent plan preview binds the exact selected revision, snapshot digest, selection,
compiler and plan/semantic digests. Start repeats mutable admission and verifies the canonical frozen
snapshot file against its database record. An unavailable provider cannot retain reference executable
configuration or become executable through campaign creation. Campaign idempotency resolves an
accepted retry or conflicting payload before new mutable admission; a new campaign still requires a
matching originally ready preflight and intact canonical snapshot. Historical evidence is not upgraded.

FR-062 additionally requires preserving externally reported claim status and associations with model
elements, scenarios, assertions and evidence. Annotation sidecar contract 1.1 adds optional
`target.claimStatus`, an opaque nonblank string of at most 256 characters without C0/DEL controls,
and optional `definitionRefs`, up to 32 exact same-run frozen definition ID/digest pairs. Existing
`elementRefs` includes snapshot XDL resources (including Scenario) as well as elements; `evidenceRefs`
continues to identify owned run evidence. Model/definition associations require the intact canonical
snapshot. Comments and unscoped historical links do not unnecessarily require source availability.

An external claim is inert reported metadata, never an assertion verdict, target validation, imported
executable code or evidence of a passed requirement. Legacy targets without claim status remain valid
and keep that absence; the UI reports it as not supplied. Revision replacement, retained history,
tombstones and exchange preserve the reported value verbatim. URI targets are never fetched. Existing
assertion v1 schema, evaluator/profile identities, frozen definitions and canonical run evidence stay
unchanged; annotation history is outside executable identity.

Compatibility: additive HTTP major v1 fields; readiness envelope 1.0 and annotation sidecar 1.1 are
advertised independently. Stable requirement/task IDs and existing stored snapshots remain unchanged.
Affected tasks T018–T020 and T094; FR-008–FR-010/FR-062 and AC-005/AC-029 remain subject to their
full integration/environment acceptance. Findings and successor checks are retained under
`evidence/studio/M1-readiness/` and `evidence/studio/M4-trace-claims/`.

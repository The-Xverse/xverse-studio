# ADR-0002: explicit authored deployment/scenario contributors

Status: implemented for Studio-owned composition; acceptance remains scoped to actual verification.
Date: 2026-10-25. Requirements/tasks/acceptance IDs are unchanged.

The pinned public XDL compiler accepts exactly one contributing System, Scenario and applicable
Deployment. A project may validly author multiple named Deployment/Scenario resources, so compiling
the entire project after adding a variant would yield an ambiguity diagnostic.

Studio first validates the entire explicitly supplied authored resource set with the authoritative
validator. Unresolved/unknown semantics anywhere remain blocked and source bytes are preserved.
An explicit resource selection then names exactly one Scenario and its *authored* Deployment and
System references. Studio supplies those resources and the explicit Component/Profile dependencies
to the same public compiler without rewriting any source. Missing, wrong-kind, ambiguous or mismatched
selection rejects; Studio never substitutes a default preset. New variants author a cloned Deployment
and a matching Scenario transactionally while retaining the existing System/component logical IDs.
If the source Scenario contains named metric dependencies, their original graph and digest/version
pins must validate before cloning. The new authored Scenario updates its own definition references
and recomputes only the cloned dependency pins in metric-first order. Original definitions and pins
remain unchanged; invalid/cyclic source assessments block cloning rather than being silently repaired.

The compilation result includes `contributingDocuments`, resolved `selection` and a
`projectRevisionInputsDigest` over every authored input byte. Runtime snapshots freeze the selected
contributors plus that full-revision identity. Start rechecks the full current authored revision,
then the worker recompiles its exact frozen contributing documents. Draft edits remain separate.

The owned reference model's admission comparison may rename only expected typed Deployment/Scenario
identity references to match the selected authored identities. This comparison does not modify input
bytes, compiled plans, resource digests or plan identities. All bindings, artifacts, topology, clocks,
stimuli and provider-supported semantics still have to match the admitted model contract. Unsupported
rebinding is inspectable authoring intent and remains execution-blocked; identity equivalence alone
never proves behavioural equivalence or physical-provider support.

Compatible profile selection pins exact namespace/version/schema/presentation digests and materializes
their packaged, inert schemas/presentation in the portable envelope. Catalog artifact registration is
metadata only and cannot fetch, build, flash, install or execute an artifact. Profiles, blueprints,
providers and catalog metadata retain separate authority boundaries.

Verification includes full-set authoritative validity, explicit selected CLI/compiler identities,
unchanged logical topology, mismatched selection rejection, failed-binding rollback, immutable profile
locks and inert artifact registration. Windows exchange and external provider variants require their
own native/integration evidence and are not inferred from these owned cases.

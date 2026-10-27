# Hybrid laboratory status

The software contains fixture-tested inventory, scoped action authority, exclusive fencing leases,
renewal/expiry, ownership-loss and clock-quality contracts. The production inventory is empty; the API
refuses physical reservation mutations pending a trusted, durable admitted provider integration.

No physical device was scanned, reserved, connected, stimulated or flashed. Real device discovery,
substitution, disconnect, clock evidence and shutdown acceptance are BLOCKED pending the prerequisites
in `docs/implementation/physical-provider-admission.md`. Fixture tests do not complete AC-021–AC-024.
Windows driver/provider support requires its own native admission; do not infer it from Studio's targets.

Open Laboratory to inspect public inventory observations, metadata, diagnostics and
their completeness. Availability, permission and readiness are separate facts. A
failed or incomplete observation cannot establish that a device is absent.

In a project's Deployment view, choose an authored Deployment and activate **Inspect
physical placements**. The report describes physical/hybrid declarations at the
committed revision, their logical references, required interfaces and observed public
asset metadata. Invalid source is reported separately from an empty binding set.
Ambiguous authored identity cannot select a document for inspection. After a stale
revision refusal, reopen the project and inspect again. Report pages show 50 bindings
at a time from the same captured response; inventory changes require a new inspection.

Inspection does not reserve an asset, contact an endpoint or grant execution permission.
Fixture scope, declared provider OS support and observed metadata do not establish
live hardware support. Canonical source and active runs remain unchanged by inspection.

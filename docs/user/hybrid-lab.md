# Hybrid laboratory status

The software contains fixture-tested inventory, scoped action authority, exclusive fencing leases,
renewal/expiry, ownership-loss and clock-quality contracts. The production inventory is empty; the API
refuses physical reservation mutations pending a trusted, durable admitted provider integration.

No physical device was scanned, reserved, connected, stimulated or flashed. Real device discovery,
substitution, disconnect, clock evidence and shutdown acceptance are BLOCKED pending the prerequisites
in `docs/implementation/physical-provider-admission.md`. Fixture tests do not complete AC-021–AC-024.
Windows driver/provider support requires its own native admission; do not infer it from Studio's targets.

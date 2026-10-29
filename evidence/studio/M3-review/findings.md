# M3 fixture-only review

Date: 2026-10-25. Reviewed explicit provider inventory, fenced reservations,
observe/stimulate authority, lease expiry/recovery, substitution projection,
clock uncertainty and loss/stop outcomes. Fifteen owned in-memory fixture tests
passed on native Linux. Default application inventory is empty and rejects an
unapproved device request with `503 ASSET_UNAVAILABLE` before any effect.

The pure registry exposes provider callbacks and has no implicit discovery or
physical command path. Recovered ownership begins unknown and an expired/stale
lease cannot enable active control. Original source time is retained and missing
clock mapping does not become precise latency. A stop request without observed
physical/cleanup acknowledgement remains unknown.

No actual physical provider is admitted. API reservation mutations deliberately
remain unavailable until a trusted integration supplies durable provider-backed
reservation operations. This is an explicit implementation gap, not a hardware
support claim. See `docs/implementation/physical-provider-admission.md` for exact
missing identity, authority, driver, clock and environment inputs. Native Windows
provider verification is NOT_RUN; actual device cases AC-021–AC-024 are BLOCKED.
M3 is not complete and fixture evidence cannot close its hardware acceptance.

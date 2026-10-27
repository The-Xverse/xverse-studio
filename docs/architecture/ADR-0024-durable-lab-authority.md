# ADR-0024 — Durable reservation operations and explicit host authority

Status: implementation and verification in progress. This does not admit a live
physical provider, complete T073/T074 or accept an M3 milestone.

Date: 2026-10-27.

T073/T074, FR-049/FR-050 and AC-022/AC-023 require API-level exclusive leases,
separate observation/stimulation/destructive permissions, truthful interruption
and fencing. A registry with only an optional persistence callback cannot supply
durable HTTP operation identity. Browser metadata cannot install a provider or
grant physical authority. The full Windows-held T023 dependency and actual-device
admission remain separate gates; authorized offline work continues.

Use the existing SQLite Store for a versioned `lab_registry/leases` snapshot.
Before delegation, persist the principal/route/idempotency mapping, operation and
server-allocated reservation identity; the registry then commits unknown intent
before calling the provider. Save acknowledged ownership separately. Retried keys
return the same operation, while changed payloads conflict. Recovery marks pending
operations and nonterminal leases unknown and never repeats reserve or silently
reacquires. A known fence can be reconciled only against matching provider facts;
a lost initial fence remains unknown. Confirmed terminal history remains terminal.

Pin each lease to the installed descriptor digest, including implementation,
version, contract, host and conformance/authorization references, and to observed
asset identity. A replacement provider or asset cannot inherit the original lease.
Server-owned exact principal/asset grants independently authorize `observe`,
`stimulate` and `destructive`; none implies another. Requests cannot supply an
owner, grant or installation. Current grant, ledger generation and deadline are
checked again inside the bounded provider thread immediately before delegation.
Unknown/expired ownership cannot provide active authority. An owned release for
cleanup does not require a newly active grant. Confirmed terminal cleanup does
not contact a replacement provider or affect a newer owner.

The native host may supply a typed `LabHostConfiguration` containing already
installed provider objects, pinned descriptor and review references, host support
and a separate `LabAuthority`. There is no JSON/config-file loader, HTTP installer,
executable path, network discovery or project-triggered import. The integrator
owns the actual conformance and permission evidence behind these references;
typed configuration is not evidence that hardware acceptance passed. The stock
native launcher supplies no configuration and retains empty/unavailable physical
integration. Restart without installation still exposes durable history as
unknown and refuses provider mutations.

Keep reservation-service discovery separate from runtime readiness. Capabilities
describe the installed lease interfaces and bounds, with fixture scope explicit.
Existing asset/placement observations continue to report unavailable runtime
admission and `activeReady=false`: this slice installs no Maestro physical run
adapter, physical command, automatic active-run renewal or ownership-loss policy.
Those integrations and the T075 reservation UI remain unfinished. No fixture
descriptor or public inventory string grants authority.

Bound storage to 1,000 leases, a 2 MiB ledger, 1,000 lab operations and 8 KiB per
operation. Read lengths before payloads and use revision checks to reject stale
writers. Preserve unknown persisted extensions privately; public lease/operation
views allow only defined fields. Each installed provider has one outstanding
callback, no queue and a host-bounded timeout up to five seconds. A timeout retains
the occupied slot until the actual callback ends; late observations are discarded.
Provider response projections exclude private/unknown fields and unrecognized
error text. This wrapper cannot terminate an already running device operation and
does not certify physical cleanup or hard real-time behavior.

Persistence failure after acknowledgement disables in-memory owned authority.
If recording the final operation fails, read back the exact record to distinguish
a committed result from an uncertain receipt; otherwise expose unknown without
redelegation and retain the durable accepted mapping. Restart does not invent a
successful acknowledgement from an operation receipt.

Private full backup/restore must reject owned or unknown lease snapshots even
when their deadline is in the past: elapsed time is not evidence of provider
release. Reject corrupt, unsupported, duplicate or oversized ledgers before
copying/restoring authority. Released/expired records and unknown payloads can
round-trip without acquiring authority. This extends the existing stopped-root
guard and uses its held-file/ownership protections; no recovery bypass is added.

Amend HTTP v1 with the third independent reservation scope, bounded renewal fence,
and explicit idempotent `POST /reservations/{id}/reconciliations`. The new route
performs only installed provider ownership inspection, never reserve or actuation.
`202` retains its existing meaning of durable acceptance, independently of outcome.

Verification uses owned in-memory providers and real SQLite, actual configured
application routes/session/Origin/CSRF, concurrent clients, restart without replay,
lost acknowledgements, persistence failures, replacement identity and private
backup/restore. Fixture-only successes do not satisfy physical acceptance. Actual
device, driver, permission, clocks, stop/restore evidence, native Windows, human/AT
measurements and independent milestone review remain unverified or blocked.

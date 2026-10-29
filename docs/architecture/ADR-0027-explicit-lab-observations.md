# ADR-0027 — Explicit, separately permitted Lab observations

Status: implemented for owned native Linux fixtures; actual provider, native Windows
and independent milestone acceptance remain open.
Date: 2026-10-28.

## Context

T075 includes explicit connection tests. The provider facade already specifies
`probe(binding, scope, deadline)` and forbids contacting imported endpoints until
an admitted, scoped probe is requested. Inventory, reservation ownership and a
successful observation are different facts. Current observation reservation
grants do not authorize a new provider operation.

Existing lease records hash their installation descriptors. Adding probe methods
or capabilities to those descriptors would invalidate original lease pins. The
stock native launcher must retain empty physical installations and no permissions.

## Decision

Add a separate native `LabProbeConfiguration`, `ProbeInstallation` and
`ProbeAuthority`. Only trusted host Python code supplies installed objects and
exact principal/asset permission to request an observation. Project/profile data,
an object's incidental `probe` attribute and reservation scopes cannot install
or authorize this service. Existing lease descriptors and scope semantics stay
unchanged. Native OS/architecture and pinned implementation/asset identities,
conformance/authorization references and contacted resource references are explicit.
Private binding data stays in native host memory, outside the operation ledger
and public responses. Installation validates and snapshots bounded JSON; it does
not discover an endpoint or call the provider. Host code remains responsible for
reviewing and admitting the actual implementation and its permitted effects.

`GET /assets/{assetId}/probe-options` reads authenticated principal, eligibility
and the separate binding pin without contacting a provider. An explicit authenticated
`POST /assets/{assetId}/probes` requires the current binding digest, an idempotency
key and the sole supported scope, `observe`. Browser-supplied endpoint, owner,
grant, deadline or active scope fields reject. There is no automatic probe during
import, project open, inventory refresh or preflight in this implementation.

Persist the original operation and key mapping transactionally before delegation.
Persist delegated state before provider contact. A duplicate key returns that
original receipt, including after revocation, missing installation or restart;
it never invokes another probe. Changed payloads conflict. Accepted/delegated
records become unknown on restart. There is no automatic retry or reconciliation
that repeats the observation. A new explicit request is a distinct operation.

The service has one outstanding callback per observation provider ID and no queue.
A timed-out callback keeps its slot until it really returns; its late result is
discarded. Check installed binding, exact permission generation and absolute
backend deadline immediately before contact and again before accepting a result.
Revocation cannot undo an already started callback. The host provider retains
responsibility for its device permits, serialization with other native operations,
actual contact identity, perturbation and cancellation/cleanup semantics. The
callback bound cannot terminate or certify a device operation.

Project only closed result fields. Check returned asset identity and actual
contacted resources against the installed pin and declared allowlist. Retain
original signed decimal source ticks, their declared clock/unit and optional
uncertainty separately from backend receipt time. Missing clock/firmware/artifact
metadata stays unknown. `observed`, `unavailable` and `unknown` remain distinct;
completion acknowledges an observation, not readiness, ownership or a verdict.
Runtime admission remains unavailable and physical commands remain empty.

Operation reads enforce ownership, record bounds and a public allowlist. Failed
final persistence yields an unknown receipt unless exact read-back proves the
write committed. No failed write authorizes redelegation. Quotas preserve history
and refuse further work rather than evicting unknown operations.

## Compatibility and verification

This is an additive Studio facade over the existing conceptual probe contract,
not a companion platform API or a new XDL resource. It does not alter canonical
Projects, snapshots, runs, reservations, lease descriptors or executable identity.
See `docs/providers/observation-service.md` for implemented bounds and limits.

Verify default absence, exact independent grants, unchanged lease pins, strict
request shape, actual session/Origin/CSRF enforcement, durable acceptance before
contact, duplicate/conflicting keys, lost acknowledgement/restart, grant/binding
changes, timeout and late completion, invalid identity/resources/clocks,
storage failures, operation ownership/redaction and quota refusal. Repeat affected
reservation/registry/HTTP tests and full backend verification. Native browser cases
exercise explicit requests, unavailable/unknown outcomes, same-key recovery,
unsupported explanations and newer context/focus protection. Labelled malformed
transport and browser-dialog controls remain fixtures. Full combined candidate
verification and clean package binding are still required before promotion.

The browser retains at most one original pending request and 20 operation
references in a versioned, bounded session-storage record (128 KiB). Saved data
never grants authority and contains no private binding or cached result. No POST
retries automatically. Explicit retry retains the exact key, asset, binding and
scope after reload/navigation or uncertain response. Inspection uses owner-checked
GET and never repeats a provider callback. Unreadable saved state blocks new
requests; a failed storage write cannot silently create a new request identity.
Only a typed first-request predelegation refusal can settle its saved attempt;
a refused retry cannot erase an earlier unconfirmed outcome.

Request and eligibility reads have independent lifetime/sequence guards. Newer
navigation, focus, dialog or principal context wins over a late reply. Result/error
focus occurs after the actual React commit. The UI preserves signed source ticks
as strings and separates source clocks/unknown uncertainty, receipt time, metadata,
physical uncertainty and execution readiness. History is limited to this tab's
saved references; the backend operation ledger retains its separately bounded
history and does not delete unknown operations to make room.

Only owned native fixtures are authorized and exercised here. No device/provider,
driver, practical access, permission/clock/stop environment or native Windows
acceptance is established. T074/T075 and AC-021–AC-024 remain open. Fixture success
cannot close actual hardware or independent milestone acceptance.

# ADR-0025 — Reservation observations and explicit browser requests

Status: implemented; fixture verification and acceptance are recorded separately.

## Context

ADR-0024 installs durable reservation operations through typed native-host configuration.
Read-only asset and placement observations deliberately retain unavailable runtime admission.
The browser needs current request eligibility and durable ownership history without treating
inventory strings, an old operation receipt, or a reservation as physical runtime authority.

## Decision

Add versioned authenticated `GET /assets/{assetId}/reservation-options` and cursor-paged
`GET /reservations`. Options observe the current exact principal/asset grants, independently
declared scopes, identity and availability through bounded, explicitly installed inventory.
Eligibility describes a request that can be attempted; it does not promise acquisition.
The mutating service rechecks its authority and provider/fence contract independently.
Options do not reserve, inspect ownership, probe a connection or send physical commands.

History filters the bounded local ledger by the authenticated principal before projecting
records. It returns expiry, original fence, scope, uncertainty and individually available
renew/release/reconcile requests. Reads make no provider call. An elapsed owned deadline
uses the registry's existing expiry transition. Unknown remains unknown; reading does not
reconcile, replay or reacquire. Provider binding changes and grant revocation remove affected
request eligibility; owned cleanup can remain available after grant revocation. All actual
mutations still enforce their full current contract, including asset identity.

Both projections carry contract version, server observation time, principal,
`runtimeAdmission=unavailable` and empty physical commands. Unknown private ledger/provider
payloads remain outside the closed public projection. Pages contain at most 200 records;
the browser requests 50 and follows at most 20 pages of the existing 1,000-record ledger.
Pages are independent observations and can change between requests.

The browser defaults to observe scope, explicitly shows separate stimulation/destructive
eligibility, and provides bounded duration, historical operation identity, ownership,
same-scope renewal, release and original-fence reconciliation. It explains unavailable
connection tests, physical commands and automatic run renewal. Fixture scope remains visible.
Physical inventory readiness remains false and the executable XDL/System is unchanged.

Serialize explicit browser mutations and persist the one unconfirmed request in private
per-tab session storage before sending it. Retain its exact principal, route, method, key
and closed body across navigation/reload. On transport/server failure or malformed receipt,
offer an explicit same-key retry; do not invent a new reservation identity. A versioned
4xx refusal of the first attempt permits a fresh request; a refused retry cannot settle
an earlier unconfirmed attempt. Restore validates the saved request and never sends it
automatically. A different current principal cannot retry it. A historical receipt does not
grant current ownership. Leaving the view aborts browser observation only; it does not
claim to cancel backend work. Reads have bounded timeouts, generation/lifetime guards and
focus guards for navigation, moved focus and dialogs.

## Compatibility and verification

This is additive HTTP v1. Existing asset/placement projections retain their original
readiness semantics, and the stock native launcher still installs no provider or grants.
History remains usable for recovered leases without a provider installation; affected
requests remain unavailable. No provider-loading route or command/probe endpoint is added.

Verification must cover actual configured application/session routes, owner isolation,
independent grants, revocation, unknown/expired/recovered state, closed projections,
bounded paging, late replies and same-key recovery through native browser interaction.
An owned native fixture host uses only fixed test scenarios, real application routes and
typed in-memory provider objects; it does not replace production routes or contact equipment.
Fixture success cannot close actual hardware, native Windows, human/AT, automatic run
renewal, provider-specific stop/restore or full milestone acceptance gates.

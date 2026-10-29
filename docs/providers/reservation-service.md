# Native-host reservation service

The stock launcher installs no physical provider and no asset permissions. Its
physical runtime remains unavailable. A host integration can configure the
reservation facade through Python `create_app(..., lab_host=...)`; there is no
HTTP, project, profile or configuration-file provider installer.

This interface is under verification. The repository's exercised providers are
owned in-memory fixtures. No actual device, driver, permission/clock/stop contract
has been nominated or admitted; see
[`physical-provider-admission.md`](../implementation/physical-provider-admission.md).
Native Windows verification remains held. Fixture results do not establish those
capabilities or physical acceptance.

Host code supplies a `LabHostConfiguration` with a tuple of
`LeaseProviderInstallation` objects and a separate `LabAuthority`. Each installation
contains an already installed object implementing the versioned inventory,
reserve, renew, release and inspect-reservation methods; a provider ID/version;
the pinned implementation digest; declared native OS/architecture support;
fixture or admitted-integration evidence scope; and opaque conformance and
authorization references. Construction checks the current host and shape without
calling the provider. References identify the integrator's reviewed evidence;
they do not perform that review or confer a user grant.

The authority maps an exact authenticated principal and asset ID to independently
allowed scopes. The current local-session principal is `local-operator`; another
tab/session does not create another reservation owner. No grants are implied.
Host code can revoke scopes or replace the exact scope set. Requests cannot
provide grants or owners. Observation, stimulation and destructive reservations
each require their own grant and declared capability. Destructive actions are not
implemented by this facade; reserving a scope does not issue a device command.

`GET /capabilities` exposes `labReservations`, the installed lease descriptors,
scope, bounds and separate unavailable runtime admission. Asset/placement views
continue to show read-only observations and unavailable physical runtime readiness.
The reservation UI reads separately versioned eligibility and local owner history,
and sends explicit idempotent requests. The physical run adapter, connection tests,
automatic active-run renewal and ownership-loss/stop integration remain unfinished. An installed lease interface
does not make an XDL physical deployment executable.

Explicit authenticated requests use the existing exact Host/Origin and CSRF
boundary. Reserve, renew, release and reconcile require an idempotency key scoped
to the principal and route/resource. Reusing a key returns the same operation;
changed payloads conflict. `202` means durable acceptance, so inspect both the
operation result and the reservation's current ownership. Defaults are observation
and 30 seconds; requested integer leases range from one to 300 seconds. Renewal
retains the original scope and fence. Reconciliation inspects the original
provider/asset identity and never acquires another lease.

`GET /assets/{assetId}/reservation-options` reads current eligibility for each
independent scope; it is advisory and cannot bypass mutation checks. `GET
/reservations` pages only the signed-in principal's bounded local history and
available request controls, without provider calls. Both carry version 1.0,
server observation time and separate unavailable runtime admission. Unknown private
payloads remain excluded. Without an installation, durable history remains visible
and provider mutations remain unavailable, including terminal cleanup requests.

SQLite stores intent before delegation and acknowledgement separately. Restart
marks pending operations and nonterminal leases unknown. A matching observed
owner/scope/fence/deadline can restore known ownership; a lost initial fence is
not invented. Changing the installed descriptor, host or observed asset identity
blocks use of an old lease. Restart without installation retains unknown history
without provider calls. Restore the original reviewed installation and inspect
the original ownership; do not create a new request merely to resolve uncertainty.

Provider callbacks have one outstanding slot, no queue and a configured timeout
from above zero to five seconds (default one). A timed-out callback retains its
slot until it actually returns, and its late result cannot grant ownership. The
wrapper cannot terminate a device operation or prove physical cleanup. Permissions,
generation and deadlines are checked again immediately before delegation.

The ledger is bounded to 1,000 lease records and 2 MiB; lab operations to 1,000 and
8 KiB each. Quota refusal preserves history. This slice adds no automatic lease
history deletion. Provider private payloads and unknown persisted extensions are
excluded from public responses. Failed lease-acknowledgement persistence disables
in-memory owned authority. Uncertain final operation recording preserves the
accepted identity and does not repeat the provider call.

Explicit owner cleanup can release a known lease after grant revocation. Repeated
released/expired cleanup cannot affect a newer owner and contacts no provider.
Private full backup/restore refuses owned or unknown lease records even after
their deadline, and refuses malformed/unsupported/oversized ledgers. First resolve
the original provider ownership through its reviewed contract; deleting a record
does not release a device. Confirmed terminal history can round-trip privately
without becoming new authority. Public project/evidence exchange is separate from
these private backups and does not install provider state.

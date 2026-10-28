# Hybrid laboratory status

The software contains fixture-tested inventory, scoped action authority, exclusive fencing leases,
renewal/expiry, ownership-loss and clock-quality contracts. The stock launcher installs no physical
provider or permissions. Separately configured native-host lease integrations can accept explicitly
granted reservation requests; this does not admit physical runtime or device commands.

No physical device was scanned, reserved, connected, stimulated or flashed. Real device discovery,
substitution, disconnect, clock evidence and shutdown acceptance are BLOCKED pending the prerequisites
in `docs/implementation/physical-provider-admission.md`. Fixture tests do not complete AC-021–AC-024.
Windows driver/provider support requires its own native admission; do not infer it from Studio's targets.

Open Laboratory to inspect public inventory observations, metadata, diagnostics and
their completeness. Availability, permission and readiness are separate facts. A
failed or incomplete observation cannot establish that a device is absent.

**Your reservations** shows the signed-in principal's local lease history, including
unknown ownership, expiry, scope and original fencing identity. Refresh makes a new
observation; it does not contact a provider. Each history page is independent and
records may change between requests. Physical state remains unknown.

On an observed asset, choose **Check reservation options**. This reads current
request eligibility from the separately configured lease service. **Observe** is
the default; each stimulation or destructive scope needs its own current grant
and declared capability. Choose a duration from 1–300 seconds and explicitly
request the scope. Reserving it sends no physical command. Fixture evidence scope
does not establish hardware support. Unavailable scopes show refusal reasons.

The operation receipt records the request's historical result; current ownership
is separate. **Renew same scope** retains the original scope and fence. **Release
reservation** reports its actual ownership outcome. **Reconcile original ownership**
explicitly inspects the original provider/fence without reacquiring. Unknown
ownership cannot renew or release, and reconciliation cannot invent a lost
original fence. An expired deadline disables renewal until a new observation.

An unconfirmed response retains the same request in this browser tab. Use **Retry
same reservation request** to recover the durable operation identity. Navigation
or reload does not cancel backend work, and the browser never retries automatically.
A refused retry cannot settle the earlier unconfirmed attempt. Keep the tab's
private session data until that outcome is resolved; clearing it does not release
a lease. Connection tests, physical commands and automatic active-run renewal
remain unavailable.

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

# Native-host observation service

The stock launcher has no observation installation or observation permissions.
There is no HTTP/project/profile provider installer. Physical execution and active
commands remain unavailable. The backend and connection-observation UI implement
the bounded observe-only contract below. Verification is retained per exact candidate;
fixture results do not establish native Windows or actual hardware support.

Trusted host code can pass `lab_probe_host=LabProbeConfiguration(...)` to
`create_app`. `ProbeInstallation` names an already installed object with
`probe(binding, scope, deadline)`, provider/version/implementation pin, exact asset
identity digest and binding reference, supported native OS/architecture, fixture
or admitted-integration scope, conformance/authorization references and one to
eight opaque contacted resource references. Its bounded private binding dictionary
is passed only to the native callback; it is never persisted or exposed by this
facade. Endpoint/credential handling remains with the reviewed host provider.
Construction performs shape and host checks without provider contact.

`ProbeAuthority` separately grants an exact principal/asset observation request.
The current authenticated local-session principal is `local-operator`. There are
no wildcard, implied reservation, stimulation or destructive permissions. Changing
or revoking a grant advances its generation. Existing lease descriptors, pins and
reservation scopes do not change when observation support is installed.

The authenticated `GET /assets/{assetId}/probe-options` returns version 1.0,
the current principal, eligibility/reason, observation scope, binding descriptor/digest and backend
observation time without provider contact. It is advisory: POST rechecks admission.
`GET /capabilities` exposes the separate `labProbes` descriptor and bounds.

An explicit `POST /assets/{assetId}/probes` accepts only
`expectedBindingDigest` and optional `scope: "observe"`, with an idempotency key.
It uses the existing Host/Origin/session/CSRF boundary. `202` means durable
acceptance; inspect operation status and result. A response may already contain
the final bounded callback result, or unknown acknowledgement. The owner can
retrieve it through `GET /operations/{operationId}`. There is no automatic probe
on import/open/refresh/preflight, no automatic retry, and no active command route.

The callback receives the installed binding's asset/provider/binding references,
identity digest, permitted resource references and private host dictionary, the
literal scope `observe`, and an absolute backend deadline. A result has:

- `status`: `observed`, `unavailable` or `unknown`;
- the exact `identityDigest` and a duplicate-free subset of declared
  `contactedResources`;
- optional `sourceTime`: opaque `clockDomain`, signed decimal-string `tick`,
  `unit` (`ns`, `us`, `ms`, `s`) and optional nonnegative `uncertaintySeconds`;
- optional public `metadata.firmwareVersion` and `metadata.artifactRevision`;
- at most 16 stable uppercase diagnostic codes.

Other provider fields stay private. A backend `receivedAt` is added separately;
it is not source time or a synchronization proof. Unsupported clock/metadata
remains null. An `observed` result does not grant ownership, readiness or execution.
An acknowledged `unavailable` observation can be completed without claiming a
working connection. Unknown results/acknowledgements remain unknown.

There are at most 32 explicitly bound installations and 1,000 observation
operations, each at most 16 KiB. Private binding JSON is at most 4 KiB. The provider
callback timeout is greater than zero and at most five seconds (default one).
One callback per observation provider ID can be outstanding; there is no queue.
Timeout retains the occupied slot until actual return and discards late results.
The host integration must also coordinate probes with its other device operations.
This wrapper cannot kill a device callback or prove device cleanup.

Acceptance and key mapping are durable before delegation, and delegated state is
durable before contact. Same-key retries return the original receipt; changed
payloads conflict. Restart turns accepted/delegated observations unknown and
never repeats them, including when no installation is configured. Historical
receipts remain inspectable without becoming current authority. Failed final
recording remains unknown unless exact read-back proves the committed result.
Quota refusal preserves history; there is no automatic observation-ledger deletion.

The exercised provider is an owned in-process fixture without equipment or network
contact. The browser exposes explicit option checks, observe-only requests,
same-key recovery and owner-only operation inspection; saved references and pending
metadata are bounded to this tab and never constitute current authority.
Native process-interruption and browser evidence remains fixture-scoped, with
native Windows and actual device/provider/driver/permission/clock/stop acceptance
separate. See [ADR-0027](../architecture/ADR-0027-explicit-lab-observations.md).

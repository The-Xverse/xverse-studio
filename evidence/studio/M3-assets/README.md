# Read-only lab inventory and canonical physical bindings — T072

The backend now connects an authored Deployment's logical references and target external-asset IDs
to explicitly registered inventory observations, using authoritative selected XDL and canonical System
endpoint/interface requirements. A revision precondition, invalid source or external-file conflict
prevents misleading resolution and does not contact inventory. Read operations preserve source bytes,
logical identity, deployment admission and run snapshots.

`GET /api/v1/assets` exposes an allowlisted bounded projection with unknown firmware/revisions,
provider failure and ambiguity diagnostics, truncation and explicit completeness. Private endpoint,
credential and provider payload fields are omitted. The selected variant's `/physical-bindings` GET
separates identity, interfaces, metadata, availability, provider admission and permission.
`activeReady` stays false; physical execution/reservation APIs remain unadmitted, and the default
inventory remains empty. A record's admission-looking evidence label cannot grant authority.

ADR-0018 and the HTTP contract document the additive observation boundary. Existing source editing
persists canonical bindings; no second binding store, UI form, discovery, probe, driver or physical
command is introduced. Inventory callables rely on the trusted provider's bounded-call contract;
the facade does not install or admit providers or supply a new timeout framework.

The focused 86-check cohort includes existing T070/T076 tests and the new canonical-source,
metadata/privacy, malformed/failing inventory, limits/completeness, source-change, variant-selection
and no-delegation cases. The primary agent's independent audit and repaired findings are retained
in `independent-review.md`. Final whole-candidate verification is recorded separately.

This completes only the owned backend component once final verification is retained. Live physical
AC-021–AC-024 still require a nominated device/provider, driver, explicit permitted environment and
actual observations. Native Windows installation/testing remains held at user request.

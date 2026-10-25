# Evidence card facet finding before repair

Source-confirmed adjacent FR-020/T027 finding in the frozen Results view: the card uses
`run.evidenceStatus`, then a cached catalogue status/integrity, but the actual owned backend run
projection reports `run.evidence`. The observation/catalogue loader depends on run identity/state
and filters, not changing evidence facets. A current invalid/unavailable facet at the same lifecycle
version can therefore coexist with a stale stronger card. This is not a claim that live corruption
was reproduced. The focused UI successor records controlled response/actual-runtime scopes separately.

Repair prioritizes the actual run evidence field and refreshes the separate reader projection when
evidence facets change. Reader integrity alone must not be substituted for collection status.
Lifecycle, assertion, cleanup and evidence remain distinct; no original journal or runtime command
is changed by this presentation repair.

# Independent review — T052 verification (2026-10-25)

A read-only reviewer checked whether the T052 claims are proven by the cited tests. No behavioural
defect was found; the coverage claim was overstated and is corrected:

1. The cited contract test did not vary `version`. Added API refusals for `1.0`, `latest`, `1.0.0-` and
   `v1.0.0` without metadata creation.
2. The capability advertised an examples constant rather than the validator's admitted list. It now
   advertises `SUPPORTED_API_VERSIONS`, asserted against the adapter identity.
3. The fixture service inherited the owned reference's provenance. It now has its own fixture provenance.
4. Side-effect checks compared names only and filtered `.tmp`. They now compare content digests of every
   file outside the database, and register a fetchable local `http` origin that must receive no request.
5. A direct API check now shows semantic edits are refused for a project containing a non-admitted XDL
   version; the evidence map distinguishes wizard, logical-asset-form and Scenario coverage, and records
   that "service" is a node role in XDL v1alpha1.

The pattern guard was confirmed correct for Unicode-sets semantics and now also fails on any future
non-literal `pattern={...}` form.

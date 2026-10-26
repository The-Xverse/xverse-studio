# ADR-0017: Owned domain presentation profiles

Status: implemented owned components under verification; no M2 acceptance claim. The project owner
decided on 2026-10-26 to use Studio-owned, inert, presentation-only profiles until real industry
profiles are nominated (T064).

## Context

FR-045 lets compatible profiles customize terminology, catalog categories, forms, icons and
documentation while the shared create/model/connect/deploy/experiment/results workflow stays the same.
No admitted industry profile existed; the admitted profiles were experiment, evaluation and connection
profiles.

## Decision

There are two owned profiles, `io.xverse.studio.domain.process-control` and
`io.xverse.studio.domain.automotive` (1.0.0, maturity `fixture`).

- **Presentation only.** Their schema allows only empty extension payloads, so the namespaces carry
  no semantics. The registry holds their presentation, which `sanitize_presentation` validates as a
  whole:
  - labels for the five core terms, as bounded plain text with no markup or control characters;
  - icon names from the shared allowlist;
  - up to eight form groups of parameter identifiers;
  - an `https:` or `urn:` documentation reference that is shown and never fetched;
  - the XDL namespaces the domain covers.
- **Effective presentation.** `GET /projects/{projectId}/presentation` resolves the terms:
  - bound domain profiles come first;
  - otherwise the blueprint's declared domain profile applies, labelled "not bound";
  - otherwise the core terms apply.

  When several bound domains disagree on a term, the core term is kept and the conflict is listed,
  and no single domain's form groups are imposed. Every admitted domain is listed, so definitions from
  any industry can be labelled when selected across industries.
- **Rendering.** The browser renders everything as text:
  - a domain badge in the header;
  - domain headings for deployment and flows;
  - parameter groups that only arrange the same parameters;
  - a domain badge on each instance-wizard definition;
  - a terminology preview in the profile list.
- **Reference provider.** It ignores bound domain profiles only after pinning their exact identity
  (version, schema and documentation refs). Terminology never changes plans, admission or
  execution.

## Consequences

The core workflows and identities are unchanged. The owned profiles make no domain-fidelity claim.
Real industry profiles replace or extend them through the same registry, after T064 nomination.

Verification: `tests/contract/test_profile_presentation.py` and `tests/e2e/profile-presentation.spec.ts`.

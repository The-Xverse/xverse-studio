# Sanitized domain presentation through shared workflows (T062)

Owner decision (2026-10-26): Studio-owned, inert, presentation-only domain profiles. Design: ADR-0017.

- **Profiles.** `io.xverse.studio.domain.process-control` and `io.xverse.studio.domain.automotive`
  1.0.0, at maturity `fixture`.
  - Their schema allows only empty extension payloads.
  - `sanitize_presentation` refuses, as a whole, any presentation that contains:
    - markup, scripts, or control, zero-width, bidirectional-override or BOM characters;
    - unknown terms or icon names outside the shared allowlist;
    - non-identifier form parameters;
    - documentation that is neither `https:` nor `urn:`.
- **Rendering in the shared workflows.** Everything renders as text only:
  - a header domain badge;
  - the System icon in the header, and Flow/Deployment/Scenario icons on the workflow tabs;
  - "Process explorer" / "Vehicle function explorer";
  - Deployment and flow headings;
  - "Author operating scenario intent";
  - the add-element dialog title;
  - parameter forms grouped by the domain's form groups (the same parameters, none dropped);
  - a domain badge on each instance-wizard definition;
  - a terminology preview with its documentation reference in the profile list (not a link, never
    fetched).
- **Cross-industry selection.** Binding both domains keeps the core terms where they disagree, lists
  the conflicts and imposes no single domain's grouping; validation passes. Definitions from any
  domain keep their own domain label.
- **Semantics.** Unchanged:
  - Binding a domain profile changes no plan digest, and the example stays ready.
  - The reference provider ignores bound domain profiles only after pinning their exact identity.
  - Binding now uses each profile's own resource name; the connections profile used to be created
    as `studio-experiments`.

Tests:
- `tests/contract/test_profile_presentation.py`: refusal of each unsafe kind of value; admission as
  presentation only; blueprint defaults and bound terms with an unchanged plan; mixed domains.
- `tests/e2e/profile-presentation.spec.ts`: badge, icons, relabelled headings, grouped parameters,
  wizard domain label, and the profile preview without links.

Real industry profiles remain T064 nomination work. Native Windows is blocked at user request.

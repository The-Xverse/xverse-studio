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

## Client discovery and binding completion amendment — 2026-10-27

Admitted-profile discovery is a loading, available or unavailable observation. A failed,
malformed, duplicate or incomplete collection leaves availability unknown and offers an
abortable retry; it cannot establish absence. Only a successful well-formed empty response
reports that no profiles were returned. Retry can focus the first available choice, the
empty observation or the retry control while focus still belongs to its origin or BODY
and no modal has superseded it. This does not grant binding or provider authority.

Binding is additive: select one to 16 exact admitted identities; unchecking a choice changes
the next submission and never removes an existing project lock. Submission freezes the
project/revision, profile/version/schema/presentation identities, selection generation and
focus origin. A synchronous send guard and disabled submit control prevent another pending
submission; checkbox changes remain editable and are not included in that earlier request.

The full Project returned by the authoritative transaction updates the active project through
the shared project/load/newer-head guard, rather than a captured reload. Equal or older
acknowledgements preserve newer history and readiness. State application is separate from
visible completion: the existing Workspace return and exact success notice occur only while
submission, selection and focus intent remain current. New checkbox edits or deliberately
moved focus keep Environment open with its selection intact and identify only the submitted
locks as saved. Obsolete completion/refusal cannot publish feedback in a departed context;
current refusal keeps the selection and supports explicit loading of the current revision.

App owns final source/error focus because normal success unmounts the binding panel. Focus
waits for busy state to settle and requires matching project/load/post-commit intent, origin
or BODY focus and no modal. Profile-panel pointer/keyboard/input interaction also advances
the shared authoring interaction sequence. It supersedes a pending foreign-project load or
recovery without changing the separate generations used to acknowledge its own revision.
Programmatic retry focus is not itself an authoring interaction.

Verification adds `tests/e2e/profile-bindings-accessibility.spec.ts`: native keyboard journeys
at both required viewports use actual additive binding and stale-refusal transactions,
canonical document/lock/sidecar preservation, validation and unchanged executable plan/provider
scope, and held replies with newer selection/focus/history/readiness or foreign recovery.
Discovery HTTP/shape/empty responses are explicitly controlled transport observations, not
live registry-absence evidence. Owned presentation remains a fixture, not domain fidelity or
runtime/device permission. Final candidate evidence and full native-platform/AT/milestone
acceptance remain separate; Windows is held at user request.

## Parameter groups and active input — 2026-10-28

An asynchronous presentation reply can change a parameter's group while its value
control has focus. Moving that control between fieldsets replaces its DOM node:
restoring focus alone cannot restore a native numeric input's Select All state.
A held actual presentation reply reproduces the resulting `6` → `67` input when
the user intended to replace the value with `7`.

Keep group membership stable while focus remains inside the parameter form.
Apply current group metadata when focus leaves the form, or immediately when the
project context changes. Labels and source-backed parameter values retain their
normal updates; deferred grouping grants no authority and changes no authored
value. Existing draft generations and completion/focus guards remain unchanged.

Verification adds `tests/e2e/parameter-presentation-selection.spec.ts` at both
required viewports. Actual metadata arrives between native Select All and typing;
the original input and intended draft stay intact. Leaving the form applies the
groups while preserving newer focus, the draft and the canonical Project response.

# Representative creation, invalid versions and inert registration — T052

Linux owned verification. `verification.json` records the candidate and results;
`independent-review.md` records the review and its repairs.

| Obligation | Verified by | Scope |
|---|---|---|
| Controller | `tests/e2e/catalog-wizard.spec.ts` (instance wizard: service and controller) | Wizard instance of a reusable Component placed on a `controller` node; post-edit authoritative validation is valid. |
| Service | same test, imported neutral fixture `tests/fixtures/projects/create_catalog_archive.py` | A neutral service definition with its own fixture provenance, placed on a `service` node. In XDL v1alpha1 the role is the node's; no "service" core type exists or is created. |
| Device, sensor, actuator, model | `tests/e2e/authoring-retention.spec.ts` with `neutral-assets-flow.ts` | Created through the neutral logical-asset form (not the component wizard), keyboard-operated, inspected and reloaded without execution. |
| Observer | `tests/e2e/scenario-authoring.spec.ts` | Experiment observer authoring through typed Scenario forms (observers are Scenario items in XDL v1alpha1, not catalog instances). |
| Artifact requirement vs choice | `catalog-wizard.spec.ts` (instance wizard: role, placement and realization) | Definition model requirement shown separately from the chosen deployment artifact. |
| Invalid versions | `catalog-wizard.spec.ts` (registration), `tests/contract/test_catalog.py` (API 422 for `1.0`, `latest`, `v1.0.0`), `catalog-wizard.spec.ts` and `tests/contract/test_capabilities.py` (non-admitted XDL `apiVersion`) | Malformed artifact versions are refused in the browser (before any request) and by the API; a definition in a non-admitted XDL version stays inspectable in source, is not instantiable in the wizard, and semantic edits are refused by the API. |
| Registration without side effects | `catalog-wizard.spec.ts` (registration) | Metadata only: `availability: unavailable`, `executionAllowed: false`; no run; every file outside the database byte-identical; a fetchable local `http` origin receives zero requests. |

Also repaired while verifying: four HTML `pattern` attributes had unescaped hyphens inside character
classes, which browsers compile with the Unicode-sets flag and silently ignore; client-side validation
of artifact versions and identifiers never ran. `tests/e2e/html-patterns.spec.ts` now compiles every
pattern with that flag (red on the old patterns, green after).

Not covered: process-level or network-wide monitoring beyond the data root and the declared origin;
gateway and stimulus creation (FR-032, not listed by T052); provider admission of a registered
artifact; Windows.

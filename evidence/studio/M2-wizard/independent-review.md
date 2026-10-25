# Independent review — instance wizard and add_binding (2026-10-25)

A separate read-only reviewer inspected the first T051 candidate against FR-029–FR-033, NFR-004,
AC-015, AGENTS.md and the pinned XDL schemas, probing `semantic_edits` in memory. Confirmed findings
were repaired before the verified successor.

| # | Finding | Disposition |
|---|---|---|
| 1 | Catalog and project definitions were merged by bare name, so the wizard showed another definition's namespace, version, maturity and digest; same-named Components collapsed. | Definitions are keyed by qualified identity; a catalog entry describes a project definition only on exact namespace/name; otherwise it is a separate "catalog only" definition, inspectable but not instantiable. `templateId` is the qualified URI. |
| 2 | `add_binding` accepted flows, interfaces, nodes, endpoints and time domains, and a second binding for an already realized element. | Only component instances, devices, sensors, actuators and models are realizable; a second realization is `REALIZATION_CONFLICT`. |
| 3 | A non-string artifact choice crashed with a server error. | Rejected as `SELECTION_UNRESOLVED`. |
| 4 | All realization classes were offered with a preselected default. | No default; classes not declared by the definition are labelled; the authoritative validator decides fit. |
| 5 | Filter-hidden selections and stale role filters stayed effective. | Selection must be visible; role and placement fall back when no longer offered. |
| 6 | Binding identifiers were unchecked in the browser. | Validated with a stated reason. |
| 7 | Disabled submit had no linked reason. | `aria-describedby` to the review status. |

Scope added from the review: schema-backed configuration (`add_element.parameterValues` limited to
declared, typed, non-constant parameters; defaults, units, constraints and descriptions shown);
artifact requirements (definition models) shown separately from chosen deployment artifacts; System
choice for multi-System projects; catalog availability and declared realization support shown; the
copied target lifecycle is listed in the review.

Retained limitations: in XDL v1alpha1 a role belongs to a node, so role is chosen by filtering and
placing on a node and cannot be assigned to an unplaced instance or create a new node; `object`/`array`
parameters are edited in source; Deployment `parameterValues` and secret references are not authored by
the wizard.

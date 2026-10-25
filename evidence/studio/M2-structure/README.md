# Model structure canvas and keyboard tree — T043

T043 is component-complete on Linux; see `verification.json` and `independent-review.md`. No
milestone, live two-industry, cross-OS or Windows acceptance is claimed.

- System explorer can group by XDL node placement (`nodeId` and `memberIds`) as a WAI-ARIA tree:
  arrows, Home/End, Right/Left expand/collapse, Enter/Space select, roving focus, visible markers for
  undeclared and unplaced placement, and search that keeps matching groups expanded.
- Canvas draws presentation-only node frames, arranges by node when grouping is enabled, warns when a
  frame covers a non-member, shows named ports on elements, and keeps zoom/minimap/search.
- Drill-down navigation: System › node › element › Component definition (interfaces, named ports,
  parameters, models), with a breadcrumb; definitions are read-only.
- Grouping, frames and drill-down never write XDL; saved layout contains exactly element positions.

Limits: edges connect elements (ports are labels, not handles); regrouping requires a source edit;
XDL v1alpha1 has no nested Systems.

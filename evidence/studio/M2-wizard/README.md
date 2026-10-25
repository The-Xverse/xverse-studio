# Element instance wizard — T051

T051 is component-complete on Linux; see `verification.json` and `independent-review.md`.

- The Add element dialog keeps the neutral Device/Sensor/Actuator/Model form and replaces the
  component path with a wizard: qualified reusable definition (project or catalog-only), instance
  identity, role filter and node placement, typed configuration from declared parameters, and an
  optional realization (Deployment binding with explicit class, target and chosen artifacts).
- One atomic semantic transaction (`add_element` with optional `nodeId`/`parameterValues`, plus the new
  `add_binding`) validated by the public XDL validator. No artifact is built, flashed or executed and no
  provider support is granted; catalog-only definitions are inspectable but not instantiable.

Limits: role is node-scoped in XDL v1alpha1; object/array parameters and Deployment parameter values are
authored in source. T052 and AC-015 provider/native gates remain open.

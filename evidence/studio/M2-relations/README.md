# Compatible targets, mapping forms and relations by kind (T055)

Connections view (`apps/studio-web/src/features/connections/`):

- **Compatible-target guidance.** The connect form lists compatible destinations first and gives the
  reason for each incompatible one. Explicit-converter interfaces now explain that a converter mapping
  the selected provider admits must be declared, or the connection is rejected.
- **Inspectable mapping form.** `FlowContractForm` declares or removes a flow's owned contract:
  - a unit delay, and/or a linear converter `y = scale·x + offset` from the interface unit;
  - it is backed by the new `set_flow_contract` semantic edit (contract amendment), which adds the
    connections Profile resource once and preserves other extensions;
  - it shows the selected provider's admitted contracts and the flow's current admission;
  - it is disabled for interfaces without a unit, and flags an authored `fromUnit` that differs from
    the interface unit.

  Admitted mappings appear in the per-flow checks as `y = scale·x + offset (from → to)`.
- **Relations by kind.** Each kind has its own border style, colour, meaning and action:
  - **Communication:** connect endpoints. It is never presented as a physical solver.
  - **Model coupling:** shown as blocking, with the backend message; it can't be created by connecting
    endpoints.
  - **Deployment:** element → target (realization), with a jump to the Deployment view.
  - **Traceability:** authored `metadata.traceability` links; never fetched and never treated as proof.

Tests:
- `tests/integration/test_connection_contracts.py`: the flow-contract edit declares, removes and
  restores contracts that admission then judges; an edited template still runs; the profile is added
  once; refusals don't advance the revision.
- `tests/e2e/connections.spec.ts`: relations by kind on a model-coupling fixture with a traceability
  link; navigation to Deployment; a unit delay outside any cycle reported as declared.

The declared/resolved/observed projections are T056. Native Windows is blocked at user request.

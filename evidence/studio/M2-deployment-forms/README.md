# Deployment resolution forms and variant comparison (T059 component; task open)

The UI lives in `apps/studio-web/src/features/deployments/` (`ResolutionPanel.tsx`,
`DeploymentComposer.tsx`).

**Resolution panel.** For the selected variant and provider it shows:

- binding checks;
- resource, time and network constraints;
- effective-value source chains, with documents and pointers and the "no defined precedence" rule;
- portable intent kept separate from environment references.

Blocking statuses use the danger tone, matching the backend set. The provider's maturity, declared
realization/target classes and fidelity limits are listed.

**Provider-supported realization.**

- Resolution checks a binding against the selected provider's declared `realizationClasses` and
  `targetClasses`; an undeclared class is `CAPABILITY_UNSUPPORTED`.
- The rebinding PATCH evaluates the same provider as the panel.

**Variant comparison.**

- Shows per-element realization and placement, with bound artifacts and resources.
- States the shared logical identity and that this does not establish equivalence.
- Compares authored values by canonical value chain and verdict, keyed per scenario.

**Forms.**

- The bound-resource form submits only resources the variant declares. It resets when the variant
  changes, and distinguishes "not offered" from "the target declares none".
- The time-mapping form uses the new `set_time_mapping` edit (contract amendment) to add, replace or
  remove a mapping.

**Tests.**

- `tests/integration/test_deployment_variants.py`: provider classes, the time-mapping edit and its
  refusals.
- `tests/e2e/deployment-resolution.spec.ts`: the exact blocking count, exact chain pointers, provider
  fidelity, comparison cells and value differences, the resource form, add and remove through the
  time-mapping form, and the untouched original variant.

T059 stays open because it depends on T058, which waits on T054. Native Windows is blocked at user
request.

## Closure (after T058)

The closure audit found every T059 clause met and flagged one control. The binding form offered
"Software" and "Emulated", which are not XDL realization classes, so the validator always refused
them. It now offers the four XDL classes and marks those the selected provider does not declare as
"not executable by" that provider (browser-tested). The resolution panel shows the provider's
connection verdict. T059 is complete; the current run is recorded in `closure-verification.json`.

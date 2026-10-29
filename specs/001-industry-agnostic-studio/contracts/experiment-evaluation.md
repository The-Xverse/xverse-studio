# Bounded experiment evaluation contract v1

**Status**: normative design for M4; no evaluator exists merely because this document or an XDL expression string exists.

## Ownership and representation

Evaluation definitions are typed declarative data in a versioned, admitted XDL Profile extension. Proposed namespace: `io.xverse.studio.experiments`; payload version `1.0`. M4 must publish the schema, test namespace compatibility and obtain support through the platform's normal profile admission mechanism. If the selected compiler cannot admit this profile, record the dependency and block execution/evaluation of that extension. Do not put executable semantics in the project manifest or layout sidecar. Existing opaque expression strings remain preserved and unevaluated until an explicit reviewed translation to this contract exists.

Each definition has `evaluationId`, `version`, `kind` (`metric` or `assertion`), `name`, `systemRef`, `scenarioRef`, `expression`, `window`, `coveragePolicy`, and optional `description`/traceability. A numeric metric also declares `resultUnit`. It references existing observers by stable identifiers. Every evaluated result records definition digest, evaluator version/digest and source evidence identities. The language does not launch workloads, change parameters, call providers or fetch resources.

## Types and expression nodes

Types are `number(unit)`, `boolean`, `numberSeries(unit, clockDomain)`, and `booleanSeries(clockDomain)`. Numeric values must be finite. Units and semantic quantities resolve through pinned profile definitions; identical text is insufficient if profile definitions conflict.

| Node | Fields | Type / semantics |
|---|---|---|
| `literal` | `value`, optional `unit` for number | Boolean or finite numeric scalar. Numeric dimensionless values declare `unit: "1"`. |
| `signal` | `observerRef`, `field` | Numeric/boolean series from a declared observer schema. Field is an exact admitted field name, not an executable selector. |
| `metric` | `evaluationRef` | Scalar result of a named, version-pinned metric definition evaluated against the same run snapshot/evidence. Dependencies must be acyclic; only a complete execution with complete admissible coverage and finite value supplies a usable scalar. |
| `convert` | `input`, `conversionRef` | Explicit named/versioned pure unit conversion admitted by the profile; preserves quantity and clock. No implicit conversion. |
| `compare` | `operator`, `left`, `right`, optional `tolerance` | Operators `lt`, `le`, `gt`, `ge`, `eq`, `ne`. Numeric units/quantities must be compatible; boolean permits `eq`/`ne` only. Produces boolean scalar or series. |
| `boolean` | `operator`, `inputs` | `and`, `or` require two or more compatible boolean operands; `not` exactly one. Produces scalar/series according to inputs. |
| `aggregate` | `operator`, `input` | `min`, `max`, `mean`, `last` on numeric series; `all`, `any` on boolean series; `count` on either series. Returns scalar; `count` is dimensionless. |

The assertion root must yield a boolean scalar. A metric root may yield a numeric scalar with an explicit result unit; a separate assertion can compare that result only through a named, acyclic definition dependency. No loops, recursion, user functions, arbitrary arithmetic code, filesystem access, network access, interpolation or dynamic imports are supported. A new operator requires a versioned schema/evaluator successor and conformance cases.

Comparing a series with a scalar broadcasts the scalar. Two series require the same admitted clock interpretation and exactly aligned ticks in the evaluation window. Missing pairings produce `indeterminate`; they are never silently interpolated or nearest-neighbour joined. Boolean operators follow the same alignment rules. `eq`/`ne` on numeric values require an explicit absolute tolerance with compatible unit; strict order operators accept no tolerance field. `last` selects greatest source tick, breaking duplicate ticks by the declared source ordering; ambiguous conflicting duplicates make evaluation indeterminate.

## Windows, clocks and coverage

`window` contains `clockDomainRef`, `startTick` and `endTick`, expressed as signed decimal integer strings in that domain's declared tick unit. The interval is half-open `[startTick,endTick)` and must be non-empty. Version 1 uses run-relative ticks, not calendar parsing or expression-defined windows.

Cross-domain inputs require an admitted, pinned mapping and explicit maximum uncertainty from the evaluation definition. Unsupported mapping, excessive uncertainty or non-monotonic source time makes the result indeterminate. Wall-clock receipt time never substitutes for missing simulation/device time.

Version 1 `coveragePolicy` is `complete`. Each observer must declare expected sampling/event coverage and provide a verified coverage record for the selected window. Missing records, observation gaps, invalid evidence, an empty required series, non-finite values, unavailable fields or unproven coverage produce `indeterminate` with reasons. A signal that emits only on changes requires an explicit provider coverage contract; the evaluator cannot infer continuity from silence. `count` does not turn absent coverage into a known zero. Displayed partial statistics may be returned with `partial=true`, but cannot support a pass/fail verdict.

## Resource bounds

Initial v1 hard caps: 128 AST nodes per definition, depth 12, 32 distinct observer-field references, 32 named metric dependencies and an acyclic dependency graph. Expanded inputs are limited to 1,000,000 samples and 64 MiB per evaluation job. These are proposed evaluator limits, not capacity claims for Lite or acceptance measurements. The runtime/provider may impose tighter limits. Advertise effective limits via capabilities; reject oversized definitions before evaluation and abort bounded reads before materializing excessive data. Window length is limited by the admitted run and retained evidence, not an invented universal duration.

A per-job wall-time budget is configured and advertised; M0/M4 reference-environment measurements determine its supported default. Exceeding budget is an execution error, not an assertion failure. Evaluation must be cancellable without mutating source evidence. The contract's resource caps must be tested with boundary and over-limit inputs.

## Result semantics

Execution status is `not_started|running|complete|unavailable|error`. Assertion verdict is separately `pass|fail|indeterminate` or `null` when no assertion evaluation has completed. A numeric metric carries `value`, `unit`, `coverage` (`complete|incomplete|invalid`) and `partial`; it always has `verdict=null` because a value alone is not a pass/fail rule. A completed metric with incomplete/invalid coverage cannot be used as a known scalar by a dependent assertion; that assertion becomes indeterminate.

- `complete/pass`: definition evaluates true with complete admissible evidence.
- `complete/fail`: definition evaluates false with complete admissible evidence.
- `complete/indeterminate`: definition is valid, but evidence/coverage/time interpretation cannot establish true or false; include reason codes.
- `unavailable/null`: evaluator/profile capability is absent; UI says “Not evaluated”.
- `error/null`: invalid definition, resource limit, cancellation or evaluator malfunction; UI says “Evaluation error” or “Cancelled”, never “Experiment failed”.

An aggregate run evaluation uses the same verdict vocabulary: fail if any required completed assertion fails; otherwise indeterminate if any required assertion is indeterminate or unfinished/unavailable/error; otherwise pass when every required assertion passes. Its execution summary retains unfinished/error details. An empty required assertion set has no verdict and is displayed as not evaluated. A completed runtime lifecycle never creates a pass.

## Illustrative payload fragment

This is evaluator extension content, not a standalone valid XDL resource:

```json
{
  "evaluationId": "level-within-bound",
  "version": "1.0",
  "kind": "assertion",
  "window": {"clockDomainRef": "process-time", "startTick": "0", "endTick": "1000"},
  "coveragePolicy": "complete",
  "expression": {
    "kind": "compare",
    "operator": "le",
    "left": {"kind": "aggregate", "operator": "max", "input": {"kind": "signal", "observerRef": "tank-observer", "field": "level"}},
    "right": {"kind": "literal", "value": 0.8, "unit": "m"}
  }
}
```

The complete profile schema also requires the resource/scenario references listed above. The example does not assert that referenced observers, units or clock domains exist.

## Conformance cases

Cover each valid operator and type; incompatible dimensions; explicit conversion; tolerance boundary; exact half-open window boundaries; duplicate/non-monotonic ticks; scalar broadcasting; misaligned series; empty/gapped/non-finite observations; corrupted source evidence; missing coverage; uncertain cross-clock mapping; dependency cycles; AST/sample/byte limits; evaluator cancellation; deterministic reevaluation of the same admitted evidence/definition; and aggregate status for mixed pass/fail/indeterminate/unavailable results. Fixture values are test inputs, never presented as measured physical outcomes.

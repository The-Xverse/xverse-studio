# ADR-0016: Owned connection contracts with real execution

Status: implemented owned components under verification; no M2 acceptance claim. Decided by the
project owner on 2026-10-26: admit converter and feedback-causality contracts only where the owned
reference provider actually executes them.

## Context

ADR-0014's connection admission blocks every explicit converter and every feedback cycle, because no
provider or profile admitted a contract for them. T054 requires admission driven by actual
provider/profile contracts and a supported causality path. AC-016 names owned interface and connection
fixtures as its environment.

The owned reference worker already executes a discrete closed loop: `control = gain·(target −
measured)` uses the sample from the previous step, and `value += control·step` follows it. That is a
unit-delay feedback loop over simulation time; until now its feedback was implicit in the model rather
than declared in the System.

## Decision

1. **Owned connections profile.** A Studio-owned profile, `io.xverse.studio.connections` 1.0.0,
   validates flow extensions against `connections/connections-v1.schema.json`:
   - `causality: {kind: unit-delay}` declares that the flow's destination uses the value from the
     previous step of the flow's time domain.
   - `converter: {kind: linear, fromUnit, toUnit, scale, offset}` declares the exact mapping
     `y = scale·x + offset`, where `scale` is finite and non-zero and `offset` is finite.

   The profile registry admits it like the evaluation profile. The adapter passes its schema to the
   pinned validator, so the platform checks the payloads.
2. **Provider declaration.** The reference provider descriptor declares
   `connectionContracts: {causality: ["unit-delay"], converters: ["linear"]}`. An unavailable or
   external provider declares none, so its cycles and converters stay unsupported.
3. **Admission.** `admit_connections` takes the selected provider. Preflight passes it, and
   `GET /connections?providerId=` defaults to `studio.reference`.
   - **Converter.** A flow over an `explicit-converter` interface passes conversion only when:
     - it carries a `linear` converter whose `fromUnit` equals the interface `unitSemantics`;
     - `toUnit` differs from `fromUnit`;
     - the provider declares `linear`.

     A missing or mismatched converter fails (`CONVERSION_INVALID`). A converter the provider does
     not declare is unsupported. A converter on an `exact` interface fails, because nothing may be
     converted implicitly.
   - **Cycle.** A feedback cycle is admitted only when all three hold; otherwise it stays unsupported
     (`CAUSALITY_UNSUPPORTED`). Acyclicity is never proof of correctness, and neither is a declared
     delay.
     - Every directed loop in the cycle passes through a flow that declares `unit-delay`. An
       undelayed sub-loop is algebraic.
     - Every member flow shares one time domain; a flow without one uses the System default.
     - The provider declares `unit-delay` and that clock domain.

     A delay declared on a flow outside any cycle is reported as `declared`, with no admission
     effect.
   - **Coefficients.** A converter's `scale` and `offset` are bounded by ±10⁶, so converted samples
     stay finite.
   - **Wording.** Admission says that the provider *declares* the contract. Whether it executes a
     given topology is decided at preflight by `reference_configuration`.
   - **Unknown providers.** An unknown `providerId` returns `404 PROVIDER_UNAVAILABLE`, and so does the
     deployment-resolution route.
4. **Execution.** A third owned blueprint, **Process control feedback reference**
   (`org.xverse.studio.feedback`), declares the loop explicitly.

   The pinned platform compiler derives a startup order from flows between component instances and
   rejects any cycle among them (`XDL1-PLAN-DEPENDENCY-CYCLE`). The loop is therefore declared through
   the model's sensing device, not as a direct controller⇄plant edge. This matches the model, whose
   measurement (`measured[n]`, frozen by the stuck-sensor fault) is distinct from the plant state:
   - `measurement-flow` runs from the plant to `sensor-device`, which carries the `state-sensor`
     element;
   - `feedback-flow` runs from the device to the controller, undelayed: sensing and control happen
     within a step;
   - `command-flow` runs from the controller to the plant and declares `unit-delay`. This is the
     model's actual delay: `state[n+1] = state[n] + command[n]·step`, so the plant applies each
     command at the next step;
   - the component start order stays controller, then plant.

   Studio's admission still sees the full dataflow cycle (controller, plant, sensor-device) and admits
   it only under the declared contract. The template also declares:
   - an `observed-state` flow to the observer over an `explicit-converter` interface, with a
     `linear` converter from `1` to `%` (scale 100).

   `reference_configuration` admits exactly this template as a variant:
   - the converter's `scale` and `offset` are run inputs, normalized like parameters before the body
     comparison;
   - every other change is still refused.

   The worker executes the same unit-delay loop. `state-flow` carries the plant state, so for each
   sample the worker computes `scale·state + offset` and emits it as `observed` in `toUnit`. The
   unconverted values are kept, and the converter is recorded in the observation's `conversion`
   field. A stuck-sensor fault freezes the measurement but not this observation. Nothing else is
   converted. The connections profile is pinned to version 1.0.0.
5. **Scope.** No other converter kind, unit system, causality kind, algebraic loop or physical
   coupling is admitted. A declared contract on a topology the provider does not execute is still
   refused at admission by `reference_configuration`.

## Consequences

- The two existing examples are unchanged. Their identities, observations and readiness stay the same.
- Profile discovery lists three admitted profiles.
- T055 can offer an inspectable converter mapping form for this one admitted converter.
- Verification:
  - `tests/contract/test_connections.py`: admission with and without the provider;
  - `tests/integration/test_connection_contracts.py`: a run executing the loop and the converter;
  - `tests/e2e/connections.spec.ts`.

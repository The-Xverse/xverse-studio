# Owned connection contracts with real execution (T054)

Decision of the project owner (2026-10-26): admit converter and feedback-causality contracts only where
the Studio-owned reference provider actually executes them. Design: ADR-0016; ADR-0014 is amended.

- **Contracts.** The owned profile `io.xverse.studio.connections` 1.0.0 is validated by the pinned
  platform through `connections/connections-v1.schema.json`. It declares `unit-delay` causality and a
  `linear` converter on flows. The reference provider declares
  `connectionContracts: {causality: [unit-delay], converters: [linear]}`. The unavailable Lite
  provider declares none.
- **Admission.**
  - Admission is driven by the selected provider. Preflight passes it; the connections route takes
    `providerId`.
  - Explicit converters pass only with a declared linear mapping from the interface unit to another
    unit, with a finite non-zero scale. A missing or invalid mapping is rejected
    (`CONVERSION_INVALID`). A converter on an `exact` interface is rejected. Without a provider
    contract, conversion is unsupported.
  - A feedback cycle is admitted only when a member flow declares `unit-delay`, all member flows share
    one time domain, and the provider declares the contract. An undelayed loop is reported as
    algebraic and unsupported; mixed clocks fail.
- **Execution.**
  - The pinned compiler rejects cycles among component instances
    (`XDL1-PLAN-DEPENDENCY-CYCLE`). The owned feedback blueprint therefore declares the loop through
    the model's sensing device: controller → plant → sensor-device → controller. It compiles, and its
    preflight is ready.
  - The delay is declared where the model has it: on the command flow, because the plant applies
    `command[n]` at step n+1. The worker executes exactly that recurrence.
  - Each sample also carries `observed = scale·state + offset` in `%`, converting the plant state its
    flow carries, with the converter recorded. A stuck-sensor fault freezes the measurement but not
    this observation.
  - `reference_configuration` admits only this template. Scale and offset are run inputs bounded by
    ±10⁶, and the connections profile is pinned to 1.0.0.
- **Tests.**
  - `tests/integration/test_connection_contracts.py`:
    - a real run whose journal confirms the converter output and the unit-delay recurrence
      (red-checked by disabling the converter);
    - blocked at preflight: undelayed loops, wrong `fromUnit`, zero or oversized scale, other target
      units, converters on exact interfaces, and an altered profile version;
    - rejected at connection level: hidden algebraic sub-loops; flows on the default clock resolve
      correctly; a stray delay is reported as `declared`;
    - an unknown provider returns 404;
    - a provider without contracts admitting neither the loop nor the converter;
    - unchanged configuration for the existing examples.
  - `tests/contract/test_connections.py` and `tests/e2e/connections.spec.ts`: provider-dependent
    verdicts; the admitted loop and the `y = 100·x + 0 (1 → %)` mapping shown in the Connections
    view.

Scope: no other converter kind, unit system, causality kind, algebraic loop or physical coupling is
admitted. External providers' contracts stay unadmitted. Native Windows is blocked at user request.

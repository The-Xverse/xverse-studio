# Independent review — connection admission (2026-10-25)

A read-only reviewer probed the first T053/T054 candidate in memory (including a 3,000-graph brute-force
check that confirmed the cycle detection). Nine confirmed defects were repaired:

| # | Finding | Disposition |
|---|---|---|
| 1 | Flows beyond the 400 bound were unevaluated while preflight passed. | `CONNECTION_LIMIT_EXCEEDED` blocks; multiplicity counts use all flows. |
| 2 | System `models` (XDL's model-coupling surface) were ignored and the "no coupling construct" claim was wrong. | Models with inputs/outputs are reported as unsupported model couplings and block; a valid-XDL coupling fixture was added. |
| 3 | Declared quality and uninterpretable multiplicity only yielded `unknown`, so execution ignored them. | Both are `unsupported` and blocking. |
| 4 | Clock and quality checks reported `pass` without evaluation. | New `declared` status; messages state "not evaluated". |
| 5 | With an invalid source set, flows not addressed by a diagnostic were `admitted`. | They are `unknown`; the report carries `sourceValid`. |
| 6 | Multiplicity double-counted self flows, ignored lower bounds with no flows, and treated inverted ranges as interpretable. | Distinct flow counting, endpoint-level checks, inverted ranges unsupported. |
| 7 | Flows inside an unsupported cycle stayed `admitted`. | Per-flow `causality` check makes them unsupported. |
| 8 | UI wording overclaimed (clock column, summary counts, cycle path order). | Corrected; cycles list members as a set. |
| 9 | A "never converts" test compared a copy with itself. | Copies before admission and compares after. |

Remaining scope recorded for the tasks: no provider/profile admits a converter, version-compatibility,
quality, causality or model-coupling contract, so the "supported" admission paths cannot yet be exercised
(T054 stays open); inspectable converter mapping forms need such a contract (T055 stays open); resolved
and observed projections are T056.

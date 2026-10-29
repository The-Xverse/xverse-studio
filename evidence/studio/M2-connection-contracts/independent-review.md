# Independent review: owned connection contracts

A time-boxed reviewer probed the variants with a scratch script. Confirmed findings and their repairs:

| Finding | Repair |
| --- | --- |
| Huge but finite coefficients passed preflight, then crashed the run with `inf` | Coefficients bounded by ±10⁶ at admission (`CONVERSION_INVALID`) and in `reference_configuration` (`LIMIT_EXCEEDED`) |
| The converter mapped the sensor measurement, although its flow carries the plant state; a stuck sensor froze it | The worker converts the plant state; tested with a stuck-sensor run in which the measurement diverges |
| The unit delay was declared on the sensor-to-controller flow, which has no delay in the model | Declared on the command flow, matching `state[n+1] = state[n] + command[n]·step`; the run asserts this recurrence |
| One delayed flow admitted a whole strongly connected component, hiding undelayed sub-loops | Every directed loop must pass through a delayed flow; undelayed sub-loops are algebraic and unsupported |
| Admission said a contract was "executed by provider" for topologies the provider refuses | Wording now says the provider *declares* the contract; preflight decides execution, and a `toUnit` change is tested as refused there |
| Flows relying on the default time domain failed the clock check; provider clock domains were not checked | The default domain is resolved; the provider's `clockDomains` is required |
| A delay on a flow outside any cycle was silently ignored | Reported as `declared`, with no admission effect |
| The connections profile version was unchecked | Pinned to 1.0.0 in `reference_configuration`; tested over HTTP |
| An unknown `providerId` silently meant "no contracts" | `404 PROVIDER_UNAVAILABLE`, also on deployment resolution |
| The zero-scale test passed even without the connection-level check | A connection-level assertion was added |

No regressions were found for the existing examples.

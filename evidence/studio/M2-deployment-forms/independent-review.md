# Independent review: T059 deployment UI

Confirmed findings and their repairs:

| Finding | Repair |
| --- | --- |
| Resource form state survived variant changes and external edits, and could revert other edits or submit hidden ids | Checkbox state comes from the authored binding unless edited for the same variant, binding and revision; the form resets on variant change; only declared resources are submitted |
| Comparison keys collapsed scenario parameters; the effective-only diff missed ambiguous differences and was key-order sensitive | Scenario-aware keys; canonical comparison of the value chain and verdict |
| A stale comparison selection could return after switching variants | Cleared when the chosen variant equals it |
| "Lowest first" implied precedence | "Value sources" with the default-only rule stated |
| Blocking `unknown`/`unresolved` looked like non-blocking warnings | Tones mirror the backend BLOCKING set |
| "Not offered" shown when the target declares nothing | Distinct "declares no offered resources; placement stays unknown" hint |
| PATCH and the panel evaluated different providers | PATCH carries `providerId` |
| Loading text not announced; heading hierarchy broken | `role="status"`; the comparison nests under the panel heading |
| Weak spec assertions (`blocking` matched "no blocking"; unescaped regexes; vacuous run check; no cell, time or untouched-variant checks) | Exact text and anchored regexes; added cells, time form, fidelity and untouched-source checks |
| No time form; no provider-supported controls; generic fidelity text only | `set_time_mapping` edit and form; provider-declared classes checked; provider limits shown |

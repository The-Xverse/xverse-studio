# Independent review: deployment resolution

A read-only reviewer ran the full backend suite (649 passed) and probed `resolve_deployment` with
platform-valid XDL. It found no crash on accepted XDL. Confirmed findings and their repairs:

| Finding | Repair |
| --- | --- |
| An unparseable draft caused a 500 on the GET route | Validate first; invalid sources return `sourceValid: false` |
| Credentials leaked through token-as-username, fragment tokens, `externalAssetRef` and parameter-chain values | `credential_free` covers all user information, secret query/fragment keys and connection strings; asset references and every chain value are scrubbed; each location reports `SECRET_INLINE` |
| Host-path false blocks: MQTT topics, Darwin hosts, `file:C:/` and `file://server/share` | POSIX paths only under conventional roots; styles are posix/windows/network; Darwin is POSIX; drive-letter file URIs are Windows; shares are declared |
| Binding values on non-component elements were dropped | Reported as `PARAMETER_UNDECLARED` |
| Mixed units failed instead of `unknown`; a missing `offeredResourceIds` meant "offers nothing" | Both are `unknown` |
| An exact-version mismatch was reported as an unknown syntax | Fails as `ARTIFACT_REQUIREMENT_UNMET` |
| Type checks stricter than JSON (`2.0` integer, `1` vs `1.0` constant) | JSON Schema semantics |
| The clock check depended on optional `defaultTimeDomainId` and ignored Scenario mappings | Reference clock is the default or the only domain; transitive mappings from the Deployment and matching Scenarios; no reference clock is `unknown` |
| Rules the schema lacks: `REALIZATION_TARGET_MISMATCH`, `RESOURCE_INVALID` | Removed; realization is `declared` and judged by the provider |
| Weak or missing tests: an either-status assertion, untested pass branches, no PATCH coverage, missing tolerance/provider/redaction/pointer cases | Added; red-checked by disabling chain scrubbing and exact-version failure |
| ADR mismatches | ADR-0015 rewritten to match the code |
| `update_binding` compatibility ignored resolution failures; its response shape differed from GET | Resolution diagnostics block compatibility; the response carries the same shape |

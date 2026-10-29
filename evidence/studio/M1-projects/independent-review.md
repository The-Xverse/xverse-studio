# Independent review: T016 inspection

A read-only reviewer reproduced the backend findings with probe imports. Confirmed findings and their
repairs:

| Finding | Repair |
| --- | --- |
| A non-string extension key, an unhashable Profile namespace or non-mapping Profile metadata caused a 500; `authored_findings` also crashed in preflight | Keys stringified for display and pointers; only string namespaces registered; `authored_findings` tolerates malformed shapes, leaving them to the validator; tested over HTTP for inspection and preflight |
| A lock object rendered as a React child would unmount the app | Lock fields are returned only as strings (`null` otherwise); keys use the lock index |
| A tampered sidecar or duplicate lock was reported "admitted" | `ProfileRegistry.lock_statuses` shares `validate_project`'s per-lock checks |
| `sourceIntegrity` was ignored, and blocked status was never shown | Included in `executionBlocked`; a status line states it |
| "Preserved byte for byte" was claimed for a re-serialized view | Wording now says it is a parsed view; the link opens the exact bytes |
| Extension walk differed from the platform's positions | Restricted to the schema-declared collections |
| Focus fell behind the open source dialog | Inspection closes before the source dialog opens; the test asserts focus inside it (red-checked against the old code) |
| The header button hid inspection failure | Failure state shown in name and badge |
| `.card-limit` contrast below AA | Darkened |
| "Not demonstrated: Owned executable reference only…" inverted the claim; what the example demonstrates was not shown | "Scope limit:" wording; "Demonstrates:" and the provider listed |
| Vacuous e2e assertions; no lock, unadmitted, unparsed or malformed tests | Exact badge and accessible-name assertions; backend cases added |

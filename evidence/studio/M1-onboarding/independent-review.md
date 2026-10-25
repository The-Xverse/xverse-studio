# Independent review: T015/T061 tests

A read-only reviewer audited the four test files against the T015/T061 task text. Confirmed findings
and their repairs:

| Finding | Repair |
| --- | --- |
| Profile "exact" metadata only compared the list endpoint with the detail endpoint (same source) | Pinned version to blueprint `profileRefs` and `schemaDigest` to the packaged schema bytes; red-checked with a wrong registry version |
| The OS-claim check named only four top-level keys | Recursive scan that also excludes `supportedHostOS`, `hostCompatible` and `architectures`; provider descriptors are asserted to carry them |
| Blueprint independence used a default project | Binding uses a project composed from a blueprint; discovery is shown to be unchanged afterwards |
| Unknown-extension test asserted only `not valid` | Asserts `XDL-SEMANTIC-PROFILE-MISSING` naming the namespace, in both validation and preflight; the browser readiness view shows the code |
| Unsafe-path refusal did not check for side effects | Project count is unchanged |
| The browser form check could race a late request | Asserts a validation message, waits, then checks there was no request and the revision is unchanged |
| Save paths were not covered (FR-004) | Layout save and source save keep the extension bytes |
| Categorical domain violation was missing (FR-005) | `fault: bogus` blocks with `CAPABILITY_UNSUPPORTED`; `stuck-sensor` is ready |
| Example scope/limitations were not asserted (FR-002) | Asserted in the API and on the browser card and scope note; added recent-project reopen |
| Unscoped `Automotive reference` and `/plant/` selectors | Scoped to `.example-grid` and the exact `plant plant` |
| Linux-only Python path in the spec | Chosen by platform (Windows execution itself remains blocked) |

Covered elsewhere, not repeated here: AC-002 YAML/JSON equivalence and declared-sidecar dependency resolution, in
`tests/contract/test_xdl_adapter.py::test_comments_line_endings_order_and_json_preserve_platform_identity`
and `tests/contract/test_profiles.py::test_declared_profile_sidecars_must_match_registry_and_actual_locked_bytes`.

Process note: a red check briefly edited the profile registry and restored it within the same second.
Python's mtime-based bytecode check then served the stale `.pyc`, and a browser run failed on a
phantom `PROFILE_CONFLICT`. The caches were cleared before the final verification.

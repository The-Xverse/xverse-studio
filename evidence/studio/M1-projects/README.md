# Project journeys, explicit dependencies and unresolved-content inspection (T016)

**Backend.** `GET /projects/{projectId}/inspection` is implemented in
`services/studio-api/src/xverse_studio/projects/inspection.py`. It is read-only and never fetches,
installs or runs anything. It reports:

- the example's declared scope: what it demonstrates, the provider it runs on, and its scope limits;
- import provenance;
- declared profile locks, verified with the same checks as admission (registry identity, sidecar
  digests, duplicates) via `ProfileRegistry.lock_statuses`;
- supporting files, with size and digest, marked never executed;
- unresolved extension payloads at their schema-declared positions, classified as `unresolved`,
  `unadmitted` or `conflict`, consistent with `XDL-SEMANTIC-PROFILE-MISSING` and the authored-profile
  findings;
- unparsed documents;
- whether execution is blocked, including when source integrity is modified.

**Browser.** `apps/studio-web/src/features/projects/ProjectInspection.tsx`:

- A header **Dependencies** button carries the unresolved count, or a visible failure state, in its
  name and badge.
- The dialog shows scope, dependencies and a parsed view of each unresolved payload. Each payload
  links to the exact source document, which receives focus.
- Example cards state their first scope limit.

**Journeys.**

- Create from an example, recent-project reopen, import and blank create are covered by
  `tests/e2e/project-onboarding.spec.ts` (T015) and existing studio specs.
- `tests/e2e/project-journeys.spec.ts` adds scoped claims, dependency review, unresolved-content
  inspection, source navigation with focus moving into the source dialog, and no mutation or execution.
- `tests/integration/test_project_inspection.py` covers:
  - example scope;
  - exact preserved payloads and pointers, including escaped namespaces;
  - explicit dependency import through an export/import round trip, with admitted locks and sidecars;
  - tampered sidecars and duplicate locks reported as conflicts;
  - unadmitted profiles;
  - malformed shapes (non-string extension keys, non-mapping metadata, unhashable namespaces), which
    return 200 and block preflight instead of raising;
  - unparsed documents.

**Not covered.** Live Lite onboarding, the five-person study and native Windows (blocked at user
request).

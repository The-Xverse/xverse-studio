# T008 complete Linux storage component review

T008 retains its original FR-001/NFR-009, AC-002 and T002/T006/T007 dependencies.
This review covers the whole storage component, including previous source-envelope
and migration repairs. Full acceptance and milestone reviews remain independent.
Clean package verification is pending at this source checkpoint; T008 stays open
until that verification and the final clause review are recorded.

| Original task clause | Current implementation and evidence |
| --- | --- |
| Project metadata storage and XDL ownership | Projects/store maintain immutable authored revisions, declared resources/supporting files and separate source/semantic identities. Platform validation/compiler remain authoritative. Final cohort includes project-store/import/inspection, model round-trip, CLI/library equivalence and sealed manifest/recovery tests. No browser graph is an alternate executable definition. |
| Separate layout and binding sidecars | Layout uses its own presentation revision and private history. New ADR-0040 adds independent version1.0 private artifact/asset/credential declarations with bindingRevision CAS and byte-sealed immutable files. Source/layout saves retain the binding head; binding saves retain source/layout/plan identity. The new browser cases verify actual authenticated competing native writes and continued source validation/reopen at1024x768 and1440x900. Binding forms and provider runtime resolution are separate tasks. |
| Atomic revision-checked writes | Existing semantic/layout CAS, external-file conflict and transactional project history are included. Binding publication writes a unique secure private file, verifies bytes, then atomically commits its head. Concurrent saves yield one200/one412. Real file/partial-write/metadata/before-commit faults preserve the old head. A real committed lost acknowledgement exposes the new head and rejects stale retry. Unique prepared files are retained, never silently adopted or overwritten. |
| Host-correct persistence/locking | Actual native Linux backends are killed at pre-head and post-commit boundaries only after verifying original PID/birth/UID/argv/parent identity. Stock launcher restart observes empty or committed state respectively, without redispatch. Existing native source/recovery, secure acquisition, private backup and Start-boundary cases remain included. No power-loss durability or unsupported-host claim is inferred from process-crash checks. |
| Explicit migration versions | Project envelope1.0 and metadata schema1 remain independent of XDL. T007/ADR-0038 supplies the supported exact metadata0-to-1 stopped-root copy transition, private backup/report and separate activation. New private-binding copy-migration and full restore cases retain exact bytes/head and unchanged plan. Unsupported heads/documents remain preserved and blocked rather than defaulted empty. |
| Portable paths and local-only environment data | Portable source paths retain existing traversal/foreign-path/collision checks. Artifact paths are stored only in private declaration sidecars and never inspected; opaque asset IDs/external credential handles cannot install providers or confer authority. Ordinary portable export excludes declarations/handles; foreign private archive files reject before project allocation. Imported projects have no declarations. A moved private root reports needs_review/unverified/executionAllowed=false; explicit redeclaration only updates context, not admission. |
| Retirement and failures | Pending/uncertain project retirement fences binding publication. New sidecar bytes invalidate older deletion fingerprints. Successful retirement removes the private head in its metadata transaction. Missing, unsafe, corrupt, oversized, future and malformed head/file cases never reset or overwrite state. Secure native I/O absence is a typed503; invalid authenticated requests do not echo private values or allocate files. |

The initial route cohort fails13/13, then passes13/13. The next corruption/failure
review passes15 and fails4: malformed head decode, unsafe stored-path diagnostics,
retirement publication fencing and orphan head removal. All four are repaired and
the original failures retained. Subsequent41/39/46 cohorts have distinct case
ledgers; their totals are not added together.

Final verification passes310 unique affected backend cases and12 native browser
journeys, including two new declaration-isolation cases and ten existing source
recovery/keyboard cases. All420 recorded source/config/test inputs and6 compiled
UI assets are unchanged before/after. Generated OpenAPI/TypeScript describe the
closed requests and responses. Ruff, TypeScript, architecture, descriptive platform
compatibility and planning consistency pass. Existing TestClient deprecation and
two native-test xunit property warnings remain; dependency pins are unchanged.

Provider resolution, physical authority, T060 artifact use, full T010/T014 security
and acceptance campaigns are not established by declaration storage. T002's remote
dependency distribution remains independently incomplete; the locally admitted
SDK and offline provisioning are a separate demonstrated environment. No SDK or
companion code is changed. Windows delivery remains out of scope under ADR-0036.
The user's existing demo, private sessions and original Argus evidence are untouched.

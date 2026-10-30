# Linux foundation component review

Authority and scope: ADR-0036, existing M0–M4 task definitions, and the admitted
Linux installation of platform `12615d402ba16cde3cd48c55b70aca464ea90261`.
The pre-repair findings are in
[`LINUX_REASSESSMENT_REVIEW.md`](../../../docs/implementation/LINUX_REASSESSMENT_REVIEW.md).
The [verification record](verification.json), case ledgers, exact input hashes and
commands retain each phase separately.

## T005 — XDL corpus and CLI/library equivalence

| Task clause | Actual evidence |
| --- | --- |
| Minimal supported corpus | Checked-in reference YAML, explicit experiment/evaluation Profile resources and expected immutable plan/semantic identities; `test_checked_in_corpus_preserves_pinned_platform_identity`. |
| Explicit dependencies and invalid inputs | Two new shared CLI/library cases remove the declared Component or experiment Profile. Both actual tools reject the same original inputs with `XDL-REFERENCE-UNRESOLVED-RESOURCE` or `XDL-SEMANTIC-PROFILE-MISSING`; unknown extensions, invalid fields/types and unsafe source names remain covered. |
| Source versus semantic identity | Comments, ordering, CRLF, JSON, Unicode/space source locators and nonsemantic display metadata retain platform identities; supported parameter changes alter them identically. |
| Native selected-library execution | All 27 adapter and 17 CLI/round-trip cases pass in the final 200-case Linux cohort. The CLI is an actual isolated interpreter/subprocess, using the same explicit admitted profile schemas. No validator/compiler stand-in is used. |

All T005 clauses are proven for the amended Linux host scope. Its component can
close. This does not implement a standalone Lite binding, accept AC-002 as a whole
or complete the separate project-format migration work.

## T009 — Negative API/import and file-boundary tests

| Task clause | Actual evidence |
| --- | --- |
| Untrusted origin/host and unauthorized mutation | Four supplemental authenticated/anonymous import cases enforce the original session, exact Host/Origin and CSRF token; valid archive payloads allocate no project through those rejected requests. Existing strict API/error-envelope negatives also pass. |
| Traversal, drive/UNC/device paths, reserved names and collisions | Existing portable-name/security cases plus new explicit device/UNC negatives run through the native Linux API. |
| Symlink/junction escape | Existing ZIP link rejection and actual managed-source/descriptor traversal tests remain retained. New foreign DOS directory/reparse attributes cannot create a junction; an allowed entry carrying such attributes becomes a plain source file, preserves the private target bytes, and cannot execute. This is inert foreign metadata, not native Windows verification. |
| Unsafe archives and oversized inputs | HTTP entry-count, per-document, compression-ratio, aggregate expansion and total-request attacks reject before allocation. Aggregate fixtures explicitly stay below each individual bound. A separate direct-host parser test covers its compressed-byte bound, which HTTP rejects earlier at the base64 request boundary. |
| Secrets, scripts and unsupported executables | Synthetic inline credentials and script-like profile sidecars reject without echoing content. Python/shell file kinds reject. HTTP negatives use a process-dispatch trap and verify existing project metadata, source bytes, file membership and operation/run ledgers remain unchanged. |
| Unknown valid data stays inert | Valid opaque manifest metadata and exact XDL bytes survive import. Existing unknown-extension inspection/admission tests preserve unsupported content and block execution. |
| Failure evidence first | Ten HTTP malformed-envelope/name/layout cases fail on the original importer. Shape guards now return typed `MANIFEST_INVALID` before allocation; the original red cases remain retained. |

The final affected cohort passes 200 cases. The expanded import suite passes 33,
overlapping the earlier 28 import cases: **205 unique final passing cases**, not
233. All prior 28 import cases are byte-identical after removing the five additions
and their TestClient import, verified against the captured source hash.

All T009 testing clauses are proven for the amended Linux scope. T009 can close;
T010's broader implementation/dependency review, T007's migration workflow and M0
acceptance remain open. Removing Windows alone did not close either task.

## Residual findings and limits

The original full run remains **1,456 passed / three failed**, on 400 unchanged
inputs. The corrected catalog assertions and new import checks passed affected
verification; no new passing full-suite claim is made. The first successor's
116/2 result retains the two incorrect proposed test assumptions, repaired before
the final passes. No production evidence-reference or profile-lock semantics
changed. All project-service AST outside `import_archive` remains identical to
the baseline. One installed FastAPI/TestClient deprecation warning remains.

The roadmap, two acceptance procedures, matching traces, package metadata and
current operator/provider guidance now use Linux delivery and Windows out of
scope. Historical Windows failure/NOT_RUN records remain unchanged. The package
description distinguishes separately configured provider admission from the stock
reference installation. No physical permission, live provider, first-time-user,
normative SADS, independent milestone or release acceptance is inferred.

The committed product candidate `63560071e76cecdfd38ee4486b2aae55fba9a9de`
subsequently passed a fresh offline native package extraction/provision/start/UI
index/Unicode-project/authoritative-compile/owned-shutdown smoke. Every archive,
manifest and extracted payload hash matches; 154 source payloads match that exact
commit and six UI files match the tested browser assets. The package retains the
canonical accepted SDK12615d402 identity and declares Windows out of scope.
The initial offline attempt lacked one cached wheel; its failed receipt is kept.
Frozen cache preparation preceded a separate fresh successful offline extraction.
This is prepared-cache installation evidence, not remote-only provisioning or a
new browser/full-suite/milestone acceptance claim.

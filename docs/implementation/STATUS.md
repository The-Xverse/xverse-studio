# Current implementation status

Scope: runnable development reference implementation on `implement/studio-m0-m4`. No M0–M4 milestone
or Studio 1.0 release is accepted. The supplied requirements/task IDs and acceptance targets remain.

Latest recorded task completion: **26/100 components**, most recently T045/T046's revision history,
undo/redo transactions and source recovery (`evidence/studio/M2-revisions/`). This is an audited task count,
not an estimate of remaining effort. T026 transport implementation is substantially repaired but
remains open pending a complete current native/browser successor. Windows installation/testing
remains blocked at user request, and native Windows secure I/O remains unimplemented/unavailable.

The latest full Linux backend run passed **547 tests**; typecheck/build and the full **51-check
browser/performance gate passed** on the current candidate (`evidence/studio/M2-revisions/`).
Fresh-host CI for b61c7ec passed (push and PR).
That includes the 30-second native expiry case with actual HTTP 410 and running verified-prefix
recovery. Fresh-host push CI for checkpoint fb8ddb6 had failed that case (a history read racing a
journal append); the PR run passed. Both outcomes are retained in `evidence/studio/native-ci/`.
Earlier failed browser runs remain recorded under `M1-session/`, `M1-modal-keyboard/` and
`release/linux-stream-recovery-2026-10-25/`; they are not rewritten.

Run controls now keep durable Start/Stop/Cancel receipts across lost acknowledgements, refresh,
page close/reopen and a second tab; offer only admitted controls with stated unavailable reasons;
show accepted/delegated/completed/rejected/failed/unknown operation outcomes; and explain unresolved
ownership/cleanup without targeting processes by name, PID or port. The owned worker records a
canonical `command.failed` for an accepted command it never applied.

The React/TypeScript browser UI and native FastAPI backend support System projects, inert import,
source-preserving edits, graph/table projections, typed parameters/connections, explicit authored
Deployment/Scenario variants, catalog/profile locks, preflight, immutable owned runs, recovery,
recorded observations, bounded assertions/metrics, finite campaigns, comparisons, annotations,
project/evidence exchange and explicit run/project/artifact-registration retention. Neutral
Device/Sensor/Actuator/Model and Scenario intent forms now share source/graph identities. Complete
private Linux backup/restore uses anchored acquisition and preserves immutable evidence.
Physical-provider inventory is empty.

Component-complete task IDs, with the exact component scope/evidence in traceability.json:
T003, T006, T013, T017, T018, T019, T020, T022, T024, T028, T029, T030, T031, T032, T036, T041, T042, T044, T045, T046, T050, T085, T086, T087, T092, T094.
T044 was reopened after review, then repaired and reverified for selected-source navigation, empty
draft retention, atomic document switching and external-source inspection.
Other tasks remain unchecked; implemented subparts are recorded as in progress instead of implying
that their native, integration, review or acceptance obligations passed.

| Milestone | Implemented evidence / remaining gates |
|---|---|
| M0 | Public pinned XDL APIs, strict contracts, transactional project revisions, local sessions/CSRF/origin, safe archives, owned executable reference and independent failure repairs. Native Windows/complete baseline gates remain open. |
| M1 | Actual native worker lifecycle/idempotence, exact requested/effective plan, backend crash recovery and real browser/keyboard workflows. Live Lite, five-person usability, full failure matrix and native Windows remain open. |
| M2 | Round-trip semantic edits, graph/source, catalog, profile locks, named authored variants and actual selected-variant runs. Independent composition repairs and successor browser/performance records are retained; live two-industry and bidirectional Windows exchange remain open. |
| M3 | Scoped inventory/authority/lease/clock/recovery fixtures and explicit unsupported production controls. Actual device/provider/driver/permission and physical evidence are BLOCKED. |
| M4 | Bounded evaluator with snapshot-bound metric dependencies, Scenario intent authoring, campaigns, comparison, immutable exchange, annotations and dependency-aware project/run/artifact-registration retention. Reported trace claims and frozen subject links are verified; broader provider effects and complete retained release gates remain open. |

Ready Linux work remains independent of hardware/Windows: T043's node grouping and drill-down
navigation on the canvas. T025 still needs both-native repetition (Windows held); T026
depends on T025; T027 retains its AC-006/007/027 environment clauses and observed partial-start/
cleanup-failure transitions.

The verification descriptions below retain earlier checkpoint results. Their counts, clean packages
and passing CI do not establish the latest candidate's still-open browser/performance gates.

Actual verification records include `evidence/studio/backend-suite.txt` (an earlier 116-test candidate),
M0/M1 independent reviews and their successor regressions, `M2-composition/verification.json`,
`M4-unit/verification.json`, `M4-exchange/verification.json`, `M4-metrics/`, and native browser summaries.
These focused records overlap; do not add their counts or present them as a single final-candidate run.
Final source-candidate verification is recorded separately when complete.

Linux Chromium browser workloads are measured separately from provider timing. The retained 50,000-event
API fixture passed correct 200-record pages at p95 about 17 ms. A Linux browser successor rendered actual
200-record pages at p95 about 180 ms and preserved the 50,000-record source digest. Canvas records include
both passing runs and a later open/validation p95 failure of about 3215 ms against 3000 ms; that failure
is retained. The bounded authoritative-validation cache successor passed open/validation at about
791 ms, selection at about 39 ms and history at about 196 ms. Final committed-candidate verification
is recorded separately; earlier passing samples never erase the intervening failure.

Concrete blockers are DEP-RUN / DEP-RUN-CONFIG (public effective-input Lite contract and permitted
live environment), DEP-FEEDBACK-COMPILER (supported feedback compilation), DEP-XDL-DIAGNOSTIC (some
malformed metadata crashes the selected public validator; Studio reports unavailable/blocks), native
Windows execution/exchange evidence, independently admitted live two-industry examples, an actual
physical provider/device/permission, and a five-person first-time-user cohort. M5 remains deferred.

Launch the current checkout after provisioning/build:

```text
uv run xverse-studio --data-dir .studio-local/data --port 8876
```

Read the local one-use bootstrap file, then use http://127.0.0.1:8876. Follow `docs/user/` for setup,
update, shutdown, backup, recovery, study protocol and retention. A fresh isolated Linux source-package
extraction was provisioned offline from the prepared dependency cache, served its browser index,
persisted a Unicode project and compiled it authoritatively; see `M1-package/linux-initial.json`.
That initial package was explicitly dirty/uncommitted, with a file-hash manifest; a committed candidate
and actual native CI results are required for publication/release claims.

The archive, repository, caches, browser binaries, test scratch directories, built assets and evidence
on the implementation machine reside on the user's loop10 filesystem. Companion repositories stayed
read-only; no physical device or arbitrary imported command was operated.


## Committed candidate verification and current Windows hold

Candidate `0dd3ea89f6b158849499d0b506b1919d05dfa953`: **224 backend tests passed** on
native Ubuntu 22.04.5, with captured application/test source hashes unchanged. Its three real browser
tests passed against the same source: selection p95 32.2 ms, open/validation 587.5 ms and 50,000-event
history presentation 194.4 ms. The exact commands/environment/raw samples are under
`evidence/studio/release/`. Native Ubuntu 24.04 CI also passed dependency installation, build, backend
checks, browser journeys, packaging and clean extraction/startup on that candidate.

The initial Windows Server 2022 Datacenter 10.0.20348 lane **failed installation** because the pinned
platform repository includes a filename invalid on Windows. Application/browser checks were NOT_RUN.
At the user's explicit instruction, Windows installation and testing are now **BLOCKED**. The CI matrix
excludes Windows until that scope is resumed. Its original failure remains in
`evidence/studio/native-ci/windows-initial-install-failure.json`; passing Linux jobs do not close it.

A byte-verified pure XDL wheel, license/provenance and preparation helper were preserved locally under
`.studio-local/held-windows-packaging/2026-10-25/` on loop10. They are held work, not integrated into
`pyproject.toml`/`uv.lock` and not presented as a verified Windows installation. No companion repository
was modified. The current Linux dependency pin remains unchanged.

## Earlier authoring, retention and recovery checkpoint

The current source cohort passed **350 backend tests**, with application/test source unchanged during
verification, and **nine Playwright checks** (six real browser journeys and three pure projection
checks), with no failures/skips. Chromium measured 30 repetitions after one warm-up: selection/inspector
p95 **38.4 ms**, open/authoritative validation **1,010 ms**, and 200-row history presentation over the
50,000-record recorded fixture **247.8 ms**. Exact logs, samples, hashes and limitations are under
`evidence/studio/release/linux-cohort-2026-10-25/`. These results overlap component runs and are not
added together. History fixture results are not external simulator/device evidence.

A fresh source-package extraction provisioned offline from the prepared dependency cache, served its
UI, persisted a project and compiled authoritatively. Its first attempt omitted the installed Python
from the child PATH and failed; the original receipt is retained alongside the successful environment
correction. The package includes its support-matrix document. Full contributor checks require the
repository checkout; the runnable application bundle does not contain the complete test/spec corpus.

Independent reviews recorded and repaired malformed dependency proofs, bounded source reads,
observer/assertion references, deep edit handling, descriptor acquisition, SQLite/WAL staging,
operation-wide directory continuity and incomplete-restore marker ordering. Original findings and
intermediate failures remain retained. Source inspection distinguishes external bytes from committed
source, preserves the bytes, and blocks authoritative save/execution until recovery.

The current secure managed-reader implementation is Linux-only and explicitly fails unavailable on
other native hosts. An admitted Windows implementation is still an owned gap, separate from the
upstream Git filename issue; Windows installation/testing stays held. No WSL/container substitution
or Windows success is claimed.

Readiness display and reported trace-claim components now have successor evidence below. Next ready
work includes remaining T018 admission negatives, source/time filtering, cursor resynchronization and
diagnostic explanation cases.
No M0–M4 milestone is accepted; M5 remains deferred.

## Readiness and reported-claim successor

T020 and T094 are component-complete after independent review and native browser repairs, bringing
the total to 17 of 100 tasks. Readiness exposes ten independent facts, exact selected-provider limits,
affected subjects/remediation and a frozen declared-intent plan. Unsupported selected providers stay
unavailable without reference substitution. Immediate Start admission and campaign replay preserve
input/provider identity and durable idempotency. Annotation sidecar 1.1 preserves exact optional
reported claim text and frozen model/Scenario/definition/evidence subjects, without changing assertion
v1 schema or canonical evidence. Run switches and delayed annotation responses cannot retarget edits.

The final native Linux backend cohort passed 393 tests with source unchanged, including the bounded
snapshot-display repair. Its earlier 388-test predecessor, 13 focused reader/rerun checks and
independent successors are retained separately; overlapping counts are not added.
The final browser source passed 15 checks (ten browser journeys and five display/projection checks),
with no failures/skips/flakes and unchanged source hashes. Thirty repetitions after one warm-up passed:
selection p95 29.5 ms, open/validation 590.4 ms, and history presentation 196.2 ms. These retain their
owned browser/recorded-fixture scope. Evidence is under
`evidence/studio/release/linux-readiness-claims-2026-10-25/`; packaging/publication evidence follows
its own recorded result. Clean product commit 180d026 passed the fresh offline package smoke;
publication/CI state is reported separately. Native Windows and all unmet milestone gates remain unchanged.

## Earlier evidence-selection checkpoint

Twenty-one task components are complete, including T018/T019's independently reviewed admission
matrix and T029/T030's owned evidence query and Results views. Evidence query 1.0 applies exact
element/emitter/observer/field/severity/time predicates before bounded paging. Source ticks remain
exact signed strings; receipt codecs and original metadata are separate. Missing/invalid time never
becomes zero or an array index. Unknown/mixed clock, resolution or numeric-unit interpretations stay
in the table. Facets, omitted rows/columns, original gaps and integrity remain explicit. Obsolete reads
cannot overwrite a newly selected run/filter, and wide raw tables support keyboard scrolling.

The current full cohort passed 466 backend tests and 21 browser checks (16 real browser journeys,
five display/projection checks), with unchanged source hashes and no failures/skips/flakes. Thirty
repetitions after one warm-up passed: selection p95 36.6 ms, open/validation 1,100.4 ms, and 200-row
history presentation over 50,000 retained fixture events 929.8 ms (limit 2,000 ms). New whole-run
metadata and filter scans add query work; these are measured browser/read workloads, not provider
scalability or physical-clock evidence. The exact receipts are under
`evidence/studio/release/linux-evidence-query-2026-10-25/`. Clean product829d428 passed native Linux
fresh offline package provisioning/start/UI/persistence/public compilation; publication/CI outcomes
are reported separately.

T028 still needs explicit restriction/private-log and advancing-producer/slow-consumer gap fixtures.
T026 expired-cursor resynchronization and T031/T032 explanations remain ready software work. The
previous published de395ff checkpoint passed both native Ubuntu24 CI runs; that evidence does not
stand in for new uncommitted work. Windows installation/testing remains held, native Windows secure
I/O is unavailable, all M0–M4 milestone gates remain open, and M5 stays deferred.

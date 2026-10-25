# Current implementation status

Scope: runnable development reference implementation on `implement/studio-m0-m4`. No M0–M4 milestone
or Studio 1.0 release is accepted. The supplied requirements/task IDs and acceptance targets remain.

The React/TypeScript browser UI and native FastAPI backend support System projects, inert import,
source-preserving edits, graph/table projections, typed parameters/connections, explicit authored
Deployment/Scenario variants, catalog/profile locks, preflight, immutable owned runs, recovery,
recorded observations, bounded assertions/metrics, finite campaigns, comparisons, annotations,
project/evidence exchange and explicit run-file retention. Physical-provider inventory is empty.

Component-complete task IDs, with the exact component scope/evidence in traceability.json:
T003, T006, T013, T017, T024, T036, T041, T042, T044, T050, T085, T086, T087.
Other tasks remain unchecked; implemented subparts are recorded as in progress instead of implying
that their native, integration, review or acceptance obligations passed.

| Milestone | Implemented evidence / remaining gates |
|---|---|
| M0 | Public pinned XDL APIs, strict contracts, transactional project revisions, local sessions/CSRF/origin, safe archives, owned executable reference and independent failure repairs. Native Windows/complete baseline gates remain open. |
| M1 | Actual native worker lifecycle/idempotence, exact requested/effective plan, backend crash recovery and real browser/keyboard workflows. Live Lite, five-person usability, full failure matrix and native Windows remain open. |
| M2 | Round-trip semantic edits, graph/source, catalog, profile locks, named authored variants and actual selected-variant runs. Independent composition repairs and successor browser/performance records are retained; live two-industry and bidirectional Windows exchange remain open. |
| M3 | Scoped inventory/authority/lease/clock/recovery fixtures and explicit unsupported production controls. Actual device/provider/driver/permission and physical evidence are BLOCKED. |
| M4 | Bounded evaluator with snapshot-bound metric dependencies and separate verdicts, campaigns, comparison, immutable exchange and revisioned annotations/run retention. Broader provider scenarios, broad shared-dependency retention and complete retained release gates remain open. |

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

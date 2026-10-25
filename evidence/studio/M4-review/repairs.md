# M4 review repairs and verification

This follows the findings retained in `findings.md`; it does not replace them.
All repairs preserve the feature's requirement, task and acceptance IDs and its
separate execution, assertion, cleanup and integrity dimensions.

| Finding | Repair | Focused verification |
|---|---|---|
| M4-R01 | Startup marks interrupted accepted/running evaluation execution `error`, verdict null, with immutable interruption reason. It does not implicitly reevaluate. | `test_restart_marks_interrupted_evaluation_and_retention_unknown_without_replay` |
| M4-R02 | Retention persists intent/idempotency before filesystem effects, rechecks the dependency fingerprint, commits each outcome, reports partial failures, and preserves snapshots/result history. Startup leaves interrupted apply unknown; an exact retry reads its durable result and never repeats deletion. | `test_retention_apply_commits_intent_and_does_not_replay_effects`, `test_retention_partial_filesystem_failure_does_not_claim_complete`, stale-plan and interrupted-apply tests |
| M4-R03 | Campaign operation reflects delegated/unknown/completed scheduling; final cancelled children preserve campaign cancellation. Cancellation has its own durable operation and per-active-run outcomes; interrupted cancellation becomes unknown without blind resend. | Pure scheduler crash/cancel tests, actual two-child native reference campaign, actual HTTP cancellation and startup interruption tests |
| M4-R04 | Extraction and evaluator use identical UTF-8 canonical definition bytes. | `test_unicode_definition_digest_uses_the_same_canonical_bytes` |
| M4-R05 | Coverage mapping uses exact rational arithmetic; mapped samples require exact integer-aligned ticks. | `test_large_clock_ticks_keep_exact_rational_coverage_boundaries`, clock-uncertainty and half-open-window fixtures |
| M4-R06 | Annotation create/update checks evidence ownership and frozen model references. Malformed/credential-bearing/executable URI targets reject as typed errors. | Revision/reference HTTP negatives, malformed URI, credential and history fixtures |
| M4-R07 | Definition extraction verifies snapshot digest and authoritative profile validation. Evaluation admission verifies selected frozen digest/references; canonical projection compares effective plan/semantic identities and invalid evidence cannot yield pass. | Snapshot mutation, wrong digest/evidence selection and canonical-journal corruption HTTP negatives |
| M4-R08 | Evaluator checks declared sample caps before serialization and counts encoded bytes incrementally with wall-budget/cancellation checks. | AST/depth/reference boundaries, tighter sample/byte caps, cancellation/budget and invalid evidence fixtures |

The final owned verification command, environment, exact source hashes and output
are in `../M4-unit/verification.json`. That record identifies a working-tree
candidate and checks that its owned files were unchanged during the run. The root
agent must additionally bind all retained evidence to the eventual release commit.

The evaluator and campaign are real owned reference implementations. The laboratory
contract cases are explicitly fixtures. Native Windows execution, two independent
industry implementations, real physical-device integration, external simulator
admission, novice measurements, performance/accessibility gates, bidirectional native
portability and full evidence-bundle exchange remain separate acceptance obligations.
No M0–M4 milestone is declared complete by this component review.

## Evidence exchange follow-up repairs

- M4-R09: run exports include exact `evaluations.json` and `annotations.json`,
  including annotation revision histories and pinned trace links. All text and
  canonical journal envelopes are screened for credentials; no secret records are
  silently removed to manufacture a clean report.
- M4-R10: imports accept only a bounded portable ZIP allowlist, reject links,
  duplicate/colliding paths and undeclared files, verify the exact digest table,
  original snapshot digest, public platform plan digest/semantic identity and the
  original canonical journal hash chain/digest. Matching installed compiler
  identities permit an offline source/plan equivalence check; absent semantics
  remain unresolved. Source-declared invalid/partial/unavailable evidence is never
  promoted. Original bytes and reports remain immutable, with separate current
  inspection status. Import creates no run, project, provider or execution authority.
- M4-R11: strict JSON rejects duplicate keys, nonfinite constants and floating
  numeric overflow (`1e999`) with a typed error.
- M4-R12: conflicting manifest/report availability uses the more conservative
  status and retains both declarations and a diagnostic.
- M4-R13: imported inspection scope identifies recorded evidence. Source scope is
  a separate declaration; unsupported provider readers are unavailable and import
  confers no provider/device admission.

The independent review agent confirmed M4-R11/R12 before these repairs. Native
reference export/import, exact derived records, tampering, unsafe archives,
credential rejection, conservative status handling and immutable stored-file
inspection are exercised in `tests/integration/test_evidence_bundle_exchange.py`.
The final command/source hashes/output are in `../M4-exchange/verification.json`.
Native Windows and bidirectional native portability remain NOT_RUN.

## Metric dependency follow-up repair

M4-R14 is repaired for the admitted reference evaluator. Snapshot extraction checks
the entire bounded definition graph, metric-only targets, acyclicity and exact
version/digest pins. The HTTP operation persists each prerequisite job before
executing it against the same frozen snapshot and canonical evidence selection,
then persists its immutable result before any dependent evaluation. Job records
include input definition/evidence identities and the evaluator implementation
SHA-256 before execution; dependency links pin actual job IDs and result digests.
Missing, invalid or unfinished prerequisite data cannot provide a known scalar.
Parent idempotency retries create no extra jobs and conflicting payloads reject.

The first real HTTP metric-reference case failed with indeterminate before this
repair, confirming the missing API resolution. After repair, eight actual HTTP
metric cases plus retained evaluator/advanced regressions passed: 46 tests in
58.20 seconds. See `../M4-metrics/verification.json`. Conversion tables remain
explicitly unadmitted; no conversion semantics or unit compatibility is invented.
Run-summary aggregation is registered through a trusted backend callback; the root
service retains lifecycle and cleanup ownership. The callback checks the actual
snapshot digest before its bounded definition cache, treats every frozen assertion
as required, selects its latest matching immutable result, and keeps scalar metrics
separate. Before any attempt the verdict is null; missing required results after an
attempt are indeterminate, failures take precedence, and all required passes produce
pass. Missing unscheduled jobs never imply a running evaluator; running, error and
complete execution statuses are recorded independently with per-definition counts.
Later interrupted/error attempts cannot retain a stale earlier pass.

The final isolated metric/aggregate HTTP suite passed all ten tests in 45.78
seconds, including required-all aggregation and preservation of lifecycle/cleanup.
See `../M4-metrics/aggregate-verification.json`. An attempted combined 48-test
capture was terminated externally with SIGTERM (exit 143) before producing a
pytest result; it is retained as incomplete in `interrupted-48-check.json`, with
no passing or application-failure claim. Root complete-candidate verification is
separate from these scoped checks.

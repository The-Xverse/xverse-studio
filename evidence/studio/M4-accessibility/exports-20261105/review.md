# Export keyboard component review

The change adds a fixed native test suite and bounded archive verifier, with no
production UI/backend semantic change. The shared contributor runner permits only
the full eight-case export matrix for exact accounting. Other suites retain their
read-only ledger guard. Imports, export operation/idempotency writes and the single
copy-local inert binding are explicitly accounted; no provider callback is admitted.

The archive verifier reads bounded ZIPs without extraction/execution, rejects
duplicate/traversing entries, checks server/download/receipt identity, and compares
authored and frozen evidence bytes independently. Private bindings, current session
values and machine-side session/database files must be absent. Current project
exports and frozen run evidence retain their separate identities. The legacy
`evidence/reference.jsonl` filename does not imply reference workload execution.

The observed valid public compilation survives both new project imports with equal
semantic and plan digests. The test compares actual original/imported compiler
outcomes rather than synthesizing a successful compilation. Evidence inspections
check original run/snapshot identities, six stored evaluations, inert authority and
Escape focus. One explicit503 per refusal case is a labelled transport fixture;
the retry reaches the actual native backend and yields a verified ZIP.

Review findings repaired in contributor verification: stored project document
descriptors lack `content`, so source readback uses `read_bounded` and the persisted
document digest. The copied export ledger is intentionally mutative; the outer
wrapper now checks exact +8 operation/idempotency and +2 project/importedEvidence
deltas. Original raw tracebacks were not retained, so history identifies that limit
instead of presenting reconstructed logs as originals. A legacy console summary
label remains qualified by the exact native ledger before/after records.

Final eight journeys and four static checks pass with575 Git-bound source inputs
and six unchanged previously reproduced UI assets. Seventeen captured original
descendant handles exit; sampling cannot establish complete short-lived coverage.
No actual Autoverse runtime infrastructure is restarted. The original environment
and unrelated checkout changes remain untouched. Current unsupported evaluation
mapping stays unsupported; historical export grants no admission.

This is a component self-review, not independent milestone acceptance. Full
binding/substitution, fresh admitted evaluation/campaign keyboard work, actual AT,
supported-browser and required-host gates remain open. Windows is separately frozen.
No task or milestone is closed by this evidence. Work pauses after this checkpoint
under the user's stop-after-current-work instruction.

# Persisted run observation review — 2026-10-30

This reviews the T023 native ownership/reconciliation boundary on source
`7f7878aedb1dd293a87a81fa8f3a26fa63f027c2`, without changing its task scope.
The historical late-Stop code mismatch stays unresolved: original raw records
were not retained, so passing repeats cannot reconstruct its original interleaving.

## Findings before repairs

`Runs.read` decodes the provider's persisted state and immediately calls `.get`,
indexes `state`, and iterates `commandResults`. Non-object roots, absent lifecycle
keys, malformed result collections and invalid field types can escape as server
exceptions or be promoted into the cached run/operation. A malformed ownership
observation must not grant command authority, trigger respawn or contact a guessed
process. An invalid new report must not erase already committed terminal facts.

Add authenticated API corruption cases using explicitly controlled metadata and
fake identities. Forbid all process lookup/launch/delegation, retain exact original
report bytes, verify unknown active ownership and pending operations, and verify
controls refuse before creating another operation. These are corruption fixtures,
not native process or physical acceptance. Existing actual owned native restart,
identity and command tests must remain separate and be repeated after any repair.

The repair must validate the existing report envelope before promotion, share the
same shape checks on terminal reacquisition, preserve unknown private fields, and
leave original report/evidence bytes untouched. No platform API, provider permit,
capability or process-signalling authority may be broadened. A short ADR will
record the closed known-field checks and retained compatibility before changes.

The initial 16 corruption cases finish 15 failed/one passed, with two additional
shutdown errors after malformed lifecycle values entered cached metadata. The
first shape-guard repair passes all 59 affected corruption/identity/owner/lifecycle/
command-event checks. This does not resolve the separate historical late-Stop race.

The same review also finds that `op.update(result)` can overwrite immutable
accepted fields or affect another run's operation if a correctly shaped report
names a foreign command ID. Add separate cross-receipt negatives before repair.
All reported command IDs must identify original accepted non-Start commands of
this run, and reported immutable identity/authority/input fields must agree with
the original acceptance. Preserve opaque result metadata and do not rewrite the
report. A malformed command section cannot promote any new observation first.

Those four scope cases fail on the first shape-guard successor; its opaque-field
positive control passes. Also cover nonfinite/unencodable result JSON before
SQLite serialization, and a known terminal run whose pending command cannot be
settled from a malformed newer report. Known termination and command uncertainty
must remain separate. These add no provider or physical operation.

The startup grace also currently treats a present rejected report like an absent
initial report. An explicitly malformed or foreign-owner report during preparing
must disable controls immediately; it cannot inherit the five-second grace meant
for an original task whose first report is not yet available. Add those two
negatives while preserving the original absent-report native startup path.

The expanded native regression finishes 103 passed/one failed in308.61s. Its
failure is a compatibility finding: owner-signed maintenance stops may have
provider-only receipt IDs with no Studio ledger row. Retain those result fields
as opaque source data and ignore them for ledger promotion; do not reject verified
lifecycle facts or allocate a Studio operation. Known foreign IDs still reject.
The v1 operation envelope also recognizes rejected/cancelled terminal receipts.
Add positive coverage for those existing statuses and unknown provider-only IDs.
Compare reserved fields by canonical JSON identity, so Boolean/numeric Python
equality cannot rewrite an accepted request's fingerprint.

The compatibility repair passes all30 focused corruption/preflight checks. A
separate source review finds a concrete terminal-boundary defect: the fallback
comment says the worker has finished, but the code checks only terminal lifecycle.
An original BackendTask may still be finalizing cleanup and its command result.
Also, a terminal snapshot read before the original producer exits may omit the
producer's final result; the current code never reacquires that final snapshot.
Add actual owned reporter-thread barriers and a delayed terminal-read fixture.
These reproduce this class of stale-result failure without claiming the missing
original historical late-Stop interleaving has been reconstructed.

All three reporter completion cases fail before repair. The existing controlled
command-event fixture also incorrectly reports `poll() == 0` while its worker
function is still executing inside the test process. Repair that fixture lifetime
to reflect the actual function return; keep it explicitly separate from the real
owned native subprocess and original backend-task cases.

The read path also lacks a comparison between the report's lifecycle version and
the already verified cached version. An old, correctly shaped report can roll
back state/CAS inputs or re-enter a completed lifecycle. Add two stale-report
negatives; stale active observations must lose authority while already known
termination and its completed receipt remain preserved.

The final native cohort passes113 cases on404 identical before/after inputs.
Review also requires that an exited producer reporting only accepted/delegated
status cannot leave an apparently progressing operation forever. Its outcome is
unknown, and repeated reads must not rewrite unchanged operation metadata. Extend
the owned reporter cases for these two nonterminal final statuses before repair.

The113 native checks and57 successor checks pass, including the two new pending
statuses and two progress-versus-completed receipt cases. Final frontend contract
review identifies one proposed guard assumption to correct: generic backup
operation history allows cancelled, but the existing RunControls v1 receipt
vocabulary has six statuses and no cancelled. A Cancel command completes normally;
it is not a cancelled receipt. Reject that unsupported status for an existing
Studio command. Conversely, a provider-only receipt's own status remains opaque;
validate Studio status semantics only after matching its accepted ledger identity.
Keep all original phase results and add those direct API cases before correction.

The final schema-consistent cohort passes58 cases with404 unchanged inputs.
A final control-flow review finds that terminal reacquisition validates shape and
owner but does not repeat monotonic lifecycle checks. A file replacement between
the first read and reacquisition could settle a command from an older version or
a different terminal state. Add producer-completion negatives before repair and
apply the same version/terminal policy to this second observation boundary.

Both final reporter-reacquisition negatives and the controlled native-exit version
case fail before repair. Applying the monotonic check to terminal reacquisition
passes61 focused,60 native/identity/cleanup and four original-argv/no-replay cases
(124 unique backend cases). Sixteen native startup/failure browser cases pass.
The extra reconnect run initially has3passes/3fixture-root refusals; correcting
only its private launcher data location makes all three refused fixture cases
pass. The three actual native expiry/acknowledgement/browser-departure cases
already passed. All404 inputs stay identical through the final phases; original
reports and failures are retained. This is no new full-suite or milestone claim.

# T008 storage integrity review — 2026-10-30

Reviewed e64a6bd before changes. Revision commits write project.studio.json and
RevisionHistory.seal retains its manifest, but reopening verifies only document
and supportingFiles entries. The generated envelope is omitted. Compilation,
preflight, semantic edits and export can ignore external envelope changes. The
recovery observer also omits it, so the existing recovery action cannot preserve
or resolve this mismatch. This is a concrete remaining T008 gap, independent of
removed Windows gates and of the completed metadata copy migration.

ADR-0039 records the exact sealed-file/legacy-metadata/layout and explicit recovery
policy before implementation. Add authenticated corruption, Start-race and recovery
cases first, with no real process/provider contact from malformed metadata.

Initial11 cases retain10fail/1pass and one teardown error. Seven corruption cases
prove ignored envelopes and the Start case reaches the forbidden launch stub.
Its pytest.fail BaseException also tears down the TestClient portal; use a recorded
OSError refusal to keep the negative fixture bounded without any process creation.
Two NEW recovery cases initially used an incorrect request schema/status; correct
them to existing expectedRevision/If-Match and200 before reproducing the missing
recovery observation. The healthy layout-only positive already passes.

With the corrected request/negative-launch fixture, all three targeted cases fail
for the actual missing manifest observation/admission. The first repair passes31
affected envelope/revision/conflict/storage cases. Add explicit older metadata
without history and corrupt/foreign history negatives before broader verification.
Read the sealed row through the caller's existing transaction: opening a second
SQLite writer during Start or recovery would deadlock on the current lock.

The broader affected cohort passes174 cases on409 unchanged tracked source/config/
test inputs and six unchanged UI assets. This includes manifest/history faults,
source conflict/recovery, import/export/CLI identity, native crash/restart and
copy migration/secure recovery. The added permanent browser file extends the
source map to410; it exercises actual envelope recovery at both viewports.

Separate T008 finding: generic project-local environment-binding sidecars are
still missing. Installed provider roots and typed asset observations are not a
generic persistent local-binding model. Do not close T008 from the manifest repair
or earlier metadata migration alone. Implement versioned private bindings with
CAS/atomic publication, export exclusion and moved-root revalidation, without
provider contact or granting execution/physical authority. T008 remains open.

All10 browser recovery cases and10 cached-receipt/frozen-rerun backend checks pass.
Final corruption review adds three first-failing cases: malformed recorded JSON,
nonfinite sealed values and unencodable sealed values currently escape inspection.
Require a finite UTF-8 canonical baseline, treat unreadable recorded rows as
unverified (not as missing legacy history), and refuse restore before allocation.
Repeat affected verification after that repair; the earlier174/10 retain their
original source scope. The current draft conflict is deliberately separate from
original frozen snapshots and previously completed idempotent receipts.

Final successor verification passes187 backend and10 actual native browser cases
on412 unchanged tracked source/config/test inputs and6 unchanged compiled UI assets.
Original174/10/boundary10 and three new history failures keep their original scope.
No full-suite, local-binding completion or milestone acceptance is inferred.

# Linux task reassessment — 2026-10-29

This continues ADR-0036 on source `e179895512ab8cae62f8d76634493436f15e07cd`.
The earlier task-closure audit retains its dated evidence and Windows qualifications;
they are historical, rather than current Linux release gates. The existing task,
requirement and acceptance IDs, dependencies and other obligations remain in force.

## Findings before repairs

The full Linux backend regression is still executing. Its 400 captured source,
test and configuration inputs were compared during execution and remain identical.
Observed failure positions identify these tests; final diagnostics and outcomes
must be retained before treating their causes as confirmed:

1. `test_resolution_uses_its_own_flow_list_and_evidence_refs_stay_unchanged`
   applies the owned reference configuration adapter to every prepared example.
   The catalog now includes separate, deliberately uninstalled-by-default external
   demo and admitted platform examples. Verify reference semantics for every
   declared reference example, and verify that other provider inputs cannot be
   executed by substituting that reference adapter.
2. `test_http_profile_locks_and_catalog_are_revisioned_and_inert` expects six
   profiles, whereas the native-runtime declaration adds a seventh. Keep an exact
   namespace/digest/lock membership check, revision checks, inert artifact checks
   and no-execution assertions.
3. `test_explicit_dependency_import_verifies_declared_locks_and_sidecars` likewise
   omits that native-runtime profile. Keep both the exact admitted namespace set
   and the tampered-digest/duplicate-lock negative. A profile declaration is not
   executable provider admission.

Two current delivery documents still say Windows verification is held:
`scripts/package_studio.py` and `docs/providers/reservation-service.md`. Align
them with ADR-0036's out-of-scope disposition. Package/default-start guidance also
needs to distinguish an unconfigured provider from the separately verified
Autoverse platform installation. Preserve earlier package manifests unchanged.

T005's existing adapter and CLI round-trip tests cover valid inputs, unknown
extensions, formatting/source-locator identity and supported semantic edits.
The explicit missing-resource and missing-profile closure cases are absent from
that shared corpus. Add those authoritative diagnostic cases, with the same
actual CLI/library comparison as its other cases, before closing the task.

T009's archive boundary declares compressed/expanded/file-count/per-file/ratio
bounds, but current negative tests do not exercise every bound or the profile
sidecar script rejection. Add authenticated HTTP cases that retain the prior
project set and prove no dispatch. Keep foreign drive/UNC/device-path defenses
on Linux; removing Windows delivery does not remove hostile-input checks.

An isolated direct-service probe on the frozen source confirmed an additional
import defect: manifest roots `[]` and `null`, and a profile-lock list containing
`null`, raise unhandled `AttributeError` with no project allocated. A manifest
whose name is an object is accepted and persists a non-text project name. The
probe uses separate private roots and forbids process dispatch; its original
results are retained in `.studio-local/linux-reassessment/import-shape-probes/`.
Add actual authenticated HTTP shape negatives before repairing the boundary.
Malformed input must have a typed response without project allocation, and
supported opaque extension content must remain preserved.

T007 remains open: current recovery supports database version 1 and refuses
unsupported versions, but that does not implement the project-format migration
preview/report/diff/application/rollback contract. Existing backup success and
unknown-version rejection must not be represented as that migration workflow.

T023 needs a separate clause-level Linux review of the actual native restart,
verified PID/birth/argv ownership, uncertain ownership, command/cleanup outcomes
and no-respawn evidence. Aggregate suite totals alone cannot close it.

No task status or milestone acceptance changes follow from this pre-repair
review. Physical-provider permission and first-time-user measurement gaps remain
independent of the Windows scope amendment. No device operation is authorized.

## Repair verification findings

The original full run finished with 1,456 passed and three failed in 1,535.05s;
all 400 captured inputs remained identical. Diagnostics confirm the three stale
catalog assumptions above. Ten new HTTP malformed-shape cases then failed on the
original importer, including unhandled exceptions and accepted invalid names or
layout roots. The importer repair validates envelope shapes before allocation
and returns `MANIFEST_INVALID`, retaining opaque unknown fields.

The first focused successor run found an overstrict new test assertion that all
evidence element references must be disjoint from resolved flows. That assertion
is wrong: observed flows deliberately remain evidence references. Preserve those
references and the existing command-flow exclusion; verify the effective plan
binding and source immutability instead. This finding concerns the proposed test,
not a production configuration change. Retain the first focused failure result.
That run finished 116 passed/two failed in 154.59s. Its second failure exposed an
incorrect comparison between the request's `profileId` field and the persisted
lock's `namespace` field. Compare the explicit mapping and all three immutable
version/schema/presentation identities. Neither finding requires product changes.

## Next dependency-ready component: T048

T043/T044/T046/T047 are complete. Current CLI/round-trip cases cover source/layout
identity, conflicts and failed-edit recovery, but their export/import stays inside
one service root. Add actual native HTTP backend exchange between separate Unicode
and space-containing roots, including reopen, CRLF/LF changes, retained private
root/session separation and an unresolved physical binding. The binding must remain
unexecutable; this is software contract verification with no admitted device or
physical permission. Compare the exact source and public CLI/compiled identities.

The first native exchange run passes the owned-reference case and fails the
proposed physical fixture's expectation of a valid executable plan. The actual
pinned compiler correctly reports `XDL1-PLAN-REALIZATION-UNSUPPORTED`: Phase1
compiles simulated/virtual/hybrid declarations, not physical realization. Keep
that original failure and verify byte preservation plus identical blocked
compiler/CLI diagnostics for the physical case. Only the supported reference
case can claim executable plan identity. No platform semantics may be weakened.

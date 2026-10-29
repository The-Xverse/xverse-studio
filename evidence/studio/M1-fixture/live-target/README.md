# Owned live target input — focused verification

This is an **uncommitted successor** to published `62c8296`, scoped to the owned
native Linux reference model. It does not accept a milestone or close T033.
The initial focused source/configuration/contract/test/UI identity is the
387-entry [input map](selected-input-hashes.json). An intermediate fixture repair
changed only two test files. The latest finite-JSON repair adds an HTTP boundary
guard; its current388-entry map is in
[finite-json/affected-green](finite-json/affected-green/inputs-before.json).

The **current finite-JSON source passes40 affected checks**. Actual authenticated
requests against a private copy of a completed native run reproduce500 for
`NaN`, `Infinity` and an overflowed exponent; the repair returns422 before
lookup/fingerprinting, preserves finite409, and leaves operations and immutable
snapshots unchanged. Nine contract negatives first fail; they now pass alongside
actual native live-control/lifecycle/I/O cases. Valid opaque JSON remains exact.
The1240 full successor was intentionally interrupted after952 passing cases for
this concrete repair; that prefix is not a full result. Fresh1250 full backend
passes **1,250 tests with no failures/errors/skips** in1157.90s, on the same388
unchanged inputs as the40-case verification. **92 affected browser checks and two
separate performance cases also pass on the identical388-input map**. Clean
native Linux packaging remains pending. The629-case/61-file full browser
collection is separate from execution. See the
[combined verification](final-verification.json).

The initial focused source passes **163 affected backend checks and four new native
browser journeys**, with identical before/after input maps in both phases.
The browser cases run at 1024×768 and 1440×900. The first full execution retains
**1,237 passed /two failed** out of1,239. The reviewed repair passes10 cases,
including an additional native parent-scheduling delay. The fresh1,240-case full
successor was interrupted as described above. The intermediate reviewed source
passes **92 affected browser and two separate performance cases** on the same387
inputs as the10-case repair. Those browser/performance results precede the new
HTTP finite-JSON guard and are not relabelled as current-source results. Published
cleanup verification retains its original source scope in the sibling directory.

The new opt-in Live target reference uses the namespaced Profile and installed
model contract in [ADR-0030](../../../../docs/architecture/ADR-0030-owned-live-target.md).
It declares a model input initialized from frozen configuration, without adding
a native XDL runtime mutability enum. Binding its schema alone grants no control
and preserves ordinary model admission. Other examples retain their controls.
Owned provider1.2 admits at most32 finite dimensionless target changes in [-100,100].

Seventeen new backend cases cover public compilation/identity, inert schema
binding, scoped capability refusals, independent worker refusal of owner-signed
bad old values/bounds/principal/state, running and paused application, actual
control/state evolution, immutable inputs and later draft isolation, concurrent
pending-command refusal, same-key payload binding, provenance, unsupported/constant
declarations and the complete32-change budget. Native helpers verify the actual
child's original PID, birth time, fixed argv and owner digest. They do not bypass
the production ownership check. Canonical completion and durable operation retain
old/new values, time, principal, authority and outcome. Running observation reads
retain `verified_prefix`; terminal reads require `valid`.

Browser cases prove a genuinely delivered change with its acknowledgement lost,
reload and exact same-key/payload recovery without another mutation. They also
verify invalid/empty proposals, preserved proposals after a later observed value,
explicit review and continued editing after another subsequent change. Original
snapshots remain identical after Stop/Cancel. Backend checks separately verify
that later draft target3 cannot replace the run's frozen1 or live2 input.

Original development failures and their original input maps remain under
`history/`. They include unregistered contract/artifact refusal, an oversized
integer overflow repaired by checking bounds before float conversion, and inert
schema binding incorrectly requiring an instance declaration. Test corrections
are identified separately: private ownership facts are not public API fields;
active evidence is a verified prefix; profile discovery now has six entries;
test HTTP mutations must supply their same-origin header. The first browser run
passed both lost-acknowledgement cases and refused both headerless test mutations
with403. No production authorization check was relaxed to repair those tests.
The initial382-input phase predates explicit hashing of the new inactive schema;
subsequent maps include that schema. Those early results are not full-source proof.

The first full failure had a stale five-profile inspection expectation; the
repair explicitly adds the sixth profile and preserves exact duplicate/digest
refusals. The second failure observed an empty child command line while testing
early journal rejection. The Linux test now holds only the original owned request
on a private FIFO until the parent verifies actual PID/birth/argv, then releases
the exact bytes and restores the regular request file. The fixed worker and all
production authority checks remain unchanged. An additional case delays parent
observation by0.35 real seconds. Gate release also runs after a failed observation
so it cannot leave the child waiting on that test input. See [the original full
result](full-original/verification.json) and [reviewed repair](full-repair/scope.json).
The original failed outcome remains separate from the10 passing repair checks;
no fresh full pass is inferred.

The broader native Windows, external Lite/runtime, physical, human/assistive
technology, normative SADS and independent acceptance gates remain open. The full
lifecycle matrix, interrupted-cleanup timing and live-input failure/recovery scope
still require clause review. Counts stay49 completed/41 in progress/10 blocked,
with zero accepted milestones. Prior CI remains source-specific: af25449 PR
passed1211/full623/package115; its push passed1211/622 but failed one keyboard Undo
assertion and did not package. Original key/focus timing and cause remain unknown;
later passing runs do not establish its resolution.

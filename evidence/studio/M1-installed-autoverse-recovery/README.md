# Installed Autoverse recording recovery — T039/T098 progress

**70 completed / 20 in progress / 10 blocked; zero accepted milestones.**
T039 and T098 remain open. This dossier verifies their installed Linux recovery
component and corrects stale Windows scope claims under current supplied rules.

Candidate `96f4b9f41aaa3a2c9f4239e160a2e83b518c3eb3` builds a clean 183-payload
[source package](studio-native-package.zip). Its archive SHA-256 is
`0025ca834be1473e175311b16fc5145899202b99bb0330ef26595c7d1cbe4c55`.
Every archive, manifest, extracted and committed payload hash matches. Six compiled
UI assets match the previously tested build. Pinned offline provisioning succeeds
using the existing prepared cache; installed backend/module origins are verified.
This is not clean-host/network provisioning or a Studio 1.0 release.

A copy of the completed actual Autoverse recording runs through the ordinary
installed native launcher with no external integration configured and no static-dir
override. HTTP serves the package's own index and five asset files exactly.
Duplicate root ownership and live backup refuse safely. Ordinary restart preserves
an unexpired session. Stopped backup and restoration preserve non-session metadata,
receipts, project revisions, snapshots, captured journals and imported evidence;
restoration invalidates copied sessions. Existing destinations and corrupted
protected snapshot data refuse before any destination is created or replaced.

The explicit migration test changes only the known schema-version header on an
actual-data copy. Copy migration preserves the original DB, exact stored identities,
all protected files and the authoritative compiled plan; it invalidates copied
sessions and starts no workload. An explicit subsequent launcher opens the migrated
root. This does not claim that an unidentified earlier release produced this copy.

Three real browser checks pass: Environment at 1024×768 and 1440×900, plus four
actual evidence file uploads/inspection across both sizes. Current inspection stays
separate from the original report; unavailable and invalid imports remain distinct.
The restored ledger retains its original one run, six evaluations and eight
operations. Importing recorded evaluations does not create evaluation jobs. No
new simulator run, operation, evaluation, campaign or dependency fetch occurs.

Three earlier focused Autoverse checks pass for discovery and two native unavailable
integration cases. Their source amendment is explicit: only the recovery driver and
its browser configuration changed afterward; all 527 other inputs stay identical.
The final installed/native/browser stage matches all 529 current Git source inputs.
Overlapping cohorts are not added together. Two harness failures and the original
incorrect Windows manifest remain in [attempts](attempts.json).

[Verification](verification.json), [package binding](package-binding.json),
[commands](commands.json), [native facts](native.json), [browser facts](browser.json)
and [separate same-agent readback](readback.json) record the evidence. The readback
verifies all four original backends and the browser driver absent, three roots
released, exact restored/migrated files and receipt rows, and five imported bundles
against their manifests/reports. Three healthy imports are explicitly unavailable
to the unsupported source reader; two damaged imports are invalid. Private backups,
DBs, sessions and ownership material stay private. The attached ZIP contains only
the exact public source package and compiled UI, not private runtime data.

Original 639 resolved payload hashes and 93 enrolled host-file hashes still match.
Original system Docker remains inactive and its host TAP absent. The pre-existing
router mismatch stays unchanged; symlink target strings were not reaudited. The
original environment was not restored or modified.

Current engineering rules require Linux and Windows. Current package, capabilities
and compatibility metadata separate required targets from verified Linux, with
Windows NOT_RUN. Earlier ADR-0036 and failed Windows checkout evidence remain
historical. Native Windows file/process primitives and installation are unresolved;
Linux results do not pass them. T091/CARLA readiness, full regression, packaging
release, performance, human/AT and independent milestone review remain open.

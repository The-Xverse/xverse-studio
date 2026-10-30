# T010 bounded exchange component review — 2026-10-30

Candidate `0dd2db26bc3d620ec778dae23ff8d901239f7c2f` implements ADR-0045. T010 remains in progress;
counts57 completed/33 in_progress/10 blocked; zero accepted milestones.

The precise20-case baseline uses archived16d2297 source with only the explicitly
recorded available-status vocabulary fix. Fifteen failures reproduce eight unsafe
or unbounded classic/platform download cases, wrong source scope, an export
verification/reopen race, two unsafe journal acquisitions and three changed
imported-file cases. Five controls pass. Inspecting the retained race artifact
confirms report.integrity=valid while included journal bytes disagree with the
original run digest. Earlier fixture omissions, too-early replacement hooks,
blocked import/detail checks and overlapping phases are explicitly qualified in
phase-history.json; they are not extra product failures or acceptance evidence.

Native anchored bounded capture now refuses links/shared files and excess bytes,
checks unchanged acquisition, and verifies exactly the journal bytes included in
the archive. Source scope/status stay exact, including available without claiming
complete coverage. Imported reads retain original source digests and manifest
semantics, enforce file/aggregate bounds, and degrade current inspection for a
rehashed replacement without changing the stored original. The unsupported
original-provider reader remains explicit and imports allocate no execution.

Final337 Autoverse API/native CLI and8 native browser checks pass with zero
skips/flakes on436 unchanged source/config/test inputs and6 tested UI assets.
Ruff for all changed Python modules/tests, architecture checks, spec-package
structure and diff checks pass. The existing TestClient/httpx deprecation stays.
No generic reference workload substitutes for this implementation confirmation.

Clean installed package167 matches161 committed payloads,6 tested UI assets,
all436 contributing inputs and canonical SDK12615d402. Prepared-cache offline
provisioning remains narrower than remote-only distribution acceptance. Its actual
complete native classic demo (browser-input variant) passes native publication,
12 invalid-caller controls/Stop refusals,15 metadata refusals,4 nonfinite refusals,
corrupt-snapshot refusal, original owned Stop and the same terminal receipt.
After Stop under invalid fresh admission it exports exactly the original journal
and frozen snapshot, preserves external_demo/available source labels and valid
export integrity, imports as inert recorded evidence with unsupported-reader
limitations, reads original-bound detail and retries the identical export receipt.
No extra run is allocated and original journal bytes stay unchanged.

All16 original PID/birth instances are absent,3 exact container/config/start
identities are stopped, root lock releases and canonical terminal cleanup facts
match actual state. All21 original platform files and frozen source/UI inputs
remain unchanged. Original native launcher SIGTERM exit-15 is the pinned Uvicorn
signal replay after shutdown, separate from the passing driver exit0. Original
operator backend/viewer/preview are preserved and not restarted. No new Pygame,
Maestro/Argus, physical, second-industry or milestone acceptance is inferred.

Continue T010's remaining native metadata, inert-import/profile/unknown-payload
and complete execution/ownership clause review, then original T011/T014 and later
lifecycle/lab/scenario/acceptance dependencies. The repaired exchange component
alone does not close all T010 or AC-003/032. Windows remains outside scope under
ADR-0036; all historical results and the full original100-task plan are retained.

# T010 session, diagnostics and portable credential component

Actual enrolled Autoverse classic/platform cases reproduce malformed-CSRF server
errors, non-finite/corrupt native-session authority, credential persistence/export
and sensitive validation-location echo. The original122 cases have106fail/16pass;
the22 additional cases have18fail/4pass. Typed UTF-8 scalar controls already work.
Original test source hashes/raw report hashes and distinct observations remain in
`phase-history.json`; overlapping later counts are not added together.

ADR-0044 verifies the existing session shape and finite expiry without repairing
corrupt bytes, compares opaque CSRF bytes safely, applies finite UTF-8 JSON to
opaque bodies/keys, preserves ordinary response security headers on early API
refusals and bounds/redacts diagnostic locations. Text screening recognizes known
authentication assignments/headers and quoted JSON escapes while retaining exact
authored bytes and external handles. Names/layouts and historical portable exports
use the same credential boundary; no secret is resolved or authority granted.

First144 cases pass, followed by an interim309/8 source cohort. A separate actual
Autoverse probe then reproduces a new false positive for gridToken. The matcher
now distinguishes that ordinary suffix from an exact idToken assignment, with
positive round-trip/plan/export/import controls and negative credential cases.
Final317 API/native CLI and8 native browser cases pass on435 unchanged inputs and
6 UI assets. Native browser checks prove inert HTML-like display labels, preserved
source after rejected credentials, redacted schema locations, HttpOnly/Strict
cookies and unauthorized mutation refusal. No runtime is claimed from authoring.

Clean candidate90d6a452ed84cd93c9013ebb502a80e1bef0e94a package167 verifies161
committed payloads,6 tested UI assets,all435 source inputs and canonical SDK12615d402
through prepared-cache offline provisioning. Its actual complete native demo
passes12 invalid-caller input/Stop attempts while running, with no input mailbox,
command, lifecycle or denied-idempotency effects. It then passes all prior active
provider/snapshot/finite-input refusals and native publication, original owned Stop
under invalid admission and identical same-key terminal receipt. All16 original
process instances are absent and3 exact container/configuration/start identities
are stopped; the native root lock releases. Actual canonical cleanup facts remain
valid,21 original platform files and all435 inputs/6UI remain unchanged. Original
native-handle SIGTERM exit-15 reflects pinned Uvicorn signal replay after shutdown;
the live driver exits0. See `nominal.json` and `package-binding.json`.

This is primary-agent component review, not independent milestone acceptance.
T010 stays open for bounded exchange/imported-evidence/metadata reads and
the full security clause review. The original full plan, task IDs/dependencies and
milestone gates remain; counts57/33/10 and zero accepted milestones. Windows is
outside scope; prior failed runs and platform/Argus evidence remain unchanged.

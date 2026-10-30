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

Clean installed complete-demo verification is pending. The live driver now checks
12 invalid-caller input/Stop attempts against an actually running Autoverse demo,
requiring refusal with unchanged mailbox/command/lifecycle before ordinary owned
Stop. T010 stays open for bounded exchange/imported-evidence/metadata reads and
the full security clause review. The original full plan, task IDs/dependencies and
milestone gates remain; counts57/33/10 and zero accepted milestones. Windows is
outside scope; prior failed runs and platform/Argus evidence remain unchanged.

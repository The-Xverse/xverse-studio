# Linux capability discovery scope repair

T004's audit found a concrete remaining ADR-0036 inconsistency: the actual
capabilities API still advertised nativeTargets Linux/Windows and classified
Windows as BLOCKED_USER_REQUEST. The Environment view labelled that field Windows
checks. This contradicts the approved removal of Windows delivery requirements.
The new contract case first fails on the actual advertised nativeTargets value.

Discovery now advertises Linux and OUT_OF_SCOPE_ADR0036; the Environment field is
Windows scope, with an undeclared fallback rather than an invented check result.
Keep the existing response key for compatibility. Host observations and installed
provider OS/architecture declarations are separate and unchanged. Existing foreign
path defenses, historical Windows failures and original package evidence remain.

All69 affected contract/preflight/scenario/inventory checks and4 native browser
journeys pass on421 unchanged source/config/test inputs and6 unchanged newly built
UI assets. Environment is inspected at1024x768 and1440x900; actual binding CAS,
source validation and reopen are also exercised against the new UI. TypeScript,
Ruff, architecture, descriptive baseline and planning consistency checks pass.
The UI is built into a private phase directory; all6 original operator-served
assets are separately verified unchanged. The demo backend is not restarted.

Clean candidate bc80579f5640ceae36c345f4a6a79ade4c5e2357 package164 passes offline
provisioning/native smoke. All158 committed files,6 tested UI assets,421 source
inputs and archive/manifest/extracted hashes match. Installed xverse-xdl retains
the canonical SDK Git URL and exact12615d402. Actual installed authenticated HTTP
verifies Linux-only delivery, Windows out-of-scope, independent provider discovery,
the exact compiled UI index, authoritative compilation and no run dispatch. The
original installed launcher is stopped. This corrects
scope reporting within T004; its whole descriptor/version/generated-contract and
failure review remains open. No task or milestone is closed. Existing dependency
publication, hardware and first-time-human prerequisites remain independent.

Pure descriptor validation probes on deep copies of the built-in reference
descriptor expose the next concrete gaps: malformed SHA256 implementation identity,
string physicalEffects, string supportedHostOS and list limits are accepted;
capabilityRecords=null raises TypeError. No provider is registered or contacted by
these probes. Their input categories/outcomes are retained separately; this scope
repair does not pretend to repair or accept those validation gaps.

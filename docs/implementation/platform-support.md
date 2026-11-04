# Native host and provider support

Current supplied engineering rules require native Linux and Windows. Only the
recorded Linux lanes below have qualifying application evidence. Windows remains
unverified: the historical dependency-checkout failure and missing native secure
file/process primitives are unresolved. The earlier user-approved ADR-0036 Linux
scope and its receipts remain historical evidence; they cannot waive the current
Windows requirement. See ADR-0063 for this precedence and verification correction.

| Lane | Recorded environment | Evidence and limits |
|---|---|---|
| Linux backend | Ubuntu22.04.5 LTS,x86_64; Python3.13.13; uv0.12.17 | Recorded owned/native and approved simulation checks qualify exact candidates. |
| Linux browser/tooling | Node24.22.1; Chromium156.0.8078.4, Playwright browser1248 | Typecheck/build, browser, keyboard and both desktop viewport checks are retained. |
| Linux CI | Ubuntu24.04 | The configured lane is Linux-only. Prior CI receipts qualify their recorded revisions; configuration alone is not current-candidate evidence. |
| Windows | NOT_RUN | Historical Server2022 dependency-checkout failure and backend/browser NOT_RUN retained; no supported release claim. |

Exact versions and source identities remain in the locks, environment records and
candidate evidence. Linux support does not imply every distribution/kernel/browser
combination. The secure-file implementation uses anchored native Linux descriptors
and refuses unavailable primitives. Windows needs its own native implementation and verification; WSL or a container
cannot establish that requirement.
Foreign path/device-name attacks remain import-security cases on Linux.

| Provider | Linux scope | Other hosts |
|---|---|---|
| `studio.reference` | Owned executable reference and controlled fixtures; exact tests qualify scope | Descriptor declarations do not establish another native Studio release lane. |
| `autoverse.demo` | Explicit installed complete simulation with original Pygame driving/cruise; exact live receipts retained | No admitted release claim. |
| `autoverse.platform` | Accepted public Maestro, actual native C++ X-COM and original Argus; two complete browser runs and independent cleanup verified in `platform-observability-foundation/live-browser-experiment.json` | No physical or other-host admission. |
| `xverse.lite` | Existing standalone candidate still requires its own admitted public mapping; Autoverse success does not silently admit it | Unavailable without separate scope/admission. |
| Physical asset provider | No nominated permitted actual device/provider; owned fixtures are not hardware acceptance | No device scan or stimulation authorized by the Linux scope change. |

The separate live-follow successor adds bounded observation polling; its evidence
is recorded independently under `platform-observability-foundation/live-follow.json`.
Native samples may coalesce. Original recorded/assessed incomplete verdicts,
unknown upstream causes and absent simulator-clock mappings stay explicit.

Installation/start/stop/recovery, paths, persistence, performance and usability
obligations remain. Existing task closures record their cited component scope;
no native Windows or full milestone acceptance follows from a Linux-only result.

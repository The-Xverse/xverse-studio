# Native host and provider support

Current supplied engineering rules require native Linux and Windows. Only the
recorded Linux lanes below have qualifying application evidence. Windows remains
unverified: the historical dependency-checkout failure and native secure
file/process obligations are unresolved. ADR-0067 adds a native managed-file
implementation candidate and ADR-0068 adds workspace ownership; Windows execution
of both is NOT_RUN. The earlier user-approved ADR-0036 Linux
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
and refuses unavailable primitives. The Windows handle implementation still needs
native verification; workspace ownership has a candidate, while worker process
ownership and recovery gaps remain. WSL or a container
cannot establish that requirement.
Foreign path/device-name attacks remain import-security cases on Linux.

The owned Windows file suite can be run with native Python 3.13 and provisioned
development dependencies, from the repository root in PowerShell or Command Prompt:

```text
python -m pytest -q tests/platform/test_windows_file_policy.py tests/platform/test_windows_managed_io_native.py
```

Use an owned temporary directory on a fixed local NTFS volume. The suite does not
run an example/provider or require Bash, WSL, a container, `mklink`, device access
or enabled privileges. A Windows fixture failure remains a failure; collection or
skips on another host are not acceptance. Retain the exact OS/release, Python,
filesystem, commands and source identity with native output. The Windows module
does not extend the verified release envelope by itself.

Workspace ownership uses the original held directory and native nonblocking lock.
The launcher refuses linked roots and checks interrupted-restore markers after
taking ownership. New roots and lock files are private. Windows existing roots
must already have a protected owner-only ACL; a refusal does not rewrite an
inherited ACL or change existing lock bytes. The native suite also checks actual
second-process contention, original-process termination/release and held ancestor
names. Linux root permissions become private after winning the advisory lock;
a refused contender changes no root permissions. See ADR-0068 for exact limits.

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

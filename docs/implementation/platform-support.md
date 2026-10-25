# Native host and provider support

Studio's native targets are Linux and Windows. A target is not a verified support claim until its
own native installation, persistence, process ownership and browser acceptance lane has run.

| Lane | Recorded environment | Current evidence |
|---|---|---|
| Linux backend | Ubuntu 22.04.5 LTS, x86_64; Python 3.13.13; uv 0.12.17 | Available host. Executed test records qualify actual supported scope. |
| Linux frontend tooling | Selected Node 24.22.1 LTS; official distribution checksum verified during provisioning | Frontend builds use the selected LTS toolchain. Exact commands and package versions are in the retained verification evidence and lockfile. |
| Linux browser | Chromium 156.0.8078.4, Playwright browser revision 1248 | Browser tests are being recorded against the native Linux backend. Only executed results establish the verified workflow scope. |
| Windows backend | Native x64 target; edition/release/filesystem/browser environment unavailable | NOT_RUN. No WSL, container or remote-Linux substitute is admitted. |
| Windows browser | No Windows desktop/browser environment available | NOT_RUN. Linux browser evidence is not native Windows backend evidence. |

No particular Windows edition/release or browser version is advertised as verified without a record
from that environment. Selecting an edition and documenting its exact installation remains an open
native support-matrix obligation under T001/T002/AC-001/AC-032.

CI declares Ubuntu 24 and Windows Server 2022 lanes for future verification. They remain unexecuted
until the implementation branch is pushed and the actual workflow results are available. CI target
names are not a claim that those hosts have already passed. The initially available Node 20.20.2/npm
10.8.2 environment was superseded by the explicitly selected Node 24 LTS toolchain.

| Provider | Linux | Windows | Meaning |
|---|---|---|---|
| `studio.reference` | Owned native model executable; actual tests qualify the claim | Native Python code path supplied; verification NOT_RUN | Fixture/reference scope only. |
| `xverse.lite` / CARLA | Unavailable: DEP-RUN + DEP-RUN-CONFIG and permitted environment required | Unavailable: native launcher/driver contract also required | Source inspection is not live admission. |
| Physical asset provider | No nominated authorized device/provider | No nominated authorized device/provider | Hardware cases BLOCKED; no device scan or stimulation performed. |
| Native X-COM | Unavailable | Unavailable | Lite flow runtime is not native-core activation. |

Application portability uses native Python paths and subprocess APIs. Portable archive paths use
relative slash-separated identifiers and must reject ambiguous names under both host interpretations.
Project roots may contain spaces/Unicode. Runtime-owned host-local bindings and credentials are
not portable XDL identities. Exact process ownership and shutdown have per-OS evidence obligations;
a PID by itself is not ownership.

The native launcher is the product entry point. Bash Spec Kit helpers remain optional contributor
tools and are not called by application startup. OS service registration, remote exposure, automatic
WSL setup and container runtime setup are not supplied native-core requirements.

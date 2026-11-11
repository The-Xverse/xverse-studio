# Reproduce the existing Autoverse development demo locally

Use **Autoverse with X-Verse platform**, the existing `autoverse-platform`
blueprint, with provider `autoverse.platform`. Its source is
[`blueprints/autoverse.py`](../../services/studio-api/src/xverse_studio/blueprints/autoverse.py).
Do not create a second System or substitute the scalar reference example. If you
already have the development project, open it and retain its edits; the example
card creates another project from the same existing blueprint when needed.

This guide targets the Linux x86_64 Autoverse provider. Windows work is frozen;
there is no verified Windows procedure for this demo. Studio's native backend
and browser are separate from the provider's Docker/KVM/graphics requirements.

## Current reproducibility limits

**This is a development procedure, not a completed clean-machine qualification.**
The existing complete blueprint was exercised locally on 2026-11-10 using the
provisioned development SDK and cached real Autoverse assets: rendered CARLA,
native Pygame driving, Android cluster speed, all three platform views and public
Stop/cleanup were checked. All test-owned runtime and infrastructure processes
were then shut down; approximately 26 GiB RAM was available afterwards. This
live check does not qualify a fresh full Autoverse installation or supply the
missing Lite flow/fault integrations.

On 2026-11-10, `uv sync --frozen` failed because the configured platform Git remote
did not supply commit `12615d402ba16cde3cd48c55b70aca464ea90261`
(`upload-pack: not our ref`). **Resolved on 2026-11-11:** the exact commit is now
published on platform branch `studio/autoverse-sdk-12615d4`. A clean install of
Studio **c8e05dd**, with an empty uv cache, passed `uv sync --frozen`; the installed
`xverse.maestro.execution` API imports and the existing blueprint compiles with
the recorded digests. No dependency or lockfile change is necessary. The native
bridge still requires the admitted offline native dependencies and matching
source/build identities described below. See the
[dependency handoff verification](../../evidence/studio/autoverse-dependency-handoff-20261111/README.md).

The existing blueprint does **not** yet execute every Lite subsystem:

| Component | Existing development integration | Limit |
|---|---|---|
| XDL | Public validation, normalization and experiment compilation | Unsupported semantics block execution. |
| Maestro | Public `xverse.maestro.execution` lifecycle and ownership | This is the admitted successor API, not the private original Lite runtime. |
| X-COM | Actual native C++ bridge on eleven VCU boundary routes | Three routes are sampled; this is distinct from Lite's Python flow runtime. |
| Argus | Actual evidence store, integrity and correlated records | Gaps/coalescing can leave an incomplete verdict. |
| Lite flow runtime | `xverse.flows.FlowRunHarness` is not connected | Native X-COM traffic does not establish Lite flow execution. |
| Lite fault scheduling | `xverse.faults.scheduler.FaultScheduler` is not connected | The classic browser-input-loss example is a different Studio lease fault. |

Completing the last two integrations requires an admitted mapping to the actual
Autoverse boundaries and live verification. Adding flow/fault declarations,
running disconnected fixtures or relabelling provider logs does not establish it.

## Repository checkout for an independent tester

The handoff is the Studio repository branch **`feat/autoverse-reproduction-guide`**,
including this guide, the existing blueprint factory, repeatable tests and dated
development evidence. It is published; the teammate needs repository access:

```sh
git clone --branch feat/autoverse-reproduction-guide https://github.com/The-Xverse/xverse-studio.git
cd xverse-studio
git rev-parse HEAD
git status --short
```

Record the full commit ID and a clean working tree in the independent report.
Use the commit supplied with the handoff; a branch name can advance. The full
recorded runtime candidate is 93ef1d9; later documentation/test-only commits retain
those unchanged production inputs. Do not assume another branch or current
companion heads identify the same tested candidate.

The exact platform SDK commit is published in `The-Xverse/xverse-platform`.
The exact multi-repository Autoverse source pins are checked in as
[`config/autoverse-development.repos`](../../config/autoverse-development.repos).
Native dependency artifacts, CARLA/Cuttlefish system images and locally built
container contents remain separate installation prerequisites.

The teammate installs dependencies and builds the UI locally with section 3,
prepares/enrolls their own environment with sections 2, 4 and 5, then performs
section 6 against the existing blueprint. They do not need a project ZIP to load
it: the example is already in the repository. The portable ZIP under dated
evidence is an optional exchange-test artifact.

Record **PASS**, **FAIL** or **BLOCKED** independently for:

1. Clean dependency installation and local UI build. Report any fetch/install
   failure with its exact command and source identity; another machine's virtual
   environment or `.studio-local` directory is not an installation.
2. Opening and validating the existing eight-file, six-binding blueprint. Compare
   its compiled digests with the dated evidence, and verify unavailable enrollment
   prevents Start rather than silently running the reference provider.
3. Complete actual execution: rendered CARLA camera/sensors, original Pygame
   driving/braking, Android app/video and changing cluster speed, then the three
   actual platform views with shared run/input identities.
4. Public Stop, aggregate cleanup **complete**, released component outcomes,
   stopped owned containers/processes and valid immutable snapshot. Record the
   Argus verdict separately; known drops/degraded intervals remain incomplete.
5. Shutdown of any extra test-owned infrastructure and comparison of pre/post
   available RAM, swap, `SUnreclaim` and `VmallocUsed`. Report a remaining large
   allocation and its owner instead of declaring cleanup from process state alone.

Include the Studio/platform commits, exact Autoverse manifest and image/build
identities, OS/tool/driver versions, commands, run ID, compiled digests, outcomes,
own functional observations and cleanup/memory readings. Redact tokens, cookies,
ADB keys, private paths and raw host logs before sharing. Existing evidence is
the development reference, not the teammate's independent result. Windows and
physical-device tests are outside this handoff's Linux simulation scope.

## 1. Prepare a Linux workstation and record the baseline

Use a graphical Linux x86_64 workstation with working graphics, Docker Engine
and Compose, accessible `/dev/kvm`, Git/Git LFS, `vcstool`, `just`, CMake, Ninja
and the platform's admitted C++ toolchain. Keep the normal user authorized for
its selected Docker daemon and KVM. Follow your system's installation procedure
for these tools; Studio does not configure kernel modules, groups or networks.

Provision Python **3.13.13**, uv **0.12.17**, Node **24.22.1** and its npm for
Studio. Autoverse's component client uses **`/usr/bin/python3`** and its matching
CARLA API, Zenoh, Pygame, NumPy and psutil packages. Installing those only inside
Studio's Python 3.13 environment is insufficient. Avoid starting Studio from a
ROS-sourced shell: foreign `PYTHONPATH` and pytest plugins can contaminate it.

As a practical capacity check, the previous complete local demo consumed about
11 GiB beyond the host's other workloads. Retain at least 6 GiB of available RAM
while running; these are observations/operating margins, not a universal minimum.
Have at least 12 GiB of free runtime disk space after provisioning; Cuttlefish
alone checks capacity for its sparse userdata image. Asset downloads, image
builds and source builds require additional space. Do not start the full demo
when the margin cannot be met or stop unrelated applications automatically.

Record OS, kernel, graphics driver, Python/uv/Node/npm versions, Studio commit,
platform commit, exact Autoverse repository manifest, container image IDs,
CARLA server/client versions, Android build/APK digest and native bridge manifest.
Keep local installation paths, tokens, ADB keys and private logs out of portable
project exports and shared evidence.

## 2. Provision the existing Autoverse installation

Use the checked-in **exact** multi-repository manifest, exported with
`vcs export --exact --nested .` from the development source root. `--nested` is
necessary: plain `vcs export --exact` stops at the enclosing Autoverse repository.
Follow the first-installation section of the pinned Autoverse README. Current
branch heads and the floating versions in `autoverse.repos` are not the handoff
identity; newer OpenSOVD/openDuT campaigns are separate from this Studio demo.

From a new parent workspace containing your Studio checkout, run:

```sh
# The manifest uses GitHub SSH URLs; configure repository access first.
cd /path/to/workspace
GIT_LFS_SKIP_SMUDGE=1 git clone --no-checkout git@github.com:The-Xverse/autoverse.git autoverse
GIT_LFS_SKIP_SMUDGE=1 git -C autoverse checkout --detach 6000fa76f4434452bb8fe241c7117167deb2bcea
GIT_LFS_SKIP_SMUDGE=1 vcs import --skip-existing --workers 1 . < xverse-studio/config/autoverse-development.repos
vcs export --exact --nested autoverse > autoverse.actual.repos
```

Compare every URL/commit in `autoverse.actual.repos` with the supplied manifest.
The root is selected before import because cloning the default branch and then
switching can hit a legacy APK ZIP/Git LFS dirty-file refusal. `--skip-existing`
preserves the root already checked out at the exact pin. Use a new workspace;
it also preserves other existing custom checkouts rather than correcting them.
These commands fetch source only. Fetch the selected providers' LFS payloads and
prepare their images/builds in the steps below before enrollment.

`aaos_digital_cluster/cuttlefish_emulator` is a clone of **`The-Xverse/aaos_cuttlefish`**
at **`b86e0de01ec21fee5417ad396eb4c507f5f1c963`**. Its tracked
`apk/digital-cluster-app-debug.zip` contains the APK used by the local demo:
`digital-cluster-app-debug.apk`, SHA-256
`daf9e86cf2f6e58536bca5cedbc695baadcbf39f0965ad22d65607ddd79827f9`.
Extract that archive as instructed by the pinned Cuttlefish setup.

The actual live test ran from a staged asset tree without `.git` directories.
The exported Git source root was independently matched to it: all 19 enrolled
runtime source files, 92 copied S-CORE files, 10 VCU files, 10 CARLA example files
and 159 SOME/IP build inputs match. This establishes the relevant source binding;
it does not put generated images, native artifacts or Android userdata into Git.
The source root has one uncommitted S-CORE `make.sh` library-check adjustment
(`ldd` resolves launcher symlinks with `readlink -f`). The manifest represents its
committed revision; that working-tree change is preserved and is not published
or silently represented by a commit pin. The compared S-CORE runtime source
files are unchanged. See the dependency evidence for this qualification.

Arrange the directories as siblings:

```text
workspace/
  autoverse/
    run_autoverse.py
    vecu/vcu_zenoh/src/main.py
    vecu/s-core/
    bridges/carla/
    bridges/someip/zenoh-someip-bridge/
    aaos_digital_cluster/cuttlefish_emulator/
  carla-simulator/
    CarlaUE4.sh
  xverse-studio/
  xverse-platform/
```

In the fresh Autoverse checkout, run `just check-host` and inspect `just --list`
against the pinned source. Its provisioning helpers are `just install-zenoh` and
`just install-client` where provided; check their resulting versions against the
actual tested component environment:

| Dependency | Recorded version |
|---|---|
| Component interpreter (`/usr/bin/python3`) | 3.10.12 |
| CARLA server/Python API | 0.9.15 |
| Zenoh router and Python `eclipse-zenoh` | 1.3.4 |
| Pygame | 2.6.1 |
| NumPy | 2.2.6 |
| psutil | 5.9.0 |

Studio's Python 3.13 environment remains separate. Fetching the pinned
`core/zenoh` repository does not select the router binary by itself. The recorded
router was the upstream `zenoh-1.3.4-x86_64-unknown-linux-gnu-standalone.zip`,
SHA-256 `67e6c2ec44ba2bf98456797181b7aa252e78c369ed5092f7ac9fff744c8073c4`.
A mismatched CARLA API/server or another router version is not the tested baseline.

Prepare the three existing companion services, one at a time, following their
pinned READMEs. The development installation uses these commands:

```sh
# From autoverse/bridges/someip/zenoh-someip-bridge
git lfs pull
./scripts/ctl.sh up
./scripts/ctl.sh stop

# From autoverse/vecu/s-core
export SCORE_FOR=X-Verse
source ./prepare.sh
./make.sh
./ctl.sh up
./ctl.sh stop

# From autoverse/aaos_digital_cluster/cuttlefish_emulator
./ctl.sh make
./ctl.sh start
./ctl.sh stop
```

These are explicit **Linux provider provisioning** commands, not commands imported
from a Studio project. `make` is for a fresh emulator installation: it can replace
existing artifacts/runtime state. On an existing working setup, reuse the prepared
assets and normal start/stop commands instead of rebuilding or resetting userdata.
During this preparation, check Android boot completes, ADB connects to the owned
emulator at `localhost:6520`, and `com.example.digitalclusterapp` is installed.
The recorded Android handoff used Android 17 build 16102939; system and CVD
artifacts must match each other and the handoff.

Before Studio enrollment, all three containers must exist and be **stopped**:

| Exact container name | Purpose |
|---|---|
| `bridge-e2e` | SOME/IP bridge |
| `docker_setup-adas_score-1` | Built S-CORE controller |
| `cuttlefish-orchestration-cont` | Android Cuttlefish |

The S-CORE container must expose the built cruise-control executables/configuration
expected by the provider, including `cruise_control_someip_config.bin`,
`gatewayd.exe`, `someipd.exe` and `cruise_control_main`. Images existing locally
without these artifacts are insufficient.

Use the emulator setup's documented host-network preparation. The provider needs
one IPv4 address on **`cvd-mtap-01`** in its selected network namespace; it does
not create or repair TAPs. `/dev/kvm`, Docker, `adb`, `zenohd`, an available
graphical session and the component interpreter must be accessible from that
same prepared environment. Use only the owned emulator; no physical Android
device or steering-wheel access is required. Do not run standalone Autoverse,
CARLA or a second Zenoh router concurrently with Studio's selected stack.

## 3. Install Studio and build its UI

Obtain the reviewed Studio checkout and the exact platform source prerequisite
from the development handoff. From the Studio repository root:

```sh
uv sync --frozen
npm ci
npm run build
```

The previous `not our ref` failure was resolved by publishing the exact pinned
platform commit. If synchronization still fails, record the fetch URL/error and
check access to that published source.
Do not copy another machine's `.venv`, invent Git provenance or edit installed
package metadata. The checked-in dependency pin and lock remain authoritative.
The browser assets should now exist in `apps/studio-web/dist`.

## 4. Prepare the matching native X-COM bridge

Use platform source at the **same pinned commit** as the installed SDK. Its
source can now be cloned explicitly:

```sh
git clone --branch studio/autoverse-sdk-12615d4 --single-branch https://github.com/The-Xverse/xverse-platform.git /path/to/xverse-platform
git -C /path/to/xverse-platform checkout --detach 12615d402ba16cde3cd48c55b70aca464ea90261
```

The platform's
native SDK requires a verified offline prefix and package manifest supplied by
the platform handoff, through `XVERSE_XCOM_TOOLCHAIN` and
`XVERSE_XCOM_PACKAGE_MANIFEST`. CMake runs
`scripts/xcom_dependency_preflight.py`; system headers or a random newer SDK
are not substitutes. Follow that revision's native build instructions and build
the `xverse_xcom_provider_loopback` target with Ninja. Retain its CMake cache,
four static libraries and admitted `nlohmann` headers. Studio does not build or
modify companion sources through its HTTP API.

Use a private, non-symlink output directory. For an optimized bridge, first
configure the Studio-owned bridge in Release mode, then run its admission helper.
Replace the placeholders with your own local verified locations:

```sh
install -d -m 0700 /path/to/private/native-bridge
cmake -S services/studio-api/native/xcom_bridge -B /path/to/private/native-bridge \
  -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DPLATFORM_SOURCE=/path/to/xverse-platform \
  -DPLATFORM_BUILD=/path/to/platform-native-build \
  -DTHIRD_PARTY_INCLUDE=/path/to/admitted-prefix/usr/include
uv run python scripts/build_native_bridge.py \
  --platform-source /path/to/xverse-platform \
  --platform-build /path/to/platform-native-build \
  --third-party-include /path/to/admitted-prefix/usr/include \
  --output /path/to/private/native-bridge
```

Create the output directory with mode `0700` before configuring. The helper
retains the configured Release cache and creates `build-manifest.json`, the
bridge binary and private execution logs. It refuses a mismatched SDK/source,
stale native libraries or unsafe paths. Supply the **directory**, not the binary,
to the launcher. An older unoptimized bridge suffered ingress backpressure in
local driving checks; a successful build alone does not establish load acceptance.

## 5. Enroll this machine and open the existing project

Confirm the selected components are stopped and ports **2000, 2001, 2002, 7447,
6520, 8443 and 8000** are free in the prepared environment. Keep Studio's API
port separate. Do not delete middleware scratch to clear a conflict: unknown
`/tmp/mw_com_lola` or `score-xverse` ownership blocks enrollment.

From the Studio root, start the native foreground owner:

```sh
uv run xverse-studio \
  --autoverse-root /path/to/workspace/autoverse \
  --autoverse-native-bridge /path/to/private/native-bridge \
  --data-dir /path/to/private/studio-data \
  --port 8881 --static-dir apps/studio-web/dist
```

Choose a new private data directory for a fresh machine/environment. Enrollment
pins actual files, images, container identities, SDK and native artifacts. It
does not download dependencies or repair a previous installation. Do not copy
another environment's enrollment/claims to the new machine. Preserve an existing
working development data directory and project; create a separate data root when
qualifying another prepared environment.

Open `http://127.0.0.1:8881`, read the printed local `bootstrap.json` path, and
enter its one-use `bootstrapToken` in **Connect to Studio**. The token expires
after five minutes; restart the launcher for a new one if necessary. Keep it out
of screenshots, URLs and shared files.

Open the existing development project, or select **Autoverse with X-Verse
platform** from the example cards. The complete project contains eight XDL files
and these six bindings:

| Binding | XDL resource / realization |
|---|---|
| `carla` | Logical device / simulated vehicle |
| `vcu` | Logical device / virtual VCU |
| `someip-bridge` | Logical device / virtual communication bridge |
| `score` | Component / virtual cruise controller |
| `android` | Component / virtual digital cluster |
| `driver` | Component / virtual native Pygame operator controls |

Select **Validate**, inspect **Connections**, **Deployment** and **Experiments**,
and confirm provider `autoverse.platform`. The default duration is 600 seconds;
the supported range is 30–1800 seconds. An unavailable provider must yield
blocked readiness and a disabled Start; valid XDL alone does not imply readiness.
Project **Export** and home-screen **Import project archive** exchange portable
declarations, not the host installation or permission to execute it.
After import, check the selected provider explicitly: this candidate can default
the imported project to `studio.reference`. In **Preflight & run**, choose
**Execution provider** → `autoverse.platform` and recheck readiness on the enrolled
host. If it is absent, resolve enrollment first. The reference provider cannot
execute this complete Autoverse System.

## 6. Run and verify the complete demonstration

1. Select **Preflight & run**, inspect diagnostics and the compiled frozen inputs,
   then **Start frozen snapshot**. Preparation/Android boot can take minutes.
   Monitor available RAM and disk; Stop if the margins above cannot be retained.
2. Wait for CARLA rendering, camera/sensor data, the original **Vehicle Manual
   Control** window and the Android digital cluster. Missing Android or a blank
   renderer is a failed complete-demo check even if process state says running.
3. Focus the native Pygame window. **W/Up** accelerates, **S/Down** brakes,
   **A/D** steers. Release the accelerator, then **C** toggles cruise;
   **Z/X** decreases/increases the target by 5 km/h. **Q** toggles reverse.
   Verify observed speed changes, then brake to rest and release all keys.
4. Open **Android digital cluster**. If its connection uses the wrong router,
   open the app's gear/settings screen, choose **client (router)** and
   `tcp/<the selected cvd-mtap-01 host IPv4>:7447`; Save and restart the app.
   Do not assume `10.0.2.2` is correct. Verify the visible cluster speed responds
   to the same drive; a connected ADB endpoint alone is insufficient.
5. In **Results**, enable **Follow live**. Inspect **Orchestration**,
   **Communications** and **Evidence**. Check the shared run/plan/evidence
   identities and requested/effective semantic and plan digests. Use causal links
   to inspect corresponding records in the same capture. Inspecting/paging pauses
   following; refresh all views to obtain another consistent capture.
6. Select **Stop**; during preparation use **Cancel**. Wait for terminal state
   **and** cleanup **complete**. Individual provider components report **released**.
   Check owned processes exit and the three containers
   stop. Refresh platform views for final evidence. Browser refresh must not start
   a second run or rewrite the frozen snapshot. Close test browsers/SSE readers
   before shutting down the foreground Studio launcher with Ctrl+C.

After testing, shut down the remaining test-owned viewers, ADB server, private
display/overlay and private Docker daemon if you created them for the test. Use
their original supervisors/ownership records; leave an existing shared host
Docker service alone. Check `free -h` and the `SUnreclaim`/`VmallocUsed` fields
in `/proc/meminfo` against the pre-test baseline. Process exit alone does not
prove kernel allocations were released. The recorded local cleanup left about
435 MiB unreclaimable and 233 MiB vmalloc memory, with no recurrence of the
earlier multi-gigabyte allocations; these are measured results, not guarantees
for another host or driver.

The native Pygame input is not browser-leased; losing the Studio browser does not
stop it. This is an interactive simulation, not deterministic replay or physical
vehicle stimulation. Evidence sampling may coalesce, and simulator-to-host clock
mapping remains unavailable. Report these separately from successful driving.

## 7. Diagnose a failed check without resetting working assets

| Symptom | Next check |
|---|---|
| Platform example is valid but Start is unavailable | Confirm both launcher enrollment flags, the actual provider and readiness diagnostic. |
| Installation changed after enrollment | Compare the reported immutable identity; reuse the admitted installation or enroll a separately prepared environment in a new data root. |
| Android never boots | Inspect the owned container's current logs, KVM/TAP accessibility, free runtime disk and matching CVD/system artifacts. Preserve userdata. |
| Viewer opens but video does not load | Check its stream connection and the selected environment's network reachability. Forwarding HTTPS alone does not establish WebRTC media reachability. |
| Cluster stays at zero | Check app process, client/router mode and actual emulator gateway; compare app receipt with observed vehicle speed. |
| Native ingress backpressure | Preserve the failure and bridge manifest, Stop, and verify the optimized admitted build. Do not enlarge queues or hide lost observations to pass. |
| Unknown owner/scratch or fenced predecessor | Follow [platform recovery](platform-recovery.md). Old PIDs and historical ready files are not current ownership. |

Retain the exact candidate, tool versions, run ID, frozen digests, preflight,
functional observations, cleanup result and limitations. Private stdout and app
logs may help diagnose a failure; they are not native Argus evidence. Keep the
existing [demo operation guide](autoverse-demo.md) alongside this provisioning
procedure. The dated [local verification record](../../evidence/studio/autoverse-reproduction-20261110/README.md)
states which parts were actually tested and which remain blocked.

# Existing Autoverse blueprint: local reproduction checks, 2026-11-10

Update 2026-11-11: the exact SDK commit is now published, a clean c8e05dd frozen
Python install passes, and an exact twelve-repository Autoverse manifest is
available. See the [dependency resolution record](../autoverse-dependency-handoff-20261111/README.md).
The original dated results below retain their historical scope.

The user's correction is authoritative: reuse the existing development blueprint.
This change adds a [from-scratch guide](../../../docs/user/autoverse-from-scratch.md)
and a repeatable browser journey for **Autoverse with X-Verse platform**
(`autoverse-platform`, provider `autoverse.platform`). No blueprint factory, XDL,
provider or executable topology changes. The abandoned separate Lite-only variant
is absent from the catalog and this change.

## Candidate and scope

Base source: `93ef1d931429f1ba8f4c593bf0883bc05e1d416b`, isolated branch
`feat/autoverse-reproduction-guide`. New documentation/test inputs are hashed in
[verification.json](verification.json). The shared checkout's unrelated work and
the existing development project/recorded runs are preserved. The full original
implementation remains paused; this separately requested Linux documentation and
verification work does not lift the Windows freeze.

## Actual local results

| Check | Result | Claim boundary |
|---|---|---|
| Fresh `uv sync --frozen --python 3.13.13` | Failed: pinned platform remote returned `upload-pack: not our ref` | Clean-machine Python installation remains blocked. |
| Fresh `npm ci`, `npm run build` | Passed | Real frontend installation/typecheck/build only. |
| Existing Autoverse contracts | 24 passed | Canonical full topology, public CLI equivalence, effective configuration, refusal, public lifecycle/owned-child cancellation and cleanup contracts. External substitutions in tests retain their original qualifications. |
| Actual native bridge contracts | 12 passed | Real C++ bridge payloads/observation/Argus and refusal contracts; no CARLA/Android workload. |
| Native Studio + Chromium, 1024×768 and 1440×900 | 2 passed, zero skips | Existing eight-file/six-binding blueprint validates; absent enrollment blocks Start; UI export/import preserves document objects and semantic/plan digests; zero runs created. |
| Fresh full Autoverse driving/Android/Stop | Functional checks and cleanup verified after capacity recovery | Actual six-binding workload, rendered camera/sensors, Pygame input, Android app/stream/speed, public platform views and complete cleanup. Uses provisioned SDK/cached assets; Argus remains incomplete for known loss. |
| All Lite components in the existing development run | Incomplete | Python Lite flow runtime and Lite fault scheduler are not wired into this provider. |

Provisioned tests used Python 3.13.13 and `xverse-xdl` 0.4.0 at exact platform
commit `12615d402ba16cde3cd48c55b70aca464ea90261`. This existing environment is
explicitly distinct from the failed fresh dependency installation. Native bridge
SHA-256: `5de52e650bcaef3c733eea36aa6dce891d9a0f3d974c95efca21f9d6f2af8682`.
It is the cached Release artifact; the helper was not rebuilt/qualified afresh here.

[The portable ZIP](autoverse-development.zip) is an actual UI export of the
existing blueprint, not a new blueprint definition or a prepared host environment.
The browser tests reimported it and compared all eight document objects and both
compiled digests. Its initial project name is **Autoverse with X-Verse platform**.
Import grants no provider admission; on a prepared host use the existing project
with its selected enrolled provider and recheck readiness. Imported projects can
default to `studio.reference` in this candidate; the guide records explicit
platform provider selection/recheck. Browser screenshots show the original
development project with `autoverse.platform` selected before export. The test
does not claim that import preserves host provider selection or admission.

## Live verification after capacity recovery

The original 8.7 GiB capacity block is retained as history. After the user made
memory available, a fresh boot/session required new ownership and enrollment.
The existing separate prepared environment reused its cached three images and
eight containers. Old namespace/PID receipts were not adopted. Prior private
scratch was preserved intact before selecting fresh private backing. The host
Docker service, host interfaces and original CARLA lower files were preserved.

Run **`run-895bbf88-9616-437f-8e2f-0394c96c9d0c`** executed the unchanged default
600-second `autoverse-platform` definition; the test stopped it explicitly before
its duration expired. Requested/effective semantic and plan digests match the
authoring/export checks above. The runtime used source 93ef1d9 from the provisioned
development checkout; production inputs in this documentation worktree and that
checkout were both unchanged from the same commit. The UI used this worktree's
freshly built assets.

- [CARLA camera capture](carla-rendered-camera.png) shows the real rendered scene,
  radar and GNSS HUD. The vehicle, original native manual window and native bridge
  belonged to the current admitted run; no null renderer or omitted sensors.
- A short owned-window throttle/brake test sampled speed rising from zero to
  13.64 km/h and released every injected key. The [actual Android capture](android-driving.png)
  shows 47 km/h at a later instant during the same throttle action; the current
  app PID also reported received/state speed values above zero. These observations
  are from different instants; no synchronized clock or exact sample equality is
  claimed. The primary 1080×600 WebRTC stream was ready/playing; the secondary
  400×600 stream was decoded but paused. Reconnecting the viewer after boot was
  needed because its initial connection preceded guest readiness.
- Native-browser Orchestration, Communications and Evidence tabs were exercised.
  All three API views verified run/plan/Maestro identity against one shared capture,
  with 426 / 1134 / 1560 matching records at that capture. Live-writer artifact
  diagnostics disappeared from the final sealed read. Final recorded and assessed
  verdicts remain **incomplete**, with `ARGUS2-LOSS-DEGRADED-INTERVAL` and
  `ARGUS2-LOSS-KNOWN-DROP`; successful driving does not upgrade that verdict.
- Public Stop produced `state=stopped`, aggregate `cleanup=complete` and 22 provider
  component outcomes `released`. All 19 recorded process instances were no longer
  live by PID/creation-time readback; all eight cached containers were stopped.
  Frozen snapshot integrity remained valid and all four frozen/effective digests
  matched their pre-Stop values.
- The original foreground supervisor then exited with its test browsers, Studio,
  guard, window manager, ADB, private display, FUSE overlay and private Docker
  daemon. No captured supervisor child remained live. The overlay was unmounted;
  its lower markers and the host Docker/interface snapshots remained unchanged.
  The FUSE child reported exit 1 during termination; the original child exited and
  the unmount/lower-byte checks passed. This is not an all-zero-exit assertion.
- Memory after full cleanup: approximately **26 GiB available**, **435 MiB
  unreclaimable**, **233 MiB vmalloc**, and 1 MiB swap occupied. The earlier
  multi-gigabyte kernel allocations did not recur in this run. No driver reset,
  cache dropping, swap disabling or unrelated process termination was used by the
  test cleanup.

Two preparation-only attempts ended before Studio/workload start: the first fresh
scratch omitted the X11 bind target; the next ADB helper queried before its owned
foreground listener was ready. Their supervisors exited and original artifacts
were retained. The successful attempt created both private X11 directories and
waited for that listener, using an explicit server address and initial empty device
list. A contributor Stop verifier first expected the provider word `released` in
the aggregate API field, whose declared enum uses `complete`; it failed after Stop.
A corrected terminal readback verified the original unchanged outcome and actual
resource identities. Its initial nine pidfds closed on verifier exit before their
exit-readiness checks, so no all-resource pidfd proof is claimed. No second workload
was started to repair that expectation.

## Repeat the narrow checks

From this Studio source with the admitted development dependencies installed:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run python -m pytest -q \
  tests/contract/test_autoverse_blueprint.py \
  tests/contract/test_autoverse_platform_mode.py \
  tests/contract/test_autoverse_maestro_execution.py \
  tests/contract/test_autoverse_cleanup.py
XVERSE_STUDIO_NATIVE_BRIDGE=/path/to/admitted/native-bridge/studio_native_xcom_bridge \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run python -m pytest -q tests/live/native_bridge_contract.py
uv run xverse-studio --data-dir /path/to/new/private/test-data --port 8879 \
  --static-dir apps/studio-web/dist
```

In another terminal, using that launcher's private data directory:

```sh
STUDIO_BASE_URL=http://127.0.0.1:8879 \
  STUDIO_BROWSER_DATA=/path/to/new/private/test-data \
  npm run test:e2e -- autoverse-development-blueprint.spec.ts
```

This browser test intentionally runs **without** Autoverse enrollment; use a new
test data root and installed Chromium for the pinned Playwright version. It does
not perform the full demo described in guide section 6. The actual checks here
used the provisioned Python interpreter with `PYTHONPATH=services/studio-api/src`
so they tested this isolated worktree rather than another editable checkout.

An initial pytest invocation picked up an unrelated host ROS plugin and failed
before collection (`No module named yaml`); the final run disabled foreign
plugin autoload. Two initial browser cases failed because the contributor's
direct compilation POST omitted Origin/CSRF headers. Adding the normal session
headers fixed the test; no application security behavior was changed. Initial
and final logs remain in private local test storage. Exported reports do not
contain tokens, session cookies, ADB keys or host-specific paths.

No original task or milestone closes from these checks. Counts remain
**72 completed / 18 in progress / 10 blocked**, with zero accepted milestones.
The full live functional/cleanup check is now recorded. The requested **all-Lite
integration and clean-machine reproduction remain incomplete** for the explicit
flow/fault and source-distribution prerequisites.

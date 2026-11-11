# Autoverse native dependency maintenance — 2026-11-11

The teammate’s four reproduction findings are repaired in published maintenance
branches and selected by the Studio guide. This records dependency admission and
native build verification; it does not replace prior full-demo evidence.

- Platform [7e6f91e](https://github.com/The-Xverse/xverse-platform/commit/7e6f91e385f836f0f0e944b8c830aee930f5c771), branch `studio/autoverse-sdk-build-fixes`:
  c-ares `1.18.1-1ubuntu0.22.04.4`, exact 45180-byte archive and SHA-256;
  both lock mentions updated; thirteen-package reconstruction/prose corrected;
  separate T025 GTest/GMock prefix documented before preflight and root CMake.
- S-CORE [a4d610f](https://github.com/The-Xverse/adas_s-core/commit/a4d610f1de8353fb5f69095edb8c35489a758f1a), branch `studio/autoverse-library-check-fix`:
  the existing `readlink -f` launcher correction is committed with two regression
  tests. The manifest advances only this one of its twelve source pins.
- [Studio guide](../../../docs/user/autoverse-from-scratch.md#4-prepare-the-matching-native-x-com-bridge):
  selects the new SDK commit, all three environment inputs and an explicit
  `BUILD_TESTING=ON` native build. Studio lock, adapter and descriptive metadata
  agree with the installed SDK. Platform and S-CORE `main` remain unchanged.

## Verification

The original reconstruction script rejects a correct thirteen-record manifest.
Its updated literal shell block reconstructs a new prefix from thirteen retained
archives plus the JSON manifest. The c-ares package was fetched independently
from the declared Ubuntu archive, and size/hash/package/version/architecture/source
were verified. `libcares.so.2` still resolves to `libcares.so.2.5.1`.

Missing the T025 prefix reproduces `XCOM-BLD-E061`. Its separately verified
GTest/GMock 1.11.0-3 prefix admits with `XCOM-T025-DEP-I000`; then both
`--verify-toolchain` and `--all` admit with `XCOM-BLD-I000`. All 39 preflight
self-tests pass. Root CMake configures in Release with `BUILD_TESTING=ON`, and
`xverse_xcom_provider_loopback` builds its four static libraries with `-j2`.

A fresh empty-cache `uv sync --frozen` installs the exact published SDK successor.
The existing blueprint compiles with six bindings and unchanged semantic/plan
digests. All 57 selected Studio contract tests and all 12 actual native bridge
contracts pass, with zero skips. The bridge admission helper builds at the exact
new SDK commit and records `companionSourceChanged: false`. Descriptive
compatibility, architecture boundaries and modified-Python undefined-name checks
pass. The two S-CORE tests use real owned ELF files and the actual shell function,
covering correct symlink resolution and rejection of a genuinely missing library.

Commands used the provisioned Python 3.13.13 environment, GCC 11.4.0, CMake 3.22.1
and Ninja. Admission/build/test checks ran in an unprivileged network namespace;
source and archive retrieval happened separately. Representative commands, with
private paths replaced by placeholders, were:

```sh
python platform/scripts/xcom_dependency_preflight.py --self-test
python platform/scripts/check_xcom_t025_test_dependencies.py GTEST_PACKAGES GTEST_PREFIX
python platform/scripts/xcom_dependency_preflight.py --verify-toolchain
python platform/scripts/xcom_dependency_preflight.py --all
cmake -S platform -B native-build -G Ninja -DBUILD_TESTING=ON -DCMAKE_BUILD_TYPE=Release -DPython3_EXECUTABLE=PYTHON
cmake --build native-build --target xverse_xcom_provider_loopback -j2
python scripts/build_native_bridge.py --platform-source platform --platform-build native-build --third-party-include PREFIX/usr/include --output native-bridge
python -I -m pytest tests/contract/test_xdl_adapter.py tests/contract/test_xdl_validation_cache.py tests/contract/test_autoverse_blueprint.py tests/contract/test_autoverse_platform_mode.py tests/contract/test_autoverse_maestro_execution.py tests/contract/test_autoverse_cleanup.py -q
XVERSE_STUDIO_NATIVE_BRIDGE=native-bridge/studio_native_xcom_bridge python -I -m pytest tests/live/native_bridge_contract.py -q
python -m unittest discover -s score/tests -p test_make_library_check.py
python scripts/check_platform_compatibility.py
python scripts/check_architecture.py
python scripts/validate_spec_package.py
```

The guide supplies the required prefix/manifest environment variables. Test runs
also set `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` to exclude unrelated host plugins.
Raw logs stay private; their hashes, outcomes and exact source identities are in
[verification.json](verification.json). The path-free
[native bridge build receipt](native-bridge-build-manifest.json) retains source,
header, static-library and executable hashes. No binaries or package archives are
committed.

## Review and limits

Read-only findings were recorded before repair. A separate diff review confirms
platform `src`, `cmake`, root CMake, `proto` and `xdl` trees are byte-identical to
12615d4; S-CORE `cc_s-core` is byte-identical to320508a. Original working trees,
including the already modified source `make.sh`, are preserved. Admission remains
exact; no payload, provenance, permission or source-identity check was relaxed.
The reference descriptor’s implementation digest is refreshed because it hashes
the XDL adapter containing the new SDK revision constant.

An existing12615d4 experiment can finish using its original frozen inputs. The
new pin requires its own matching SDK/native source/build and enrollment. The
teammate’s section5/6 result remains pending. No simulator, Android VM or GPU
workload is started here; original implementation work remains paused and Windows
work frozen. Missing Lite flow/fault integration and the earlier incomplete
Argus verdict are unchanged. No task or milestone closes (72 completed,
18 in progress,10 blocked). Temporary build resources are removed after checks;
final cleanup and memory observations are recorded in the verification JSON.

Next work is the teammate’s remaining enrollment/full-demo check. For subsequent
provenance/admission review, Terra with high reasoning remains the recommendation;
this is a task judgment, not a measured cost comparison.

# Autoverse teammate dependency handoff — 2026-11-11

The teammate reported that Studio c8e05dd could not fetch platform commit
`12615d402ba16cde3cd48c55b70aca464ea90261` and lacked an exact Autoverse source
manifest. The user requested publication of that exact commit and the source
handoff. These source-distribution gaps are now resolved; fresh full-machine
native-build/live acceptance and the missing Lite flow/fault integration remain
separate work.

## Exact platform commit published and consumed

Published the existing accepted commit, unchanged, to
[`The-Xverse/xverse-platform`, branch `studio/autoverse-sdk-12615d4`](https://github.com/The-Xverse/xverse-platform/tree/studio/autoverse-sdk-12615d4).
Remote readback matches the full commit above. The platform's current local HEAD
and main branch were not pushed or changed. No platform implementation change,
new acceptance, main merge or tag is claimed.

An isolated consumer exported from **Studio c8e05dd** was installed using Python
3.13.13, `uv sync --frozen` and a newly empty uv cache. Installation passed using
the configured HTTPS Git dependency. Installed `xverse-xdl` 0.4.0 reports the exact
Git commit in its distribution metadata. Public `PublicExecutionService`,
`NativeObservationBatch` and `RecoveryRetirement` import successfully. The
unchanged existing Autoverse platform example compiles with six bindings:

- Semantic: `sha256:d938b685194e149cfe0cc1b31e6f3f0b37f5db4d096360fd0b143c5e15cf21c6`
- Plan: `sha256:40f813c0adec313f855c3159484dc2293684bc79013291b1490b477bb35fdcd4`

The teammate can retry `uv sync --frozen` on c8e05dd without editing its dependency
pin or lockfile. New Studio documentation is needed only for the source manifest
and corrected checkout/provisioning instructions.

## Exact source manifest and Cuttlefish

[`config/autoverse-development.repos`](../../../config/autoverse-development.repos)
is the literal `vcs export --exact --nested .` output from the development source
root. All twelve exported revisions were already reachable from their GitHub
repositories. A second set of isolated remote clones, using the documented
root-first sequence, checked out all twelve pins; a new nested export matches
the manifest and all twelve tracked trees are clean. LFS smudging was disabled
for the source-only check. Selected runtime payloads still require provisioning.

Yes: `aaos_digital_cluster/cuttlefish_emulator` is
[`The-Xverse/aaos_cuttlefish`](https://github.com/The-Xverse/aaos_cuttlefish), commit
**`b86e0de01ec21fee5417ad396eb4c507f5f1c963`**. That commit was verified at remote
main and in a new clone. Its tracked `apk/digital-cluster-app-debug.zip` contains
the actual tested APK, SHA-256
`daf9e86cf2f6e58536bca5cedbc695baadcbf39f0965ad22d65607ddd79827f9`.
Its `ctl.sh` also matches the tested staged bytes.

The actual live demo used a staged, non-Git asset tree. Its provenance was checked
against these source revisions rather than falsely claiming a VCS export of that
staging directory. All 19 enrolled runtime source files match. Independent copied
source checks match 92 S-CORE files, 10 VCU files, 10 CARLA example files and 159
SOME/IP build inputs; those groups can overlap the enrolled file set.

The original S-CORE source working tree contains an uncommitted `make.sh` check
adjustment: it passes `readlink -f` results to `ldd` for native launcher symlinks.
It is outside the compared S-CORE runtime sources and is not represented by the
committed manifest. That existing working change was preserved, not committed or
published as though it were accepted implementation. Cuttlefish's untracked
local `runtime` link is likewise generated environment state, not a missing
source commit. No other companion repository source was modified or pushed.

## Failed first import and corrected procedure

The first one-step `vcs import` fetched all pins but failed the root checkout:
cloning default main first left a legacy `AAOS-Xverse.zip`/LFS dirty-file refusal
when switching to the pinned development commit. Its other eleven source clones
checked out successfully. The corrected attempt used a separate fresh workspace:

1. Clone the Autoverse root with `--no-checkout`.
2. Select exact root commit `6000fa76f4434452bb8fe241c7117167deb2bcea` before creating a default-branch working tree.
3. Run `vcs import --skip-existing --workers 1` with the full manifest, preserving that already pinned root.
4. Export with `--exact --nested` and compare every URL/commit.

The corrected twelve-repository attempt passed. No force checkout, production
workspace reset or source repinning was used to conceal the failure. Exact
commands are in the updated [reproduction guide](../../../docs/user/autoverse-from-scratch.md).

## Scope and cleanup

This verifies source availability, exact checkout, Python installation and pure
blueprint compilation. It does not verify a fresh CARLA/Cuttlefish download,
native offline toolchain construction, new image build, hardware or Windows.
The prior actual full demo/Stop evidence remains separately dated 2026-11-10.
Its final Argus verdict remains incomplete for known drops/degraded intervals.

No simulator, VM, GPU workload, test Docker daemon or graphical session was
started here. Temporary source checkouts, Python environment and dependency
cache are removed after retaining results; existing source working trees,
prepared assets and running user applications are preserved. No original task
or milestone closes; Windows remains frozen.

Machine-readable source pins, measured versions and source comparisons are in
[verification.json](verification.json).

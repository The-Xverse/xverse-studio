# Selected Studio integration baseline

Initial inspection: 2026-10-25, using repository contents and GitHub `commits/main`
responses independently. Updated 2026-10-29 after the separately authorized public
Maestro capability was accepted and integrated into local platform `main`.

| Input | Selected immutable revision | Admission scope |
|---|---|---|
| [xverse-platform](https://github.com/The-Xverse/xverse-platform/tree/12615d402ba16cde3cd48c55b70aca464ea90261) | `12615d402ba16cde3cd48c55b70aca464ea90261` | Installed `xverse-xdl`0.4.0 from accepted local main; matching public execution modules and offline XDL/Argus checks. Explicit Autoverse platform enrollment has actual complete Linux browser/native evidence; this does not admit unrelated Lite/compat/blueprint bindings. |
| [xverse-compat](https://github.com/The-Xverse/xverse-compat/tree/f5b3957ca84cccfd98cddd9eb3ab95b0a4643eed) | `f5b3957ca84cccfd98cddd9eb3ab95b0a4643eed` | Source inspection only; no driver/simulator admission. |
| [xverse-blueprints](https://github.com/The-Xverse/xverse-blueprints/tree/0741e01b9e86b9bb9360e2feb220807b36bcbdc4) | `0741e01b9e86b9bb9360e2feb220807b36bcbdc4` | Source inspection only; no live blueprint admission. |

The initial source register retains platform `7fab6a290c3731533c2b88517158055c768b9d4e`
as its historical inspection identity. ADR-0034 records this successor admission.
The new commit is local and has not been published; its GitHub link is an identity
reference, not a claim of remote availability. Provisioning used a temporary Git
URL rewrite to the accepted local repository, with the canonical source URL and
commit retained in the lock and installed distribution metadata. No global Git
configuration was changed. A remote-only installation cannot fetch this commit
until publication is separately authorized.

These revisions differ from the historical rc.1 compatibility set. Their selection
does not establish a mutually admitted live runtime set. The selected XDL file
hashes below are unchanged from the initial baseline. Historical Linux and Windows
evidence retain their original candidates/outcomes; Windows is now outside the
required delivery scope under ADR-0036. The actual admitted simulation subset is
recorded in `evidence/studio/platform-observability-foundation/live-browser-experiment.json`
and `live-follow.json`, rather than inferred from this source-head inventory.

The dependency pin is an immutable Git revision, resolved in `uv.lock`. The Studio adapter imports
public exports from `xverse_xdl`: `validate_sources`, `canonical_json`,
`compile_experiment_sources`, `plan_matches_digest`, public limits, API versions and package version.
It passes explicitly supplied in-memory document bytes and explicit packaged schema paths. It does
not discover dependencies recursively, fetch a schema URL, execute imported content, or infer readiness
from compilation.

| Installed platform artifact | SHA-256 |
|---|---|
| `xverse_xdl/__init__.py` | `0e0ca25bf3afab9276a4a18900ed2fc3d82e4c3bf23854c4c9c69b3791cec8ce` |
| `xverse_xdl/experiment_plan.py` | `4e4affa52fe77cea4f37598cd6bce2309a0a767a7e878372ecee0a5599603393` |
| `xverse_xdl/validate.py` | `a2f57ead55dc805bdc37a3a79d91bbfa04e92ed7902636b4c3d6d978ce578fa2` |
| `xverse_xdl/normalize.py` | `d7c933d90d6901fc693f35d575260c73e370ab012604a260d8885f7ffa6dd5f7` |
| `xverse_xdl/profiles/experiment-lite-v0.1.schema.json` | `a2123b3349ab016fda829d57084d9142565bf76fdafd474fe19fe222562dfc30` |

Authoritative diagnostics retain platform codes, gates, pointers, resource references and source
locations. Source locators are document identifiers, never browser-selected host paths. The adapter
retains platform input semantic and plan digests with a `sha256:` prefix. Comments, document names,
line endings, YAML/JSON formatting and source order do not alter those executable identities.

`tests/contract/test_xdl_adapter.py` executes the real installed platform CLI and public library over
the same inputs and compares the complete emitted plan. The test also exercises hostile YAML,
unresolved extensions, source locations, changed parameter identities and unsupported provider edits.
Historical native Windows parity remains NOT_RUN and is outside current delivery
requirements under ADR-0036. Current Linux Autoverse CLI/API and persistence
verification is recorded separately by T014; older fixture results retain their scope.

Current live limitations are concrete:

- `automotive/thesis-lite-carla-closed-loop/run-live.sh` remains a Linux/Bash harness running a test
  entry. Its `test_live_closed_loop.py` imports `_OriginalRuntimeRun` and builds XDL internally using
  `build_documents`. Studio does not import those private runtime internals or invoke that harness.
  DEP-RUN and DEP-RUN-CONFIG need an admitted public effective-input contract, read-only prelaunch
  equality check, permitted live environment and postlaunch effective identity evidence.
- The platform compiler currently rejects a declared feedback cycle with
  `XDL1-PLAN-DEPENDENCY-CYCLE`, while its base validator accepts the same XDL. Studio preserves that
  distinction. FR-038 requires a compatible compiler/provider path for supported feedback semantics;
  it is not satisfied by deleting cycles or bypassing the compiler.
- The compiler accepts explicit locally admitted additional Profile schemas and retains their payload
  in semantic identities. The Studio assessment Profile adds bounded derived evaluation declarations;
  the compiler itself does not evaluate them or confer live runtime support.
- Malformed `metadata` such as a list reaches `ResourceIdentity.from_mapping` before schema
  diagnostics in the pinned validator, raising `AttributeError`. Studio catches this public-library
  failure as `XDL_PLATFORM_FAILURE` with validation unavailable and execution blocked, preserves
  exact authored bytes, and returns an empty graph projection. This is not replacement validation or
  a claim that the platform produced semantic diagnostics. A corrected admitted public validator is
  needed to close DEP-XDL-DIAGNOSTIC; companion source is not patched by Studio.
- Lite flow evidence is distinct from native C++ X-COM activation. The separately
  enrolled `autoverse.platform` provider has complete Linux experiment and linked
  Maestro/native X-COM/Argus view evidence in
  `evidence/studio/platform-observability-foundation/live-browser-experiment.json`
  and `live-follow.json`. Original classic `autoverse.demo` results retain their
  component-only scope. This explicit platform enrollment does not admit the old
  Lite harness, arbitrary providers, physical equipment or general model coupling.

The executable `studio.reference` provider is Studio-owned and has its own finite model contract.
Its evidence scope is `owned_reference` and maturity is `fixture`. It proves owned application
behaviour only; it does not establish compatibility, vehicle dynamics, industrial fidelity or hardware.

The selected facts are also recorded in [the machine-readable baseline](../../config/platform-compatibility.json).
It includes selected source/package/schema identities and limits, declared provider snapshots, the
exact recorded Linux evidence candidate, held Windows status and unavailable integrations. Its
`admittedLiveCompatibilitySet` is null. It is descriptive metadata; application admission uses the
existing backend contracts and never reads this file to grant authority.

`uv run python -I scripts/check_platform_compatibility.py` checks it in a fully provisioned contributor
checkout. The contributor gate runs the same check before the backend suite. It compares installed
XDL Git provenance and selected file hashes, lock/package versions, schema bytes, descriptors,
toolchain declarations and fixed evidence receipts. It does not start/probe a provider or repeat the
historical browser measurements. Intentional baseline changes need reviewed manifest/evidence
updates; the checker does not rewrite the manifest. Repository evidence links require the checkout,
and wheel-only provenance needs its own admission update. T001's Linux baseline
component is complete; its historical results do not accept an entire milestone.

T014 rechecks the exact installed SDK pin and current Autoverse contracts, native
project persistence, hostile imports and security boundaries. The standalone Lite
binding remains unavailable for the precise provider-specific reasons in
[dependencies.md](dependencies.md#standalone-lite-binding--t014-classification).
The public Maestro API exists at the selected pin; its existence does not supply
an admitted Lite configuration adapter or open the older private runtime path.

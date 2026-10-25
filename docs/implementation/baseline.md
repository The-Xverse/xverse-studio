# Selected Studio integration baseline

Inspected 2026-10-25. Repository contents and GitHub `commits/main` responses were read independently.
Companion repositories were not modified and their live launchers were not executed.

| Input | Selected immutable revision | Admission scope |
|---|---|---|
| [xverse-platform](https://github.com/The-Xverse/xverse-platform/tree/7fab6a290c3731533c2b88517158055c768b9d4e) | `7fab6a290c3731533c2b88517158055c768b9d4e` | Installed `xverse-xdl` 0.4.0; public offline validation/compilation APIs exercised by Studio tests. |
| [xverse-compat](https://github.com/The-Xverse/xverse-compat/tree/f5b3957ca84cccfd98cddd9eb3ab95b0a4643eed) | `f5b3957ca84cccfd98cddd9eb3ab95b0a4643eed` | Source inspection only; no driver/simulator admission. |
| [xverse-blueprints](https://github.com/The-Xverse/xverse-blueprints/tree/0741e01b9e86b9bb9360e2feb220807b36bcbdc4) | `0741e01b9e86b9bb9360e2feb220807b36bcbdc4` | Source inspection only; no live blueprint admission. |

These main heads match the package's source register, but differ from the historical rc.1
compatibility set. Matching current heads does not establish a mutually admitted live runtime set.

The dependency pin is an immutable Git revision, resolved in `uv.lock`. The Studio adapter imports
only public exports from `xverse_xdl`: `validate_sources`, `canonical_json`,
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
Native Windows parity and portable exchange remain NOT_RUN until a Windows host is available.

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
- Lite flow evidence is distinct from native C++ X-COM activation. Physical equipment, native X-COM
  integration, general model coupling and simulator operation remain unavailable.

The executable `studio.reference` provider is Studio-owned and has its own finite model contract.
Its evidence scope is `owned_reference` and maturity is `fixture`. It proves owned application
behaviour only; it does not establish compatibility, vehicle dynamics, industrial fidelity or hardware.

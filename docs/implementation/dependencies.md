# Dependency selection and reproducibility

The immutable platform source pin is recorded in [baseline.md](baseline.md). Native application
dependencies are locked in root `uv.lock` and `package-lock.json`; those files, rather than prose,
are the complete transitive resolution authority. No companion repository mutation is required.

The 2026-10-29 public Maestro successor was separately authorized, accepted and
merged locally in the platform repository. Studio's new immutable pin is local
and unpublished. Its Git dependency was provisioned through a temporary Git URL
rewrite to that accepted checkout; the lock and installed `direct_url.json`
preserve the canonical repository identity and exact commit. No publication or
remote-only install success is claimed. See ADR-0034 and the SDK admission evidence.

The separately accepted released-registration recovery successor is now admitted at
platform12615d402. Its assembled verification covers236 source/46 installed recovery
checks and3selected native CTests. All10 installed execution modules match that
source. Studio's native bridge was rebuilt against the exact accepted revision.
See ADR-0035 and the recovery integration evidence; full live browser acceptance is
separate from dependency admission.

The installed backend environment was queried through `importlib.metadata.version`:

| Distribution | Resolved version |
|---|---|
| Python | 3.13.13 |
| uv | 0.12.17 |
| FastAPI | 0.135.1 |
| Uvicorn | 0.41.0 |
| Pydantic | 2.12.5 |
| psutil | 7.2.2 |
| xverse-xdl | 0.4.0 at selected Git commit |
| jsonschema | 4.26.0 |
| referencing | 0.37.0 |
| ruamel.yaml | 0.19.1 |
| pytest | 9.0.2 |
| httpx | 0.28.1 |
| Ruff | 0.15.4 |

Platform dependency compatibility was checked against its actual `pyproject.toml`: Python >=3.11,
jsonschema >=4.26,<5, referencing >=0.37,<1 and ruamel.yaml >=0.19.1,<0.20. Studio deliberately pins
a narrower Python environment for the current candidate. Provider interpreters and drivers are
separate capabilities; CARLA's interpreter requirements do not become Studio's Python requirement.

The frontend uses Node LTS/npm, React, TypeScript and React Flow as required by the supplied plan.
Exact resolved frontend package versions are in the npm lockfile. Dependencies are fetched during
provisioning; ordinary provisioned core operation does not contact registries or cloud services.
An air-gapped installation additionally requires prepared wheels/assets; a lockfile alone is not an
offline installation bundle. Refer to the packaging evidence before claiming that envelope.

This Linux host has a ROS `PYTHONPATH`/pytest plugin environment. Verification removes that unrelated
path and disables ambient pytest plugin auto-discovery to avoid loading ROS Python 3.10 plugins into
the pinned Python 3.13 application environment. This is test isolation, not a product dependency.

## Standalone Lite binding — T014 classification

On 2026-10-30, the exact selected SDK remains
`12615d402ba16cde3cd48c55b70aca464ea90261`; the selected blueprint remains
`0741e01b9e86b9bb9360e2feb220807b36bcbdc4`. Inspection uses those Git objects
and matching installed public modules, rather than newer companion checkout heads.
The SDK exports `xverse.maestro.execution` inspection, preparation and public
host-bound lifecycle operations. Their accepted boundary is separately admitted
for Studio's explicit `autoverse.platform` provider. This is an available scoped
public interface, not a missing generic API.

The **standalone `xverse.lite` binding remains blocked** by DEP-RUN/DEP-RUN-CONFIG.
At the selected blueprint revision, `run-live.sh` launches its test harness, whose
`test_live_closed_loop.py` builds its own documents with `build_documents` and
constructs `_OriginalRuntimeRun`. The old candidate `RuntimeService` remains
execution-disabled by default and requires that private class. Studio does not
import or execute either path. Neither the public SDK nor a successful Autoverse
run supplies the missing provider-specific mapping for the requested Lite inputs.

| Required operation | Exact prerequisite and owner |
|---|---|
| Inspect requested versus actual Lite inputs before effects | A separately admitted Lite adapter in the owning blueprint/compat integration must expose effective generated documents, selected model, semantic/plan digests, pinned artifact/installation identity and supported edits through a public contract. Unknown or ignored edits must reject. |
| Start and observe the same inspected Lite configuration | Bind that adapter to the accepted public Maestro interface (or another separately admitted public interface), with exact host/resource permissions, expiry, original ownership and bounded lifecycle/evidence results. No private-class shim or legacy approval may be inferred. |
| Claim live Lite support | Nominate the permitted actual Lite environment and verify the exact provider/driver/artifact set: supported changed input equality, deliberately ignored edit refusal, nominal/failure execution and owned cleanup. Docker availability alone is insufficient. |

The Studio owner is currently `providers/registry.py`: `xverse.lite` advertises
`available=false`, no operations and `DEP-RUN-CONFIG`. There is no implemented
`integrations/lite/` binding. Current Autoverse-targeted checks directly request
that unavailable provider and prove refusal before dispatch or fallback while
authoring/compilation remains usable. Those negative results are not Lite execution.
T012 and its live dependents remain blocked; T014's foundation checks can complete
with that explicit classification. Companion changes need their own scoped work;
this dependency record grants no new authority or publication permission.

The descriptive compatibility manifest covers the default baseline, not every
optional native enrollment. Its generic `native_XCOM` unavailable entry does not
negate the separately admitted Autoverse platform experiment, nor does that one
experiment admit a general native X-COM provider. Original claims/Argus records
and historical inspection identities remain unchanged.

Native Windows dependency installation was attempted on Server 2022 and failed because the full
pinned Git tree contains nonportable filenames. Windows installation/testing are outside the
current release scope under ADR-0036; historical backend/browser checks remain NOT_RUN. A portable wheel preparation is held locally
and is not integrated or a passing native result.

`config/platform-compatibility.json` snapshots the selected lock digests and backend distribution
versions alongside source and evidence scope. `scripts/check_platform_compatibility.py` rejects drift
against the provisioned checkout; it is a contributor consistency check, not application startup or
runtime admission. The locks still own the complete transitive resolution.

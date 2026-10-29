# Dependency selection and reproducibility

The immutable platform source pin is recorded in [baseline.md](baseline.md). Native application
dependencies are locked in root `uv.lock` and `package-lock.json`; those files, rather than prose,
are the complete transitive resolution authority. No companion repository mutation is required.

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

Native Windows dependency installation was attempted on Server 2022 and failed because the full
pinned Git tree contains nonportable filenames. Windows installation/testing are now BLOCKED at
user request; backend/browser checks remain NOT_RUN. A portable wheel preparation is held locally
and is not integrated or a passing native result.

`config/platform-compatibility.json` snapshots the selected lock digests and backend distribution
versions alongside source and evidence scope. `scripts/check_platform_compatibility.py` rejects drift
against the provisioned checkout; it is a contributor consistency check, not application startup or
runtime admission. The locks still own the complete transitive resolution.

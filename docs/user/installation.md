# Native installation scope

Use [getting started](getting-started.md) for source-checkout Linux commands and native PowerShell
instructions, with their actual verification status. The foreground launcher installs no OS service.
No WSL, Bash, container or remote Linux host is part of its runtime startup.

For a reviewed source bundle produced by `scripts/package_studio.py`, verify the distributed archive
SHA and each `package-manifest.json` file digest before installing. The bundle contains compiled browser
assets and pinned backend sources/locks; Node is not needed to run those already-built assets.
Provision native Python 3.13.13, uv 0.12.17 and Git for the pinned XDL Git dependency, extract the trusted
application bundle, and run from its `xverse-studio` directory:

```text
uv sync --frozen --no-dev
uv run --no-dev xverse-studio --data-dir .studio-local/data --port 8876
```

A package is trusted application code, unlike an inert project/evidence ZIP. Never install application
code supplied inside a project or profile. Dependencies are downloaded only during explicit provisioning;
air-gapped first installation needs a prepared, verified native wheelhouse that is outside this bundle.

The shared package entry point is `uv run python scripts/package_studio.py`. It refuses output overwrite,
requires an existing frontend build, excludes caches/secrets and records exact contributing file hashes,
Git candidate and dirty-tree state. A dirty package is an explicitly identified development artifact,
not an exact committed release. Native Windows acceptance and OS-specific process/ACL behaviour require
actual native verification; the presence of a Windows-targeted command or CI file does not pass it.

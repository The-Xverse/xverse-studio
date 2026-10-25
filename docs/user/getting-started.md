# Run the current reference implementation

This candidate implements native local Studio workflows with its owned executable first-order model.
It is not an accepted M0–M4 release. External Lite/CARLA, physical devices and native X-COM remain
unavailable. A successful reference run proves only the explicitly labelled reference scope.

## Provision Linux

Use Python 3.13.13, uv 0.12.17, Node 24.22.1 and npm from that Node distribution. Git is needed to
provision the pinned public XDL dependency. After provisioning, core operation is local/offline.
No Bash, container or remote runtime is involved in application startup.

From the repository root:

```text
uv sync --frozen
npm ci
npm run build
uv run xverse-studio --data-dir .studio-local/data --port 8876
```

The backend serves the built UI at http://127.0.0.1:8876. Open `.studio-local/data/bootstrap.json`
locally and enter its one-use `bootstrapToken` in the browser. It expires after five minutes and is
removed after use; the secret is never put in a URL or ordinary logs. Native launcher output names
the file without printing its contents. Restart the launcher to obtain a fresh bootstrap when needed.

On the implementation host all repository, data, build and temporary files reside on the user's
selected loop10 filesystem. Set tool caches and temporary roots there too when provisioning on
that host; do not redirect application data into another filesystem.

## Provision native Windows (verification pending)

These commands are supplied for native PowerShell; they have not passed the required Windows lane
in this session. They do not invoke WSL or Bash. Install native Python 3.13.13, Node 24.22.1 and Git,
then install uv 0.12.17 through the approved native installer or Python package:

```powershell
py -3.13 -m pip install uv==0.12.17
uv sync --frozen
npm ci
npm run build
uv run xverse-studio --data-dir .studio-local/data --port 8876
```

Read the sign-in bootstrap locally with `Get-Content .studio-local/data/bootstrap.json`.
A Windows browser pointed at the Linux backend does not establish this native lane. The CI matrix
requests Ubuntu 24.04 and Windows Server 2022; only actual successful jobs qualify those exact hosts.
Windows desktop/driver support requires separately recorded evidence. Provider availability remains
independent of Studio support.

## Guided prepared example

1. Sign in and choose **Process control reference** or **Automotive reference**. Both use the same
   core workflow and bounded normalized model; neither claims process equipment or vehicle fidelity.
2. Select an element and inspect role, source reference, interfaces and parameter provenance.
   Change **Target**, **Response gain** or **Duration** and apply the edit. Units and bounds are shown.
3. Validate, then select **Preflight & run**. Static model validity and target readiness are distinct.
   Inspect the frozen plan identity and diagnostic details. Only a ready preflight enables Start.
4. Start the frozen snapshot. Results report lifecycle, cleanup, evidence and evaluations separately.
   Browser refresh/reconnect reads the existing backend-owned run; it does not issue Start again.
5. Use **Reference fault → stuck-sensor** in the scenario parameters to run a supported owned failure
   example. Fault intent and observed activation remain separate events. The model can finish while an
   assertion is indeterminate or fails; run termination does not automatically pass an assertion.
6. Inspect the authoritative XDL source. Compare changes before saving. Layout is a separate sidecar,
   and moving graph elements does not modify the executable plan. Invalid drafts remain inspectable.
7. Use Results definitions/evaluations, annotations and finite campaigns only within advertised limits.
   Compare exact input/configuration differences before interpreting observation differences.

The Model, Connections, Deployment, Experiments and Results views share the same XDL identities.
Source edits and typed semantic edits use the public pinned XDL APIs. Unsupported topology, profiles,
physical coupling or cyclic compiler plans remain blocked instead of being silently approximated.

## Stop and remove

Ctrl+C in the native foreground launcher requests cancellation only for ownership-confirmed reference
workers, waits for their outcomes and stops the backend. An unknown process/ownership state is never
permission to terminate a PID. Data is retained. Closing the browser does not stop execution.

Stop Studio and preserve a full backup before uninstalling. Removing the local checkout/virtual
environment removes this source installation; remove the explicitly selected data directory separately
only when its projects and evidence are no longer needed. No system service is installed.

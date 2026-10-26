# Clean committed-candidate native Linux package smoke

Product candidate: `b2cf71a22bf990031f11543ab8b8fec559698086`.

A detached, clean checkout under `.studio-local/native-package-source/b2cf71a` used the browser build
already verified against exactly that application source. The source bundle includes the new lab
module and all 98 selected product files. Its manifest records `workingTreeDirty: false` and exact
file hashes; `receipt.json` identifies the retained archive and source-tree digest.

The shared `scripts/smoke_package.py` then created a fresh extraction and installed offline using the
prepared dependency cache. It passed native startup, browser-index HTTP 200, Unicode project
persistence and authoritative compilation, then stopped only its own backend. Browser interaction is
verified separately by the full 77-check cohort; this package smoke supplies no new browser claim.

Two failed receipts are retained. The original contributor environment used symlink-relative cache
and temporary paths containing `..`, and isolated provisioning could not import the declared, pinned
hatchling backend. Removing host ROS PYTHONPATH alone did not resolve it. Switching to resolved
physical loop-filesystem paths succeeded. A control with the same workspace virtualenv interpreter
also passed using those physical paths: the virtualenv interpreter itself was not the cause. Both
base-interpreter and workspace-interpreter success receipts are retained. Dependencies and package
source were unchanged; no missing build dependency was invented or added.

Commands were the committed `scripts/smoke_package.py --output <receipt>` from that isolated source,
executed by the contributor Python with `-I`, using the loop-local UV cache/TMPDIR and
`UV_PYTHON_DOWNLOADS=never`. The successful environments use resolved physical loop-filesystem paths and explicitly
selected Python executables. No Bash, container or WSL runtime requirement is introduced; shell syntax was
contributor orchestration on this Linux host only.

This is a fresh local extraction with prepared dependencies, not a newly provisioned host. Native
Ubuntu CI remains a separate record. Windows installation/testing stays held and physical/Lite
provider admission is unavailable. No Studio 1.0 or milestone release is claimed.

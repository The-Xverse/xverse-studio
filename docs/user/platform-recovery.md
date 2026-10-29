# Retiring a released simulation registration

This host maintenance tool is available for the admitted Linux Autoverse platform
provider. Stop Studio before using it. It cannot recover original process handles,
force cleanup, signal a process, replay an old run or repair incomplete lifecycle
provenance. Retain the original claims and Argus evidence.

Use the same data directory, explicitly enrolled Autoverse installation and verified
native bridge build as the launcher. Inspect each predecessor's original run ID:

```text
python -I scripts/recover_platform_registration.py --data-dir <existing-data-dir> --autoverse-root <installed-demo> --autoverse-native-bridge <verified-build> --run-id <original-run-id>
```

Inspection does not authorize a new activation. When the public SDK reports
`eligible: true` and the host operator authorizes retirement, repeat with
`--retire --approval-reference <host-authorization-reference>`. The tool grants
60 seconds for the exact inspection and current installed provider bindings.
Use repeated `--run-id` arguments for multiple predecessors; unknown or ineligible
selected sources refuse the operation. Other unresolved claims still block Start.

A separate durable retirement receipt preserves the original claim and evidence
bytes and their incomplete verdicts. Restart Studio with the identical installation
and build. It recognizes only verified public receipts; any prior Studio owner
marker is archived unchanged before a new owner can record its run. A missing,
corrupt or stale receipt keeps execution blocked. Rebuilding or changing the
installed provider can invalidate bindings and requires a new inspection/grant.

The tool is a local repository-owned host command. There is no browser recovery
grant, imported project command or physical/Windows recovery capability. A valid
retirement is a separate fact; the old lost-owner runtime read remains unknown.

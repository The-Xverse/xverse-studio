# ADR-0036: Linux delivery scope

Status: approved by the user's2026-10-29 instruction, “continue the implementation
of the remaining tasks. Remove windowns requirements.”

## Decision

Linux is the required native Studio host for the existing M0–M4 delivery. Remove
native Windows installation, process/file ownership, browser, packaging, performance,
accessibility and cross-OS exchange acceptance as release gates. Keep the original
requirement, task, acceptance and success-criterion IDs; amend their host scope.
Windows is outside this release scope, rather than a failed or passed Linux gate.
Future Windows support requires its own explicit scope and native evidence.

The browser application, native Linux backend, safe ownership, offline provisioned
core workflows, source/semantic preservation and all other quality/performance
requirements remain. Containers/Bash/remote services are not implicit core
requirements. An explicitly admitted simulation provider may have separate host
dependencies. Industry neutrality and provider permissions remain unchanged.

Keep inert-import defenses against drive/UNC/device paths, alternate data streams,
reserved names and case collisions: these are hostile package inputs on Linux too.
Existing portable code paths need not be deleted. A declared provider OS capability
is separate from a release support claim and is not proof of native verification.

## Trace and evidence impact

Amend constitution1.1.0, repository instructions, feature spec/plan/research,
contracts, acceptance, task descriptions and traceability consistently. CI remains
Linux-only, with its scope stated rather than a held Windows lane. Mark the current
Windows support-matrix disposition OUT_OF_SCOPE while preserving original failed
installation and NOT_RUN evidence. Do not rewrite historical verification claims.

Reassess remaining tasks against their complete amended Linux requirements and
actual evidence. Removing one gate does not automatically complete a task: missing
SADS source, actual live/provider permissions, first-time-user measurements and
other required outcomes retain their own dispositions. Update tasks and traces
together only when the corresponding remaining requirements are proven.

No companion repository change, physical device operation, cloud deployment or
publication is authorized by this host-scope decision. The request authorizes
continuation of the existing Studio implementation plan, including the ongoing
live-follow presentation work, rather than regeneration of the plan or task IDs.

Implementation follow-up2026-10-30: capabilities discovery advertises only Linux
as a Studio native delivery target and retains windowsAcceptance with the explicit
OUT_OF_SCOPE_ADR0036 disposition. Environment labels this Windows scope. Provider
host declarations remain independent. Current proof is in
evidence/studio/linux-capability-scope/; this correction does not close T004.

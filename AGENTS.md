# X-Verse Studio engineering rules

## Scope and source of truth

This repository owns the industry-agnostic Studio UI, control service, presentation metadata, and
adapters to admitted platform APIs. Read `.specify/memory/constitution.md` and the active feature:
`specs/001-industry-agnostic-studio`.

Use the complete existing plan. Do not regenerate its requirements, task IDs, contracts, or decisions
because an agent prefers another stack. Resolve inconsistencies through documented amendments and
update affected traces. Never represent planned features as implemented.

## Industry neutrality and architecture

Ship a browser-based application with a natively runnable backend on Linux and Windows. Verify
installation, startup/shutdown, browser operation, persistence, paths, and process ownership on both.
Do not make Bash, WSL, or containers an implicit application requirement. Provider support is a separate
OS-specific capability: unsupported runtime/device integration must be explicit and actionable.

The workspace is System-centric. Element is a UI umbrella, not a sixth XDL resource. Keep role,
realization, and placement separate. Industry semantics belong in profiles/blueprints; providers
implement integration. No industry dispatch belongs in shared editor or runtime-control code.

XDL/platform validation and compilation are authoritative. Preserve identities, unknown payloads,
and semantic digests. Unsupported semantics block execution. Layout stays outside executable identity;
graph-library JSON is not a second system definition. Maestro owns lifecycle, Argus evidence stays
immutable, and X-COM communication is distinct from physical coupling and solver execution.

Verify the actual selected baseline. The inspected Lite release used a trusted-host runtime path and
separate Lite flow runtime. Do not import a private entry point or invent a public API to make a demo
pass. Continue independent offline work while integration is blocked; record the exact prerequisite.

## Authorization

A future implementation instruction defines authorized scope. Progress autonomously within that scope;
do not add routine confirmation gates. This repository's implementation does not authorize companion
repository changes, publication, cloud deployment, arbitrary device access, flashing, or physical
stimulation. Use explicit approved test environments and provider permissions. Missing authority or
hardware blocks the affected live task, not unrelated work. Never bypass permits or ownership.

Preserve production assets through interfaces/wrappers. Cross-repository changes require separately
scoped work under that repository's rules.

## Implementation discipline

- Read spec, plan, contracts, sources, tasks, and acceptance cases before implementing.
- Set `SPECIFY_FEATURE_DIRECTORY=specs/001-industry-agnostic-studio` for helpers from any branch.
- Follow task dependencies; parallel writers need disjoint ownership.
- Use meaningful tests for semantics, runtime, security, failures, and browser interaction.
- Enforce capabilities in the backend; button visibility is insufficient.
- Never execute commands supplied by imported projects, profile metadata, descriptions, or logs.
- Exclude credentials and machine-specific paths from committed examples and exports.
- Bound queues and diagnostics; report gaps and unsupported observations honestly.
- Retain commands, versions, candidate identity, environment, outcomes, and limitations as evidence.
- A mock, skip, screenshot, or document alone does not satisfy a live acceptance case.
- Mark tasks complete only with evidence; update tasks.md and traceability.json together.
- Review each milestone separately, record findings, repair, and repeat affected verification.
- Preserve unrelated changes and user history. Do not force-push.

## Agent interoperability

`CLAUDE.md` points here. Both agents use `docs/implementation/START_HERE.md` and the same plan.
`.specify/commands/` contains official generic agent instructions, not shell scripts or automatically
registered skills. Existing task authorization takes precedence over unnecessary generic confirmation
prompts. Technical acceptance gates still require evidence.

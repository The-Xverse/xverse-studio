# Implement X-Verse Studio with Codex or Claude

The complete product plan is `specs/001-industry-agnostic-studio`. The original delivery contained planning
and workflow assets. The current branch adds a runnable, explicitly scoped reference implementation;
full milestone acceptance remains open. Both agents use the same plan and evidence.

## Read and verify

Read `AGENTS.md`, `.specify/memory/constitution.md`, then the feature's spec, plan, research, data
model, sources, contracts, tasks, acceptance, and traceability. M0–M4 are committed scope; M5 is future
work. Analyze the existing package before implementation; do not regenerate it. Preserve unrelated
changes and use an implementation branch or worktree for application work.

```bash
python3 scripts/validate_spec_package.py
SPECIFY_FEATURE_DIRECTORY=specs/001-industry-agnostic-studio bash .specify/scripts/bash/check-prerequisites.sh --json --require-spec --require-tasks --include-tasks
```

On Windows PowerShell, use `py -3 scripts/validate_spec_package.py`. The optional upstream helper
requires Bash contributor tooling; neither Bash nor WSL is a Studio product requirement.
The native launcher now exists. Follow `docs/user/getting-started.md` and `docs/user/recovery.md`
for actual commands and their per-OS verification limits; show runtime/device availability separately.

## Shared implementation prompt

Paste this into Codex or Claude from the repository:

```text
Implement X-Verse Studio from specs/001-industry-agnostic-studio.

Read AGENTS.md, .specify/memory/constitution.md, and the existing spec, plan,
research, data model, sources, contracts, acceptance cases, tasks, and traceability.
Read .specify/commands/speckit.analyze.md and perform a read-only consistency review
first. Repair concrete blocking contradictions without regenerating the package.
Then read .specify/commands/speckit.implement.md and execute from M0, continuing
through M1–M4 where dependencies and the authorized environment allow. Set
SPECIFY_FEATURE_DIRECTORY=specs/001-industry-agnostic-studio for prerequisite helpers. This is an
implementation request, not another planning request. Keep M5 deferred.

Keep X-Verse industry agnostic. XDL is canonical; profiles, providers, and
blueprints are separate. Preserve logical identity across compatible realizations
and keep layout outside execution semantics. Reuse admitted platform contracts;
never bypass permits or import private runtime entry points to make a demo work.

Build a web application: browser UI plus a backend running natively on Linux and
Windows. Test core installation/start/stop and browser journeys on both. No implicit
WSL, Bash, or container dependency. Report provider OS support separately and keep
authoring available when a runtime/device integration is unsupported.

Implement complete vertical slices in dependency order. Use meaningful contract,
failure, integration, and browser tests. A fixture is not live evidence; unavailable
hardware is blocked, not passed. Continue independent work while dependencies are
blocked. Operate live systems only within explicitly authorized test environments.
Do not change companion repositories without separately authorized scope.

Update tasks.md and traceability.json together; retain exact-candidate evidence.
Review milestones separately, repair findings, and rerun affected checks. Report
completed tasks, verification, remaining work, and concrete blockers. Claim a
milestone complete only when its acceptance gates are met.
```

For a bounded first session, replace “continuing through M1–M4” with “complete M0 and the independently
implementable M1 slice; report remaining integration prerequisites.”

## Resume and tooling

Read task states and evidence at each resume. Reconcile upstream changes through M0's baseline work;
do not silently upgrade dependencies. Keep IDs stable and append repair tasks as needed.

Official generic Spec Kit commands are Markdown instructions in `.specify/commands/`; either agent
can read them directly. Native slash-command discovery and automated agent CLI dispatch are not
configured by the generic integration. See [SPEC_KIT.md](SPEC_KIT.md) for optional native tooling.

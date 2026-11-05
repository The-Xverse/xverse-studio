Current instruction — 2026-11-05: user explicitly resumed with the active goal "keep going without interruption". Continue the full existing Linux/Autoverse plan; Windows remains separately frozen. Historical pause instructions below are superseded. Current T096 work starts with offline profiling of the retained live pressure failures; do not trust old infrastructure owners as live.

Current instruction — 2026-11-05: **work is paused until explicit user resume.**
The current T096 verification checkpoint is terminal with two retained live lease
expiry failures; T096 remains open. All owned private test services are stopped.
Windows remains separately frozen until explicitly lifted. Counts72/18/10,zero
accepted milestones. This instruction supersedes historical active/resume notes
below. See [status](STATUS.md) and
[evidence](../../evidence/studio/M4-control-pressure-20261105/README.md).

Latest checkpoint: T096's current finite Autoverse-derived benchmarks and53
stream/reader guards pass; full T096 live producer/control scope remains pending.
Counts72 completed /18 in progress /10 blocked; zero accepted milestones. Work is
active, Windows separately frozen. See [status](STATUS.md) and
[evidence](../../evidence/studio/M4-performance/autoverse-20261105/README.md).

Latest checkpoint: T091's original clause audit is complete. Counts72 completed /
18 in progress /10 blocked; zero accepted milestones. Linux/Autoverse work remains
active after explicit user resume; Windows remains separately frozen. See
[status](STATUS.md) and [T091 evidence](../../evidence/studio/M4-comparison-rerun-closure-20261105/README.md).
No new runtime should use stale process/namespace metadata from the shut-down
private environment; current admission/ownership/readiness must be revalidated.

Current instruction: the user explicitly reactivated the goal on 2026-11-05 after
the saved fresh-rerun checkpoint. Resume independently authorized Linux/Autoverse
work. Windows remains separately frozen. Previous pause records below are historical.
Private test services were cleanly shut down; do not treat old PIDs or namespace
bindings as live authority. Current work is the original T091 clause/evidence audit;
no new model or reference workload is needed for its initial read-only checks.

**Current user instruction (2026-11-05): finish the current task, then stop until
explicit resume.** The complete fresh Autoverse rerun verification/evidence
checkpoint is finished, owned private test services are shut down, and work is
paused. Do not follow historical resume instructions below until the user resumes.
Windows remains separately frozen until explicitly lifted. Counts71/19/10,zero
accepted milestones; T091's original full clause audit remains pending. See
[latest status](STATUS.md) and [evidence](../../evidence/studio/M4-fresh-autoverse-rerun-20261105/README.md).

# Implement X-Verse Studio with Codex or Claude

**User resumed the goal on 2026-11-05 (ADR-0069).** Continue independently
authorized Linux/Autoverse work. The separate Windows freeze remains active until
explicitly lifted; no Windows implementation or tests are resumed.

**Active user hold (2026-11-04, ADR-0069): freeze all Windows-related work until the
user explicitly lifts the hold.** Preserve the existing Windows code/evidence;
do not execute historical Windows instructions or portable Windows policy/ABI tests.
Continue independently authorized Linux/Autoverse work. Requirements and acceptance
gates remain open; this hold is not a waiver or task closure.

Current host-requirement amendment (2026-11-04, ADR-0063): the supplied engineering
rules require native Linux and Windows installation, start/stop, browser operation,
persistence, paths and process ownership. This takes precedence over historical
ADR-0036 Linux-only scope statements below. Preserve all original IDs/dependencies
and recorded component evidence. Windows remains unverified; Linux-only evidence
does not close Windows or milestone acceptance. Provider admission stays separate.


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

Windows delivery is outside the current scope under ADR-0036. The optional upstream
helper uses Bash contributor tooling; Bash is not a Studio product requirement.
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

Build a web application: browser UI plus a backend running natively on Linux. Test core installation/start/stop and browser
journeys on the recorded native Linux host. Windows requirements are removed by ADR-0036. No implicit
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

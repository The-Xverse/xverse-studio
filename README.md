# X-Verse Studio

Model, connect, execute, and observe cyber-physical systems across simulated and physical environments.

**Status: runnable development reference implementation; M0–M4 acceptance is incomplete.**

The React/TypeScript browser application and native Python/FastAPI backend implement project/source
editing, graph projections, preflight, durable reference-run control, observations, bounded assertions,
finite campaigns, comparisons, annotations, safe exchange and retention. The executable reference model
is explicitly scoped; it does not establish CARLA, physical-device, Argus or native X-COM integration.
Native Windows, real hardware and first-time usability gates remain unverified or blocked.

After provisioning the pinned Python 3.13.13/uv 0.12.17 and Node 24.22.1 toolchain:

```text
uv sync --frozen
npm ci
npm run build
uv run xverse-studio --data-dir .studio-local/data --port 8876
```

Open http://127.0.0.1:8876 and enter the one-use token from `.studio-local/data/bootstrap.json`.
See [native setup and the guided example](docs/user/getting-started.md),
[recovery/update procedures](docs/user/recovery.md), and [provider limits](docs/providers/README.md).
Run `uv run python scripts/run_checks.py` for backend checks and
`uv run python scripts/test_browser.py` after provisioning Playwright Chromium for real browser checks.
All workspace, cache, build, temporary and evidence files on the implementation machine use loop10.

Studio is an industry-agnostic engineering workbench over X-Verse. Its primary workspace is a System;
users add elements, connect interfaces, choose realizations, run experiments, and inspect evidence.
ECUs, PLCs, robot controllers, and energy equipment are profile specializations. XDL is canonical;
Maestro owns execution, X-COM communication contracts, and Argus observation/evidence boundaries.

Studio targets a **browser UI and native Linux/Windows backends**. This candidate is verified on
recorded Linux hosts; Windows installation and tests are currently **blocked at user request**, after
an initial dependency-checkout failure. Local Linux operation needs no WSL or cloud account. Provider
OS support is declared separately, and unavailable providers preserve authoring/inspection workflows.

## Specification and implementation evidence

Read [the Codex / Claude handoff](docs/implementation/START_HERE.md), [engineering rules](AGENTS.md),
and [the constitution](.specify/memory/constitution.md).

| Document | Purpose |
|---|---|
| [Specification](specs/001-industry-agnostic-studio/spec.md) | Stories, requirements, quality attributes, success criteria |
| [Plan](specs/001-industry-agnostic-studio/plan.md) | Architecture, stack, module boundaries, delivery sequence |
| [Tasks](specs/001-industry-agnostic-studio/tasks.md) | Ordered implementation work; unchecked means unfinished |
| [Acceptance](specs/001-industry-agnostic-studio/acceptance.md) | Observable verification cases and required environments |
| [Traceability](specs/001-industry-agnostic-studio/traceability.json) | Requirement/task/acceptance mappings |
| [Data model](specs/001-industry-agnostic-studio/data-model.md) | Identities, revisions, realization, run state |
| [Contracts](specs/001-industry-agnostic-studio/contracts/studio-api.md) | API; companion contracts cover projects, providers, events |
| [Roadmap](specs/001-industry-agnostic-studio/roadmap.md) | Milestone gates, dependencies, deferred extensions |
| [Quickstart](specs/001-industry-agnostic-studio/quickstart.md) | Planning checks and future user journeys |
| [Sources](specs/001-industry-agnostic-studio/sources.md) | Inspected baselines and evidence limits |

## Delivery milestones

1. **M0 — Foundation:** baseline, contracts, XDL boundary, execution integration assessment.
2. **M1 — Guided operation / 0.1:** supported example, preflight, admitted run, results.
3. **M2 — Visual composition / 0.2:** catalog, graph/source editing, deployments, two-industry proof.
4. **M3 — Hybrid laboratory / 0.3:** real device provider, asset ownership, controls, mixed clocks.
5. **M4 — Experiment management / 1.0:** scenarios, evaluated assertions, faults, campaigns, evidence.

Each milestone needs implementation evidence. An offline fixture does not establish live integration;
a skipped hardware case does not establish hardware support. M5 is separately scoped future work.

## Check the planning package

```bash
python3 scripts/validate_spec_package.py
SPECIFY_FEATURE_DIRECTORY=specs/001-industry-agnostic-studio bash .specify/scripts/bash/check-prerequisites.sh --json --require-spec --require-tasks --include-tasks
```

These check planning consistency, not the future application. Official GitHub Spec Kit **1.2.3** is
initialized with generic integration and Bash helpers. Both agents can read `.specify/commands/`
directly; native slash-command discovery is not assumed. See [tooling provenance](docs/implementation/SPEC_KIT.md).
On Windows PowerShell, use `py -3 scripts/validate_spec_package.py`; the optional Bash helper is
contributor tooling, not an application prerequisite.

## License

The existing [Apache-2.0 license](LICENSE) covers original repository work. Vendored Spec Kit assets
retain their [upstream MIT license](.specify/UPSTREAM_LICENSE).

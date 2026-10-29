# Spec Kit provenance and use

Initialized on 2026-10-25 using official GitHub Spec Kit **v1.2.3**, commit
`5ea8b1cf0a38699340a38e00d02770308997d8c0`.

Source: https://github.com/github/spec-kit/tree/5ea8b1cf0a38699340a38e00d02770308997d8c0

The official CLI was run with:

```bash
specify init --here --force --non-interactive --integration generic --integration-options='--commands-dir .specify/commands' --script sh
```

This records provenance; do not rerun initialization over the authored plan. Generated core commands,
Bash scripts, templates, workflow, and integration metadata are retained. The constitution is authored
for Studio. Upstream assets retain `.specify/UPSTREAM_LICENSE`; the original Apache-2.0 license is unchanged.

## Direct use

Codex/Claude can read generated commands and invoke committed helpers without installing the CLI.
`scripts/validate_spec_package.py` uses Python's standard library. Select the feature with
`SPECIFY_FEATURE_DIRECTORY=specs/001-industry-agnostic-studio` from main or any implementation branch.
`SPECIFY_FEATURE` supplies branch context and does not select the directory in this pinned version.
The helper may save an ignored `.specify/feature.json` pointer. Set `SPECIFY_FEATURE_NO_PERSIST=1`
when a read-only prerequisite check is wanted.

The shipped upstream helpers use Bash. They are optional contributor tooling and are not a Studio
installation or runtime dependency. On Windows, run the portable package check in PowerShell with
`py -3 scripts/validate_spec_package.py`; agents can read the command Markdown directly. The Bash
prerequisite helper additionally needs a contributor-installed Bash environment such as Git Bash.
Native Windows product setup and start/stop commands must be implemented and verified separately.

Specification-quality checklists concern the written requirements, not runtime completion. Runtime
acceptance starts NOT_RUN in `acceptance.md`. The generic integration does not dispatch agent CLIs.

## Optional CLI/native integration

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v1.2.3
```

Review integration status before changing it. Follow the pinned
[Codex guide](https://github.com/github/spec-kit/blob/5ea8b1cf0a38699340a38e00d02770308997d8c0/docs/integrations/codex.md)
or [Claude guide](https://github.com/github/spec-kit/blob/5ea8b1cf0a38699340a38e00d02770308997d8c0/docs/integrations/claude.md)
for native skills installation later. Switching agents does not require regenerating this feature.

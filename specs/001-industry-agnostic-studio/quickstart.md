# Quickstart and intended walkthroughs

## Available at package delivery

This is a specification package with official Spec Kit workflow assets. Studio application/API and launch
commands are not implemented. From the repository root:

```bash
python3 scripts/validate_spec_package.py
SPECIFY_FEATURE_DIRECTORY=specs/001-industry-agnostic-studio bash .specify/scripts/bash/check-prerequisites.sh --json --require-spec --require-tasks --include-tasks
```

Then use [the implementation handoff](../../docs/implementation/START_HERE.md).

On Windows PowerShell, the package validator is `py -3 scripts/validate_spec_package.py`.
The optional upstream prerequisite helper uses Bash (for example, Git Bash); this does not impose
Bash or WSL on the Studio product. Studio must provide native Linux and Windows setup/start/stop
instructions and a browser UI. Runtime/device providers declare their own host compatibility.

## Intended M1 journey

1. Install locked dependencies on native Linux or Windows and select an admitted local baseline.
2. Launch using host-appropriate commands verified by M1; open the web UI in a supported browser.
   The backend owns execution; inspect provider compatibility separately from core app health.
3. Open a supported example; inspect actual artifacts and provider availability.
4. Change a parameter through a bounded form and save the project revision.
5. Validate/compile through the platform, then perform separate live preflight.
6. Run the inspected snapshot; observe events/signals and refresh the browser without duplicating the run.
7. Stop/cancel through a supported operation; inspect execution, cleanup, and evidence separately.

An absent integration leaves authoring/validation available and explains why Run is unavailable.
A frontend preview never substitutes for live acceptance.

## Intended M2 journey

Compose a System from controller, sensor/process-model, stimulus, and observer elements. Select role,
realization, and placement independently. Connect compatible interfaces with explicit mappings. Switch
graph/XDL views without semantic changes. Move a node and verify its executable digest is unchanged.
Create another Deployment while retaining logical identities.

Repeat with two independent domain profiles: automotive and process control. A simple owned process
model is acceptable with declared fidelity; it does not validate real plant physics. The common editor
must need no new industry conditional.

## Intended M3 journey

In an authorized isolated bench, identify/reserve one real asset, inspect capabilities, connect observe-only,
then perform only permitted stimulation. Bind it to a compatible logical element; retain interfaces and
show actual clock mappings/uncertainty. Verify disconnect, ownership conflict, stop, cleanup, and release.
Absent hardware blocks the live claim; fake-provider results remain offline evidence.

## Intended M4 journey

Author explicit timing, stimuli, supported faults, observers, and assertions using the implemented
restricted evaluator. Pin a baseline, execute a bounded parameter campaign, compare observations with
gaps/clock uncertainty, and export evidence. Previous runs remain immutable after project edits.
Replay observations separately from rerunning; distinguish failed assertions from invalid/incomplete runs.

Every diagnostic links an observed fact, affected element, uncertainty/prerequisite, and actionable next
step. A root-cause hypothesis, heartbeat, or command echo is not proven system behaviour.

#!/usr/bin/env python3
"""Check the authored Studio plan; never claim application acceptance from this result."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / "specs/001-industry-agnostic-studio"
errors: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def index(items: list[dict], label: str) -> dict[str, dict]:
    ids = [item.get("id") for item in items]
    require(all(isinstance(value, str) and value for value in ids), f"{label}: invalid ID")
    require(len(ids) == len(set(ids)), f"{label}: duplicate IDs")
    return {item["id"]: item for item in items if isinstance(item.get("id"), str)}


def check_dag(items: dict[str, dict], label: str) -> None:
    visited: set[str] = set()
    active: set[str] = set()

    def visit(key: str) -> None:
        if key in active:
            errors.append(f"{label}: dependency cycle at {key}")
            return
        if key in visited or key not in items:
            return
        active.add(key)
        for dep in items[key].get("depends_on", []):
            require(dep in items, f"{label}: {key} references missing dependency {dep}")
            visit(dep)
        active.remove(key)
        visited.add(key)

    for key in items:
        visit(key)


def main() -> int:
    required = [
        ROOT / "AGENTS.md", ROOT / "CLAUDE.md", ROOT / "README.md",
        ROOT / ".specify/memory/constitution.md",
        ROOT / ".specify/commands/speckit.implement.md",
        ROOT / ".specify/commands/speckit.analyze.md",
        ROOT / ".specify/UPSTREAM_LICENSE",
        ROOT / "docs/implementation/START_HERE.md",
        ROOT / "docs/implementation/SPEC_KIT.md",
        *[FEATURE / name for name in (
            "spec.md", "plan.md", "tasks.md", "acceptance.md", "traceability.json",
            "data-model.md", "research.md", "roadmap.md", "quickstart.md", "sources.md",
            "contracts/studio-api.md", "contracts/project-format.md",
            "contracts/provider-contract.md", "contracts/run-events.md", "contracts/experiment-evaluation.md",
            "checklists/requirements.md",
        )],
    ]
    for path in required:
        require(path.is_file() and path.stat().st_size > 0, f"Missing/empty: {path.relative_to(ROOT)}")
    if errors:
        print(json.dumps({"valid": False, "scope": "planning-package", "errors": errors}, indent=2))
        return 1

    data = json.loads((FEATURE / "traceability.json").read_text(encoding="utf-8"))
    require(data.get("feature_id") == FEATURE.name, "Feature identity mismatch")
    spec = (FEATURE / "spec.md").read_text(encoding="utf-8")
    task_text = (FEATURE / "tasks.md").read_text(encoding="utf-8")
    acceptance_text = (FEATURE / "acceptance.md").read_text(encoding="utf-8")
    declared = re.findall(r"^- \*\*((?:FR|NFR)-\d+)\*\*", spec, re.M)
    declared_sc = re.findall(r"^- \*\*(SC-\d+)\b", spec, re.M)
    require(len(declared) == len(set(declared)), "Duplicate requirement declaration in spec")
    require(len(declared_sc) == len(set(declared_sc)), "Duplicate success criterion in spec")
    requirements = index(data["requirements"], "requirements")
    tasks = index(data["tasks"], "tasks")
    cases = index(data["acceptance_cases"], "acceptance cases")
    criteria = index(data["success_criteria"], "success criteria")
    milestones = index(data["milestones"], "milestones")
    require(set(declared) == set(requirements), "spec/trace requirement sets differ")
    require(set(declared_sc) == set(criteria), "spec/trace success criterion sets differ")
    task_rows = re.findall(r"^- \[([ xX])\] (T\d+)\b", task_text, re.M)
    require(len(task_rows) == len({key for _, key in task_rows}), "Duplicate task declaration in tasks.md")
    require({key for _, key in task_rows} == set(tasks), "tasks.md/trace task sets differ")
    for marker, key in task_rows:
        require((marker.lower() == "x") == (tasks[key].get("status") == "completed"),
                f"{key}: checkbox/status mismatch")

    for key, item in requirements.items():
        require(bool(item.get("task_ids")), f"{key}: no tasks")
        require(bool(item.get("acceptance_ids")), f"{key}: no acceptance cases")
        for tid in item.get("task_ids", []):
            require(tid in tasks and key in tasks[tid].get("requirements", []), f"{key}/{tid}: inverse task trace missing")
        for aid in item.get("acceptance_ids", []):
            require(aid in cases and key in cases[aid].get("requirements", []), f"{key}/{aid}: inverse acceptance trace missing")

    for key, item in tasks.items():
        require(item.get("milestone") in milestones, f"{key}: invalid milestone")
        require(item.get("status") in {"not_started", "in_progress", "blocked", "completed"}, f"{key}: invalid task status")
        require(bool(item.get("paths")), f"{key}: no implementation/evidence paths")
        require(bool(item.get("requirements")), f"{key}: no requirement trace")
        require(bool(item.get("acceptance_ids")), f"{key}: no acceptance trace")
        for rid in item.get("requirements", []):
            require(rid in requirements and key in requirements[rid].get("task_ids", []), f"{key}/{rid}: inverse requirement trace missing")
        for aid in item.get("acceptance_ids", []):
            require(aid in cases and key in cases[aid].get("task_ids", []), f"{key}/{aid}: inverse case trace missing")
        for path in item.get("paths", []):
            require(not Path(path).is_absolute() and ".." not in Path(path).parts, f"{key}: non-project path {path}")

    for key, item in cases.items():
        require(key in acceptance_text, f"{key}: absent from acceptance.md")
        require(item.get("milestone") in milestones, f"{key}: invalid milestone")
        require(item.get("status") in {"NOT_RUN", "PASS", "FAIL", "BLOCKED"}, f"{key}: invalid acceptance status")
        require(bool(item.get("required_environment")), f"{key}: missing required environment")
        for rid in item.get("requirements", []):
            require(rid in requirements and key in requirements[rid].get("acceptance_ids", []), f"{key}/{rid}: inverse requirement trace missing")
        for tid in item.get("task_ids", []):
            require(tid in tasks and key in tasks[tid].get("acceptance_ids", []), f"{key}/{tid}: inverse task trace missing")
        for sid in item.get("success_criteria", []):
            require(sid in criteria and key in criteria[sid].get("acceptance_ids", []), f"{key}/{sid}: inverse success trace missing")

    for key, item in criteria.items():
        require(bool(item.get("acceptance_ids")), f"{key}: no acceptance cases")
        require(bool(item.get("task_ids")), f"{key}: no tasks")
        for aid in item.get("acceptance_ids", []):
            require(aid in cases and key in cases[aid].get("success_criteria", []), f"{key}/{aid}: inverse success trace missing")
        for tid in item.get("task_ids", []):
            require(tid in tasks, f"{key}: unknown task {tid}")

    for key, item in milestones.items():
        for aid in item.get("exit_acceptance_ids", []):
            require(aid in cases, f"{key}: unknown exit case {aid}")
    check_dag(tasks, "tasks")
    check_dag(milestones, "milestones")

    authored = [ROOT / "README.md", ROOT / "AGENTS.md", ROOT / "CLAUDE.md",
                ROOT / ".specify/memory/constitution.md", *ROOT.glob("docs/**/*.md"), *FEATURE.glob("**/*.md")]
    for path in authored:
        text = path.read_text(encoding="utf-8")
        require(not re.search(r"\[(?:NEEDS CLARIFICATION|INSERT[^\]]*|TODO)\]", text), f"Unfilled placeholder: {path.relative_to(ROOT)}")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            target = target.split("#", 1)[0].strip("<>")
            if not target or re.match(r"^[a-zA-Z]+:", target):
                continue
            require((path.parent / unquote(target)).exists(), f"Broken local link in {path.relative_to(ROOT)}: {target}")

    print(json.dumps({
        "valid": not errors, "scope": "planning-package", "application_acceptance": "not_evaluated_by_this_check",
        "requirements": len(requirements), "success_criteria": len(criteria), "tasks": len(tasks),
        "acceptance_cases": len(cases), "milestones": len(milestones), "errors": errors,
    }, indent=2))
    return bool(errors)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyError, TypeError, ValueError, OSError) as exc:
        print(json.dumps({"valid": False, "scope": "planning-package", "errors": [str(exc)]}, indent=2))
        sys.exit(1)

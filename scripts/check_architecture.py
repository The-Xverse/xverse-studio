"""Static checks for installed core boundaries; these do not admit external providers."""

import ast
from pathlib import Path
import re
import sys

DOMAINS = {"automotive", "process_control", "process-control", "ecu", "plc", "carla"}


def inspect_source(source, filename):
    issues = []
    for node in ast.walk(ast.parse(source)):
        modules = []
        if isinstance(node, ast.ImportFrom) and node.module:
            modules = [node.module]
        elif isinstance(node, ast.Import):
            modules = [x.name for x in node.names]
        if any(set(module.lower().split(".")) & DOMAINS for module in modules):
            issues.append(
                f"{filename}:{node.lineno}: core imports industry implementation"
            )
        if isinstance(node, ast.ImportFrom) and any(
            x.name == "_OriginalRuntimeRun" for x in node.names
        ):
            issues.append(f"{filename}:{node.lineno}: private runtime import")
        if isinstance(node, ast.If):
            terms = [
                n.value.lower()
                for n in ast.walk(node.test)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
            ]
            if any(
                any(
                    domain in re.split(r"[./:_-]", term) or term == domain
                    for domain in DOMAINS
                )
                for term in terms
            ):
                issues.append(
                    f"{filename}:{node.lineno}: industry dispatch in shared core"
                )
        if isinstance(node, ast.Call):
            name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else node.func.attr
                if isinstance(node.func, ast.Attribute)
                else None
            )
            if name in ("eval", "exec"):
                issues.append(f"{filename}:{node.lineno}: executable input")
            if any(
                k.arg == "shell"
                and isinstance(k.value, ast.Constant)
                and k.value.value is True
                for k in node.keywords
            ):
                issues.append(f"{filename}:{node.lineno}: shell execution")
    return issues


def main():
    root = Path(__file__).resolve().parents[1]
    issues = []
    for path in (root / "services/studio-api/src/xverse_studio").rglob("*.py"):
        issues.extend(inspect_source(path.read_text(), str(path.relative_to(root))))
    if issues:
        print("\n".join(issues))
        return 1
    print(
        "Architecture boundaries: passed (imports, industry dispatch, private runtime and executable input)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

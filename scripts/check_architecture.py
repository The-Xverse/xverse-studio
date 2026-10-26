"""Static checks for installed core boundaries; these do not admit external providers.

* no core import of an industry implementation, private runtime, eval/exec or shell execution;
* no industry dispatch: a domain literal may appear in declarative data, never in a comparison,
  conditional expression, loop or assert test, comprehension filter or `match` case;
* dependency direction: foundational packages never import feature packages, and only the API
  and host layers import the API layer;
* the browser renders profile and authored content as text: no executable HTML or code hooks.
"""

import ast
from pathlib import Path
import re

DOMAINS = {"automotive", "process_control", "process-control", "ecu", "plc", "carla"}
# Foundational packages and what they may never import. `xdl` may use the assertion and scenario
# authoring helpers it validates; nothing below the feature layer reaches up into it.
FOUNDATIONAL = {"storage", "security", "evidence", "events", "xdl"}
FEATURES = {"profiles", "connections", "deployments", "projects", "runs", "api", "catalog", "preflight",
            "providers", "retention", "lab", "campaigns", "comparison", "annotations", "diagnostics", "host",
            "exchange", "integrations"}
# Deliberate exemption: `xdl` edits delegate to the assertion and scenario-authoring helpers, which in
# turn use `xdl`; they are semantic helpers of the XDL layer, recorded in the T063 evidence.
SEMANTIC_HELPERS = {"assertions", "experiments"}
API_IMPORTERS = {"api", "host"}
# Modules whose job is declarative domain data (owned blueprints and their presentation).
DATA_MODULES = {"xdl/examples.py"}
WEB_FORBIDDEN = (
    (re.compile(r"dangerouslySetInnerHTML|\b(?:inner|outer)HTML\b|insertAdjacentHTML|document\.write|\bsrcdoc\b"),
     "executable HTML hook"),
    (re.compile(r"(?<![\w.])Function\(|\beval\(|\bset(?:Timeout|Interval)\(\s*[\"'`]"), "executable code hook"),
    (re.compile(r"javascript:", re.IGNORECASE), "script URL"),
)


def _domain(text):
    lowered = text.lower()
    return any(re.search(r"(?:^|[./:_\-\s])" + re.escape(domain) + r"(?:$|[./:_\-\s])", lowered) for domain in DOMAINS)


def _has_domain_literal(node):
    return any(isinstance(n, ast.Constant) and isinstance(n.value, str) and _domain(n.value) for n in ast.walk(node))


def _module_path(filename):
    """Package path of a source file below xverse_studio, e.g. ["xdl"] for xdl/edits.py."""
    parts = Path(filename).parts
    if "xverse_studio" not in parts[:-1]:
        return None
    inner = list(parts[parts.index("xverse_studio") + 1:])
    return inner[:-1]


def _package(filename):
    parts = Path(filename).parts
    return parts[parts.index("xverse_studio") + 1].removesuffix(".py") if "xverse_studio" in parts[:-1] else None


def _targets(node, filename):
    """Top-level xverse_studio packages an import statement or importlib call reaches."""
    if isinstance(node, ast.Import):
        return [n.name.split(".")[1] for n in node.names if n.name.startswith("xverse_studio.")]
    if isinstance(node, ast.ImportFrom):
        if node.level == 0:
            parts = (node.module or "").split(".")
            return [parts[1]] if parts[0] == "xverse_studio" and len(parts) > 1 else []
        base = _module_path(filename)
        if base is None or node.level - 1 > len(base):
            return []
        anchor = base[:len(base) - (node.level - 1)]
        full = anchor + (node.module.split(".") if node.module else [])
        return [full[0]] if full else [alias.name for alias in node.names]
    if isinstance(node, ast.Call):
        name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", None)
        if (name in ("import_module", "__import__") and node.args and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str) and node.args[0].value.startswith("xverse_studio.")):
            return [node.args[0].value.split(".")[1]]
    return []


def _keyed_by_domain(node):
    """Domain literals used to select behaviour: subscripts, lookups, prefix tests and dict keys."""
    if isinstance(node, ast.Subscript):
        return _has_domain_literal(node.slice)
    if isinstance(node, ast.Call):
        name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", None)
        if name in ("get", "getattr", "hasattr", "startswith", "endswith", "pop", "setdefault"):
            return any(_has_domain_literal(arg) for arg in node.args)
    if isinstance(node, ast.Dict):
        return any(key is not None and _has_domain_literal(key) for key in node.keys)
    return False


def inspect_source(source, filename):
    issues = []
    package = _package(filename)
    relative = "/".join(_module_path(filename) + [Path(filename).name]) if package else None
    for node in ast.walk(ast.parse(source)):
        modules = []
        if isinstance(node, ast.ImportFrom) and node.module:
            modules = [node.module]
        elif isinstance(node, ast.Import):
            modules = [x.name for x in node.names]
        if any(set(module.lower().split(".")) & DOMAINS for module in modules):
            issues.append(f"{filename}:{node.lineno}: core imports industry implementation")
        for target in _targets(node, filename):
            if package in FOUNDATIONAL and (target in FEATURES or (package != "xdl" and target in SEMANTIC_HELPERS)):
                issues.append(f"{filename}:{node.lineno}: foundational {package} imports feature {target}")
            if target == "api" and package not in API_IMPORTERS and package is not None:
                issues.append(f"{filename}:{node.lineno}: {package} imports the API layer")
        if relative not in DATA_MODULES and _keyed_by_domain(node):
            issues.append(f"{filename}:{node.lineno}: industry dispatch in shared core")
        if isinstance(node, ast.ImportFrom) and any(x.name == "_OriginalRuntimeRun" for x in node.names):
            issues.append(f"{filename}:{node.lineno}: private runtime import")
        tests = []
        if isinstance(node, (ast.If, ast.IfExp, ast.While, ast.Assert)):
            tests.append(node.test)
        elif isinstance(node, ast.comprehension):
            tests.extend(node.ifs)
        elif isinstance(node, ast.Compare):
            tests.append(node)
        elif isinstance(node, ast.match_case):
            tests.append(node.pattern)
        flagged = [test for test in tests if _has_domain_literal(test)]
        if flagged:
            line = getattr(node, "lineno", None) or getattr(flagged[0], "lineno", 0)
            issues.append(f"{filename}:{line}: industry dispatch in shared core")
        if isinstance(node, ast.Call):
            name = (node.func.id if isinstance(node.func, ast.Name)
                    else node.func.attr if isinstance(node.func, ast.Attribute) else None)
            if name in ("eval", "exec"):
                issues.append(f"{filename}:{node.lineno}: executable input")
            if any(k.arg == "shell" and isinstance(k.value, ast.Constant) and k.value.value is True for k in node.keywords):
                issues.append(f"{filename}:{node.lineno}: shell execution")
    return sorted(set(issues))


def inspect_web(source, filename):
    issues = []
    for pattern, reason in WEB_FORBIDDEN:
        match = pattern.search(source)
        if match:
            issues.append(f"{filename}:{source[:match.start()].count(chr(10)) + 1}: {reason}")
    return issues


def main():
    root = Path(__file__).resolve().parents[1]
    issues = []
    for path in (root / "services/studio-api/src/xverse_studio").rglob("*.py"):
        issues.extend(inspect_source(path.read_text(), str(path.relative_to(root))))
    web = [*(root / "apps/studio-web/src").rglob("*.ts*"), root / "apps/studio-web/index.html"]
    for path in web:
        if path.exists():
            issues.extend(inspect_web(path.read_text(), str(path.relative_to(root))))
    if issues:
        print("\n".join(issues))
        return 1
    print("Architecture boundaries: passed (imports, dependency direction, industry dispatch, private runtime, "
          "executable input and browser executable hooks).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

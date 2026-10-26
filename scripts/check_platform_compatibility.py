"""Check the descriptive baseline against a provisioned contributor checkout.

No provider is launched/probed and no application admission decision reads this file.
Only fixed repository/distribution paths are read; manifest strings never select paths,
commands, imports, endpoints or executable hooks. Full contributor evidence is required.
"""

from dataclasses import asdict
import hashlib
from importlib.metadata import distribution, version
from importlib.resources import files
import json
from pathlib import Path
import re
import tomllib

import xverse_xdl
from ruamel.yaml import YAML
from xverse_studio.providers.registry import descriptors
from xverse_studio.xdl import MAX_DOCUMENT_BYTES, MAX_DOCUMENTS, PLATFORM_REVISION, XDLAdapter
from xverse_studio.xdl.examples import (
    CONNECTIONS_NAMESPACE, DOMAIN_PROFILES, EVALUATION_NAMESPACE, PROFILE_NAMESPACE, reference_resources,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/platform-compatibility.json"
MAX_MANIFEST_BYTES = 256 * 1024


class BaselineDrift(ValueError):
    """Fixed diagnostic codes from this checker, never manifest or metadata values."""


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def package_key(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def observed_baseline():
    """Independent lock/library/descriptor/evidence facts; no admission side effects."""
    baseline = (ROOT / "docs/implementation/baseline.md").read_text(encoding="utf-8")
    revisions = dict(re.findall(
        r"https://github.com/The-Xverse/(xverse-(?:platform|compat|blueprints))/tree/([0-9a-f]{40})",
        baseline,
    ))
    if set(revisions) != {"xverse-platform", "xverse-compat", "xverse-blueprints"}:
        raise BaselineDrift("BASELINE_SOURCE_PINS_MISSING")
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    packages = {package_key(p["name"]): p for p in lock["package"]}
    service = tomllib.loads((ROOT / "services/studio-api/pyproject.toml").read_text(encoding="utf-8"))
    platform_pin = revisions["xverse-platform"]
    expected_git = "https://github.com/The-Xverse/xverse-platform.git?rev=" + platform_pin + "#" + platform_pin
    if packages["xverse-xdl"]["source"] != {"git": expected_git} or PLATFORM_REVISION != platform_pin:
        raise BaselineDrift("XDL_LOCK_ADAPTER_REVISION_DRIFT")
    requirement = "xverse-xdl @ git+https://github.com/The-Xverse/xverse-platform.git@" + platform_pin
    if requirement not in service["project"]["dependencies"]:
        raise BaselineDrift("XDL_DIRECT_REQUIREMENT_DRIFT")
    direct = json.loads(distribution("xverse-xdl").read_text("direct_url.json") or "{}")
    if direct.get("vcs_info", {}).get("commit_id") != platform_pin:
        raise BaselineDrift("INSTALLED_XDL_REVISION_DRIFT")
    backend_names = ["fastapi", "uvicorn", "pydantic", "psutil", "xverse-xdl", "jsonschema", "referencing", "ruamel.yaml"]
    backend_versions = {name: version(name) for name in backend_names}
    if any(backend_versions[name] != packages[package_key(name)]["version"] for name in backend_names):
        raise BaselineDrift("INSTALLED_BACKEND_LOCK_DRIFT")
    adapter = XDLAdapter()
    exports = ["validate_sources", "canonical_json", "compile_experiment_sources", "plan_matches_digest",
               "LoadLimits", "ExperimentLimits", "SUPPORTED_API_VERSIONS", "__version__"]
    if not all(hasattr(xverse_xdl, name) for name in exports):
        raise BaselineDrift("PUBLIC_XDL_SURFACE_DRIFT")
    selected = ["__init__.py", "experiment_plan.py", "validate.py", "normalize.py", "profiles/experiment-lite-v0.1.schema.json"]
    selected_hashes = {"xverse_xdl/" + name: sha256(files("xverse_xdl").joinpath(name)) for name in selected}
    recorded = read_json(ROOT / "evidence/studio/M0-linux-baseline/verification.json")
    if set(selected_hashes) != set(recorded["installedFileChecks"]):
        raise BaselineDrift("SELECTED_XDL_FILE_SET_DRIFT")
    if any(selected_hashes[name] != "sha256:" + record["expected"] for name, record in recorded["installedFileChecks"].items()):
        raise BaselineDrift("SELECTED_XDL_FILE_DRIFT")
    profile_versions = {r["spec"]["extensionNamespace"]: r["metadata"]["version"]
                        for r in reference_resources(feedback=True).values() if r["kind"] == "Profile"}
    profile_namespaces = [[{"namespace": name, "version": profile_versions[name]}]
                         for name in [PROFILE_NAMESPACE, EVALUATION_NAMESPACE, CONNECTIONS_NAMESPACE]] + [
                          [{"namespace": p["namespace"], "version": p["version"]} for p in DOMAIN_PROFILES]]
    profiles = []
    for index, (path, namespaces) in enumerate(zip(adapter.profile_schema_paths, profile_namespaces, strict=True)):
        path = Path(path)
        profiles.append({"schemaId": read_json(path)["$id"], "sha256": sha256(path), "profiles": namespaces,
                         "artifact": "xverse_xdl/profiles/experiment-lite-v0.1.schema.json" if index == 0 else path.relative_to(ROOT).as_posix(),
                         "origin": "installed_platform_distribution" if index == 0 else "studio_owned",
                         "scope": "presentation_only" if index == 3 else "offline_schema_admission; execution requires separate provider admission"})
    providers = descriptors()
    if [p["providerId"] for p in providers] != ["studio.reference", "xverse.lite"] or providers[1]["available"] or providers[1]["operations"]:
        raise BaselineDrift("PROVIDER_BASELINE_CHANGED_REQUIRES_REVIEW")
    provider_fields = ["providerId", "providerVersion", "contractVersion", "implementationDigest", "maturity", "evidenceScope",
                       "supportedHostOS", "architectures", "operations", "connectionContracts", "limits", "available", "blockedReasons", "limitations"]
    environment = read_json(ROOT / "evidence/studio/M3-physical-contracts/environment.json")
    browser = read_json(ROOT / "evidence/studio/M1-shell-operability/journeys/1024x768/login/native-browser-environment.json")
    if environment.get("os") != "Linux" or browser.get("platform") != "linux":
        raise BaselineDrift("RECORDED_NATIVE_LANE_MISMATCH")
    workflow_receipt = read_json(ROOT / "evidence/studio/M1-shell-operability/verification.json")
    stats = workflow_receipt["browser"]
    if (workflow_receipt.get("sourceUnchanged") is not True or type(stats.get("expected")) is not int or stats["expected"] <= 0 or
            any(type(stats.get(key)) is not int or stats[key] != 0 for key in ("unexpected", "skipped", "flaky")) or
            any(workflow_receipt["checks"].get(key) != "passed" for key in ("typecheck", "build", "architecture", "specStructure")) or
            not re.fullmatch(r"[0-9a-f]{40}", workflow_receipt.get("committedProductCandidate", "")) or
            not re.fullmatch(r"sha256:[0-9a-f]{64}", workflow_receipt.get("applicationAndTestSourceDigest", ""))):
        raise BaselineDrift("LINUX_WORKFLOW_EVIDENCE_NOT_PASSING")
    windows = read_json(ROOT / "evidence/studio/native-ci/windows-initial-install-failure.json")
    npm = read_json(ROOT / "package.json")
    npm_lock = read_json(ROOT / "package-lock.json")
    playwright = npm["devDependencies"]["@playwright/test"]
    if npm_lock["packages"]["node_modules/@playwright/test"]["version"] != playwright:
        raise BaselineDrift("PLAYWRIGHT_LOCK_DRIFT")
    workflow = YAML(typ="safe").load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    steps = workflow["jobs"]["native"]["steps"]
    node_pin = next(s["with"]["node-version"] for s in steps if s.get("uses", "").startswith("actions/setup-node@"))
    python_pin = next(s["with"]["python-version"] for s in steps if s.get("uses", "").startswith("actions/setup-python@"))
    uv_pin = next(re.fullmatch(r"python -m pip install uv==([0-9.]+)", s.get("run", ""))[1]
                  for s in steps if re.fullmatch(r"python -m pip install uv==([0-9.]+)", s.get("run", "")))
    if (ROOT / ".python-version").read_text().strip() != python_pin:
        raise BaselineDrift("PYTHON_TOOLCHAIN_PIN_DRIFT")
    expected = {
        "formatVersion": "1.0", "scope": "descriptive_selected_baseline; not runtime authority",
        "runtimeAdmissionAuthority": False, "admittedLiveCompatibilitySet": None,
        "sourceRevisions": {name: {"repository": "https://github.com/The-Xverse/" + name,
            "revision": revision, "status": "offline_xdl_verified_on_recorded_linux" if name == "xverse-platform" else "source_inspection_only"}
            for name, revision in revisions.items()},
        "xdl": {"identity": adapter.identity, "publicExportsUsed": exports, "selectedFilesSha256": selected_hashes,
            "profiles": profiles, "studioAdapterLimits": {"maxDocuments": MAX_DOCUMENTS, "maxDocumentBytes": MAX_DOCUMENT_BYTES},
            "platformLoadDefaults": asdict(xverse_xdl.LoadLimits()), "platformExperimentDefaults": asdict(xverse_xdl.ExperimentLimits()),
            "executionBoundary": "Public offline validation/declared-intent compilation; no runtime launch"},
        "dependencies": {"lockFiles": {name: sha256(ROOT / name) for name in ["uv.lock", "package-lock.json"]},
            "backendPackages": backend_versions, "pythonRequirement": service["project"]["requires-python"],
            "nodeRequirement": npm["engines"]["node"], "toolchainPins": {"python": python_pin, "node": node_pin, "uv": uv_pin, "playwright": playwright}},
        "providerDescriptorSnapshots": [{key: p[key] for key in provider_fields if key in p} for p in providers],
        "nativeHosts": {"Linux": {"distribution": environment["distribution"], "architecture": environment["architecture"],
            "python": environment["python"], "node": environment["node"], "browserVersion": browser["browser"],
            "verification": "scoped owned/offline workflows; no live-provider compatibility claim",
            "evidenceCandidate": workflow_receipt["committedProductCandidate"],
            "evidenceSourceDigest": workflow_receipt["applicationAndTestSourceDigest"],
            "repositoryEvidence": ["evidence/studio/M3-physical-contracts/environment.json", "evidence/studio/M1-shell-operability/verification.json",
                "evidence/studio/M1-shell-operability/journeys/1024x768/login/native-browser-environment.json"]},
            "Windows": {"lastAttempt": windows["platform"], "installation": windows["installation"], "applicationAndBrowser": "NOT_RUN",
                "currentStatus": "BLOCKED_USER_REQUEST", "installationDiagnostic": "UPSTREAM_NONPORTABLE_FILENAMES",
                "knownOwnedGap": {"diagnostic": "PLATFORM_IO_UNAVAILABLE", "basis": "source inspection; native Windows execution NOT_RUN"},
                "repositoryEvidence": ["evidence/studio/native-ci/windows-initial-install-failure.json", "docs/implementation/platform-support.md"]}},
        "unavailableIntegrations": [
            {"integration": "Lite_runtime_and_CARLA", "status": "unavailable", "diagnostics": ["DEP-RUN", "DEP-RUN-CONFIG"],
             "prerequisite": "Admitted public effective-input/plan contract and permitted per-OS live environment"},
            {"integration": "native_XCOM", "status": "unavailable", "prerequisite": "Separate admitted native adapter; Lite flow evidence is not native-core activation"},
            {"integration": "physical_assets", "status": "unavailable", "scope": "Live device/provider admission; read-only inventory contracts exist",
             "prerequisite": "Nominated provider/device, permitted operations and per-host driver/ownership/clock/stop evidence"}],
        "sads": {"allocatedSourceIds": [f"XVE-SYS-{number:04d}" for number in range(159, 179)], "normativeText": "unavailable",
            "satisfaction": "not_claimed", "repositoryEvidence": ["docs/implementation/sads-dispositions.md"]},
        "repositoryEvidence": ["docs/implementation/baseline.md", "docs/implementation/dependencies.md", "docs/implementation/platform-support.md",
            "evidence/studio/M0-linux-baseline/verification.json"],
        "limitations": ["Source pins do not establish a coherent admitted live execution set.",
            "Provider supportedHostOS/available fields are descriptor declarations; native host evidence qualifies verification independently.",
            "Repository evidence references require the source checkout; they are not promises that evidence is embedded in the application bundle.",
            "Native Windows is held; normative SADS and live runtime/provider gates remain open. T001 remains in progress."],
    }
    # These references come from the checker literals above, never from the input manifest.
    def fixed_evidence(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "repositoryEvidence":
                    for relative in item:
                        path = (ROOT / relative).resolve()
                        if not path.is_relative_to(ROOT) or not path.is_file():
                            raise BaselineDrift("RECORDED_EVIDENCE_MISSING")
                else:
                    fixed_evidence(item)
        elif isinstance(value, list):
            for item in value:
                fixed_evidence(item)
    fixed_evidence(expected)
    return expected


def unique_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise BaselineDrift("DUPLICATE_MANIFEST_KEY")
        value[key] = item
    return value


def main():
    errors = []
    try:
        raw = MANIFEST.read_bytes()
        if len(raw) > MAX_MANIFEST_BYTES:
            raise BaselineDrift("MANIFEST_SIZE_EXCEEDED")
        recorded = json.loads(raw, object_pairs_hook=unique_pairs)
        expected = observed_baseline()
        if not isinstance(recorded, dict):
            raise BaselineDrift("MANIFEST_OBJECT_REQUIRED")
        if set(recorded) != set(expected):
            errors.append("Manifest sections differ from descriptive format 1.0.")
        errors.extend(f"{key}: differs from pinned sources, installed library, descriptors or recorded scope."
                      for key, value in expected.items() if key not in recorded or
                      json.dumps(recorded[key], sort_keys=True, allow_nan=False) != json.dumps(value, sort_keys=True, allow_nan=False))
    except BaselineDrift as error:
        errors.append(f"{error}: reconcile the selected locks, installed library and recorded evidence in a full contributor checkout.")
    except (OSError, ValueError, KeyError, TypeError, StopIteration, RecursionError):
        # Avoid dumping manifest contents, local paths or installed metadata into logs.
        errors.append("Baseline prerequisites unavailable, malformed or drifting; use a provisioned full contributor checkout.")
    print(json.dumps({"valid": not errors, "scope": "descriptive_platform_baseline_only", "runtimeAdmission": False,
                      "errors": errors}, indent=2))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())

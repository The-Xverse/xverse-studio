"""Profile/inspection semantics and repeated decoding on actual Autoverse inputs."""

from copy import deepcopy
import json
import os
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from xverse_studio.projects.inspection import inspect_project
from xverse_studio.projects.service import Projects
from xverse_studio.profiles import ProfileRegistry
from xverse_studio.storage.core import Store, digest
from xverse_studio.xdl import XDLAdapter
from xverse_studio.xdl.examples import dump_yaml


@pytest.fixture
def authored():
    selected = os.environ.get("STUDIO_AUTOVERSE_PERFORMANCE_INPUTS")
    assert selected, "Explicit prepared actual Autoverse benchmark inputs required"
    prepared = Path(selected)
    context = json.loads((prepared / "fixtures.json").read_bytes())
    root = Path(
        json.loads((prepared / "data-root.private.json").read_bytes())["dataRoot"]
    )
    adapter = XDLAdapter()
    projects = Projects(Store(root), adapter)
    project = projects.read(context["model"]["projectId"])
    assert project["sourceIntegrity"] == "intact"
    registry = ProfileRegistry(adapter)
    return project, registry


def test_actual_autoverse_inspection_decodes_large_model_once(authored, monkeypatch):
    project, registry = authored
    sources = {doc["path"]: doc["content"] for doc in project["documents"].values()}
    expected = registry.authored_findings(sources)
    original = YAML.load
    counts = {name: 0 for name in sources}

    def measured(loader, stream):
        for name, content in sources.items():
            if stream == content:
                counts[name] += 1
        return original(loader, stream)

    before = deepcopy(project)
    monkeypatch.setattr(YAML, "load", measured)
    report = inspect_project(project, registry)
    assert project == before
    assert report["projectId"] == project["projectId"]
    assert not report["unparsed"]
    system = next(name for name in sources if name.endswith("system.xdl.yaml"))
    assert counts[system] == 1, (
        "Inspection must not re-decode the large model to find Profile declarations"
    )
    assert expected == []


@pytest.mark.parametrize(
    "case",
    [
        "admitted",
        "unknown",
        "version",
        "schema",
        "missing",
        "malformed-model",
        "opaque-model-extension",
    ],
)
def test_actual_autoverse_profile_decisions_remain_complete_and_read_only(
    authored, case
):
    project, registry = authored
    project = deepcopy(project)
    yaml = YAML(typ="safe")
    resources = {
        key: yaml.load(doc["content"]) for key, doc in project["documents"].items()
    }
    profile = next(
        key for key, value in resources.items() if value["kind"] == "Profile"
    )
    system = next(key for key, value in resources.items() if value["kind"] == "System")
    if case == "unknown":
        resources[profile]["spec"]["extensionNamespace"] = "org.example.unadmitted"
    elif case == "version":
        resources[profile]["metadata"]["version"] = "999.0.0"
    elif case == "schema":
        resources[profile]["spec"]["schemaRef"] = "urn:unadmitted:schema"
    elif case == "missing":
        del project["documents"][profile]
    elif case == "malformed-model":
        project["documents"][system]["content"] = "spec: [unterminated"
    elif case == "opaque-model-extension":
        resources[system].setdefault("extensions", {})["org.example.unknown"] = {
            "opaque": [True, "keep Ω", {"unknown": 1}]
        }
    for key in list(project["documents"]):
        if case == "malformed-model" and key == system:
            continue
        project["documents"][key]["content"] = dump_yaml(resources[key])
        project["documents"][key]["digest"] = digest(
            project["documents"][key]["content"].encode()
        )
    before = deepcopy(project)
    sources = {doc["path"]: doc["content"] for doc in project["documents"].values()}
    original_findings = registry.authored_findings(sources)
    observed = []
    original = registry.authored_findings

    def checked(documents):
        result = original(documents)
        observed.extend(result)
        return result

    registry.authored_findings = checked
    report = inspect_project(project, registry)
    assert project == before
    assert observed == original_findings
    assert all(item["executionAllowed"] is False for item in report["unresolved"])
    assert report["executionBlocked"] is bool(
        report["unresolved"] or report["unparsed"]
    )
    if case != "admitted":
        assert report["executionBlocked"] is True
    if case == "malformed-model":
        assert system in {item["documentId"] for item in report["unparsed"]}
    if case == "opaque-model-extension":
        assert any(
            item["namespace"] == "org.example.unknown" and "keep Ω" in item["content"]
            for item in report["unresolved"]
        )

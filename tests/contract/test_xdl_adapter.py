import json
from pathlib import Path
import subprocess
import sys

import pytest

from xverse_studio.xdl import XDLAdapter, XDLRejected, examples, reference_configuration
from xverse_studio.xdl.examples import PROFILE_NAMESPACE, dump_yaml
from ruamel.yaml import YAML


@pytest.fixture
def documents():
    return examples()[0]["documents"]


def test_both_owned_examples_compile_with_public_platform_apis():
    for entry in examples():
        validation = XDLAdapter().validate(entry["documents"])
        compiled = XDLAdapter().compile(entry["documents"])
        assert validation["valid"], validation["diagnostics"]
        assert compiled["valid"], compiled["diagnostics"]
        assert compiled["semanticDigest"].startswith("sha256:")
        assert compiled["planDigest"].startswith("sha256:")
        assert entry["scope"] == "owned_reference"
        assert reference_configuration(entry["documents"], compiled)["gain"] == .8


def test_checked_in_corpus_preserves_pinned_platform_identity():
    corpus = Path(__file__).parents[1] / "fixtures" / "xdl" / "reference"
    documents = {p.name: p.read_text(encoding="utf-8") for p in corpus.glob("*.yaml")}
    expected = json.loads((corpus / "expected-identities.json").read_text())
    compiled = XDLAdapter().compile(documents)
    assert compiled["valid"], compiled["diagnostics"]
    assert compiled["planDigest"] == expected["planDigest"]
    assert compiled["semanticDigest"] == expected["semanticDigest"]


def test_real_cli_and_library_emit_identical_plan(documents, tmp_path):
    inputs = []
    for name, source in documents.items():
        path = tmp_path / name
        path.write_text(source, encoding="utf-8")
        inputs.append(str(path))
    schemas = XDLAdapter().profile_schema_paths
    schema_args = [part for schema in schemas for part in ("--profile-schema", schema)]
    completed = subprocess.run([sys.executable, "-m", "xverse_xdl", "experiment", "compile", "--format", "json",
                                *schema_args, *inputs], capture_output=True, text=True, timeout=20)
    assert completed.returncode == 0, completed.stderr
    cli = json.loads(completed.stdout)
    api = XDLAdapter().compile(documents)
    assert cli["plan"] == api["plan"]
    assert cli["plan"]["digest"]["value"] == api["planDigest"].removeprefix("sha256:")


def test_comments_line_endings_order_and_json_preserve_platform_identity(documents):
    yaml = YAML(typ="safe")
    equivalent = {name.removesuffix("yaml") + "json": json.dumps(yaml.load(source), indent=4)
                  for name, source in reversed(list(documents.items()))}
    first = XDLAdapter().compile(documents)
    second = XDLAdapter().compile(equivalent)
    commented = {name: "# A presentation comment\r\n" + source.replace("\n", "\r\n") for name, source in documents.items()}
    third = XDLAdapter().compile(commented)
    assert first["valid"] and second["valid"] and third["valid"]
    assert first["semanticDigest"] == second["semanticDigest"] == third["semanticDigest"]
    assert first["planDigest"] == second["planDigest"] == third["planDigest"]


def test_authoritative_diagnostic_has_document_source_location(documents):
    docs = {**documents, "system.xdl.yaml": documents["system.xdl.yaml"].replace("clockClass: simulation", "clockClass: invented")}
    report = XDLAdapter().validate(docs)
    assert report["valid"] is False
    diagnostic = next(d for d in report["diagnostics"] if d["code"].startswith("XDL-SCHEMA"))
    assert diagnostic["location"]["documentId"] == "system.xdl.yaml"
    assert diagnostic["location"]["line"] > 0
    assert diagnostic["pointer"].startswith("/spec/timeDomains")


def test_unknown_payload_is_preserved_and_cannot_execute(documents):
    yaml = YAML(typ="safe")
    resource = yaml.load(documents["system.xdl.yaml"])
    resource["extensions"] = {"org.example.unknown": {"opaque": {"retain": [1, "hello"]}}}
    original = dump_yaml(resource)
    docs = {**documents, "system.xdl.yaml": original}
    report = XDLAdapter().compile(docs)
    assert not report["valid"] and report["plan"] is None
    assert docs["system.xdl.yaml"] == original
    with pytest.raises(XDLRejected, match="compiler rejected"):
        reference_configuration(docs)


def test_permitted_parameter_edit_changes_effective_requested_plan(documents):
    yaml = YAML(typ="safe")
    resource = yaml.load(documents["scenario.xdl.yaml"])
    next(p for p in resource["extensions"][PROFILE_NAMESPACE]["parameters"] if p["id"] == "target")["value"] = 2
    edited = {**documents, "scenario.xdl.yaml": dump_yaml(resource)}
    original = XDLAdapter().compile(documents)
    compiled = XDLAdapter().compile(edited)
    assert compiled["valid"]
    assert compiled["planDigest"] != original["planDigest"]
    effective = reference_configuration(edited, compiled)
    assert effective["target"] == 2
    assert effective["planDigest"] == compiled["planDigest"]
    with pytest.raises(XDLRejected) as error:
        reference_configuration(edited, original)
    assert error.value.code == "PREFLIGHT_STALE"


def test_unsupported_executable_edit_does_not_run_a_fixed_preset(documents):
    yaml = YAML(typ="safe")
    resource = yaml.load(documents["system.xdl.yaml"])
    resource["spec"]["nodes"].append({"id": "another-node", "roles": ["compute"]})
    edited = {**documents, "system.xdl.yaml": dump_yaml(resource)}
    assert XDLAdapter().compile(edited)["valid"]
    with pytest.raises(XDLRejected, match="cannot execute"):
        reference_configuration(edited)


@pytest.mark.parametrize("name,value", [("gain", 100), ("gain", -1), ("fault", "shell-command"), ("duration", 30.1), ("timestep", .03)])
def test_reference_bounds_reject_before_effects(documents, name, value):
    yaml = YAML(typ="safe")
    resource = yaml.load(documents["scenario.xdl.yaml"])
    next(p for p in resource["extensions"][PROFILE_NAMESPACE]["parameters"] if p["id"] == name)["value"] = value
    edited = {**documents, "scenario.xdl.yaml": dump_yaml(resource)}
    with pytest.raises(XDLRejected):
        reference_configuration(edited)


def test_feedback_cycle_keeps_base_validity_and_compiler_limitation_explicit(documents):
    yaml = YAML(typ="safe")
    resource = yaml.load(documents["system.xdl.yaml"])
    next(p for p in resource["spec"]["endpoints"] if p["id"] == "observer-in")["ownerId"] = "controller"
    edited = {**documents, "system.xdl.yaml": dump_yaml(resource)}
    assert XDLAdapter().validate(edited)["valid"]
    compiled = XDLAdapter().compile(edited)
    assert not compiled["valid"]
    assert any(d["code"] == "XDL1-PLAN-DEPENDENCY-CYCLE" for d in compiled["diagnostics"])


@pytest.mark.parametrize("name", ["../escape.yaml", "/etc/unsafe.yaml", "C:drive.yaml", "folder\\file.yaml"])
def test_source_names_never_become_host_file_requests(name):
    with pytest.raises(XDLRejected):
        XDLAdapter().validate({name: "hello"})


def test_unsafe_yaml_and_duplicate_keys_are_not_projected():
    for source in ("!!python/object/apply:os.system ['echo unsafe']", "kind: System\nkind: Component", "a: &a [*a]"):
        report = XDLAdapter().project({"unsafe.yaml": source})
        assert not report["valid"]
        assert report["elements"] == []


def test_assessment_is_admitted_inert_but_definition_identity_is_retained(documents):
    yaml = YAML(typ="safe")
    scenario = yaml.load(documents["scenario.xdl.yaml"])
    definition = scenario["extensions"]["io.xverse.studio.experiments"]["definitions"][0]
    definition["expression"]["right"]["value"] = .5
    updated = {**documents, "scenario.xdl.yaml": dump_yaml(scenario)}
    before = XDLAdapter().compile(documents)
    after = XDLAdapter().compile(updated)
    assert after["valid"]
    assert before["planDigest"] != after["planDigest"]
    assert reference_configuration(updated, after)["target"] == 1
    definition["systemRef"] = "xdl://org.example/system/another-system"
    invalid = {**documents, "scenario.xdl.yaml": dump_yaml(scenario)}
    with pytest.raises(XDLRejected, match="references"):
        reference_configuration(invalid)


@pytest.mark.parametrize("field,value", [("componentInstances", None), ("endpoints", "invalid"), ("flows", None),
                                         ("nodes", None), ("timeDomains", None), ("metadata", []), ("spec", None)])
def test_invalid_draft_collections_return_diagnostics_without_rewriting_source(documents, field, value):
    yaml = YAML(typ="safe")
    resource = yaml.load(documents["system.xdl.yaml"])
    if field in {"metadata", "spec"}:
        resource[field] = value
    else:
        resource["spec"][field] = value
    original = dump_yaml(resource)
    inputs = {**documents, "system.xdl.yaml": original}
    projected = XDLAdapter().project(inputs)
    assert projected["valid"] is False
    assert projected["diagnostics"]
    assert projected["elements"] == []
    assert projected["connections"] == []
    assert inputs["system.xdl.yaml"] == original

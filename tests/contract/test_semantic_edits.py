import pytest
from ruamel.yaml import YAML

from xverse_studio.xdl import XDLAdapter, XDLRejected, examples
from xverse_studio.xdl.edits import semantic_edits


@pytest.fixture
def documents():
    return examples()[0]["documents"]


def test_parameter_edit_preserves_comment_and_changes_compiled_plan(documents):
    documents["scenario.xdl.yaml"] = "# keep this authored comment\n" + documents["scenario.xdl.yaml"]
    before = XDLAdapter().compile(documents)
    changed = semantic_edits(documents, [{"kind": "set_parameter", "parameterId": "gain", "value": .4}])
    assert changed["scenario.xdl.yaml"].startswith("# keep this authored comment")
    assert changed["system.xdl.yaml"] == documents["system.xdl.yaml"]
    assert XDLAdapter().compile(changed)["valid"]
    assert XDLAdapter().compile(changed)["planDigest"] != before["planDigest"]


def test_add_element_has_distinct_definition_and_instance_identity(documents):
    updated = semantic_edits(documents, [{"kind": "add_element", "templateId": "reference-plant", "elementId": "second-plant", "nodeId": "plant-node"}])
    assert XDLAdapter().validate(updated)["valid"]
    system = YAML(typ="safe").load(updated["system.xdl.yaml"])
    added = next(n for n in system["spec"]["componentInstances"] if n["id"] == "second-plant")
    assert added["componentRef"]["name"] == "reference-plant"
    assert added["id"] != added["componentRef"]["name"]


def test_endpoint_connections_validate_units_and_preserve_transaction(documents):
    with pytest.raises(XDLRejected):
        semantic_edits(documents, [{"kind": "connect_endpoints", "flowId": "bad-flow", "sourceEndpointId": "plant-in", "destinationEndpointIds": ["controller-out"], "interfaceId": "command"}])
    assert "bad-flow" not in documents["system.xdl.yaml"]


def test_remove_referenced_element_requires_explicit_impacts(documents):
    with pytest.raises(XDLRejected, match="referenced"):
        semantic_edits(documents, [{"kind": "remove_element", "elementId": "plant"}])


def test_unknown_extension_is_preserved_or_edit_refused(documents):
    original = documents["system.xdl.yaml"] + "extensions:\n  org.example.opaque:\n    important: keep-me\n"
    documents["system.xdl.yaml"] = original
    try:
        updated = semantic_edits(documents, [{"kind": "set_parameter", "parameterId": "gain", "value": .3}])
    except XDLRejected:
        assert documents["system.xdl.yaml"] == original
    else:
        assert updated["system.xdl.yaml"] == original


def test_semantic_transaction_rejects_unknown_operations(documents):
    with pytest.raises(XDLRejected):
        semantic_edits(documents, [{"kind": "run_shell", "command": "bad"}])


def test_removal_is_scoped_to_stable_resource_identity(documents):
    updated = semantic_edits(documents, [{"kind": "add_element", "templateId": "reference-plant", "elementId": "state-out"}])
    removed = semantic_edits(updated, [{"kind": "remove_element", "elementId": "state-out"}])
    # Component endpoint state-out is a different stable resource element from the new instance.
    assert removed["plant.xdl.yaml"] == documents["plant.xdl.yaml"]
    assert XDLAdapter().validate(removed)["valid"]


@pytest.mark.parametrize("kind,fields", [
    ("set_parameter", {"parameterId": "gain", "value": .4}),
    ("remove_element", {"elementId": "plant"}),
    ("disconnect_flow", {"flowId": "state-flow"}),
])
def test_edit_never_ignores_an_incompatible_stable_target(documents, kind, fields):
    with pytest.raises(XDLRejected) as error:
        semantic_edits(documents, [{"kind": kind, "elementRef": "xdl://org.other/system/another#plant", **fields}])
    assert error.value.code == "SELECTION_UNRESOLVED"

"""Neutral logical authoring against the admitted public XDL validator."""
from copy import deepcopy

import pytest
from ruamel.yaml import YAML

from xverse_studio.xdl import XDLAdapter, XDLRejected, examples, reference_configuration
from xverse_studio.xdl.edits import semantic_edits


def asset(kind, identifier, properties, **extra):
    return {"kind": "add_logical_asset", "documentId": "system.xdl.yaml", "assetKind": kind,
            "elementId": identifier, "properties": properties, **extra}


@pytest.fixture
def documents():
    return examples()[0]["documents"]


def device(identifier="measurement-device"):
    return asset("device", identifier, {"capabilities": ["measurement"],
                 "supportedRealizationClasses": ["simulated", "physical"], "nodeId": "plant-node"})


def test_create_all_asset_kinds_projects_qualified_identities_and_preserves_source(documents):
    documents["system.xdl.yaml"] = "# preserve author intent\n" + documents["system.xdl.yaml"]
    original = deepcopy(documents)
    updated = semantic_edits(documents, [device(),
        asset("sensor", "measurement", {"deviceId": "measurement-device", "observedQuantity": "state",
              "outputEndpointId": "plant-out", "unitSemantics": "1", "maturity": "prototype"}),
        asset("actuator", "command-actuator", {"deviceId": "measurement-device", "controlledQuantity": "command",
              "inputEndpointId": "plant-in", "unitSemantics": "1", "limits": {"vendorOpaque": {"kept": True}}}),
        asset("model", "external-model", {"modelKind": "opaque-reference", "externalRef": "urn:example:model:1",
              "inputs": ["command"], "outputs": ["state"], "maturity": "architectural-target"})])
    assert documents == original
    assert updated["system.xdl.yaml"].startswith("# preserve author intent")
    assert all(updated[name] == source for name, source in documents.items() if name != "system.xdl.yaml")
    assert XDLAdapter().validate(updated)["valid"]
    projected = XDLAdapter().project(updated)
    found = {e["id"]: e for e in projected["elements"]}
    for identifier in ("measurement-device", "measurement", "command-actuator", "external-model"):
        assert found[identifier]["ref"].endswith("/system/reference-loop#" + identifier)
    assert found["command-actuator"]["limits"] == {"vendorOpaque": {"kept": True}}
    revised = semantic_edits(updated, [{"kind": "update_logical_asset", "documentId": "system.xdl.yaml",
        "assetKind": "actuator", "elementId": "command-actuator", "properties": {"controlledQuantity": "requested-command"}}])
    actuator = next(e for e in XDLAdapter().project(revised)["elements"] if e["id"] == "command-actuator")
    assert actuator["limits"] == {"vendorOpaque": {"kept": True}}
    with pytest.raises(XDLRejected):
        reference_configuration(updated)


def test_device_and_endpoint_bundle_are_one_validated_transaction(documents):
    changed = semantic_edits(documents, [device() | {"endpoints": [{"id": "measurement-out", "ownerId": "measurement-device",
        "interfaceId": "state", "direction": "output"}]},
        asset("sensor", "measurement", {"deviceId": "measurement-device", "observedQuantity": "state",
            "outputEndpointId": "measurement-out", "unitSemantics": "1", "maturity": "prototype"})])
    assert XDLAdapter().validate(changed)["valid"]


def test_update_keeps_identity_and_independent_capability_and_placement(documents):
    added = semantic_edits(documents, [device()])
    namespace = YAML(typ="safe").load(added["system.xdl.yaml"])["metadata"]["namespace"]
    changed = semantic_edits(added, [{"kind": "update_logical_asset", "documentId": "system.xdl.yaml",
        "assetKind": "device", "elementId": "measurement-device", "elementRef": f"xdl://{namespace}/system/reference-loop#measurement-device",
        "properties": {"nodeId": "controller-node", "capabilities": ["capture"]}}])
    value = next(e for e in XDLAdapter().project(changed)["elements"] if e["id"] == "measurement-device")
    assert value["nodeId"] == "controller-node"
    assert value["capabilities"] == ["capture"]
    assert value["supportedRealizationClasses"] == ["simulated", "physical"]


@pytest.mark.parametrize("invalid", [
    device("plant"), device() | {"properties": {"id": "identity-substitution"}},
    device() | {"assetKind": "ecu"}, device() | {"properties": {"capabilities": ["x"], "supportedRealizationClasses": ["software"]}},
    device() | {"properties": {"capabilities": ["x"], "supportedRealizationClasses": ["physical"], "nodeId": "missing"}},
    asset("sensor", "bad-sensor", {"observedQuantity": "state", "outputEndpointId": "missing", "unitSemantics": "1", "maturity": "prototype"}),
    asset("actuator", "bad-actuator", {"controlledQuantity": "state", "inputEndpointId": "plant-out", "unitSemantics": "1"}),
    asset("model", "bad-model", {"modelKind": "opaque", "externalRef": "urn:example:model:1", "inputs": ["missing"], "outputs": [], "maturity": "prototype"}),
    device() | {"endpoints": [{"id": "plant-in", "ownerId": "measurement-device", "interfaceId": "command", "direction": "input"}]},
    device() | {"endpoints": [{"id": "measurement-out", "ownerId": "plant", "interfaceId": "state", "direction": "output"}]},
])
def test_invalid_transaction_preserves_all_inputs(documents, invalid):
    before = deepcopy(documents)
    with pytest.raises(XDLRejected):
        semantic_edits(documents, [device("prior-valid-add"), invalid])
    assert documents == before


def test_update_never_ignores_incompatible_qualified_identity(documents):
    added = semantic_edits(documents, [device()])
    with pytest.raises(XDLRejected) as error:
        semantic_edits(added, [{"kind": "update_logical_asset", "assetKind": "device", "elementId": "measurement-device",
            "elementRef": "xdl://other/system/wrong#measurement-device", "properties": {"nodeId": "controller-node"}}])
    assert error.value.code == "SELECTION_UNRESOLVED"


def test_unknown_envelope_and_executable_properties_are_rejected(documents):
    for invalid in (device() | {"command": "anything"}, device() | {"properties": {"capabilities": ["x"],
            "supportedRealizationClasses": ["simulated"], "command": "anything"}}):
        with pytest.raises(XDLRejected):
            semantic_edits(documents, [invalid])


@pytest.mark.parametrize("changes", [
    {"assetKind": "sensor"}, {"properties": {"id": "replacement"}}, {"properties": {}},
    {"properties": {"supportedRealizationClasses": ["emulated"]}},
    {"properties": {"nodeId": None}},
])
def test_update_rejects_kind_identity_and_schema_changes_atomically(documents, changes):
    added = semantic_edits(documents, [device()])
    before = deepcopy(added)
    edit = {"kind": "update_logical_asset", "assetKind": "device", "elementId": "measurement-device",
            "properties": {"capabilities": ["new-role"]}} | changes
    with pytest.raises(XDLRejected):
        semantic_edits(added, [edit])
    assert added == before


def test_endpoint_bundle_is_bounded(documents):
    with pytest.raises(XDLRejected) as error:
        semantic_edits(documents, [device() | {"endpoints": [{"id": f"port-{i}", "ownerId": "measurement-device",
            "interfaceId": "state", "direction": "output"} for i in range(65)]}])
    assert error.value.code == "INVALID_EDIT"


def test_malformed_port_direction_is_a_rejected_transaction(documents):
    with pytest.raises(XDLRejected):
        semantic_edits(documents, [device() | {"endpoints": [{"id": "measurement-out", "ownerId": "measurement-device",
            "interfaceId": "state", "direction": {"malformed": True}}]},
            asset("sensor", "measurement", {"deviceId": "measurement-device", "observedQuantity": "state",
                "outputEndpointId": "measurement-out", "unitSemantics": "1", "maturity": "prototype"})])


def test_explicit_unplacement_preserves_device_identity_and_supported_realizations(documents):
    added = semantic_edits(documents, [device()])
    changed = semantic_edits(added, [{"kind": "update_logical_asset", "assetKind": "device",
        "elementId": "measurement-device", "properties": {}, "unsetProperties": ["nodeId"]}])
    value = next(e for e in XDLAdapter().project(changed)["elements"] if e["id"] == "measurement-device")
    assert "nodeId" not in value
    assert value["supportedRealizationClasses"] == ["simulated", "physical"]
    assert value["capabilities"] == ["measurement"]


@pytest.mark.parametrize("unset", [["id"], ["capabilities"], ["supportedRealizationClasses"], ["unknown"], ["nodeId", "nodeId"], "nodeId"])
def test_unset_cannot_remove_identity_or_required_fields(documents, unset):
    added = semantic_edits(documents, [device()])
    with pytest.raises(XDLRejected):
        semantic_edits(added, [{"kind": "update_logical_asset", "assetKind": "device", "elementId": "measurement-device",
            "properties": {}, "unsetProperties": unset}])


def test_conflicting_property_set_and_unset_is_rejected(documents):
    added = semantic_edits(documents, [device()])
    with pytest.raises(XDLRejected):
        semantic_edits(added, [{"kind": "update_logical_asset", "assetKind": "device", "elementId": "measurement-device",
            "properties": {"nodeId": "controller-node"}, "unsetProperties": ["nodeId"]}])

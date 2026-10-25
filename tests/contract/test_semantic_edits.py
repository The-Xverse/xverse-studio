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


ADD_PLANT = {"kind": "add_element", "templateId": "reference-plant", "elementId": "second-plant", "nodeId": "plant-node"}


def binding(**fields):
    return {"kind": "add_binding", "bindingId": "second-plant-binding", "elementId": "second-plant",
            "targetId": "reference-target", "realizationClass": "simulated"} | fields


def test_add_binding_realizes_a_new_instance_separately_from_role_and_placement(documents):
    updated = semantic_edits(documents, [ADD_PLANT, binding(artifactIds=["reference-model"])])
    assert XDLAdapter().validate(updated)["valid"]
    deployment = YAML(typ="safe").load(updated["deployment.xdl.yaml"])
    added = next(b for b in deployment["spec"]["bindings"] if b["id"] == "second-plant-binding")
    target = next(t for t in deployment["spec"]["targets"] if t["id"] == "reference-target")
    assert added["logicalRef"] == {"apiVersion": "xverse.io/xdl/v1alpha1", "kind": "System",
                                   "namespace": "org.xverse.studio.process-control",
                                   "name": "reference-loop", "element": "second-plant"}
    assert added["realizationClass"] == "simulated" and added["lifecycle"] == target["lifecycle"]
    assert added["artifactIds"] == ["reference-model"]
    system = YAML(typ="safe").load(updated["system.xdl.yaml"])
    # Placement stays on the System instance; realization is only the binding.
    assert next(i for i in system["spec"]["componentInstances"] if i["id"] == "second-plant")["nodeId"] == "plant-node"
    without = semantic_edits(documents, [ADD_PLANT])
    assert len(YAML(typ="safe").load(without["deployment.xdl.yaml"])["spec"]["bindings"]) == 2


@pytest.mark.parametrize("fields,code", [
    ({"bindingId": "plant-binding"}, "IDENTITY_CONFLICT"),
    ({"targetId": "unknown-target"}, "SELECTION_UNRESOLVED"),
    ({"realizationClass": "firmware"}, "INVALID_EDIT"),
    ({"elementId": "not-an-element"}, "SELECTION_UNRESOLVED"),
    ({"artifactIds": ["undeclared-artifact"]}, "SELECTION_UNRESOLVED"),
    ({"bindingId": "Bad_Id"}, "INVALID_EDIT"),
    ({"artifactIds": [{"not": "an id"}]}, "SELECTION_UNRESOLVED"),
])
def test_add_binding_refuses_unresolved_or_conflicting_choices(documents, fields, code):
    before = dict(documents)
    with pytest.raises(XDLRejected) as error:
        semantic_edits(documents, [ADD_PLANT, binding(**fields)])
    assert error.value.code == code
    assert documents == before


def test_api_instance_and_binding_commit_atomically(client):
    p = client.post("/api/v1/projects", json={"name": "wizard transaction"}).json()
    rejected = client.post(
        f"/api/v1/projects/{p['projectId']}/edits",
        headers={"If-Match": str(p["revision"])},
        json={"baseRevision": p["revision"], "edits": [ADD_PLANT, binding(targetId="missing")]},
    )
    assert rejected.status_code == 422
    current = client.get(f"/api/v1/projects/{p['projectId']}").json()
    assert current["revision"] == p["revision"]
    assert "second-plant" not in "".join(d["content"] for d in current["documents"].values())
    accepted = client.post(
        f"/api/v1/projects/{p['projectId']}/edits",
        headers={"If-Match": str(p["revision"])},
        json={"baseRevision": p["revision"], "edits": [ADD_PLANT, binding()]},
    )
    assert accepted.status_code == 200, accepted.text
    text = "".join(d["content"] for d in accepted.json()["documents"].values())
    assert "second-plant-binding" in text
    history = client.get(f"/api/v1/projects/{p['projectId']}/revisions").json()
    assert history["items"][0]["origin"]["edits"] == ["add_element", "add_binding"]


@pytest.mark.parametrize("element", ["command-flow", "state", "plant-node", "plant-in"])
def test_add_binding_realizes_only_realizable_members(documents, element):
    with pytest.raises(XDLRejected) as error:
        semantic_edits(documents, [binding(bindingId="extra-binding", elementId=element)])
    assert error.value.code == "SELECTION_UNRESOLVED"


def test_add_binding_refuses_a_second_realization_of_the_same_element(documents):
    with pytest.raises(XDLRejected) as error:
        semantic_edits(documents, [binding(bindingId="plant-again", elementId="plant")])
    assert error.value.code == "REALIZATION_CONFLICT"


@pytest.fixture
def configurable(documents):
    plant = YAML(typ="safe").load(documents["plant.xdl.yaml"])
    plant["spec"]["parameters"] = [
        {"id": "response-scale", "valueType": "number", "unitSemantics": "1",
         "mutability": "configuration", "default": 1.0, "description": "Scales the response."},
        {"id": "fixed-mode", "valueType": "string", "unitSemantics": "1", "mutability": "constant", "default": "a"},
    ]
    from io import StringIO
    out = StringIO()
    YAML().dump(plant, out)
    documents["plant.xdl.yaml"] = out.getvalue()
    assert XDLAdapter().validate(documents)["valid"]
    return documents


def test_instance_configuration_uses_declared_typed_parameters(configurable):
    updated = semantic_edits(configurable, [ADD_PLANT | {"parameterValues": {"response-scale": 2.5}}])
    assert XDLAdapter().validate(updated)["valid"]
    system = YAML(typ="safe").load(updated["system.xdl.yaml"])
    added = next(i for i in system["spec"]["componentInstances"] if i["id"] == "second-plant")
    assert added["parameterValues"] == {"response-scale": 2.5}
    # The reusable definition keeps its own default.
    assert updated["plant.xdl.yaml"] == configurable["plant.xdl.yaml"]


@pytest.mark.parametrize("values,code", [
    ({"undeclared": 1}, "PARAMETER_UNRESOLVED"),
    ({"response-scale": "fast"}, "INVALID_EDIT"),
    ({"response-scale": True}, "INVALID_EDIT"),
    ({"fixed-mode": "b"}, "PARAMETER_IMMUTABLE"),
    ({}, "PARAMETER_UNRESOLVED"),
])
def test_instance_configuration_refuses_undeclared_mistyped_or_constant_values(configurable, values, code):
    with pytest.raises(XDLRejected) as error:
        semantic_edits(configurable, [ADD_PLANT | {"parameterValues": values}])
    assert error.value.code == code

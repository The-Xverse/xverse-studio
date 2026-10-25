"""Typed authored intent remains XDL; authoring never grants runtime authority."""

from copy import deepcopy
from io import StringIO

import pytest
from ruamel.yaml import YAML

from xverse_studio.xdl import XDLAdapter, XDLRejected, examples, reference_configuration
from xverse_studio.xdl.edits import semantic_edits


def documents():
    return deepcopy(examples()[0]["documents"])


def scenario(sources):
    return YAML(typ="safe").load(sources["scenario.xdl.yaml"])


def operation(kind, item_kind, identifier, properties=None):
    result = {
        "kind": kind,
        "documentId": "scenario.xdl.yaml",
        "itemKind": item_kind,
        "itemId": identifier,
    }
    if properties is not None:
        result["properties"] = properties
    return result


def test_author_steps_faults_observers_and_metrics_as_one_validated_transaction():
    original = documents()
    spec = scenario(original)["spec"]
    changed = semantic_edits(
        original,
        [
            operation(
                "add_scenario_item",
                "step",
                "stimulus-one",
                {
                    k: v
                    for k, v in {
                        **spec["steps"][0],
                        "schedule": {"at": 0.5, "unit": "s"},
                        "actionKind": "set_parameter",
                        "action": {"parameter": "target", "value": 2},
                    }.items()
                    if k != "id"
                },
            ),
            operation(
                "add_scenario_item",
                "fault",
                "fault-one",
                {
                    "targetRef": spec["steps"][0]["targetRef"],
                    "faultKind": "provider-defined",
                    "activation": "opaque activation intent",
                    "recovery": "opaque recovery intent",
                    "maturity": "prototype",
                },
            ),
            operation(
                "add_scenario_item",
                "observer",
                "observer-two",
                {k: v for k, v in spec["observers"][0].items() if k != "id"},
            ),
            operation(
                "add_scenario_item",
                "metric",
                "metric-two",
                {
                    k: v
                    for k, v in {
                        **spec["metrics"][0],
                        "observerIds": ["observer-two"],
                    }.items()
                    if k != "id"
                },
            ),
        ],
    )
    assert XDLAdapter().validate(changed)["valid"]
    assert all(
        changed[name] == content
        for name, content in original.items()
        if name != "scenario.xdl.yaml"
    )
    assert len(scenario(changed)["spec"]["steps"]) == 2
    assert (
        scenario(changed)["spec"]["faults"][0]["activation"]
        == "opaque activation intent"
    )
    assert len(scenario(original)["spec"]["steps"]) == 1
    with pytest.raises(XDLRejected):
        reference_configuration(changed)


def test_update_and_remove_preserve_opaque_payloads_and_unselected_comments():
    source = documents()
    source["scenario.xdl.yaml"] = (
        "# keep authored intent\n" + source["scenario.xdl.yaml"]
    )
    spec = scenario(source)["spec"]
    fields = {k: v for k, v in spec["steps"][0].items() if k != "id"}
    fields["action"] = {"operation": "opaque", "vendorPayload": {"unknown": [1, 2, 3]}}
    added = semantic_edits(
        source, [operation("add_scenario_item", "step", "other-step", fields)]
    )
    updated = semantic_edits(
        added,
        [
            operation(
                "update_scenario_item",
                "step",
                "other-step",
                {"schedule": {"at": 1, "unit": "s"}},
            )
        ],
    )
    assert scenario(updated)["spec"]["steps"][1]["action"] == fields["action"]
    assert updated["scenario.xdl.yaml"].startswith("# keep authored intent")
    removed = semantic_edits(
        updated, [operation("remove_scenario_item", "step", "other-step")]
    )
    assert scenario(removed)["spec"]["steps"] == spec["steps"]


@pytest.mark.parametrize(
    "edit",
    [
        operation(
            "update_scenario_item", "step", "start-reference", {"id": "replacement"}
        ),
        operation(
            "update_scenario_item",
            "step",
            "start-reference",
            {"schedule": {"at": -1, "unit": "s"}},
        ),
        operation(
            "update_scenario_item",
            "step",
            "start-reference",
            {"timeDomainId": "missing-clock"},
        ),
        operation(
            "update_scenario_item",
            "observer",
            "state-observer",
            {"targetRef": {"element": "missing"}},
        ),
        operation("remove_scenario_item", "step", "start-reference"),
        operation("remove_scenario_item", "observer", "state-observer"),
        operation(
            "update_scenario_item", "metric", "missing", {"acceptance": "new intent"}
        ),
        operation(
            "add_scenario_item", "device", "wrong-kind", {"anything": "anything"}
        ),
        operation(
            "update_scenario_item", "metric", "final-state", {"unknownField": True}
        ),
    ],
)
def test_invalid_scenario_transaction_keeps_entire_source_set(edit):
    source = documents()
    before = deepcopy(source)
    with pytest.raises(XDLRejected):
        semantic_edits(source, [edit])
    assert source == before


def test_conditions_and_qualified_selection_are_revision_transaction_inputs():
    source = documents()
    resource = scenario(source)
    ref = f"xdl://{resource['metadata']['namespace']}/scenario/{resource['metadata']['name']}"
    changed = semantic_edits(
        source,
        [
            {
                "kind": "set_scenario_conditions",
                "documentId": "scenario.xdl.yaml",
                "elementRef": ref,
                "properties": {
                    "initialConditions": {
                        "stateParameterRef": "initial",
                        "opaque": {"kept": True},
                    },
                    "acceptanceIntent": "Authored intent only",
                },
            }
        ],
    )
    assert scenario(changed)["spec"]["initialConditions"]["opaque"] == {"kept": True}
    with pytest.raises(XDLRejected):
        semantic_edits(
            source,
            [
                {
                    "kind": "set_scenario_conditions",
                    "elementRef": "xdl://other/scenario/wrong",
                    "properties": {"acceptanceIntent": "wrong target"},
                }
            ],
        )


def test_authoring_bounds_and_nonfinite_values_reject_before_commit():
    source = documents()
    from xverse_studio.experiments.authoring import edit_scenario

    resource = scenario(source)
    many = deepcopy(resource)
    many["spec"]["steps"] = [
        {**resource["spec"]["steps"][0], "id": f"step-{i}"} for i in range(64)
    ]
    with pytest.raises(XDLRejected, match="limit"):
        edit_scenario(
            many,
            operation(
                "add_scenario_item",
                "step",
                "too-many",
                {k: v for k, v in resource["spec"]["steps"][0].items() if k != "id"},
            ),
        )
    with pytest.raises(XDLRejected):
        semantic_edits(
            source,
            [
                operation(
                    "update_scenario_item",
                    "step",
                    "start-reference",
                    {"schedule": {"at": float("nan"), "unit": "s"}},
                )
            ],
        )


@pytest.mark.parametrize(
    "invalid",
    [
        {"kind": []},
        {"kind": {}},
        {
            "kind": "set_scenario_conditions",
            "documentId": [],
            "properties": {"acceptanceIntent": "intent"},
        },
        {
            "kind": "set_scenario_conditions",
            "elementRef": [],
            "properties": {"acceptanceIntent": "intent"},
        },
    ],
)
def test_malformed_selectors_are_typed_rejections_without_source_effects(invalid):
    source = documents()
    before = deepcopy(source)
    with pytest.raises(XDLRejected):
        semantic_edits(source, [invalid])
    assert source == before


def test_observer_removal_preserves_admitted_assessment_references_and_atomic_repair():
    original = documents()
    resource = scenario(original)
    resource["spec"]["observers"].append(
        {**resource["spec"]["observers"][0], "id": "other-observer"}
    )
    definitions = resource["extensions"]["io.xverse.studio.experiments"]["definitions"]
    definitions[0]["expression"]["left"]["input"]["observerRef"] = "other-observer"
    stream = StringIO()
    YAML().dump(resource, stream)
    original["scenario.xdl.yaml"] = stream.getvalue()
    before = deepcopy(original)
    removal = operation("remove_scenario_item", "observer", "other-observer")
    with pytest.raises(XDLRejected) as rejected:
        semantic_edits(original, [removal])
    assert rejected.value.code == "DEFINITION_REFERENCE_UNRESOLVED"
    assert original == before
    repaired = deepcopy(definitions)
    repaired[0]["expression"]["left"]["input"]["observerRef"] = "state-observer"
    changed = semantic_edits(
        original,
        [
            removal,
            {
                "kind": "set_assessment_definitions",
                "documentId": "scenario.xdl.yaml",
                "definitions": repaired,
            },
        ],
    )
    assert len(scenario(changed)["spec"]["observers"]) == 1
    assert XDLAdapter().validate(changed)["valid"]


def test_deep_patch_and_logical_asset_payloads_have_typed_bounded_refusal():
    nested = {"leaf": "opaque"}
    for _ in range(600):
        nested = {"nested": nested}
    original = documents()
    for edit in [
        {
            "kind": "set_scenario_conditions",
            "properties": {"initialConditions": nested},
        },
        {
            "kind": "add_logical_asset",
            "assetKind": "device",
            "elementId": "deep-device",
            "properties": nested,
        },
    ]:
        with pytest.raises(XDLRejected) as rejected:
            semantic_edits(original, [edit])
        assert rejected.value.code == "LIMIT_EXCEEDED"

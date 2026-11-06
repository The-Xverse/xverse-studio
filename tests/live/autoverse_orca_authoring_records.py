"""Narrow readback for explicit copy-local scenario authoring AT journeys."""

import copy
import hashlib
import json

from ruamel.yaml import YAML

from xverse_studio.storage.core import canonical


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_conditions(
    before, after, files_before, files_after, baseline, data, width, passed
):
    pid = baseline["projectId"]
    key = ("project", pid)
    project_before = json.loads(before[key])
    project_after = json.loads(after[key])
    advances = project_after["revision"] - project_before["revision"]
    assert advances in (0, 1) and (not passed or advances == 1)
    assert not (set(before) - set(after))
    changed = {k for k in before if before[k] != after[k]}
    added = set(after) - set(before)
    for name, digest in files_before.items():
        assert files_after.get(name) == digest, (
            "A previously committed project byte changed"
        )
    if advances == 0:
        assert not changed and not added and files_before == files_after
        return {
            "acceptedSemanticEdits": 0,
            "originalProjectBytesRetained": True,
            "allOriginalRecordsRetained": True,
        }
    revision = project_after["revision"]
    revision_key = ("revision", f"{pid}:{revision}")
    assert changed == {key} and added == {revision_key}
    assert {
        k: v for k, v in project_before.items() if k not in ("revision", "documents")
    } == {k: v for k, v in project_after.items() if k not in ("revision", "documents")}
    assert set(project_before["documents"]) == set(project_after["documents"])
    yaml = YAML(typ="safe")
    scenarios = [
        (identity, document)
        for identity, document in baseline["documents"].items()
        if yaml.load(document["content"]).get("kind") == "Scenario"
    ]
    assert len(scenarios) == 1
    identity, scenario = scenarios[0]
    expected = yaml.load(scenario["content"])
    initial = copy.deepcopy(expected["spec"]["initialConditions"])
    initial["orcaOpaque"] = {"width": width, "preserved": [1, "untouched"]}
    expected["spec"]["initialConditions"] = initial
    documents = {}
    for doc_id, meta in project_after["documents"].items():
        previous = project_before["documents"][doc_id]
        assert {k: v for k, v in meta.items() if k != "digest"} == {
            k: v for k, v in previous.items() if k != "digest"
        }
        path = data / "projects" / pid / "revisions" / str(revision) / meta["path"]
        raw = path.read_bytes()
        assert "sha256:" + sha(raw) == meta["digest"]
        if doc_id == identity:
            assert yaml.load(raw) == expected
        else:
            assert raw.decode() == baseline["documents"][doc_id]["content"]
        documents[meta["path"]] = raw
    seal = json.loads(after[revision_key])
    assert seal["projectId"] == pid and seal["revision"] == revision
    assert (
        seal["documents"] == project_after["documents"]
        and seal["manifest"] == project_after["manifest"]
    )
    assert seal["origin"] == {
        "kind": "semantic_edit",
        "edits": ["set_scenario_conditions"],
    }
    supporting = baseline.get("supportingFiles", {})
    assert seal["supportingFiles"] == {
        name: "sha256:" + sha(content.encode()) for name, content in supporting.items()
    }
    new_files = {
        f"projects/{pid}/revisions/{revision}/{name}": sha(raw)
        for name, raw in documents.items()
    }
    new_files.update(
        {
            f"projects/{pid}/revisions/{revision}/{name}": sha(content.encode())
            for name, content in supporting.items()
        }
    )
    manifest = (
        data / "projects" / pid / "revisions" / str(revision) / "project.studio.json"
    )
    assert manifest.read_bytes() == canonical(project_after["manifest"]).encode()
    new_files[f"projects/{pid}/revisions/{revision}/project.studio.json"] = sha(
        manifest.read_bytes()
    )
    for raw in [
        *documents.values(),
        *(content.encode() for content in supporting.values()),
    ]:
        name = f"projects/{pid}/objects/{sha(raw)}"
        if name not in files_before:
            new_files[name] = sha(raw)
    assert set(files_after) - set(files_before) == set(new_files)
    assert all(files_after[name] == digest for name, digest in new_files.items())
    return {
        "acceptedSemanticEdits": 1,
        "fromRevision": project_before["revision"],
        "toRevision": revision,
        "scenarioDocumentId": identity,
        "expectedInitialConditions": initial,
        "newProjectFiles": len(new_files),
        "newRevisionSealed": True,
        "originalProjectBytesRetained": True,
        "allOtherOriginalRecordsRetained": True,
        "onlySelectedProjectAndNewRevisionChanged": True,
        "unknownPayloadsPreserved": True,
    }


def verify_stimulus(
    before, after, files_before, files_after, baseline, data, width, passed
):
    """Admit only add/update/remove of one deterministic step in three new seals."""
    yaml = YAML(typ="safe")
    resources = [yaml.load(d["content"]) for d in baseline["documents"].values()]
    scenario = next(r for r in resources if r.get("kind") == "Scenario")
    reference = scenario["spec"]["systemRef"]
    system = next(
        r
        for r in resources
        if r.get("kind") == "System"
        and r["metadata"]["name"] == reference["name"]
        and r["metadata"]["namespace"] == reference["namespace"]
    )
    assert system["spec"]["nodes"], (
        "This enrolled Autoverse target has no first declared node"
    )
    identifier = f"orca-step-{width}"
    step = {
        "id": identifier,
        "targetRef": {
            "apiVersion": system["apiVersion"],
            "kind": "System",
            "namespace": system["metadata"]["namespace"],
            "name": system["metadata"]["name"],
            "element": system["spec"]["nodes"][0]["id"],
        },
        "timeDomainId": system["spec"]["timeDomains"][0]["id"],
        "actionKind": "set_parameter",
        "schedule": {"at": 0, "unit": "s"},
        "action": {"parameter": "target", "value": 1, "opaque": {"retained": width}},
    }
    assert not any(s["id"] == identifier for s in scenario["spec"]["steps"])
    first = copy.deepcopy(scenario)
    first["spec"]["steps"].append(step)
    second = copy.deepcopy(first)
    second["spec"]["steps"][-1]["schedule"]["at"] = 0.5
    states = [first, second, scenario]
    origins = ["add_scenario_item", "update_scenario_item", "remove_scenario_item"]
    return verify_scenario_history(
        before,
        after,
        files_before,
        files_after,
        baseline,
        data,
        states,
        origins,
        passed,
    )


def verify_observer_metric(
    before, after, files_before, files_after, baseline, data, width, passed
):
    """Admit one new observer/metric, reference refusal and ordered removal."""
    yaml = YAML(typ="safe")
    resources = [yaml.load(d["content"]) for d in baseline["documents"].values()]
    scenario = next(r for r in resources if r.get("kind") == "Scenario")
    reference = scenario["spec"]["systemRef"]
    system = next(
        r
        for r in resources
        if r.get("kind") == "System"
        and r["metadata"]["name"] == reference["name"]
        and r["metadata"]["namespace"] == reference["namespace"]
    )
    observer_id, metric_id = f"orca-observer-{width}", f"orca-metric-{width}"
    assert all(o["id"] != observer_id for o in scenario["spec"]["observers"])
    assert all(m["id"] != metric_id for m in scenario["spec"]["metrics"])
    observer = {
        "id": observer_id,
        "targetRef": {
            "apiVersion": system["apiVersion"],
            "kind": "System",
            "namespace": system["metadata"]["namespace"],
            "name": system["metadata"]["name"],
            "element": system["spec"]["nodes"][0]["id"],
        },
        "timeDomainId": system["spec"]["timeDomains"][0]["id"],
        "samplingIntent": f"Opaque authored sampling {width}; no live observation.",
        "payloadSchema": "urn:xverse:studio:normalized-scalar:v1",
        "unitSemantics": "1",
        "evidenceSinkRef": "urn:xverse:studio:reference:evidence",
    }
    metric = {
        "id": metric_id,
        "observerIds": [observer_id],
        "calculationRef": "urn:example:metric:opaque",
        "unitSemantics": "1",
        "acceptance": f"Opaque authored acceptance {width}; no verdict.",
    }
    first = copy.deepcopy(scenario)
    first["spec"]["observers"].append(observer)
    second = copy.deepcopy(first)
    second["spec"]["metrics"].append(metric)
    return verify_scenario_history(
        before,
        after,
        files_before,
        files_after,
        baseline,
        data,
        [first, second, first, scenario],
        [
            "add_scenario_item",
            "add_scenario_item",
            "remove_scenario_item",
            "remove_scenario_item",
        ],
        passed,
    )


def verify_fault(
    before,
    after,
    files_before,
    files_after,
    baseline,
    data,
    width,
    passed,
    *,
    source_only=False,
):
    """Admit only this prototype fault's exact authored timing/opaque intent."""
    yaml = YAML(typ="safe")
    resources = [yaml.load(d["content"]) for d in baseline["documents"].values()]
    scenario = next(r for r in resources if r.get("kind") == "Scenario")
    reference = scenario["spec"]["systemRef"]
    system = next(
        r
        for r in resources
        if r.get("kind") == "System"
        and r["metadata"]["name"] == reference["name"]
        and r["metadata"]["namespace"] == reference["namespace"]
    )
    identifier = f"orca-fault-{width}"
    assert all(f["id"] != identifier for f in scenario["spec"]["faults"])
    fault = {
        "id": identifier,
        "targetRef": {
            "apiVersion": system["apiVersion"],
            "kind": "System",
            "namespace": system["metadata"]["namespace"],
            "name": system["metadata"]["name"],
            "element": system["spec"]["nodes"][0]["id"],
        },
        "faultKind": "provider-defined",
        "activation": f"Opaque activation {width}; no runtime permission.",
        "recovery": f"Opaque recovery {width}; no runtime permission.",
        "maturity": "prototype",
    }
    if any(
        r.get("kind") == "Profile"
        and r.get("metadata", {}).get("version") == "0.1.0"
        and r.get("spec", {}).get("extensionNamespace") == "io.xverse.experiment"
        and r.get("spec", {}).get("schemaRef")
        == "https://xverse.io/profiles/experiment-lite/v0.1/schema.json"
        for r in resources
    ):
        fault["extensions"] = {
            "io.xverse.experiment": {
                "schemaVersion": "0.1",
                "kind": "fault-intent",
                "target": {
                    "apiVersion": scenario["apiVersion"],
                    "kind": "Scenario",
                    "namespace": scenario["metadata"]["namespace"],
                    "name": scenario["metadata"]["name"],
                    "element": identifier,
                },
                "trigger": {"kind": "time", "at": 2, "unit": "s"},
                "duration": {"value": 2, "unit": "s"},
                "timeDomainId": system["spec"].get("defaultTimeDomainId")
                or system["spec"]["timeDomains"][0]["id"],
            }
        }
    first = copy.deepcopy(scenario)
    first["spec"]["faults"].append(fault)
    second = copy.deepcopy(first)
    second["spec"]["faults"][-1]["recovery"] = (
        f"Edited opaque recovery {width}; no runtime permission."
    )
    states = [first, scenario] if source_only else [first, second, scenario]
    origins = (
        ["add_scenario_item", "remove_scenario_item"]
        if source_only
        else ["add_scenario_item", "update_scenario_item", "remove_scenario_item"]
    )
    return verify_scenario_history(
        before,
        after,
        files_before,
        files_after,
        baseline,
        data,
        states,
        origins,
        passed,
    )


def verify_fault_source(*args):
    return verify_fault(*args, source_only=True)


def verify_scenario_history(
    before, after, files_before, files_after, baseline, data, states, origins, passed
):
    pid = baseline["projectId"]
    key = ("project", pid)
    old = json.loads(before[key])
    current = json.loads(after[key])
    count = current["revision"] - old["revision"]
    assert 0 <= count <= len(states) and (not passed or count == len(states))
    assert not set(before) - set(after)
    for name, digest in files_before.items():
        assert files_after.get(name) == digest, "A previous project byte changed"
    if count == 0:
        assert before == after and files_before == files_after
        return {
            "acceptedSemanticEdits": 0,
            "originalProjectBytesRetained": True,
            "allOriginalRecordsRetained": True,
        }
    assert {k for k in before if before[k] != after[k]} == {key}
    revisions = list(range(old["revision"] + 1, current["revision"] + 1))
    assert set(after) - set(before) == {("revision", f"{pid}:{r}") for r in revisions}
    assert {k: v for k, v in old.items() if k not in ("revision", "documents")} == {
        k: v for k, v in current.items() if k not in ("revision", "documents")
    }
    yaml = YAML(typ="safe")
    identity = next(
        i
        for i, d in baseline["documents"].items()
        if yaml.load(d["content"]).get("kind") == "Scenario"
    )
    expected_files = {}
    supporting = baseline.get("supportingFiles", {})
    for index, revision in enumerate(revisions):
        seal = json.loads(after[("revision", f"{pid}:{revision}")])
        assert (
            seal["projectId"] == pid
            and seal["revision"] == revision
            and seal["manifest"] == old["manifest"]
        )
        assert seal["origin"] == {"kind": "semantic_edit", "edits": [origins[index]]}
        assert set(seal["documents"]) == set(old["documents"])
        contents = []
        for doc_id, meta in seal["documents"].items():
            assert {k: v for k, v in meta.items() if k != "digest"} == {
                k: v for k, v in old["documents"][doc_id].items() if k != "digest"
            }
            name = f"projects/{pid}/revisions/{revision}/{meta['path']}"
            raw = (data / name).read_bytes()
            assert meta["digest"] == "sha256:" + sha(raw)
            if doc_id == identity:
                assert yaml.load(raw) == states[index]
            else:
                assert raw.decode() == baseline["documents"][doc_id]["content"]
            expected_files[name] = sha(raw)
            contents.append(raw)
        assert seal["supportingFiles"] == {
            name: "sha256:" + sha(content.encode())
            for name, content in supporting.items()
        }
        for name, content in supporting.items():
            expected_files[f"projects/{pid}/revisions/{revision}/{name}"] = sha(
                content.encode()
            )
            contents.append(content.encode())
        manifest = canonical(seal["manifest"]).encode()
        name = f"projects/{pid}/revisions/{revision}/project.studio.json"
        assert (data / name).read_bytes() == manifest
        expected_files[name] = sha(manifest)
        for raw in contents:
            name = f"projects/{pid}/objects/{sha(raw)}"
            if name not in files_before:
                expected_files[name] = sha(raw)
    assert current["documents"] == seal["documents"]
    assert set(files_after) - set(files_before) == set(expected_files)
    assert all(files_after[name] == digest for name, digest in expected_files.items())
    return {
        "acceptedSemanticEdits": count,
        "fromRevision": old["revision"],
        "toRevision": current["revision"],
        "newRevisionSeals": revisions,
        "expectedEditKinds": origins[:count],
        "newProjectFiles": len(expected_files),
        "originalProjectBytesRetained": True,
        "allOtherOriginalRecordsRetained": True,
        "scenarioStatesIndependentlyVerified": count,
        "onlySelectedProjectAndNewRevisionsChanged": True,
        "originalScenarioSemanticsRestoredOnComplete": passed
        and states[-1] == yaml.load(baseline["documents"][identity]["content"]),
    }

"""Campaign mapping admission on the actual installed classic provider.

Static checks never probe or dispatch. Explicit native readiness cases are kept
separate and require the prepared environment; they still do not launch a workload.
"""

from copy import deepcopy
import json
import os
from pathlib import Path

import pytest

from autoverse_provider_admission import application, authenticated
from xverse_studio.blueprints.autoverse import documents
from xverse_studio.providers.autoverse.adapter import AutoverseProvider
from xverse_studio.storage.core import Problem
from xverse_studio.xdl import XDLAdapter


@pytest.fixture
def provider():
    receipt = json.loads(
        Path(os.environ["STUDIO_AUTOVERSE_TEST_INSTALLATION"]).read_bytes()
    )
    return AutoverseProvider(receipt["classic"])


def test_classic_duration_mapping_is_closed_and_preserves_every_other_payload(provider):
    sources = documents("studio-browser")
    before = deepcopy(sources)
    changed = provider.campaign_documents(sources, {"durationSeconds": 35})
    from ruamel.yaml import YAML

    yaml = YAML(typ="safe")
    assert set(changed) == set(sources)
    for name in sources:
        actual, expected = yaml.load(changed[name]), yaml.load(sources[name])
        if name == "scenario.xdl.yaml":
            expected["extensions"]["io.xverse.studio.native-runtime"][
                "durationSeconds"
            ] = 35
        assert actual == expected
    compiled = XDLAdapter().compile(changed)
    assert provider.configuration(changed, compiled)["durationSeconds"] == 35
    assert sources == before
    contract = provider.descriptor()["campaignContract"]
    assert contract["parameters"] == {
        "durationSeconds": {
            "type": "integer",
            "minimum": 30,
            "maximum": 1800,
            "unit": "s",
        }
    }
    assert contract["seedPolicy"] == "unsupported" and contract["maxConcurrency"] == 1


@pytest.mark.parametrize(
    "parameters",
    [
        {"seed": 1},
        {"durationSeconds": True},
        {"durationSeconds": 30.0},
        {"durationSeconds": 29},
        {"durationSeconds": 1801},
        {"durationSeconds": 35, "extra": 1},
    ],
)
def test_static_mapping_rejects_unsupported_axes_or_duration(provider, parameters):
    sources = documents("studio-browser")
    before = deepcopy(sources)
    with pytest.raises(Problem):
        provider.campaign_documents(sources, parameters)
    assert sources == before


def test_mapping_never_repairs_unsupported_source_to_gain_admission(provider):
    sources = documents("studio-browser")
    from ruamel.yaml import YAML
    from xverse_studio.xdl.examples import dump_yaml

    yaml = YAML(typ="safe")
    scenario = yaml.load(sources["scenario.xdl.yaml"])
    scenario["extensions"]["io.xverse.studio.native-runtime"]["unknown"] = "inert"
    sources["scenario.xdl.yaml"] = dump_yaml(scenario)
    before = deepcopy(sources)
    with pytest.raises(Problem):
        provider.campaign_documents(sources, {"durationSeconds": 35})
    assert sources == before


def test_real_ready_campaign_children_have_fresh_full_preflights(
    provider, tmp_path, monkeypatch
):
    app = application(tmp_path / "native readonly campaign admission Ω", provider)
    # Disable only scheduler advancement. Every readiness check below is real;
    # this case never claims runtime execution or mutable worker dispatch.
    monkeypatch.setattr(app.state.studio, "campaign_tick", lambda: None)

    def forbidden(*args, **kwargs):
        pytest.fail("Read-only campaign admission dispatched a worker")

    monkeypatch.setattr(app.state.studio.runs, "_dispatch", forbidden)
    with authenticated(app) as api:
        p = api.post(
            "/api/v1/projects",
            json={
                "name": "Actual campaign admission",
                "blueprintRef": "autoverse-classic",
            },
        ).json()
        response = api.post(
            f"/api/v1/projects/{p['projectId']}/preflights",
            json={"revision": p["revision"], "providerId": "autoverse.demo"},
        )
        assert response.status_code == 200, response.text
        pf = response.json()
        assert pf["status"] == "ready", pf["diagnostics"]
        store, runs = app.state.studio.store, app.state.studio.runs
        base = store.get("snapshot", pf["snapshotId"])
        original = deepcopy(base)
        body = {
            "snapshotId": base["snapshotId"],
            "matrix": {"durationSeconds": [30, 35]},
            "budget": {"maxRuns": 2, "maxTotalSeconds": 70},
            "concurrency": 1,
        }
        count = len(store.all("snapshot"))
        for changes, code in [
            ({"matrix": {"seed": [1]}}, "INVALID_MATRIX"),
            ({"matrix": {"durationSeconds": [30.0]}}, "INVALID_PARAMETER"),
            ({"matrix": {"durationSeconds": [29]}}, "INVALID_PARAMETER"),
            ({"matrix": {"durationSeconds": [1801]}}, "INVALID_PARAMETER"),
            ({"concurrency": 2}, "CAMPAIGN_CONCURRENCY"),
            ({"budget": {"maxRuns": 1}}, "CAMPAIGN_BUDGET"),
            ({"budget": {"maxRuns": 2, "maxTotalSeconds": 69}}, "CAMPAIGN_BUDGET"),
        ]:
            for route in ["/api/v1/campaigns/preview", "/api/v1/campaigns"]:
                refused = api.post(
                    route,
                    json={**body, **changes},
                    headers={"Idempotency-Key": "refused-contract"},
                )
                assert refused.status_code == 422 and refused.json()["code"] == code, (
                    refused.text
                )
        assert store.all("campaign") == store.all("operation") == []
        assert len(store.all("snapshot")) == count
        preview = api.post("/api/v1/campaigns/preview", json=body)
        assert preview.status_code == 200, preview.text
        assert (
            preview.json()["cardinality"] == 2
            and preview.json()["estimatedTotalSeconds"] == 70
        )
        assert len(store.all("snapshot")) == count and store.all("campaign") == []
        accepted = api.post(
            "/api/v1/campaigns",
            json=body,
            headers={"Idempotency-Key": "actual-campaign-admission"},
        )
        assert accepted.status_code == 202, accepted.text
        assert (
            api.post(
                "/api/v1/campaigns",
                json=body,
                headers={"Idempotency-Key": "actual-campaign-admission"},
            ).json()
            == accepted.json()
        )
        campaign = store.get("campaign", accepted.json()["campaignId"])
        before = len(store.all("snapshot"))
        altered = deepcopy(campaign["children"][0])
        altered["childKey"] = "sha256:" + "0" * 64
        with pytest.raises(Problem, match="original bounded matrix"):
            runs.prepare_campaign_child(campaign, altered)
        original_mapper = provider.campaign_documents
        with monkeypatch.context() as changed_mapping:
            changed_mapping.setattr(
                provider,
                "campaign_documents",
                lambda sources, parameters: original_mapper(
                    sources, {"durationSeconds": 30}
                ),
            )
            with pytest.raises(Problem, match="exact declared child parameters"):
                runs.prepare_campaign_child(campaign, campaign["children"][1])
        assert len(store.all("snapshot")) == before
        children = [
            runs.prepare_campaign_child(campaign, child)
            for child in campaign["children"]
        ]
        assert len({c["snapshotId"] for c in children}) == 2
        for prepared, seconds, child in zip(children, [30, 35], campaign["children"]):
            frozen = store.get("snapshot", prepared["snapshotId"])
            ready = store.get("preflight", prepared["preflightId"])
            assert ready["status"] == "ready" and ready["diagnostics"] == []
            assert (
                ready["readinessVersion"] == "1.0"
                and ready["readiness"]["observations"]
            )
            assert frozen["parentSnapshotId"] == base["snapshotId"]
            assert frozen["configuration"]["durationSeconds"] == seconds
            assert frozen["campaignChildKey"] == child["childKey"]
            assert (
                frozen["selection"] == base["selection"]
                and frozen["profileLocks"] == base["profileLocks"]
            )
            assert frozen["projectDocuments"] == frozen["documents"]
            runs.verify_snapshot(frozen)
        assert store.get("snapshot", base["snapshotId"]) == original
        assert api.get(f"/api/v1/projects/{p['projectId']}").json() == p
        assert store.all("run") == []


@pytest.mark.parametrize(
    "case",
    [
        "duration-list",
        "rule-type-list",
        "extra-contract",
        "boolean-concurrency",
        "uncontrolled-seed",
        "nonfinite-bound",
        "excess-duration",
        "unavailable-provider",
    ],
)
def test_decoded_contract_counterexamples_fail_closed_without_callback(
    provider, monkeypatch, case
):
    """Decoded schema units; altered descriptions are never installed as authority."""
    from xverse_studio.campaigns.mapping import InstalledCampaign

    descriptor = deepcopy(provider.descriptor())
    contract = descriptor["campaignContract"]
    if case == "duration-list":
        contract["durationParameter"] = []
    elif case == "rule-type-list":
        contract["parameters"]["durationSeconds"]["type"] = []
    elif case == "extra-contract":
        contract["extra"] = "inert"
    elif case == "boolean-concurrency":
        contract["maxConcurrency"] = True
    elif case == "uncontrolled-seed":
        contract["seedPolicy"] = "implicitly-applied"
    elif case == "nonfinite-bound":
        contract["parameters"]["durationSeconds"]["maximum"] = float("inf")
    elif case == "excess-duration":
        contract["parameters"]["durationSeconds"]["maximum"] = 1801
    else:
        descriptor["available"] = False
    sources = documents("studio-browser")
    config = provider.configuration(sources, XDLAdapter().compile(sources))
    snapshot = {
        "providerId": descriptor["providerId"],
        "providerIdentity": deepcopy(descriptor),
        "configuration": config,
    }

    def forbidden(*args, **kwargs):
        pytest.fail("Malformed contract invoked source mapping")

    monkeypatch.setattr(provider, "campaign_documents", forbidden)
    with pytest.raises(Problem):
        InstalledCampaign(snapshot, provider, descriptor)


def test_callable_mapping_without_frozen_contract_grants_no_authority(
    provider, monkeypatch
):
    from xverse_studio.campaigns.mapping import InstalledCampaign

    descriptor = deepcopy(provider.descriptor())
    descriptor.pop("campaignContract")
    snapshot = {"providerId": descriptor["providerId"], "providerIdentity": descriptor}

    def forbidden(*args, **kwargs):
        pytest.fail("Missing frozen contract invoked the inherited source mapper")

    monkeypatch.setattr(provider, "campaign_documents", forbidden)
    with pytest.raises(Problem):
        InstalledCampaign(snapshot, provider, descriptor)


def test_unicode_inert_metadata_keeps_actual_campaign_provenance_verifiable(
    provider, tmp_path, monkeypatch
):
    from ruamel.yaml import YAML
    from xverse_studio.xdl.examples import dump_yaml

    app = application(tmp_path / "Unicode campaign provenance Ω", provider)
    monkeypatch.setattr(app.state.studio, "campaign_tick", lambda: None)
    with authenticated(app) as api:
        p = api.post(
            "/api/v1/projects",
            json={
                "name": "Unicode campaign source",
                "blueprintRef": "autoverse-classic",
            },
        ).json()
        key, doc = next(
            (k, v)
            for k, v in p["documents"].items()
            if Path(v["path"]).name == "scenario.xdl.yaml"
        )
        scenario = YAML(typ="safe").load(doc["content"])
        scenario["metadata"]["description"] = "Durée μ: inert text, no execution"
        content = dump_yaml(scenario)
        assert "Durée μ" in content
        changed = api.put(
            f"/api/v1/projects/{p['projectId']}/documents/{key}",
            headers={"If-Match": str(p["revision"])},
            json={"content": content},
        )
        assert changed.status_code == 200, changed.text
        p = changed.json()
        pf = api.post(
            f"/api/v1/projects/{p['projectId']}/preflights",
            json={"revision": p["revision"], "providerId": "autoverse.demo"},
        ).json()
        assert pf["status"] == "ready", pf["diagnostics"]
        response = api.post(
            "/api/v1/campaigns/preview",
            json={
                "snapshotId": pf["snapshotId"],
                "matrix": {"durationSeconds": [30]},
                "budget": {"maxRuns": 1, "maxTotalSeconds": 30},
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["baseInput"]["status"] == "verified"
        assert (
            app.state.studio.store.all("run")
            == app.state.studio.store.all("campaign")
            == app.state.studio.store.all("operation")
            == []
        )

        body = {
            "snapshotId": pf["snapshotId"],
            "matrix": {"durationSeconds": [30]},
            "budget": {"maxRuns": 1, "maxTotalSeconds": 30},
        }
        created = api.post(
            "/api/v1/campaigns",
            headers={"Idempotency-Key": "unicode-provenance"},
            json=body,
        )
        assert created.status_code == 202, created.text
        identity = created.json()["campaignId"]
        detail = api.get("/api/v1/campaigns/" + identity).json()
        assert detail["baseInput"]["status"] == "verified"
        store = app.state.studio.store
        frozen = store.root / "snapshots" / pf["snapshotId"] / "snapshot.json"
        frozen.write_bytes(frozen.read_bytes() + b" ")
        unavailable = api.get("/api/v1/campaigns/" + identity).json()
        assert unavailable["baseInput"] == {
            "status": "unavailable",
            "reason": "SNAPSHOT_INTEGRITY",
        }
        assert unavailable["children"] == detail["children"]
        assert store.all("run") == []
        assert len(store.all("campaign")) == len(store.all("operation")) == 1

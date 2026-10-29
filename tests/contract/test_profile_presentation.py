"""T062: inert, sanitized domain presentation through the shared workflows."""
import pytest

from xverse_studio.profiles import ProfileRegistry
from xverse_studio.profiles.presentation import DOMAIN_PROFILES, sanitize_presentation
from xverse_studio.storage.core import Problem
from xverse_studio.xdl import XDLAdapter

PROCESS = "io.xverse.studio.domain.process-control"
AUTOMOTIVE = "io.xverse.studio.domain.automotive"


def _lock(client, namespace):
    entry = client.get("/api/v1/profiles/" + namespace).json()
    return {k: entry[k] for k in ("profileId", "version", "schemaDigest", "presentationDigest")}


def _bind(client, project, *namespaces):
    response = client.post(f"/api/v1/projects/{project['projectId']}/profile-bindings", headers={"If-Match": str(project["revision"])},
                           json={"baseRevision": project["revision"], "profiles": [_lock(client, n) for n in namespaces]})
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize("change", [
    lambda p: p["labels"].update(Element="<img src=x onerror=alert(1)>"),
    lambda p: p["labels"].update(Element="line\nbreak"),
    lambda p: p["labels"].update(Widget="Unknown core term"),
    lambda p: p["icons"].update(Element="javascript"),
    lambda p: p.update(documentation="javascript:alert(1)"),
    lambda p: p.update(documentation="http://insecure.example/doc"),
    lambda p: p["formGroups"].append({"id": "x", "label": "Run", "parameters": ["Not An Id"]}),
    lambda p: p.update(script="fetch('/')"),
    # Invisible and direction-changing characters can disguise text; they are not plain text.
    lambda p: p["labels"].update(Element="Unit\u202eevil"),
    lambda p: p["labels"].update(Element="Un\u200bit"),
    lambda p: p["labels"].update(Element="Unit\x85"),
    lambda p: p.update(description="\ufeffOwned"),
])
def test_presentation_with_markup_scripts_or_unknown_names_is_refused_whole(change):
    from copy import deepcopy

    value = deepcopy(DOMAIN_PROFILES[0]["presentation"])
    change(value)
    with pytest.raises(Problem) as error:
        sanitize_presentation(value)
    assert error.value.code == "PROFILE_CONFLICT"


def test_owned_domain_profiles_are_admitted_presentation_only():
    entries = {e["namespace"]: e for e in ProfileRegistry(XDLAdapter())._entries()}
    for namespace in (PROCESS, AUTOMOTIVE):
        entry = entries[namespace]
        assert entry["kind"] == "domain-presentation" and entry["maturity"] == "fixture" and entry["executionAllowed"] is False
        assert entry["schema"]["maxProperties"] == 0  # extension payloads carry no semantics
        assert entry["presentation"] == sanitize_presentation(entry["presentation"])


def test_blueprints_present_their_domain_terms_without_changing_semantics(client):
    process = client.post("/api/v1/projects", json={"name": "Process terms", "blueprintRef": "reference-process-control"}).json()
    automotive = client.post("/api/v1/projects", json={"name": "Vehicle terms", "blueprintRef": "reference-automotive"}).json()
    plain = client.get(f"/api/v1/projects/{process['projectId']}/presentation").json()
    assert plain["labels"]["Element"] == "Unit" and plain["source"] == "blueprint default (not bound)"
    assert [g["id"] for g in plain["formGroups"]] == ["setpoint", "horizon", "instrument-faults"]
    vehicle = client.get(f"/api/v1/projects/{automotive['projectId']}/presentation").json()
    assert vehicle["labels"]["Element"] == "ECU" and vehicle["domains"][0]["domain"] == "Automotive"
    from xverse_studio.profiles.presentation import effective_presentation

    # A project with neither a bound domain profile nor a blueprint keeps the core terms.
    core = effective_presentation({"manifest": {"profiles": [], "provenance": {"imported": True}}}, ProfileRegistry(XDLAdapter()))
    assert core["source"] == "core" and core["labels"]["Element"] == "Element" and core["formGroups"] == []
    before = client.post(f"/api/v1/projects/{process['projectId']}/compilations", json={"revision": process["revision"]}).json()["planDigest"]
    bound = _bind(client, process, PROCESS)
    presented = client.get(f"/api/v1/projects/{process['projectId']}/presentation").json()
    assert presented["source"] == "bound" and presented["labels"]["Flow"] == "Signal"
    after = client.post(f"/api/v1/projects/{process['projectId']}/compilations", json={"revision": bound["revision"]}).json()["planDigest"]
    assert after == before  # terminology never changes the executable plan
    preflight = client.post(f"/api/v1/projects/{process['projectId']}/preflights", json={"revision": bound["revision"]}).json()
    assert preflight["status"] == "ready", preflight["diagnostics"]


def test_compatible_cross_industry_selection_keeps_core_terms_where_domains_disagree(client):
    project = client.post("/api/v1/projects", json={"name": "Mixed domains"}).json()
    bound = _bind(client, project, PROCESS, AUTOMOTIVE)
    presented = client.get(f"/api/v1/projects/{project['projectId']}/presentation").json()
    assert {d["domain"] for d in presented["domains"]} == {"Process control", "Automotive"}
    assert presented["labels"]["Element"] == "Element" and "Element" in presented["conflicts"]
    assert presented["formGroups"] == []  # no single domain's grouping is imposed on a mixed project
    profiles = [d["path"] for d in bound["documents"].values() if "profile" in d["path"]]
    assert "xdl/profile-domain-process-control.xdl.yaml" in profiles and "xdl/profile-domain-automotive.xdl.yaml" in profiles
    validation = client.post(f"/api/v1/projects/{project['projectId']}/validations", json={"revision": bound["revision"]}).json()
    assert validation["valid"], validation["diagnostics"]

"""T014 authoritative CLI/API and native persistence checks on actual Autoverse.

Compilation proves declared intent, never readiness or execution. Lite refusal
uses the enrolled Autoverse project and may not dispatch a fallback workload.
"""

import json
from pathlib import Path
import subprocess
import sys

import pytest
from ruamel.yaml import YAML

import autoverse_provider_admission as enrollment
from autoverse_provider_admission import application, authenticated, project
from xverse_studio.host.ownership import own_root, RootOwnedError
from xverse_studio.storage.core import digest

target = enrollment.target


def checked(response, expected=200):
    assert response.status_code == expected, response.text
    return response.json()


def compile_project(api, p, provider_id):
    result = checked(api.post(
        f"/api/v1/projects/{p['projectId']}/compilations",
        json={"revision": p["revision"], "providerId": provider_id},
    ))
    assert result["valid"], result["diagnostics"]
    return result


def forbidden(*args, **kwargs):
    raise AssertionError("Foundation inspection attempted runtime dispatch or readiness contact")


@pytest.mark.parametrize("representation", ["original", "comments-crlf", "json-reordered"])
def test_actual_autoverse_cli_and_http_emit_the_same_full_authoritative_plan(
    target, tmp_path, monkeypatch, representation
):
    provider, blueprint = target
    app = application(tmp_path / "Autoverse CLI equivalence Ω", provider)
    monkeypatch.setattr(app.state.studio.runs, "_dispatch", forbidden)
    monkeypatch.setattr(provider, "readiness", forbidden)
    with authenticated(app) as api:
        p = project(api, blueprint)
        original = compile_project(api, p, provider.descriptor()["providerId"])
        sources = {d["path"]: d["content"] for d in p["documents"].values()}
        if representation != "original":
            yaml = YAML(typ="safe")
            for doc_id, document in list(p["documents"].items()):
                source = document["content"]
                changed = ("# Inert presentation comment Ω\r\n" + source.replace("\n", "\r\n")
                           if representation == "comments-crlf" else json.dumps(yaml.load(source), indent=3))
                p = checked(api.put(
                    f"/api/v1/projects/{p['projectId']}/documents/{doc_id}",
                    headers={"If-Match": str(p["revision"])},
                    json={"content": changed, "format": "json" if representation == "json-reordered" else "yaml"},
                ))
                assert p["documents"][doc_id]["content"] == changed
            sources = {d["path"]: d["content"] for d in p["documents"].values()}
        if representation == "json-reordered":
            sources = {str(Path(name).with_suffix(".json")): source for name, source in reversed(list(sources.items()))}
        inputs = []
        cli_root = tmp_path / "Explicit CLI inputs Ω"
        cli_root.mkdir()
        for name, source in sources.items():
            path = cli_root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(source.encode("utf-8"))
            inputs.append(str(path))
        schemas = [part for schema in app.state.studio.adapter.profile_schema_paths for part in ("--profile-schema", schema)]
        argv = [sys.executable, "-I", "-m", "xverse_xdl", "experiment", "compile", "--format", "json", *schemas, *inputs]
        result = subprocess.run(argv, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stderr
        cli = json.loads(result.stdout)
        library = app.state.studio.adapter.compile(sources)
        http = compile_project(api, p, provider.descriptor()["providerId"])
        assert cli["plan"] == library["plan"] == http["plan"] == original["plan"]
        assert library["planDigest"] == http["planDigest"] == original["planDigest"]
        assert library["semanticDigest"] == http["semanticDigest"] == original["semanticDigest"]
        assert cli["plan"]["digest"]["value"] == http["planDigest"].removeprefix("sha256:")
        assert app.state.studio.store.all("run") == []
        assert app.state.studio.store.all("snapshot") == []
        (tmp_path / "cli-plan-observation.json").write_text(json.dumps({
            "target": blueprint, "representation": representation,
            "scope": "actual public compiler declared intent; no runtime readiness",
            "compiler": library["compiler"], "planDigest": http["planDigest"],
            "semanticDigest": http["semanticDigest"], "fullPlanEqual": True,
            "sourceBytesDigest": digest(sources), "cliReturnCode": result.returncode,
        }, indent=2) + "\n")


def test_actual_autoverse_native_reopen_preserves_source_and_separate_layout(
    target, tmp_path, monkeypatch
):
    provider, blueprint = target
    data = tmp_path / "Native persisted Autoverse Ω"
    data.mkdir(mode=0o700)
    with own_root(data):
        app = application(data, provider)
        monkeypatch.setattr(app.state.studio.runs, "_dispatch", forbidden)
        with authenticated(app) as api:
            p = project(api, blueprint)
            initial = compile_project(api, p, provider.descriptor()["providerId"])
            doc_id, document = next(iter(p["documents"].items()))
            changed = document["content"] + "\n# Persisted inert comment Ω\n"
            p = checked(api.put(
                f"/api/v1/projects/{p['projectId']}/documents/{doc_id}",
                headers={"If-Match": str(p["revision"])},
                json={"content": changed, "format": document["format"]},
            ))
            source_revision = p["revision"]
            exact_documents = p["documents"]
            expected_layout = {"positions": {"persisted-element": {"x": 31.5, "y": -12.0}}, "viewport": {"x": 3.0, "y": 4.0, "zoom": 1.5}}
            p = checked(api.put(
                f"/api/v1/projects/{p['projectId']}/layout",
                headers={"If-Match": str(p["presentationRevision"])}, json=expected_layout,
            ))
            assert p["revision"] == source_revision and p["documents"] == exact_documents
            after = compile_project(api, p, provider.descriptor()["providerId"])
            assert initial["plan"] == after["plan"]
            assert initial["semanticDigest"] == after["semanticDigest"]
            with pytest.raises(RootOwnedError):
                with own_root(data):
                    raise AssertionError("Second owner acquired the current native workspace")
    with own_root(data):
        reopened = application(data, provider)
        monkeypatch.setattr(reopened.state.studio.runs, "_dispatch", forbidden)
        with authenticated(reopened) as api:
            current = checked(api.get(f"/api/v1/projects/{p['projectId']}"))
            assert current == p and current["sourceIntegrity"] == "intact"
            assert current["layout"] == expected_layout
            assert current["documents"][doc_id]["content"] == changed
            assert compile_project(api, current, provider.descriptor()["providerId"])["plan"] == initial["plan"]
            assert reopened.state.studio.store.all("run") == []
            assert reopened.state.studio.store.all("snapshot") == []


def test_unavailable_lite_cannot_adopt_actual_autoverse_project_or_dispatch_fallback(
    target, tmp_path, monkeypatch
):
    provider, blueprint = target
    app = application(tmp_path / "Autoverse explicit Lite refusal Ω", provider)
    with authenticated(app) as api:
        p = project(api, blueprint)
        monkeypatch.setattr(subprocess, "Popen", forbidden)
        monkeypatch.setattr(app.state.studio.runs, "_dispatch", forbidden)
        monkeypatch.setattr(provider, "readiness", forbidden)
        lite = next(d for d in checked(api.get("/api/v1/providers"))["items"] if d["providerId"] == "xverse.lite")
        assert lite["available"] is False and lite["operations"] == []
        assert lite["blockedReasons"][0]["code"] == "DEP-RUN-CONFIG"
        assert compile_project(api, p, provider.descriptor()["providerId"])["valid"]
        pf = checked(api.post(
            f"/api/v1/projects/{p['projectId']}/preflights",
            json={"revision": p["revision"], "providerId": "xverse.lite"},
        ))
        assert pf["status"] == "blocked" and pf["providerId"] == "xverse.lite"
        start = api.post(
            "/api/v1/runs", headers={"Idempotency-Key": "lite-must-remain-unavailable"},
            json={k: pf[k] for k in ("snapshotId", "preflightId")},
        )
        assert start.status_code == 422 and start.json()["code"] == "ADMISSION_REJECTED"
        assert app.state.studio.store.all("run") == []
        assert app.state.studio.store.all("operation") == []
        assert checked(api.get(f"/api/v1/projects/{p['projectId']}")) == p

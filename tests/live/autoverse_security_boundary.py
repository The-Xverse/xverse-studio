"""Actual enrolled Autoverse targets for session and portable-content boundaries.

Synthetic markers are never production credentials. No readiness, process start,
device contact or compiler substitution establishes a passing refusal here.
"""

import base64
from contextlib import contextmanager
import hashlib
import io
import json
import time
import zipfile

from fastapi.testclient import TestClient
import pytest

import autoverse_provider_admission as enrollment
from autoverse_provider_admission import application, project

target = enrollment.target
MARKER = "owned-synthetic-private-marker"
BOOTSTRAP = "owned-autoverse-contract-check"
PAYLOADS = [
    "password: " + MARKER,
    "bootstrapToken: " + MARKER,
    '"csrfToken": "' + MARKER + '"',
    "session_token=" + MARKER,
    "studio_session=" + MARKER,
    "refreshToken: " + MARKER,
    "idToken: " + MARKER,
    "Authorization: Bearer " + MARKER,
    '"Authorization": "Basic b3duZWQtc3ludGhldGljLW1hcmtlcg=="',
    '"bootstrap\\u0054oken": "' + MARKER + '"',
    '"endpoint": "https://user:' + MARKER + '\\u0040example.invalid"',
]


@contextmanager
def signed_in(app):
    with TestClient(app, raise_server_exceptions=False) as api:
        api.headers["Origin"] = "http://testserver"
        response = api.post("/api/v1/session", json={"bootstrapToken": BOOTSTRAP})
        assert response.status_code == 200
        api.headers["X-CSRF-Token"] = response.json()["csrfToken"]
        yield api


@pytest.mark.parametrize("kind", ["bad-utf8", "wrong", "query-only", "expired"])
def test_autoverse_bootstrap_refusal_never_consumes_or_echoes_credentials(
    target, tmp_path, monkeypatch, kind
):
    provider, blueprint = target
    app = application(tmp_path / "Autoverse authentication Ω", provider)
    with TestClient(app, raise_server_exceptions=False) as api:
        api.headers["Origin"] = "http://testserver"
        if kind == "bad-utf8":
            response = api.post(
                "/api/v1/session",
                content=b'{"bootstrapToken":"\\ud800"}',
                headers={"Content-Type": "application/json"},
            )
            expected = 422
        elif kind == "query-only":
            response = api.post("/api/v1/session?bootstrapToken=" + BOOTSTRAP)
            expected = 422
        elif kind == "expired":
            original = time.time
            with monkeypatch.context() as patch:
                patch.setattr(time, "time", lambda: original() + 301)
                response = api.post(
                    "/api/v1/session", json={"bootstrapToken": BOOTSTRAP}
                )
            expected = 401
        else:
            response = api.post("/api/v1/session", json={"bootstrapToken": MARKER})
            expected = 401
        assert response.status_code == expected
        assert BOOTSTRAP not in response.text and MARKER not in response.text
        assert app.state.studio.store.all("session") == []
        assert app.state.studio.store.all("project") == []
        # The clock-negative does not alter the real clock or bootstrap bytes.
        valid = api.post("/api/v1/session", json={"bootstrapToken": BOOTSTRAP})
        assert valid.status_code == 200
        assert not (app.state.studio.store.root / "bootstrap.json").exists()
        cookie = valid.headers["set-cookie"].lower()
        assert (
            "httponly" in cookie and "samesite=strict" in cookie and "path=/" in cookie
        )
        assert (
            api.post("/api/v1/session", json={"bootstrapToken": BOOTSTRAP}).status_code
            == 401
        )
        api.headers["X-CSRF-Token"] = valid.json()["csrfToken"]
        p = project(api, blueprint)
        assert p["revision"] == 1 and app.state.studio.store.all("run") == []


@pytest.mark.parametrize(
    "kind",
    [
        "nonascii-csrf",
        "wrong-csrf",
        "missing-csrf",
        "missing-origin",
        "wrong-origin",
        "null-origin",
        "wrong-host",
        "scheme-mismatch",
        "missing-cookie",
        "forged-cookie",
        "expired-session",
        "contract-version",
    ],
)
def test_autoverse_authentication_refuses_before_authoring_or_dispatch(
    target, tmp_path, kind
):
    provider, blueprint = target
    app = application(tmp_path / "Autoverse access refusal Ω", provider)
    with signed_in(app) as api:
        headers = {}
        status = 403
        if kind == "nonascii-csrf":
            headers = [(b"X-CSRF-Token", b"\xff")]
        elif kind == "wrong-csrf":
            headers["X-CSRF-Token"] = MARKER
        elif kind == "missing-csrf":
            api.headers.pop("X-CSRF-Token")
        elif kind == "missing-origin":
            api.headers.pop("Origin")
        elif kind in {"wrong-origin", "null-origin", "scheme-mismatch"}:
            headers["Origin"] = {
                "wrong-origin": "http://foreign.invalid",
                "null-origin": "null",
                "scheme-mismatch": "https://testserver",
            }[kind]
        elif kind == "wrong-host":
            headers["Host"] = "foreign.invalid"
        elif kind in {"missing-cookie", "forged-cookie"}:
            headers["Cookie"] = (
                "" if kind == "missing-cookie" else "studio_session=" + MARKER
            )
            status = 401
        elif kind == "expired-session":
            store = app.state.studio.store
            key = hashlib.sha256(api.cookies.get("studio_session").encode()).hexdigest()
            value = store.get("session", key)
            value["expiresAt"] = time.time() - 1
            store.put("session", key, value)
            status = 401
        else:
            headers["X-Studio-Contract-Version"] = "unsupported"
            status = 426
        response = api.post(
            "/api/v1/projects",
            headers=headers,
            json={"name": "Blocked Autoverse request", "blueprintRef": blueprint},
        )
        assert response.status_code == status
        assert MARKER not in response.text
        assert response.headers.get("cache-control") == "no-store"
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-request-id") == response.json()["requestId"]
        assert app.state.studio.store.all("project") == []
        assert app.state.studio.store.all("run") == []
        assert not (app.state.studio.store.root / "projects").exists()


@pytest.mark.parametrize(
    "key", ["bootstrapToken=" + MARKER, "/home/" + MARKER + "/project", "x" * 2048]
)
def test_autoverse_schema_diagnostics_bound_and_redact_sensitive_locations(
    target, tmp_path, key
):
    provider, blueprint = target
    app = application(tmp_path / "Autoverse safe diagnostics Ω", provider)
    with signed_in(app) as api:
        response = api.post(
            "/api/v1/projects",
            json={"name": "Autoverse", "blueprintRef": blueprint, key: MARKER},
        )
        assert response.status_code == 422
        assert key not in response.text and MARKER not in response.text
        assert len(response.content) < 4096
        assert response.json()["diagnostics"][0]["location"]["redacted"] is True
        assert app.state.studio.store.all("project") == []


@pytest.mark.parametrize("payload", PAYLOADS)
@pytest.mark.parametrize("surface", ["source", "import", "legacy-export", "name"])
def test_autoverse_inline_authentication_material_is_never_published_or_exported(
    target, tmp_path, payload, surface
):
    provider, blueprint = target
    app = application(tmp_path / "Autoverse credential exclusion Ω", provider)
    with signed_in(app) as api:
        store = app.state.studio.store
        if surface == "name":
            response = api.post(
                "/api/v1/projects", json={"name": payload, "blueprintRef": blueprint}
            )
            p = None
        else:
            p = project(api, blueprint)
            if surface == "source":
                docid, document = next(iter(p["documents"].items()))
                response = api.put(
                    f"/api/v1/projects/{p['projectId']}/documents/{docid}",
                    headers={"If-Match": str(p["revision"])},
                    json={
                        "content": document["content"] + "\n# " + payload + "\n",
                        "format": document["format"],
                    },
                )
            elif surface == "import":
                data = io.BytesIO()
                with zipfile.ZipFile(data, "w", compression=zipfile.ZIP_DEFLATED) as z:
                    z.writestr("project.studio.json", json.dumps(p["manifest"]))
                    for document in p["documents"].values():
                        z.writestr(document["path"], document["content"])
                    z.writestr("README.md", payload)
                response = api.post(
                    "/api/v1/projects/imports",
                    json={"archiveBase64": base64.b64encode(data.getvalue()).decode()},
                )
            else:
                record = store.get("project", p["projectId"])
                record["supportingFiles"]["README.md"] = payload
                store.put("project", p["projectId"], record)
                response = api.post(
                    f"/api/v1/projects/{p['projectId']}/exports",
                    headers={"Idempotency-Key": "credential-exclusion"},
                    json={"revision": p["revision"]},
                )
        assert response.status_code == 422
        assert response.json()["code"] == "CREDENTIAL_REJECTED"
        assert MARKER not in response.text
        assert len(store.all("project")) == (1 if p else 0)
        assert store.all("run") == [] and store.all("operation") == []
        if p and surface in {"source", "import"}:
            assert api.get(f"/api/v1/projects/{p['projectId']}").json() == p
        if surface == "legacy-export":
            assert (
                store.get("project", p["projectId"])["supportingFiles"]["README.md"]
                == payload
            )
            assert not (store.root / "exports").exists()


def test_autoverse_layout_cannot_hide_credentials_in_opaque_element_keys(
    target, tmp_path
):
    provider, blueprint = target
    app = application(tmp_path / "Autoverse layout exclusion Ω", provider)
    with signed_in(app) as api:
        p = project(api, blueprint)
        response = api.put(
            f"/api/v1/projects/{p['projectId']}/layout",
            headers={"If-Match": str(p["presentationRevision"])},
            json={"positions": {"sessionToken=" + MARKER: {"x": 0, "y": 0}}},
        )
        assert (
            response.status_code == 422
            and response.json()["code"] == "CREDENTIAL_REJECTED"
        )
        assert api.get(f"/api/v1/projects/{p['projectId']}").json() == p


def test_autoverse_external_handles_and_unicode_round_trip_without_secret_rewriting(
    target, tmp_path
):
    provider, blueprint = target
    app = application(tmp_path / "Autoverse permitted references Ω", provider)
    with signed_in(app) as api:
        p = project(api, blueprint)
        before = api.post(
            f"/api/v1/projects/{p['projectId']}/compilations",
            json={"revision": p["revision"]},
        )
        assert before.status_code == 200 and before.json()["valid"]
        docid, document = next(iter(p["documents"].items()))
        comment = '\n# Ω credentialRef: secret://autoverse-demo/session\n# sessionTokenRef: urn:autoverse:credential\n# gridToken: ordinary-value\n# "grid\\u0054oken": "ordinary"\n'
        content = document["content"] + comment
        response = api.put(
            f"/api/v1/projects/{p['projectId']}/documents/{docid}",
            headers={"If-Match": str(p["revision"])},
            json={"content": content, "format": document["format"]},
        )
        assert response.status_code == 200
        saved = response.json()
        after = api.post(
            f"/api/v1/projects/{p['projectId']}/compilations",
            json={"revision": saved["revision"]},
        )
        assert (
            after.status_code == 200
            and after.json()["planDigest"] == before.json()["planDigest"]
        )
        exported = api.post(
            f"/api/v1/projects/{p['projectId']}/exports",
            headers={"Idempotency-Key": "permitted-handles"},
            json={"revision": saved["revision"]},
        )
        assert exported.status_code == 202
        raw = api.get(exported.json()["result"]["downloadUrl"])
        assert raw.status_code == 200
        with zipfile.ZipFile(io.BytesIO(raw.content)) as z:
            assert z.read(document["path"]).decode() == content
        inspection = api.post(
            "/api/v1/projects/imports",
            json={"archiveBase64": base64.b64encode(raw.content).decode()},
        )
        assert inspection.status_code == 201
        assert any(
            d["content"] == content for d in inspection.json()["documents"].values()
        )
        assert api.get(f"/api/v1/projects/{p['projectId']}").json() == saved
        ordinary = api.post(
            "/api/v1/projects",
            json={
                "name": "Autoverse",
                "blueprintRef": blueprint,
                "unsupportedField": 1,
            },
        )
        assert ordinary.status_code == 422
        assert (
            ordinary.json()["diagnostics"][0]["location"]["pointer"]
            == "body/unsupportedField"
        )
        assert app.state.studio.store.all("run") == []


@pytest.mark.parametrize(
    "kind",
    [
        "nan-expiry",
        "infinite-expiry",
        "text-expiry",
        "missing-expiry",
        "missing-csrf",
        "unencodable-csrf",
    ],
)
def test_autoverse_corrupt_native_session_is_never_authority(target, tmp_path, kind):
    provider, blueprint = target
    app = application(tmp_path / "Autoverse corrupt local session Ω", provider)
    with signed_in(app) as api:
        store = app.state.studio.store
        key = hashlib.sha256(api.cookies.get("studio_session").encode()).hexdigest()
        value = store.get("session", key)
        if kind == "nan-expiry":
            value["expiresAt"] = float("nan")
        elif kind == "infinite-expiry":
            value["expiresAt"] = float("inf")
        elif kind == "text-expiry":
            value["expiresAt"] = MARKER
        elif kind == "missing-expiry":
            value.pop("expiresAt")
        elif kind == "missing-csrf":
            value.pop("csrfToken")
        else:
            value["csrfToken"] = "\ud800"
        # A controlled native persisted-state fault, never an API granting a
        # credential. Preserve malformed bytes; do not fabricate a valid receipt.
        raw = json.dumps(value)
        with store.tx() as db:
            db.execute(
                "UPDATE records SET body=? WHERE kind='session' AND id=?",
                (raw, key),
            )
        response = api.post(
            "/api/v1/projects", json={"name": "Autoverse", "blueprintRef": blueprint}
        )
        assert response.status_code == 401
        assert MARKER not in response.text
        assert store.all("project") == [] and store.all("run") == []
        with store.tx() as db:
            assert (
                db.execute(
                    "SELECT body FROM records WHERE kind='session' AND id=?", (key,)
                ).fetchone()[0]
                == raw
            )


@pytest.mark.parametrize("kind", ["name", "source", "layout", "campaign", "edits"])
def test_autoverse_nonfinite_or_unencodable_body_refuses_before_effects(
    target, tmp_path, kind
):
    provider, blueprint = target
    app = application(tmp_path / "Autoverse invalid request text Ω", provider)
    with signed_in(app) as api:
        if kind == "name":
            route, body = (
                "/api/v1/projects",
                {"name": "\ud800", "blueprintRef": blueprint},
            )
        elif kind == "campaign":
            route, body = (
                "/api/v1/campaigns",
                {
                    "snapshotId": "not-a-snapshot",
                    "matrix": {},
                    "budget": {"unexpected": float("inf")},
                },
            )
        elif kind == "edits":
            route, body = (
                "/api/v1/projects/not-a-project/edits",
                {
                    "baseRevision": 1,
                    "edits": [{"kind": "unknown", "value": float("nan")}],
                },
            )
        elif kind == "source":
            route, body = (
                "/api/v1/projects/not-a-project/documents/not-a-document",
                {"content": "\ud800", "format": "yaml"},
            )
        else:
            route, body = (
                "/api/v1/projects/not-a-project/layout",
                {"positions": {"\ud800": {"x": 0}}},
            )
        method = "PUT" if kind in {"source", "layout"} else "POST"
        response = api.request(
            method,
            route,
            headers={"Content-Type": "application/json", "If-Match": "1"},
            content=json.dumps(body).encode(),
        )
        assert (
            response.status_code == 422 and response.json()["code"] == "REQUEST_INVALID"
        )
        assert app.state.studio.store.all("project") == []
        assert app.state.studio.store.all("operation") == []
        assert app.state.studio.store.all("run") == []

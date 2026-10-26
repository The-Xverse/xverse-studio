"""Studio library adapter versus the pinned `xdl` CLI over the round-trip corpus, plus HTTP layout,
edit, conflict and failed-edit recovery scenarios (T041 corpus; T048 Linux execution)."""
import base64
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import pytest

from xverse_studio.xdl import XDLAdapter
from xverse_studio.xdl.examples import examples

# Loaded under a unique module name so no other `cases` module can shadow or be shadowed by it.
_spec = importlib.util.spec_from_file_location(
    "xdl_roundtrip_cases", Path(__file__).resolve().parents[1] / "fixtures" / "xdl" / "roundtrip" / "cases.py")
_cases = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cases)
CASES, baseline = _cases.CASES, _cases.baseline

# Exactly the explicit profile schemas Studio's adapter passes to the platform.
PROFILE_SCHEMAS = list(XDLAdapter().profile_schema_paths)


def cli(documents, tmp_path, command):
    """Write the exact bytes and run the pinned CLI on them in an isolated interpreter."""
    root = Path(tempfile.mkdtemp(prefix="cli-", dir=tmp_path))
    paths = []
    for name, content in documents.items():
        target = root / name  # the same relative document paths Studio holds
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content.encode())
        paths.append(str(target))
    schemas = [arg for schema in PROFILE_SCHEMAS for arg in ("--profile-schema", schema)]
    result = subprocess.run([sys.executable, "-I", "-m", "xverse_xdl", *command, "--format", "json", *schemas, *paths],
                            capture_output=True, text=True, timeout=120)
    assert "Traceback" not in result.stderr, result.stderr
    report = json.loads(result.stdout)
    assert (result.returncode == 0) == report["valid"], (result.returncode, result.stderr)
    return report


def identities(documents, tmp_path):
    studio = XDLAdapter().compile(documents)
    compiled = cli(documents, tmp_path, ["experiment", "compile"])
    plan = compiled.get("plan") or {}
    tool = {"valid": compiled["valid"],
            "semanticDigest": "sha256:" + plan["provenance"]["inputSemanticDigest"]["value"] if plan else None,
            "planDigest": "sha256:" + plan["digest"]["value"] if plan else None,
            "codes": sorted({d["code"] for d in compiled["diagnostics"]})}
    mine = {"valid": studio["valid"], "semanticDigest": studio["semanticDigest"], "planDigest": studio["planDigest"],
            "codes": sorted({d["code"] for d in studio["diagnostics"]})}
    return mine, tool


@pytest.mark.parametrize("example", range(len(examples())))
def test_studio_and_pinned_cli_agree_on_admitted_examples(example, tmp_path):
    mine, tool = identities(baseline(example), tmp_path)
    assert mine == tool and mine["valid"]


@pytest.mark.parametrize("name,derive,expectation,code", CASES, ids=[case[0] for case in CASES])
def test_roundtrip_corpus_has_equal_identities_in_studio_and_cli(name, derive, expectation, code, tmp_path):
    base, _ = identities(baseline(), tmp_path)
    assert base["valid"] and base["semanticDigest"] and base["planDigest"]
    derived = derive(baseline())
    assert derived != baseline()  # every case really changes the authored bytes
    mine, tool = identities(derived, tmp_path)
    assert mine == tool  # equivalent supported inputs yield equal identities in both tools
    if expectation == "equal":
        assert mine["valid"] and (mine["semanticDigest"], mine["planDigest"]) == (base["semanticDigest"], base["planDigest"])
    elif expectation == "changed":
        assert mine["valid"] and mine["semanticDigest"] != base["semanticDigest"] and mine["planDigest"] != base["planDigest"]
    else:
        assert not mine["valid"] and code in mine["codes"]


def _sources(project):
    return {d["path"]: d["content"] for d in project["documents"].values()}


def test_http_layout_edit_conflict_and_failed_edit_recovery_keep_cli_identity(client, tmp_path):
    project = client.post("/api/v1/projects", json={"name": "Round trip Ω"}).json()
    pid = project["projectId"]
    original = _sources(project)
    base, tool = identities(original, tmp_path)
    assert base == tool and base["valid"]
    # Layout-only change: no source byte and no identity changes.
    layout = client.put(f"/api/v1/projects/{pid}/layout", headers={"If-Match": str(project["presentationRevision"])},
                        json={"positions": {"plant": {"x": 10.0, "y": 20.0}}})
    assert layout.status_code == 200 and _sources(layout.json()) == original
    assert layout.json()["revision"] == project["revision"]
    # A semantic edit changes identity identically in both tools.
    edited = client.post(f"/api/v1/projects/{pid}/edits", headers={"If-Match": str(project["revision"])},
                         json={"baseRevision": project["revision"], "edits": [{"kind": "set_parameter", "parameterId": "duration", "value": 7}]})
    assert edited.status_code == 200, edited.text
    after = _sources(edited.json())
    mine, tool = identities(after, tmp_path)
    assert mine == tool and mine["semanticDigest"] != base["semanticDigest"]
    compiled = client.post(f"/api/v1/projects/{pid}/compilations", json={"revision": edited.json()["revision"]}).json()
    assert (compiled["semanticDigest"], compiled["planDigest"]) == (mine["semanticDigest"], mine["planDigest"])
    # A stale writer conflicts without changing bytes.
    stale = client.post(f"/api/v1/projects/{pid}/edits", headers={"If-Match": str(project["revision"])},
                        json={"baseRevision": project["revision"], "edits": [{"kind": "set_parameter", "parameterId": "duration", "value": 9}]})
    assert stale.status_code == 412 and _sources(client.get(f"/api/v1/projects/{pid}").json()) == after
    # The conflicting write left no trace: the stored bytes still have the pre-conflict identity in both tools.
    kept, kept_tool = identities(_sources(client.get(f"/api/v1/projects/{pid}").json()), tmp_path)
    assert kept == kept_tool == mine
    # A failed edit leaves the revision and bytes intact; an invalid draft is diagnosed alike by both tools.
    refused = client.post(f"/api/v1/projects/{pid}/edits", headers={"If-Match": str(edited.json()["revision"])},
                          json={"baseRevision": edited.json()["revision"], "edits": [{"kind": "set_parameter", "parameterId": "duration", "value": "x"}]})
    assert refused.status_code == 422 and client.get(f"/api/v1/projects/{pid}").json()["revision"] == edited.json()["revision"]
    system_id = next(i for i, d in project["documents"].items() if d["path"].endswith("/system.xdl.yaml"))
    broken = client.put(f"/api/v1/projects/{pid}/documents/{system_id}", headers={"If-Match": str(edited.json()["revision"])},
                        json={"content": after["xdl/system.xdl.yaml"].replace("kind: System", "kind: Systems", 1)})
    assert broken.status_code == 200, broken.text
    mine, tool = identities(_sources(broken.json()), tmp_path)
    assert not mine["valid"] and mine == tool and mine["codes"]
    # Recovery restores the exact earlier bytes and identity as a new forward revision.
    restored = client.post(f"/api/v1/projects/{pid}/revisions/{edited.json()['revision']}/restore",
                           headers={"If-Match": str(broken.json()["revision"])})
    assert restored.status_code == 200, restored.text
    assert restored.json()["revision"] > broken.json()["revision"] and _sources(restored.json()) == after
    # Export/import keeps the exact bytes, so identity survives exchange.
    op = client.post(f"/api/v1/projects/{pid}/exports", headers={"Idempotency-Key": "roundtrip-" + pid},
                     json={"revision": restored.json()["revision"]})
    archive = client.get(op.json()["result"]["downloadUrl"]).content
    imported = client.post("/api/v1/projects/imports", json={"archiveBase64": base64.b64encode(archive).decode()}).json()
    assert _sources(imported) == after
    exported = zipfile.ZipFile(io.BytesIO(archive))
    assert {name: exported.read(name).decode() for name in after} == after

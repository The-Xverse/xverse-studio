"""Actual retained Stop receipt and controlled mutations of new local copies.

The original failed whole verifier remains failed. These checks establish only
the existing durable request/mailbox/producer binding, with no runtime dispatch.
"""

from contextlib import closing
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess

import pytest


@pytest.fixture
def receipt(tmp_path, monkeypatch):
    saved = Path(os.environ["STUDIO_AUTOVERSE_CONTROL_RECORDING"])
    result = json.loads((saved / "native-result.json").read_bytes())
    original = Path(json.loads((saved / "data-root.private.json").read_bytes())["dataRoot"])
    run_id, operation_id = result["runId"], result["controlResult"]["operationId"]
    source_root = original / "runs" / run_id
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in [original / "studio.sqlite", *[source_root / n for n in ["command.json", "owner.key", "state.json", "evidence.jsonl"]]]}
    data = tmp_path / "inert-control-copy"
    root = data / "runs" / run_id
    root.mkdir(parents=True)
    for name in ["command.json", "owner.key", "state.json"]:
        shutil.copyfile(source_root / name, root / name)
    with closing(sqlite3.connect((original / "studio.sqlite").as_uri() + "?mode=ro", uri=True)) as source, closing(sqlite3.connect(data / "studio.sqlite")) as db:
        source.backup(db)
        settled = json.loads(db.execute("SELECT body FROM records WHERE kind='operation' AND id=?", (operation_id,)).fetchone()[0])
        command = json.loads(db.execute("SELECT result FROM idempotency WHERE key=?", ("pressure-owned-stop",)).fetchone()[0])
    rows = [json.loads(line) for line in (source_root / "evidence.jsonl").read_bytes().splitlines()]
    running = next(row for row in reversed(rows) if row["type"] == "run.state_changed" and row["payload"].get("state") == "running")
    request = {"kind": "stop", "expectedStateVersion": running["payload"]["stateVersion"], "parameters": {}}
    spec = importlib.util.spec_from_file_location("actual_pressure_receipt", Path(__file__).with_name("autoverse_control_pressure_native.py"))
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)

    def forbidden(*args, **kwargs):
        pytest.fail("Receipt verification attempted native contact")

    for name in ["Popen", "run", "check_output"]:
        monkeypatch.setattr(subprocess, name, forbidden)
    yield helper, data, run_id, request, command, settled
    assert {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in before} == before


def test_actual_stop_request_and_receipt_bind_without_an_invented_operation_field(receipt):
    helper, data, run_id, request, command, settled = receipt
    assert "expectedStateVersion" not in settled
    facts = helper.verify_control_receipt(data, run_id, request, "pressure-owned-stop", command, settled)
    assert all(value is True for key, value in facts.items() if key != "expectedStateVersion")
    assert facts["expectedStateVersion"] == request["expectedStateVersion"]


@pytest.mark.parametrize("fault", ["request-version", "request-kind", "operation-kind", "operation-run", "operation-id", "operation-status", "fingerprint", "mailbox-kind", "mailbox-signature", "owner-key", "producer-receipt"])
def test_control_binding_rejects_changed_request_or_receipt(receipt, fault):
    helper, data, run_id, request, command, settled = receipt
    request, settled = deepcopy(request), deepcopy(settled)
    root = data / "runs" / run_id
    if fault == "request-version":
        request["expectedStateVersion"] += 1
    elif fault == "request-kind":
        request["kind"] = "cancel"
    elif fault.startswith("operation-"):
        key = {"operation-kind": "kind", "operation-run": "runId", "operation-id": "operationId", "operation-status": "status"}[fault]
        settled[key] = "unrelated-inert-value"
    elif fault == "fingerprint":
        with sqlite3.connect(data / "studio.sqlite") as db:
            db.execute("UPDATE idempotency SET fingerprint=? WHERE key=?", ("sha256:" + "0" * 64, "pressure-owned-stop"))
    elif fault.startswith("mailbox-"):
        path = root / "command.json"
        mailbox = json.loads(path.read_bytes())
        mailbox["kind" if fault == "mailbox-kind" else "signature"] = "unrelated-inert-value"
        path.write_text(json.dumps(mailbox))
    elif fault == "owner-key":
        (root / "owner.key").write_bytes(b"different-inert-key")
    else:
        path = root / "state.json"
        producer = json.loads(path.read_bytes())
        producer["commandResults"] = {}
        path.write_text(json.dumps(producer))
    with pytest.raises((AssertionError, KeyError, StopIteration)):
        helper.verify_control_receipt(data, run_id, request, "pressure-owned-stop", command, settled)

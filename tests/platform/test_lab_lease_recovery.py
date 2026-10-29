"""Actual stopped-root backup/restore against owned SQLite lease snapshots."""

from copy import deepcopy
import hashlib
import json
import sqlite3

import pytest
from xverse_studio.host.recovery import (
    backup_full,
    restore_full,
    verify_backup,
    RecoveryError,
)
from xverse_studio.storage.core import Store, canonical, digest


def ledger(status):
    return {
        "contractVersion": "1.0",
        "revision": 1,
        "records": [
            {
                "reservationId": "fixture-reservation",
                "assetId": "fixture:asset",
                "providerId": "fixture",
                "owner": "fixture-owner",
                "scope": "observe",
                "expiry": 0,
                "status": status,
                "fencingIdentity": None if status == "unknown" else "fixture-fence",
                "lastRenewal": None,
                "evidenceScope": "fixture",
            }
        ],
    }


@pytest.mark.parametrize("status", ["owned", "unknown"])
def test_backup_refuses_unsettled_leases_even_when_deadline_is_past(tmp_path, status):
    root, saved = tmp_path / "owned lease data Ω", tmp_path / "private backup Ω"
    store = Store(root)
    value = ledger(status)
    store.put("lab_registry", "leases", value)
    with pytest.raises(RecoveryError, match="^RECOVERY_EXECUTION_UNSETTLED$"):
        backup_full(root, saved)
    assert store.get("lab_registry", "leases") == value and not saved.exists()


@pytest.mark.parametrize("status", ["released", "expired"])
def test_confirmed_terminal_lease_history_roundtrips_without_new_authority(
    tmp_path, status
):
    root, saved, target = (
        tmp_path / name for name in ["owned Ω", "backup Ω", "restore Ω"]
    )
    store = Store(root)
    value = ledger(status)
    value["records"][0]["opaqueHistory"] = {"preserve": "private uninterpreted history"}
    store.put("lab_registry", "leases", value)
    assert backup_full(root, saved)["integrity"] == "valid"
    assert verify_backup(saved)["integrity"] == "valid"
    assert restore_full(saved, target)["status"] == "restored"
    assert Store(target).get("lab_registry", "leases") == value


@pytest.mark.parametrize(
    "mutation",
    ["version", "shape", "revision", "duplicate", "oversized", "extra-ledger"],
)
def test_corrupt_or_unbounded_lease_snapshots_refuse_copy_without_rewrite(
    tmp_path, mutation
):
    root, saved = tmp_path / "owned data", tmp_path / "backup"
    store = Store(root)
    value = ledger("released")
    if mutation == "version":
        value["contractVersion"] = "2.0"
    elif mutation == "shape":
        value["records"] = {}
    elif mutation == "revision":
        value["revision"] = True
    elif mutation == "duplicate":
        value["records"].append(deepcopy(value["records"][0]))
    elif mutation == "oversized":
        value["opaqueHistory"] = "x" * (2 * 1024 * 1024)
    store.put("lab_registry", "leases", value)
    if mutation == "extra-ledger":
        store.put("lab_registry", "unexpected-ledger", value)
    with pytest.raises(RecoveryError, match="^RECOVERY_DATABASE_INVALID$"):
        backup_full(root, saved)
    assert store.get("lab_registry", "leases") == value and not saved.exists()


def test_hash_valid_foreign_backup_cannot_restore_unsettled_lease_authority(tmp_path):
    root, saved, target = (
        tmp_path / name for name in ["owned Ω", "backup Ω", "restore Ω"]
    )
    store = Store(root)
    store.put("lab_registry", "leases", ledger("released"))
    backup_full(root, saved)
    database = saved / "files/studio.sqlite"
    with sqlite3.connect(database) as db:
        db.execute(
            "UPDATE records SET body=? WHERE kind='lab_registry' AND id='leases'",
            (canonical(ledger("owned")),),
        )
    manifest_path = saved / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    raw = database.read_bytes()
    for entry in manifest["files"]:
        if entry["path"] == "studio.sqlite":
            entry.update(
                size=len(raw), digest="sha256:" + hashlib.sha256(raw).hexdigest()
            )
    manifest["filesDigest"] = digest(manifest["files"])
    manifest_path.write_text(canonical(manifest))
    with pytest.raises(RecoveryError, match="^RECOVERY_EXECUTION_UNSETTLED$"):
        restore_full(saved, target)
    assert not target.exists() and database.read_bytes() == raw

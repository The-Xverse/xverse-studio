"""Private backups/migration preserve bytes; movement never validates declarations."""

from contextlib import closing
import sqlite3

import pytest

from test_metadata_migration import inventory
from xverse_studio.host.migration import migrate_full
from xverse_studio.host.recovery import backup_full, restore_full
from xverse_studio.projects.local_bindings import LocalBindings, LocalBindingsUpdate
from xverse_studio.projects.service import Projects
from xverse_studio.storage.core import Store
from xverse_studio.xdl import XDLAdapter


@pytest.mark.parametrize("mode", ["private-restore", "known-schema-copy-migration"])
def test_moved_private_bindings_require_review_without_changing_portable_identity(tmp_path, mode):
    source, backup, target = (tmp_path / name for name in ["original Ω", "private backup Ω", "moved candidate Ω"])
    store = Store(source)
    projects = Projects(store, XDLAdapter())
    project = projects.create("Movement System")
    plan = projects.adapter.compile(projects.sources(project))
    assert plan["valid"], plan
    values = [{"kind": "artifact", "bindingId": "model", "reference": "urn:fixture:model",
               "providerId": "uninstalled.fixture", "path": str(tmp_path / "uncontacted.bin")}]
    declared = LocalBindings(store).save(project["projectId"], 0, LocalBindingsUpdate(bindings=values))
    assert declared["state"] == "declared" and declared["validation"] == "unverified"
    head = store.get("project_local_bindings", project["projectId"])
    original = (source / head["sidecar"]).read_bytes()
    if mode == "known-schema-copy-migration":
        # Construct the exact supported prior metadata shape, not a claim about
        # an unidentified old release or a different project/XDL format.
        with closing(sqlite3.connect(store.dbpath)) as db:
            db.execute("PRAGMA journal_mode=DELETE")
            db.execute("PRAGMA user_version=0")
    before = inventory(source)
    if mode == "private-restore":
        assert backup_full(source, backup)["integrity"] == "valid"
        restore_full(backup, target)
    else:
        assert migrate_full(source, backup, target)["status"] == "migrated"
    assert inventory(source) == before
    assert (backup / "files" / head["sidecar"]).read_bytes() == original
    assert (target / head["sidecar"]).read_bytes() == original
    moved_store = Store(target)
    moved = LocalBindings(moved_store)
    observed = moved.read(project["projectId"])
    assert observed["bindings"] == values and observed["bindingRevision"] == 1
    assert observed["state"] == "needs_review" and observed["environmentChanged"] is True
    assert observed["validation"] == "unverified" and observed["executionAllowed"] is False
    assert moved_store.get("project_local_bindings", project["projectId"]) == head
    replacement = moved.save(project["projectId"], 1, LocalBindingsUpdate(bindings=values))
    assert replacement["bindingRevision"] == 2 and replacement["environmentChanged"] is False
    assert replacement["state"] == "declared" and replacement["executionAllowed"] is False
    assert (target / head["sidecar"]).read_bytes() == original
    moved_projects = Projects(moved_store, XDLAdapter())
    after = moved_projects.read(project["projectId"])
    assert after == project
    assert moved_projects.adapter.compile(moved_projects.sources(after))["planDigest"] == plan["planDigest"]
    assert moved_store.all("run") == [] and moved_store.all("snapshot") == []
    assert not (tmp_path / "uncontacted.bin").exists()

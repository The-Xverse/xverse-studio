"""Readonly startup inspection must observe committed WAL schema, not just DB header."""

from contextlib import closing
import sqlite3

import pytest

from test_metadata_migration import unversioned_root
from xverse_studio.storage.core import Problem, Store


@pytest.mark.parametrize("version", [0, 1])
def test_startup_inspection_honors_committed_wal_without_promoting_unversioned_data(tmp_path, version):
    root = tmp_path / "committed schema Ω"
    unversioned_root(root)
    with closing(sqlite3.connect(root / "studio.sqlite")) as writer:
        writer.execute("PRAGMA journal_mode=WAL")
        with writer:
            writer.execute(f"PRAGMA user_version={version}")
            writer.execute("INSERT INTO records VALUES('opaque','committed',?)", ('{"preserve":"WAL"}',))
        original = {name: (root / name).read_bytes() for name in ["studio.sqlite", "studio.sqlite-wal"]}
        if version == 0:
            with pytest.raises(Problem) as error:
                Store(root)
            assert error.value.code == "MIGRATION_REQUIRED"
            assert {name: (root / name).read_bytes() for name in original} == original
        else:
            assert Store(root).get("opaque", "committed") == {"preserve": "WAL"}

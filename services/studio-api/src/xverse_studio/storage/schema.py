"""The exact unversioned metadata shape previously accepted by Store."""

import re


LEGACY_TABLES = {
    "records": "CREATE TABLE records (kind TEXT NOT NULL, id TEXT NOT NULL, body TEXT NOT NULL, PRIMARY KEY(kind,id))",
    "idempotency": "CREATE TABLE idempotency (scope TEXT NOT NULL, key TEXT NOT NULL, fingerprint TEXT NOT NULL, result TEXT NOT NULL, PRIMARY KEY(scope,key))",
}


def legacy_metadata_shape(db):
    """No added SQL objects/constraints are admitted as an implicit old schema."""
    objects = db.execute("SELECT type,CASE WHEN length(name)<=128 THEN name END,"
                         "CASE WHEN length(sql)<=512 THEN sql END FROM sqlite_schema LIMIT 5").fetchall()
    expected = {(name, re.sub(r"\s+", "", sql).casefold()) for name, sql in LEGACY_TABLES.items()}
    tables = set()
    indices = set()
    for kind, name, sql in objects:
        if kind == "table" and isinstance(sql, str):
            tables.add((name, re.sub(r"\s+", "", sql).casefold()))
        elif kind == "index" and sql is None:
            indices.add(name)
        else:
            return False
    return tables == expected and indices == {"sqlite_autoindex_records_1", "sqlite_autoindex_idempotency_1"}

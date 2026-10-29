"""Disposable admitted-journal fixtures; never execute or open a private stream."""

from __future__ import annotations

import hashlib
from pathlib import Path

from xverse_studio.storage.core import canonical, digest


class AdvancingJournal:
    """A deterministic fixture producer; appends never rewrite previous bytes."""

    def __init__(
        self, root: Path, *, run_id="fixture-stream", snapshot_id="fixture-snapshot"
    ):
        self.root, self.run_id, self.snapshot_id = root, run_id, snapshot_id
        root.mkdir(parents=True, exist_ok=False)
        self.path = root / "evidence.jsonl"
        self.path.touch(exist_ok=False)
        self.records = []
        self.previous = "0" * 64
        self.state = "running"

    def append(
        self, count=1, *, message="Public fixture log; protected fields redacted"
    ):
        prefix = self.path.read_bytes()
        with self.path.open("ab") as output:
            for _ in range(count):
                sequence = str(len(self.records) + 1)
                record = {
                    "schemaVersion": "1.0",
                    "eventId": self.run_id + "-event-" + sequence,
                    "runId": self.run_id,
                    "snapshotId": self.snapshot_id,
                    "sequence": sequence,
                    "recordedAt": "2026-01-01T00:00:00Z",
                    "sourceTime": {"clockDomain": "fixture-clock", "tick": sequence},
                    "source": {
                        "providerId": "owned.public-stream-fixture",
                        "version": "1",
                    },
                    "type": "log.appended",
                    "elementRefs": ["xdl://org.example/system/fixture#controller"],
                    "payload": {"severity": "info", "message": message},
                    "previousDigest": self.previous,
                }
                self.previous = hashlib.sha256(canonical(record).encode()).hexdigest()
                record["digest"] = self.previous
                output.write((canonical(record) + "\n").encode())
                self.records.append(record)
        assert self.path.read_bytes().startswith(prefix)
        return self.records[-count:]

    def read(self, run_id):
        if run_id != self.run_id:
            raise AssertionError("Fixture received another run identity")
        return {
            "runId": self.run_id,
            "snapshotId": self.snapshot_id,
            "state": self.state,
            "evidenceScope": "recorded_fixture",
            "evidence": "partial",
            "capabilities": [],
            **(
                {"journalDigest": digest(self.path.read_bytes())}
                if self.state == "stopped"
                else {}
            ),
        }

    def directory(self, run_id):
        assert run_id == self.run_id
        return self.root


def private_backing_fixture(root: Path):
    """A real protected backing file distinct from the admitted public journal."""
    root.mkdir(parents=True, exist_ok=False)
    private = root / "excluded-provider-private.log"
    secret = "PRIVATE-BACKING-SENTINEL-DO-NOT-EXPOSE-7d8a02"
    private.write_text(secret, encoding="utf-8")
    private.chmod(0o600)
    return private, secret

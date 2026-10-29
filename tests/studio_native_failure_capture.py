"""Bounded diagnostics for explicitly marked Studio-owned native test failures.

Never reconcile, command or signal a run while collecting diagnostics. Raw files
are limited to the original state report and journal. Keys, signed mailboxes,
requests, snapshots, bootstrap/session files and SQLite databases are not copied.
"""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import uuid


RUN_FIELDS = ('runId', 'snapshotId', 'operationId', 'state', 'stateVersion',
              'observationVersion', 'cleanup', 'evidence', 'reason', 'pendingCommandId',
              'journalDigest', 'planDigest', 'semanticDigest', 'effectivePlanDigest',
              'effectiveSemanticDigest', 'ownerDigest', 'pid', 'createTime', 'launchArgvDigest')
OP_FIELDS = ('operationId', 'runId', 'kind', 'status', 'code', 'expectedStateVersion')


class NativeFailureCapture:
    MAX_CASES = 8
    MAX_RUNS = 4
    MAX_OPERATIONS = 8
    MAX_ROW_BYTES = 64 * 1024
    MAX_FILE_BYTES = 4 * 1024 * 1024
    MAX_SESSION_BYTES = 16 * 1024 * 1024

    def __init__(self, output):
        self.output = Path(output) / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex)
        self.cases = 0
        self.bytes_written = 0

    def _records(self, studio, kind, fields, limit):
        # LIMIT and row-size bounds precede JSON materialization. Never copy the
        # auth DB or arbitrary record kinds into a diagnostic artifact.
        with studio.store.tx() as db:
            rows = db.execute(
                "SELECT CASE WHEN length(CAST(body AS BLOB)) <= ? THEN body END "
                "FROM records WHERE kind=? ORDER BY rowid DESC LIMIT ?",
                (self.MAX_ROW_BYTES, kind, limit + 1),
            ).fetchall()
        incomplete = len(rows) > limit
        result = []
        for row in rows[:limit]:
            try:
                value = json.loads(row[0])
                if not isinstance(value, dict):
                    raise ValueError
                result.append({field: value[field] for field in fields if field in value})
            except (TypeError, ValueError):
                incomplete = True
        return result, incomplete

    def _copy_source(self, root, source, target):
        from xverse_studio.security.managed_io import open_read, SafeIOError

        remaining = self.MAX_SESSION_BYTES - self.bytes_written
        if remaining <= 0:
            return {'status': 'omitted', 'code': 'CAPTURE_BYTE_BUDGET'}
        limit = min(self.MAX_FILE_BYTES, remaining)
        data, size, error = None, None, None
        try:
            with open_read(root, source) as stream:
                size = os.fstat(stream.fileno()).st_size
                data = stream.read(limit + 1)
        except SafeIOError as exc:
            error = exc.code
        except OSError:
            error = 'SOURCE_UNAVAILABLE'
        if data is None:
            return {'status': 'unavailable', 'code': error}
        raw = data[:limit]
        target.write_bytes(raw)
        self.bytes_written += len(raw)
        truncated = len(data) > limit or size > limit
        return {'status': 'partial' if error or truncated else 'copied',
                'code': error, 'bytes': len(raw), 'sourceBytesObserved': size,
                'truncated': truncated, 'stableAcquisition': error is None,
                'capturedBytesSha256': hashlib.sha256(raw).hexdigest()}

    def capture(self, studio, nodeid):
        if self.cases >= self.MAX_CASES:
            return {'status': 'omitted', 'code': 'CAPTURE_CASE_BUDGET'}
        self.cases += 1
        self.output.mkdir(parents=True, exist_ok=True, mode=0o700)
        destination = self.output / (str(self.cases) + '-' + hashlib.sha256(nodeid.encode()).hexdigest()[:16])
        destination.mkdir(mode=0o700)
        runs, runs_incomplete = self._records(studio, 'run', RUN_FIELDS, self.MAX_RUNS)
        operations, ops_incomplete = self._records(studio, 'operation', OP_FIELDS, self.MAX_OPERATIONS)
        manifest = {'scope': 'Explicitly marked owned native test diagnostics; not runtime admission',
                    'nodeId': nodeid, 'capturedBeforeFixtureTeardown': True,
                    'observedAt': datetime.now(timezone.utc).isoformat(),
                    'runs': runs, 'operations': operations,
                    'metadataIncomplete': runs_incomplete or ops_incomplete,
                    'fileAllowlist': ['state.json', 'evidence.jsonl'],
                    'fileBytesLimit': self.MAX_FILE_BYTES, 'sessionBytesLimit': self.MAX_SESSION_BYTES,
                    'files': []}
        for run in runs:
            rid = run.get('runId')
            if not isinstance(rid, str):
                manifest['metadataIncomplete'] = True
                continue
            name = hashlib.sha256(rid.encode()).hexdigest()[:16]
            retained = destination / name
            retained.mkdir(mode=0o700)
            try:
                directory = studio.runs.directory(rid)
                for filename in manifest['fileAllowlist']:
                    observation = self._copy_source(studio.store.root, directory / filename, retained / filename)
                    manifest['files'].append({'runId': rid, 'path': name + '/' + filename, **observation})
            except (OSError, ValueError):
                manifest['files'].append({'runId': rid, 'status': 'unavailable', 'code': 'RUN_PATH_UNAVAILABLE'})
        manifest['sessionBytesWritten'] = self.bytes_written
        (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        return {'status': 'retained', 'captureId': destination.name,
                'manifest': destination / 'manifest.json'}

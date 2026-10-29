"""Failure retention tooling: actual native control and explicit safety fixtures."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from studio_native_failure_capture import NativeFailureCapture
from xverse_studio.storage.core import Store, canonical, digest


@pytest.mark.skipif(sys.platform != 'linux', reason='Anchored Linux diagnostic acquisition; native Windows held')
def test_real_native_failure_is_retained_before_teardown_without_auth_files(tmp_path, record_property):
    repo = Path(__file__).resolve().parents[2]
    private = tmp_path / 'capture control Ω'
    private.mkdir()
    source = private / 'test_control.py'
    source.write_text('''import pytest
from test_native_command_terminal_boundaries import test_native_late_command_outcome_preserves_natural_completion_and_exact_retry

@pytest.mark.capture_owned_native_failure
def test_deliberate_capture_control(client,monkeypatch,record_property):
    test_native_late_command_outcome_preserves_natural_completion_and_exact_retry(client,monkeypatch,record_property,'stop','after_final_poll')
    raise AssertionError('OWNED_CAPTURE_CONTROL: original native workflow assertions passed')
''')
    runner = private / 'run_control.py'
    runner.write_text('''import importlib.util,sys,pytest
from pathlib import Path
repo=Path(sys.argv.pop(1))
sys.path[:0]=[str(repo/'tests'),str(repo/'tests/integration')]
spec=importlib.util.spec_from_file_location('owned_capture_conftest',repo/'tests/conftest.py')
plugin=importlib.util.module_from_spec(spec);spec.loader.exec_module(plugin)
raise SystemExit(pytest.main(sys.argv[1:],plugins=[plugin]))
''')
    retained = private / 'retained'
    command = [sys.executable, '-I', str(runner), str(repo), '-q', '--tb=short',
               '--confcutdir=' + str(private), '--rootdir=' + str(private),
               '--basetemp=' + str(private / 'disposable pytest data'),
               '--owned-failure-dir=' + str(retained), str(source)]
    env = {k: v for k, v in os.environ.items() if k not in ('PYTEST_ADDOPTS', 'PYTHONPATH')}
    env['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
    completed = subprocess.run(command, cwd=private, env=env, text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=45)
    assert completed.returncode == 1 and 'OWNED_CAPTURE_CONTROL' in completed.stdout, completed.stdout
    assert '1 failed' in completed.stdout and 'Capture status: retained' in completed.stdout
    manifests = list(retained.glob('*/*/manifest.json'))
    assert len(manifests) == 1
    manifest = json.loads(manifests[0].read_text())
    assert manifest['capturedBeforeFixtureTeardown'] is True and manifest['metadataIncomplete'] is False
    assert len(manifest['runs']) == 1 and len(manifest['operations']) == 2
    assert all(row['status'] == 'copied' and row['stableAcquisition'] and not row['truncated'] for row in manifest['files'])
    files = {Path(row['path']).name: manifests[0].parent / row['path'] for row in manifest['files']}
    assert set(files) == {'state.json', 'evidence.jsonl'}
    assert {p.name for p in retained.rglob('*') if p.is_file()} == {'manifest.json', 'state.json', 'evidence.jsonl'}
    for row in manifest['files']:
        assert hashlib.sha256((manifests[0].parent / row['path']).read_bytes()).hexdigest() == row['capturedBytesSha256']
    state = json.loads(files['state.json'].read_text())
    assert state['state'] == 'stopped' and state['cleanup'] == state['evidence'] == 'complete'
    assert state['journalDigest'] == digest(files['evidence.jsonl'].read_bytes())
    previous = '0' * 64
    for sequence, line in enumerate(files['evidence.jsonl'].read_text().splitlines(), 1):
        row = json.loads(line)
        actual = row.pop('digest')
        assert row['sequence'] == str(sequence) and row['previousDigest'] == previous
        assert row['runId'] == manifest['runs'][0]['runId']
        assert hashlib.sha256(canonical(row).encode()).hexdigest() == actual
        previous = actual
    assert retained.is_relative_to(private) and not retained.is_relative_to(private / 'disposable pytest data')
    record_property('owned_capture_control', json.dumps(dict(
        scope='Real owned native workflow followed by intentional harness failure; not an application regression',
        originalNativeAssertionsPassed=True, capturedBeforeTeardown=True,
        persistedOutsideDisposablePytestData=True, journalChainAndTerminalDigestVerified=True,
        ownerKeysSignedMailboxesRequestsSnapshotsAndAuthDatabaseExcluded=True)))


def fixture_studio(tmp_path):
    root = tmp_path / 'owned fixture'
    store = Store(root)
    rid = 'run-capture-fixture'
    directory = root / 'runs' / rid
    directory.mkdir(parents=True)
    store.put('run', rid, {'runId': rid, 'state': 'unknown', 'unrelatedPrivateField': 'not-exported'})
    store.put('operation', 'op-capture', {'operationId': 'op-capture', 'runId': rid,
                                      'status': 'unknown', 'privateParameters': 'not-exported'})
    (directory / 'state.json').write_text('{"state":"unknown"}')
    return SimpleNamespace(store=store, runs=SimpleNamespace(directory=lambda selected: directory)), directory


@pytest.mark.skipif(sys.platform != 'linux', reason='Anchored Linux source/symlink fixture; no Windows result')
def test_capture_refuses_linked_sources_and_never_collects_private_files(tmp_path):
    studio, directory = fixture_studio(tmp_path)
    outside = tmp_path / 'unrelated-secret.txt'
    outside.write_text('private-canary-that-must-not-be-copied')
    (directory / 'evidence.jsonl').symlink_to(outside)
    for name in ['owner.key', 'command.json', 'request.json', 'bootstrap.json']:
        (directory / name).write_text('private-canary-that-must-not-be-copied')
    capture = NativeFailureCapture(tmp_path / 'retained')
    result = capture.capture(studio, 'explicit safety fixture')
    manifest = json.loads(result['manifest'].read_text())
    rejected = next(row for row in manifest['files'] if row['path'].endswith('evidence.jsonl'))
    assert rejected['status'] == 'unavailable' and rejected['code'] == 'UNSAFE_PATH'
    assert {p.name for p in capture.output.rglob('*') if p.is_file()} == {'state.json', 'manifest.json'}
    assert all(b'private-canary' not in p.read_bytes() for p in capture.output.rglob('*') if p.is_file())
    assert 'unrelatedPrivateField' not in result['manifest'].read_text()
    assert 'privateParameters' not in result['manifest'].read_text()
    assert outside.read_text() == 'private-canary-that-must-not-be-copied'


@pytest.mark.skipif(sys.platform != 'linux', reason='Anchored Linux bounded-source fixture; no Windows result')
def test_capture_marks_truncation_and_enforces_session_and_case_limits(tmp_path):
    studio, directory = fixture_studio(tmp_path)
    original = b'bounded-evidence-fixture\n' * 100
    (directory / 'evidence.jsonl').write_bytes(original)
    capture = NativeFailureCapture(tmp_path / 'retained')
    capture.MAX_FILE_BYTES = 100
    capture.MAX_SESSION_BYTES = 150
    capture.MAX_CASES = 2
    first = capture.capture(studio, 'first budget fixture')
    manifest = json.loads(first['manifest'].read_text())
    journal = next(row for row in manifest['files'] if row['path'].endswith('evidence.jsonl'))
    assert journal['status'] == 'partial' and journal['truncated'] is True and journal['bytes'] == 100
    second = capture.capture(studio, 'second budget fixture')
    later = json.loads(second['manifest'].read_text())
    assert any(row.get('code') == 'CAPTURE_BYTE_BUDGET' for row in later['files'])
    assert capture.bytes_written == 150
    assert capture.capture(studio, 'third budget fixture') == {'status': 'omitted', 'code': 'CAPTURE_CASE_BUDGET'}
    assert len(list(capture.output.glob('*/manifest.json'))) == 2
    assert (directory / 'evidence.jsonl').read_bytes() == original

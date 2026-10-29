"""Real owned-process delivery faults; no replacement worker or simulated clock."""

import hashlib
import hmac
import json
import sys
import time

import psutil
import pytest

from test_reference_pause import wait_state
from xverse_studio.storage.core import canonical, digest


def journal(directory):
    # Active reads can end during an append; only complete original frames are
    # observations. Terminal validity is independently checked by the API.
    return [json.loads(line) for line in (directory / 'evidence.jsonl').read_bytes().splitlines(keepends=True)
            if line.endswith(b'\n')]


def native_run(client):
    studio = client.app.state.studio
    project = client.post('/api/v1/projects', json={'name': 'Native late command'}).json()
    changed = client.post(f"/api/v1/projects/{project['projectId']}/edits",
        headers={'If-Match': str(project['revision'])},
        json={'baseRevision': project['revision'], 'edits': [
            {'kind': 'set_parameter', 'parameterId': 'duration', 'value': 3},
            {'kind': 'set_parameter', 'parameterId': 'timestep', 'value': 1},
        ]})
    assert changed.status_code == 200, changed.text
    project = changed.json()
    checked = client.post(f"/api/v1/projects/{project['projectId']}/preflights", json={'revision': project['revision']})
    assert checked.status_code == 200 and checked.json()['status'] == 'ready', checked.text
    preflight = checked.json()
    request = {'snapshotId': preflight['snapshotId'], 'preflightId': preflight['preflightId']}
    started = client.post('/api/v1/runs', headers={'Idempotency-Key': 'native-boundary-start'}, json=request)
    assert started.status_code == 202, started.text
    run = wait_state(client, started.json()['runId'], 'running')
    directory = studio.runs.directory(run['runId'])
    child = studio.runs.children[run['runId']]
    known = studio.store.get('run', run['runId'])
    state = json.loads((directory / 'state.json').read_text())
    process = psutil.Process(child.pid)
    argv = [sys.executable, '-I', '-m', 'xverse_studio.providers.worker', str(directory)]
    assert child.pid == known['pid'] == state['pid'] and child.pid != psutil.Process().pid
    assert child.poll() is None and process.cmdline() == argv
    assert process.create_time() == known['createTime'] == state['createTime']
    assert known['launchArgvDigest'] == digest(argv)
    assert digest((directory / 'owner.key').read_bytes()) == known['ownerDigest'] == state['ownerDigest']
    snapshot = studio.store.root / 'snapshots' / run['snapshotId'] / 'snapshot.json'
    return project, preflight, request, started.json(), run, directory, child, known, snapshot


@pytest.mark.parametrize('kind', ['stop', 'cancel'])
@pytest.mark.parametrize('boundary', ['after_final_poll', 'after_exit'])
def test_native_late_command_outcome_preserves_natural_completion_and_exact_retry(
    client, monkeypatch, record_property, kind, boundary
):
    from xverse_studio.runs import service

    project, preflight, start_body, start_receipt, run, directory, child, known, snapshot = native_run(client)
    studio = client.app.state.studio
    immutable = snapshot.read_bytes()
    original_request = (directory / 'request.json').read_bytes()
    original_atomic = service.atomic
    deliveries = []
    retained_terminal = []
    final_tick = str(round((3-1) * 1_000_000))

    def late_mailbox(path, body):
        if path != directory / 'command.json':
            return original_atomic(path, body)
        command = json.loads(body)
        signature = command.pop('signature')
        assert hmac.compare_digest(signature, hmac.new((directory / 'owner.key').read_bytes(), canonical(command).encode(), hashlib.sha256).hexdigest())
        assert command['kind'] == kind
        operation = studio.store.get('operation', command['operationId'])
        assert operation['status'] == 'accepted' and operation['kind'] == kind
        assert studio.store.get('run', run['runId'])['pendingCommandId'] == command['operationId']
        assert not path.exists()
        if boundary == 'after_final_poll':
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                samples = [row for row in journal(directory) if row['type'] == 'observation.available']
                if samples and samples[-1]['sourceTime']['tick'] == final_tick:
                    break
                assert child.poll() is None, 'The native delivery window ended before the final sample was observed'
                time.sleep(.01)
            else:
                raise AssertionError('No actual native final sample was observed')
            process = psutil.Process(child.pid)
            assert child.poll() is None and process.create_time() == known['createTime']
            assert process.cmdline() == [sys.executable, '-I', '-m', 'xverse_studio.providers.worker', str(directory)]
            assert json.loads((directory / 'state.json').read_text())['state'] == 'running'
        else:
            assert child.wait(timeout=10) == 0
            state = json.loads((directory / 'state.json').read_text())
            assert state['state'] == 'stopped' and state['commandResults'] == {}
            assert state['cleanup'] == state['evidence'] == 'complete'
            retained_terminal.append((directory / 'evidence.jsonl').read_bytes())
        deliveries.append(command['operationId'])
        return original_atomic(path, body)

    monkeypatch.setattr(service, 'atomic', late_mailbox)
    body = {'kind': kind, 'expectedStateVersion': run['stateVersion']}
    headers = {'Idempotency-Key': 'native-late-' + kind}
    endpoint = f"/api/v1/runs/{run['runId']}/commands"
    response = client.post(endpoint, headers=headers, json=body)
    assert response.status_code == 202 and response.json()['status'] == 'accepted', response.text
    accepted = response.json()
    ended = wait_state(client, run['runId'], 'stopped')
    assert child.wait(timeout=5) == 0
    operation = client.get('/api/v1/operations/' + accepted['operationId']).json()
    code = 'RUN_COMPLETED_BEFORE_COMMAND' if boundary == 'after_final_poll' else 'RUN_TERMINAL_BEFORE_COMMAND'
    assert operation['status'] == 'failed' and operation['code'] == code
    assert deliveries == [accepted['operationId']]
    assert ended['cleanup'] == ended['evidence'] == 'complete' and ended['verdict'] is None
    assert 'pendingCommandId' not in ended
    rows = journal(directory)
    samples = [row for row in rows if row['type'] == 'observation.available']
    assert [row['sourceTime']['tick'] for row in samples] == ['0', '1000000', final_tick]
    terminal = [row for row in rows if row['type'] == 'run.state_changed'][-1]
    assert terminal['payload']['reason'] == 'duration_complete'
    assert [row for row in rows if row['type'] == 'evidence.updated'][-1]['payload']['coverage']['complete'] is True
    assert not any(row['type'] in ('command.delegated', 'command.completed') for row in rows)
    failures = [row for row in rows if row['type'] == 'command.failed']
    if boundary == 'after_final_poll':
        assert len(failures) == 1 and failures[0]['payload']['operationId'] == accepted['operationId']
        assert failures[0]['payload']['kind'] == kind and failures[0]['payload']['code'] == code
    else:
        assert failures == [] and (directory / 'evidence.jsonl').read_bytes() == retained_terminal[0]
    sealed = (directory / 'evidence.jsonl').read_bytes()
    assert client.post(endpoint, headers=headers, json=body).json() == accepted
    assert client.post('/api/v1/runs', headers={'Idempotency-Key': 'native-boundary-start'},
                       json={'snapshotId': preflight['snapshotId'], 'preflightId': preflight['preflightId']}).json() == start_receipt
    conflict = client.post(endpoint, headers=headers, json={**body, 'kind': 'cancel' if kind == 'stop' else 'stop'})
    assert conflict.status_code == 409 and conflict.json()['code'] == 'IDEMPOTENCY_CONFLICT'
    assert len(studio.store.all('run')) == 1 and len(studio.store.all('operation')) == 2
    assert deliveries == [accepted['operationId']] and (directory / 'evidence.jsonl').read_bytes() == sealed
    assert client.get(f"/api/v1/runs/{run['runId']}/history").json()['integrity'] == 'valid'
    assert ended['effectivePlanDigest'] == preflight['planDigest'] == json.loads(immutable)['planDigest']
    assert snapshot.read_bytes() == immutable and (directory / 'request.json').read_bytes() == original_request
    assert studio.projects.read(project['projectId']) == project
    record_property('native_late_command', json.dumps(dict(kind=kind, boundary=boundary,
        scope='Actual owned native process and source ticks; signed mailbox delivery fault only; no equipment',
        originalPidBirthArgvOwnerVerified=True, finalSampleTick=final_tick, operation=code,
        naturalCompletion=True, originalJournalUnchangedAfterRetry=True, immutableInputs=True)))

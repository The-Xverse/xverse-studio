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


pytestmark = pytest.mark.capture_owned_native_failure


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


def assert_original_process(child, known, directory):
    process = psutil.Process(child.pid)
    assert child.poll() is None and child.pid == known['pid']
    assert process.create_time() == known['createTime']
    assert digest(process.cmdline()) == known['launchArgvDigest']
    assert process.cmdline() == [sys.executable, '-I', '-m', 'xverse_studio.providers.worker', str(directory)]
    assert digest((directory / 'owner.key').read_bytes()) == known['ownerDigest']


def wait_actual_sample(directory, child):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if any(row['type'] == 'observation.available' for row in journal(directory)):
            return
        assert child.poll() is None, 'Original worker exited before an actual sample was observed'
        time.sleep(.01)
    raise AssertionError('No actual native sample was observed')


def hold_signed_mailbox(monkeypatch, studio, run, directory, kind):
    from xverse_studio.runs import service

    actual = service.atomic
    held = []

    def hold(path, body):
        if path != directory / 'command.json':
            return actual(path, body)
        command = json.loads(body)
        signature = command.pop('signature')
        assert hmac.compare_digest(signature, hmac.new((directory / 'owner.key').read_bytes(), canonical(command).encode(), hashlib.sha256).hexdigest())
        assert command['kind'] == kind and not path.exists()
        assert studio.store.get('operation', command['operationId'])['status'] == 'accepted'
        assert studio.store.get('run', run['runId'])['pendingCommandId'] == command['operationId']
        # Controlled delivery loss: retain the original signed bytes without
        # replacing the worker or changing its clock, inputs or state file.
        held.append(command['operationId'])

    monkeypatch.setattr(service, 'atomic', hold)
    return held


def assert_preserved(client, context, immutable, original_request, accepted, headers, body):
    project, preflight, start_body, start_receipt, run, directory, child, known, snapshot = context
    studio = client.app.state.studio
    sealed = (directory / 'evidence.jsonl').read_bytes()
    assert client.post(f"/api/v1/runs/{run['runId']}/commands", headers=headers, json=body).json() == accepted
    assert client.post('/api/v1/runs', headers={'Idempotency-Key': 'native-boundary-start'}, json=start_body).json() == start_receipt
    assert len(studio.store.all('run')) == 1 and len(studio.store.all('operation')) == 2
    assert (directory / 'evidence.jsonl').read_bytes() == sealed
    assert snapshot.read_bytes() == immutable and (directory / 'request.json').read_bytes() == original_request
    assert studio.projects.read(project['projectId']) == project
    assert json.loads(immutable)['planDigest'] == preflight['planDigest']
    assert not any(row['type'].startswith('command.') for row in journal(directory))


@pytest.mark.parametrize('kind', ['stop', 'cancel'])
@pytest.mark.parametrize('fault', ['worker_interrupted', 'recorded_owner_lost'])
def test_native_pending_command_stays_unknown_without_owned_terminal_proof(
    client, monkeypatch, record_property, kind, fault
):
    context = native_run(client)
    project, preflight, start_body, start_receipt, run, directory, child, known, snapshot = context
    studio = client.app.state.studio
    immutable, original_request = snapshot.read_bytes(), (directory / 'request.json').read_bytes()
    wait_actual_sample(directory, child)
    assert_original_process(child, known, directory)
    held = hold_signed_mailbox(monkeypatch, studio, run, directory, kind)
    endpoint = f"/api/v1/runs/{run['runId']}/commands"
    headers = {'Idempotency-Key': 'native-unknown-' + kind}
    body = {'kind': kind, 'expectedStateVersion': run['stateVersion']}
    response = client.post(endpoint, headers=headers, json=body)
    assert response.status_code == 202 and response.json()['status'] == 'accepted', response.text
    accepted = response.json()
    assert held == [accepted['operationId']] and not (directory / 'command.json').exists()
    assert studio.store.get('operation', accepted['operationId'])['status'] == 'delegated'
    assert_original_process(child, known, directory)
    if fault == 'worker_interrupted':
        # Terminate only this test's verified original Popen child. This is an
        # interruption fault, not an application Stop or a portable signal claim.
        child.terminate()
        assert child.wait(timeout=10) != 0
    else:
        recorded = studio.store.get('run', run['runId'])
        recorded['createTime'] = known['createTime'] - 60
        studio.store.put('run', run['runId'], recorded)

    unknown = client.get('/api/v1/runs/' + run['runId']).json()
    assert unknown['state'] == 'unknown' and unknown['reason'] == 'OWNERSHIP_UNKNOWN'
    assert unknown['cleanup'] == 'unknown' and unknown['evidence'] == 'partial'
    assert unknown['pendingCommandId'] == accepted['operationId']
    assert client.get('/api/v1/operations/' + accepted['operationId']).json()['status'] == 'unknown'
    denied = client.post(endpoint, headers={'Idempotency-Key': 'native-no-authority'},
                         json={'kind': kind, 'expectedStateVersion': unknown['stateVersion']})
    assert denied.status_code == 409 and denied.json()['code'] == 'STATE_CONFLICT'
    assert client.post(endpoint, headers=headers, json=body).json() == accepted
    assert held == [accepted['operationId']]

    if fault == 'recorded_owner_lost':
        assert_original_process(child, known, directory)
        assert child.wait(timeout=10) == 0
        terminal = json.loads((directory / 'state.json').read_text())
        assert terminal['state'] == 'stopped' and terminal['cleanup'] == terminal['evidence'] == 'complete'
        assert terminal['pid'] == child.pid == known['pid']
        assert terminal['createTime'] == known['createTime'] and terminal['ownerDigest'] == known['ownerDigest']
        assert digest((directory / 'owner.key').read_bytes()) == known['ownerDigest']
        assert studio.store.get('run', run['runId'])['launchArgvDigest'] == known['launchArgvDigest']
        sealed = (directory / 'evidence.jsonl').read_bytes()
        still_unknown = client.get('/api/v1/runs/' + run['runId']).json()
        assert still_unknown['state'] == still_unknown['cleanup'] == 'unknown'
        assert client.get('/api/v1/operations/' + accepted['operationId']).json()['status'] == 'unknown'
        # Undo precisely the test-injected identity fault. Normal reconciliation
        # must validate the original terminal evidence; no guard is bypassed.
        recorded = studio.store.get('run', run['runId'])
        recorded['createTime'] = known['createTime']
        studio.store.put('run', run['runId'], recorded)
        ended = client.get('/api/v1/runs/' + run['runId']).json()
        assert ended['state'] == 'stopped' and ended['cleanup'] == ended['evidence'] == 'complete'
        assert ended['effectivePlanDigest'] == preflight['planDigest'] and ended['verdict'] is None
        assert 'pendingCommandId' not in ended
        operation = client.get('/api/v1/operations/' + accepted['operationId']).json()
        assert operation['status'] == 'failed' and operation['code'] == 'RUN_TERMINAL_BEFORE_COMMAND'
        assert (directory / 'evidence.jsonl').read_bytes() == sealed
        assert client.get(f"/api/v1/runs/{run['runId']}/history").json()['integrity'] == 'valid'
    else:
        state = json.loads((directory / 'state.json').read_text())
        assert state['state'] == 'running' and not state.get('journalDigest')
        assert client.get(f"/api/v1/runs/{run['runId']}/history").json()['integrity'] == 'verified_prefix'
        assert client.get('/api/v1/runs/' + run['runId']).json()['state'] == 'unknown'
        assert client.get('/api/v1/operations/' + accepted['operationId']).json()['status'] == 'unknown'
    assert_preserved(client, context, immutable, original_request, accepted, headers, body)
    assert held == [accepted['operationId']] and not (directory / 'command.json').exists()
    record_property('native_pending_command', json.dumps(dict(kind=kind, fault=fault,
        scope='Actual owned native process; signed mailbox delivery loss and explicit test fault; no equipment',
        originalPidBirthArgvOwnerVerified=True, uncertainOutcomeRetained=True,
        ownershipRecovery=('original recorded birth restored after original worker natural exit' if fault == 'recorded_owner_lost' else 'not recovered'),
        noReplayOrRespawn=True, immutableInputs=True)))


@pytest.mark.parametrize('kind', ['stop', 'cancel'])
def test_native_reconciliation_before_delegation_does_not_reopen_settled_command(
    client, monkeypatch, record_property, kind
):
    from xverse_studio.runs import service

    context = native_run(client)
    project, preflight, start_body, start_receipt, run, directory, child, known, snapshot = context
    studio = client.app.state.studio
    immutable, original_request = snapshot.read_bytes(), (directory / 'request.json').read_bytes()
    wait_actual_sample(directory, child)
    assert_original_process(child, known, directory)
    actual, original_atomic = studio.store.idempotent, service.atomic
    settled, attempted = [], []

    def delayed_acceptance(principal, route, key, payload, fn):
        result, new = actual(principal, route, key, payload, fn)
        if route.endswith('/commands') and new:
            assert studio.store.get('operation', result['operationId'])['status'] == 'accepted'
            assert not (directory / 'command.json').exists()
            assert child.wait(timeout=10) == 0
            terminal = (directory / 'evidence.jsonl').read_bytes()
            # A real intervening read reconciles actual worker exit, without
            # manufacturing an operation result or editing worker state.
            ended = studio.runs.read(run['runId'])
            operation = studio.store.get('operation', result['operationId'])
            assert ended['state'] == 'stopped' and ended['cleanup'] == ended['evidence'] == 'complete'
            assert operation['status'] == 'failed' and operation['code'] == 'RUN_TERMINAL_BEFORE_COMMAND'
            assert 'pendingCommandId' not in ended
            assert (directory / 'evidence.jsonl').read_bytes() == terminal
            settled.append(result['operationId'])
        return result, new

    def observe_mailbox(path, data):
        if path == directory / 'command.json':
            attempted.append(True)
        return original_atomic(path, data)

    monkeypatch.setattr(studio.store, 'idempotent', delayed_acceptance)
    monkeypatch.setattr(service, 'atomic', observe_mailbox)
    headers = {'Idempotency-Key': 'native-settled-' + kind}
    body = {'kind': kind, 'expectedStateVersion': run['stateVersion']}
    response = client.post(f"/api/v1/runs/{run['runId']}/commands", headers=headers, json=body)
    assert response.status_code == 202 and response.json()['status'] == 'accepted', response.text
    accepted = response.json()
    assert settled == [accepted['operationId']] and attempted == []
    assert not (directory / 'command.json').exists()
    operation = client.get('/api/v1/operations/' + accepted['operationId']).json()
    assert operation['status'] == 'failed' and operation['code'] == 'RUN_TERMINAL_BEFORE_COMMAND'
    assert client.get(f"/api/v1/runs/{run['runId']}/history").json()['integrity'] == 'valid'
    assert_preserved(client, context, immutable, original_request, accepted, headers, body)
    assert settled == [accepted['operationId']] and attempted == []
    record_property('native_settled_command', json.dumps(dict(kind=kind,
        scope='Actual owned native process and intervening read after natural exit; no equipment',
        originalPidBirthArgvOwnerVerified=True, originalOperationResultPreserved=True,
        noMailboxWrite=True, noReplayOrRespawn=True, immutableInputs=True)))


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

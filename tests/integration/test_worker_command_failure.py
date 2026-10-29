"""Actual native workload failure before an accepted Stop/Cancel is polled.

Delivery is held until the original child is sleeping after a real sample. Its
original signed mailbox is written, then a real ownership-verified SIGINT causes
the unchanged worker's exception path to record the unapplied request failure.
"""

import hashlib
import hmac
import json
from pathlib import Path
import sys
import time

import pytest

from test_campaign_worker_failure import interrupt_owned_sleeping_worker
from test_native_command_terminal_boundaries import (
    assert_original_process, journal, native_run, wait_actual_sample,
)
from xverse_studio.storage.core import canonical


@pytest.mark.skipif(sys.platform != 'linux', reason='Owned Linux SIGINT/sleep fault lane; native Windows held')
@pytest.mark.parametrize('kind', ['stop', 'cancel'])
def test_native_workload_failure_settles_unapplied_command_without_inventing_stop(
    client, monkeypatch, record_property, kind
):
    from xverse_studio.runs import service

    project, preflight, start_body, start_receipt, run, directory, child, known, snapshot = native_run(client)
    studio = client.app.state.studio
    immutable, request = snapshot.read_bytes(), (directory / 'request.json').read_bytes()
    wait_actual_sample(directory, child)
    assert_original_process(child, known, directory)
    actual = service.atomic
    faults = []

    def deliver_during_original_sleep(path, body):
        if path != directory / 'command.json':
            return actual(path, body)
        command = json.loads(body)
        signature = command.pop('signature')
        assert hmac.compare_digest(signature, hmac.new((directory / 'owner.key').read_bytes(), canonical(command).encode(), hashlib.sha256).hexdigest())
        assert command['kind'] == kind and not path.exists()
        assert studio.store.get('operation', command['operationId'])['status'] == 'accepted'
        assert studio.store.get('run', run['runId'])['pendingCommandId'] == command['operationId']
        channel = Path('/proc') / str(child.pid) / 'wchan'
        started = json.loads((directory / 'state.json').read_text())['startedAt']
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            elapsed = time.time() - started
            if channel.read_text().strip() == 'hrtimer_nanosleep' and .2 <= elapsed % 1 <= .5:
                break
            assert child.poll() is None
            time.sleep(.005)
        else:
            raise AssertionError('Original worker had no bounded sleeping delivery window')
        assert_original_process(child, known, directory)
        actual(path, body)
        interrupted, witness = interrupt_owned_sleeping_worker(studio.runs, studio.store, run['runId'])
        assert interrupted is child
        faults.append(dict(operationId=command['operationId'], nativeInterruption=witness))

    monkeypatch.setattr(service, 'atomic', deliver_during_original_sleep)
    endpoint = f"/api/v1/runs/{run['runId']}/commands"
    headers = {'Idempotency-Key': 'native-failed-before-' + kind}
    body = {'kind': kind, 'expectedStateVersion': run['stateVersion']}
    response = client.post(endpoint, headers=headers, json=body)
    assert response.status_code == 202 and response.json()['status'] == 'accepted', response.text
    accepted = response.json()
    assert child.wait(timeout=10) == 1
    failed = client.get('/api/v1/runs/' + run['runId']).json()
    assert failed['state'] == 'failed' and failed['reason'] == 'REFERENCE_WORKER_ERROR'
    assert failed['cleanup'] == 'unknown' and failed['evidence'] == 'partial' and failed['verdict'] is None
    assert failed['effectivePlanDigest'] == preflight['planDigest'] and 'pendingCommandId' not in failed
    operation = client.get('/api/v1/operations/' + accepted['operationId']).json()
    assert operation['status'] == 'failed' and operation['code'] == 'REFERENCE_WORKER_ERROR'
    assert len(faults) == 1 and faults[0]['operationId'] == accepted['operationId']
    rows = journal(directory)
    command_failures = [row for row in rows if row['type'] == 'command.failed']
    assert len(command_failures) == 1
    assert command_failures[0]['payload']['operationId'] == accepted['operationId']
    assert command_failures[0]['payload']['kind'] == kind
    assert command_failures[0]['payload']['code'] == 'REFERENCE_WORKER_ERROR'
    assert not any(row['type'] in ('command.completed', 'command.delegated', 'cleanup.updated', 'evidence.updated') for row in rows)
    errors = [row for row in rows if row['type'] == 'log.appended' and row['payload'].get('code') == 'REFERENCE_WORKER_ERROR']
    assert len(errors) == 1 and 'workload failed' in errors[0]['payload']['message'].lower()
    assert client.get(f"/api/v1/runs/{run['runId']}/history").json()['integrity'] == 'verified_prefix'
    sealed = (directory / 'evidence.jsonl').read_bytes()
    assert client.post(endpoint, headers=headers, json=body).json() == accepted
    conflict = client.post(endpoint, headers=headers, json={**body, 'kind': 'cancel' if kind == 'stop' else 'stop'})
    assert conflict.status_code == 409 and conflict.json()['code'] == 'IDEMPOTENCY_CONFLICT'
    assert client.post('/api/v1/runs', headers={'Idempotency-Key': 'native-boundary-start'}, json=start_body).json() == start_receipt
    assert len(studio.store.all('run')) == 1 and len(studio.store.all('operation')) == 2 and len(faults) == 1
    assert snapshot.read_bytes() == immutable and (directory / 'request.json').read_bytes() == request
    assert studio.projects.read(project['projectId']) == project
    assert (directory / 'evidence.jsonl').read_bytes() == sealed
    record_property('native_command_workload_failure', json.dumps(dict(kind=kind, fault=faults[0],
        scope='Actual owned Linux worker after real sample; signed delivery and original-child SIGINT; no equipment',
        runOutcome='failed', commandOutcome='failed', code=operation['code'], cleanup='unknown', evidence='partial',
        originalInputsPreserved=True, noReplayOrRespawn=True)))

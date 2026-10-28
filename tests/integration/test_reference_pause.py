"""Actual owned native controls; no signal-based pause or external equipment."""

import hashlib
from copy import deepcopy
import hmac
import json
import time

import pytest


def running_reference(client, duration=5):
    response = client.post('/api/v1/projects', json={'name': 'Owned bounded pause'})
    assert response.status_code == 201
    project = response.json()
    edited = client.post(
        f"/api/v1/projects/{project['projectId']}/edits",
        headers={'If-Match': str(project['revision'])},
        json={'baseRevision': project['revision'], 'edits': [
            {'kind': 'set_parameter', 'parameterId': 'duration', 'value': duration},
        ]},
    )
    assert edited.status_code == 200
    project = edited.json()
    preflight = client.post(
        f"/api/v1/projects/{project['projectId']}/preflights",
        json={'revision': project['revision']},
    ).json()
    assert preflight['status'] == 'ready'
    accepted = client.post('/api/v1/runs', headers={'Idempotency-Key': 'start'},
                           json={'snapshotId': preflight['snapshotId'], 'preflightId': preflight['preflightId']})
    assert accepted.status_code == 202
    run = wait_state(client, accepted.json()['runId'], 'running')
    directory = client.app.state.studio.runs.directory(run['runId'])
    snapshot = client.app.state.studio.store.root / 'snapshots' / run['snapshotId'] / 'snapshot.json'
    return project, run, directory, snapshot


def wait_state(client, run_id, expected, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        response = client.get('/api/v1/runs/' + run_id)
        assert response.status_code == 200
        run = response.json()
        if run['state'] == expected:
            return run
        assert run['state'] not in ('failed', 'unknown'), run
        time.sleep(0.05)
    raise AssertionError(run)


def command(client, run, kind, key=None):
    body = {'kind': kind, 'expectedStateVersion': run['stateVersion']}
    response = client.post(f"/api/v1/runs/{run['runId']}/commands",
                           headers={'Idempotency-Key': key or kind}, json=body)
    assert response.status_code == 202, response.text
    return body, response.json()


def assert_completed(client, receipt):
    operation = client.get('/api/v1/operations/' + receipt['operationId'])
    assert operation.status_code == 200
    assert operation.json()['status'] == 'completed', operation.text


def records(directory):
    return [json.loads(line) for line in (directory / 'evidence.jsonl').read_text().splitlines()]


def test_native_pause_resume_retains_clock_inputs_and_same_key_operation(client):
    project, run, directory, snapshot = running_reference(client)
    immutable = snapshot.read_bytes()
    worker = client.app.state.studio.runs.children[run['runId']]
    payload, pause = command(client, run, 'pause')
    paused = wait_state(client, run['runId'], 'paused')
    assert_completed(client, pause)
    journal = (directory / 'evidence.jsonl').read_bytes()
    assert any(e['type'] == 'run.state_changed' and e['payload']['state'] == 'paused' for e in records(directory))
    time.sleep(0.35)
    assert (directory / 'evidence.jsonl').read_bytes() == journal
    assert worker.poll() is None
    assert client.get('/api/v1/runs/' + run['runId']).json()['state'] == 'paused'
    # State-specific refusal and stale CAS do not overwrite the accepted command.
    for kind, version in [('pause', paused['stateVersion']), ('resume', run['stateVersion'])]:
        refused = client.post(f"/api/v1/runs/{run['runId']}/commands",
                              headers={'Idempotency-Key': 'refused-' + kind},
                              json={'kind': kind, 'expectedStateVersion': version})
        assert refused.status_code == 409
    _, resume = command(client, paused, 'resume')
    running = wait_state(client, run['runId'], 'running')
    assert_completed(client, resume)
    replay = client.post(f"/api/v1/runs/{run['runId']}/commands",
                         headers={'Idempotency-Key': 'pause'}, json=payload)
    assert replay.status_code == 202 and replay.json() == pause
    assert client.get('/api/v1/runs/' + run['runId']).json()['state'] == 'running'
    refused = client.post(f"/api/v1/runs/{run['runId']}/commands",
                          headers={'Idempotency-Key': 'resume-while-running'},
                          json={'kind': 'resume', 'expectedStateVersion': running['stateVersion']})
    assert refused.status_code == 409
    _, stop = command(client, running, 'stop')
    ended = wait_state(client, run['runId'], 'stopped')
    assert_completed(client, stop)
    assert worker.wait(timeout=5) == 0
    events = records(directory)
    for receipt in [pause, resume, stop]:
        assert len([e for e in events if e['type'] == 'command.completed' and e['payload']['operationId'] == receipt['operationId']]) == 1
    ticks = [int(e['sourceTime']['tick']) for e in events if e['type'] == 'observation.available']
    assert len(ticks) > 0 and ticks == list(range(0, len(ticks) * 100000, 100000))
    assert ended['cleanup'] == ended['evidence'] == 'complete' and ended['verdict'] is None
    assert ended['effectivePlanDigest'] == json.loads(immutable)['planDigest']
    assert ended['effectiveSemanticDigest'] == json.loads(immutable)['semanticDigest']
    assert client.get(f"/api/v1/runs/{run['runId']}/observations").json()['integrity'] == 'valid'
    assert snapshot.read_bytes() == immutable
    assert hashlib.sha256(snapshot.read_bytes()).digest() == hashlib.sha256(immutable).digest()
    assert client.app.state.studio.projects.read(project['projectId']) == project
    assert len(client.app.state.studio.store.all('run')) == 1


@pytest.mark.parametrize('kind', ['stop', 'cancel'])
def test_native_stop_and_cancel_settle_while_simulation_is_paused(client, kind):
    _, run, directory, snapshot = running_reference(client)
    immutable = snapshot.read_bytes()
    _, pause = command(client, run, 'pause')
    paused = wait_state(client, run['runId'], 'paused')
    assert_completed(client, pause)
    _, stopped = command(client, paused, kind)
    ended = wait_state(client, run['runId'], 'stopped')
    assert_completed(client, stopped)
    assert ended['cleanup'] == ended['evidence'] == 'complete'
    assert ended['verdict'] is None and snapshot.read_bytes() == immutable
    assert len([e for e in records(directory) if e['type'] == 'command.completed' and e['payload']['operationId'] == pause['operationId']]) == 1


def test_native_pause_has_a_declared_finite_wall_budget_without_silent_resume(client):
    _, run, directory, _ = running_reference(client, duration=2)
    _, pause = command(client, run, 'pause')
    paused = wait_state(client, run['runId'], 'paused')
    assert_completed(client, pause)
    assert paused['controlLimits']['maxPausedWallSeconds'] == 30
    # A genuine Resume/Pause cycle spends the same cumulative budget.
    time.sleep(1.5)
    _, resume = command(client, paused, 'resume')
    running = wait_state(client, run['runId'], 'running')
    assert_completed(client, resume)
    _, second_pause = command(client, running, 'pause', key='second-pause')
    wait_state(client, run['runId'], 'paused')
    assert_completed(client, second_pause)
    frozen = (directory / 'evidence.jsonl').read_bytes()
    begin = time.monotonic()
    ended = wait_state(client, run['runId'], 'stopped', timeout=35)
    assert time.monotonic() - begin < 35
    assert ended['reason'] == 'PAUSE_BUDGET_EXHAUSTED'
    assert ended['cleanup'] == ended['evidence'] == 'complete' and ended['verdict'] is None
    events = records(directory)
    assert (directory / 'evidence.jsonl').read_bytes().startswith(frozen)
    pause_index = max(i for i,e in enumerate(events) if e['type'] == 'run.state_changed' and e['payload']['state'] == 'paused')
    assert not any(e['type'] == 'observation.available' for e in events[pause_index:])
    exhaustion = next(e for e in events if e['type'] == 'run.state_changed' and e['payload'].get('reason') == 'PAUSE_BUDGET_EXHAUSTED')
    # The provider stop observation precedes terminal fsync/API publication.
    # Its retained wall timestamps show that Resume did not reset the budget.
    assert 26 <= exhaustion['recordedAt'] - events[pause_index]['recordedAt'] < 29.8
    coverage = [e['payload']['coverage'] for e in events if e['type'] == 'evidence.updated'][-1]
    assert coverage['complete'] is False


def test_owned_shutdown_cancels_a_paused_reference_worker(client):
    _, run, _, _ = running_reference(client)
    _, pause = command(client, run, 'pause')
    wait_state(client, run['runId'], 'paused')
    assert_completed(client, pause)
    client.app.state.studio.runs.shutdown()
    ended = wait_state(client, run['runId'], 'stopped')
    assert ended['cleanup'] == ended['evidence'] == 'complete'
    assert run['runId'] not in client.app.state.studio.runs.children
    operations = client.app.state.studio.store.all('operation')
    cancelled = [op for op in operations if op.get('runId') == run['runId'] and op['kind'] == 'cancel']
    assert len(cancelled) == 1 and cancelled[0]['status'] == 'completed'


@pytest.mark.parametrize('budget', [None, 0, 1, 31, True])
def test_inconsistent_installed_pause_budget_blocks_preflight_before_launch(client, monkeypatch, budget):
    from xverse_studio.providers.registry import descriptors
    from xverse_studio.runs import service
    rows = deepcopy(descriptors())
    reference = next(item for item in rows if item['providerId'] == 'studio.reference')
    if budget is None:
        reference['limits'].pop('maxPausedWallSeconds')
    else:
        reference['limits']['maxPausedWallSeconds'] = budget
    monkeypatch.setattr(service, 'descriptors', lambda: rows)
    project = client.post('/api/v1/projects', json={'name': 'Invalid installed budget'}).json()
    response = client.post(f"/api/v1/projects/{project['projectId']}/preflights", json={'revision': project['revision']})
    assert response.status_code == 200
    assert response.json()['status'] == 'blocked'
    assert 'LIMITS_UNKNOWN' in [d['code'] for d in response.json()['diagnostics']]
    assert client.app.state.studio.runs.children == {}
    assert client.app.state.studio.store.all('run') == []


@pytest.mark.parametrize('missing', ['operation', 'record', 'nonphysical_authority'])
def test_pause_requires_the_frozen_scoped_nonphysical_capability(client, monkeypatch, missing):
    from xverse_studio.providers.registry import descriptors
    from xverse_studio.runs import service
    rows = deepcopy(descriptors())
    reference = next(item for item in rows if item['providerId'] == 'studio.reference')
    if missing == 'operation':
        reference['operations'].remove('pause')
    elif missing == 'record':
        reference['capabilityRecords'] = [r for r in reference['capabilityRecords'] if r['kind'] != 'pause']
    else:
        next(r for r in reference['capabilityRecords'] if r['kind'] == 'pause')['physicalEffects'] = True
    monkeypatch.setattr(service, 'descriptors', lambda: rows)
    _, run, directory, _ = running_reference(client)
    assert 'pause' not in run['capabilities']
    response = client.post(f"/api/v1/runs/{run['runId']}/commands", headers={'Idempotency-Key': 'unsupported-pause'},
                           json={'kind': 'pause', 'expectedStateVersion': run['stateVersion']})
    assert response.status_code == 422 and response.json()['code'] == 'CAPABILITY_UNSUPPORTED'
    assert not (directory / 'command.json').exists()
    command(client, run, 'cancel')
    wait_state(client, run['runId'], 'stopped')


def test_worker_independently_refuses_a_stale_owner_signed_optional_transition(client, monkeypatch):
    """Trusted test faults the delegated mailbox copy after normal API admission."""
    from xverse_studio.runs import service
    from xverse_studio.storage.core import canonical
    _, run, directory, _ = running_reference(client)
    original = service.atomic
    injected = []

    def stale_delegated_copy(path, body):
        if path == directory / 'command.json':
            value = json.loads(body)
            if value['kind'] == 'pause':
                value.pop('signature')
                value['expectedStateVersion'] = run['stateVersion'] - 1
                value['signature'] = hmac.new((directory / 'owner.key').read_bytes(), canonical(value).encode(), hashlib.sha256).hexdigest()
                injected.append(value['operationId'])
                return original(path, canonical(value).encode())
        return original(path, body)

    monkeypatch.setattr(service, 'atomic', stale_delegated_copy)
    _, pause = command(client, run, 'pause')
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        current = client.get('/api/v1/runs/' + run['runId']).json()
        outcome = client.get('/api/v1/operations/' + pause['operationId']).json()
        if outcome['status'] == 'failed':
            break
        time.sleep(0.05)
    assert outcome['status'] == 'failed' and outcome['code'] == 'COMMAND_STATE_CONFLICT'
    assert injected == [pause['operationId']]
    assert current['state'] == 'running' and current['stateVersion'] == run['stateVersion']
    assert not any(e['type'] == 'run.state_changed' and e['payload']['state'] == 'paused' for e in records(directory))
    command(client, current, 'cancel')
    wait_state(client, run['runId'], 'stopped')


def test_campaign_cancellation_stops_a_paused_child_without_releasing_its_slot_early(client):
    project, seed, _, snapshot = running_reference(client)
    immutable = snapshot.read_bytes()
    command(client, seed, 'stop')
    wait_state(client, seed['runId'], 'stopped')
    created = client.post('/api/v1/campaigns', headers={'Idempotency-Key': 'paused-campaign'}, json={
        'snapshotId': seed['snapshotId'], 'matrix': {'gain': [0.5, 0.6]},
        'budget': {'maxRuns': 2, 'maxTotalSeconds': 10}, 'concurrency': 1,
    })
    assert created.status_code == 202, created.text
    campaign_id = created.json()['campaignId']
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        campaign = client.get('/api/v1/campaigns/' + campaign_id).json()
        active = next((c for c in campaign['children'] if c['runId']), None)
        if active:
            break
        time.sleep(0.05)
    assert active is not None
    run = wait_state(client, active['runId'], 'running')
    _, pause = command(client, run, 'pause')
    wait_state(client, run['runId'], 'paused')
    assert_completed(client, pause)
    time.sleep(0.35)
    campaign = client.get('/api/v1/campaigns/' + campaign_id).json()
    pending = [c for c in campaign['children'] if c['runId'] is None]
    assert len(pending) == 1 and pending[0]['state'] == 'pending'
    assert len(client.app.state.studio.store.all('run')) == 2
    cancelled = client.post(f'/api/v1/campaigns/{campaign_id}/cancel', headers={'Idempotency-Key': 'cancel-paused-campaign'}, json={})
    assert cancelled.status_code == 202, cancelled.text
    outcomes = cancelled.json()['activeCancellationOutcomes']
    assert len(outcomes) == 1 and outcomes[0]['runId'] == run['runId']
    assert outcomes[0]['status'] == 'accepted'
    ended = wait_state(client, run['runId'], 'stopped')
    assert_completed(client, outcomes[0])
    assert ended['cleanup'] == ended['evidence'] == 'complete'
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        campaign = client.get('/api/v1/campaigns/' + campaign_id).json()
        if campaign['status'] == 'cancelled':
            break
        time.sleep(0.05)
    assert campaign['status'] == 'cancelled'
    assert [c['state'] for c in campaign['children']] == ['stopped', 'cancelled']
    replay = client.post(f'/api/v1/campaigns/{campaign_id}/cancel', headers={'Idempotency-Key': 'cancel-paused-campaign'}, json={})
    assert replay.status_code == 202 and replay.json() == cancelled.json()
    assert len(client.app.state.studio.store.all('run')) == 2
    assert snapshot.read_bytes() == immutable
    assert client.app.state.studio.projects.read(project['projectId']) == project


@pytest.mark.parametrize('reason', ['OWNERSHIP_UNKNOWN', 'LAUNCH_ACKNOWLEDGEMENT_LOST'])
def test_native_reconciliation_clears_only_resolved_ownership_reason(client, monkeypatch, reason):
    """Injected OS observation denial; recovery observes the original real worker."""
    from xverse_studio.runs import service
    project, run, directory, snapshot = running_reference(client, duration=10)
    studio = client.app.state.studio
    worker = studio.runs.children[run['runId']]
    immutable = snapshot.read_bytes()
    process_factory = service.psutil.Process

    def denied_observation(pid, *args, **kwargs):
        if pid == worker.pid:
            raise service.psutil.AccessDenied(pid)
        return process_factory(pid, *args, **kwargs)

    with monkeypatch.context() as fault:
        fault.setattr(service.psutil, 'Process', denied_observation)
        unknown = client.get('/api/v1/runs/' + run['runId']).json()
        assert unknown['state'] == 'unknown' and unknown['reason'] == 'OWNERSHIP_UNKNOWN'
        assert unknown['stateVersion'] == run['stateVersion']
        assert unknown['observationVersion'] > run['observationVersion']
        refused = client.post(f"/api/v1/runs/{run['runId']}/commands", headers={'Idempotency-Key': 'unknown-pause'},
                              json={'kind': 'pause', 'expectedStateVersion': unknown['stateVersion']})
        assert refused.status_code == 409 and refused.json()['code'] == 'STATE_CONFLICT'
        assert not (directory / 'command.json').exists()
        if reason == 'LAUNCH_ACKNOWLEDGEMENT_LOST':
            # Separate labelled durable-metadata case; not an actual OS lost handle.
            persisted = studio.store.get('run', run['runId'])
            persisted['reason'] = reason
            studio.store.put('run', run['runId'], persisted)
    original_state = (directory / 'state.json').read_bytes()
    reported_unknown = json.loads(original_state)
    reported_unknown['state'] = 'unknown'
    # Labelled mutable observation fault, not a worker or physical outcome.
    try:
        service.atomic(directory / 'state.json', service.canonical(reported_unknown).encode())
        still_unknown = client.get('/api/v1/runs/' + run['runId']).json()
        assert still_unknown['state'] == 'unknown' and still_unknown['reason'] == reason
    finally:
        service.atomic(directory / 'state.json', original_state)
    recovered = client.get('/api/v1/runs/' + run['runId']).json()
    assert recovered['state'] == 'running'
    assert 'reason' not in recovered
    assert recovered['stateVersion'] == run['stateVersion']
    assert recovered['observationVersion'] > still_unknown['observationVersion'] >= unknown['observationVersion']
    assert studio.runs.children[run['runId']] is worker and worker.poll() is None
    assert snapshot.read_bytes() == immutable
    assert studio.projects.read(project['projectId']) == project
    _, pause = command(client, recovered, 'pause')
    paused = wait_state(client, run['runId'], 'paused')
    assert_completed(client, pause)
    for _ in range(3):
        stable = client.get('/api/v1/runs/' + run['runId']).json()
        assert stable['observationVersion'] == paused['observationVersion']
    command(client, paused, 'cancel')
    ended = wait_state(client, run['runId'], 'stopped')
    assert ended['cleanup'] == ended['evidence'] == 'complete'
    assert len(studio.store.all('run')) == 1

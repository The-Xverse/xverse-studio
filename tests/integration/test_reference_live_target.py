"""Owned native live model input; frozen XDL configuration is never rewritten."""

from copy import deepcopy
import hashlib
import hmac
import json
import sys
import time

import psutil
import pytest

from xverse_studio.xdl import XDLAdapter, reference_configuration
from xverse_studio.xdl.examples import reference_resources, dump_yaml, PROFILE_NAMESPACE
from xverse_studio.storage.core import canonical, digest
from test_reference_pause import wait_state, command, assert_completed, records


def live_documents():
    return {k: dump_yaml(v) for k, v in reference_resources(live_controls=True).items()}


def live_run(client, *, admitted=True):
    studio = client.app.state.studio
    project = studio.projects.create("Owned live target", documents=live_documents())
    checked = client.post(f"/api/v1/projects/{project['projectId']}/preflights", json={"revision": project["revision"]})
    assert checked.status_code == 200 and checked.json()["status"] == "ready", checked.text
    pf = checked.json()
    response = client.post('/api/v1/runs', headers={'Idempotency-Key': 'live-start'},
                           json={'snapshotId': pf['snapshotId'], 'preflightId': pf['preflightId']})
    assert response.status_code == 202, response.text
    run = wait_state(client, response.json()['runId'], 'running')
    assert ('set_parameter' in run['capabilities']) is admitted
    directory = studio.runs.directory(run['runId'])
    child = studio.runs.children[run['runId']]
    process = psutil.Process(child.pid)
    known = studio.store.get('run', run['runId'])
    state = json.loads((directory/'state.json').read_text())
    assert process.create_time() == known['createTime'] == state['createTime'] and child.poll() is None
    assert process.cmdline() == [sys.executable, '-I', '-m', 'xverse_studio.providers.worker', str(directory)]
    assert digest((directory/'owner.key').read_bytes()) == known['ownerDigest'] == state['ownerDigest']
    snapshot = studio.store.root/'snapshots'/run['snapshotId']/'snapshot.json'
    return project, run, directory, snapshot, child


@pytest.mark.parametrize('missing', ['operation', 'schema', 'nonphysical_authority'])
def test_live_target_requires_frozen_scoped_capability(client, monkeypatch, missing):
    from xverse_studio.providers.registry import descriptors
    from xverse_studio.runs import service
    rows = deepcopy(descriptors())
    reference = rows[0]
    capability = next(r for r in reference['capabilityRecords'] if r['kind'] == 'set_parameter')
    if missing == 'operation':
        reference['operations'].remove('set_parameter')
    elif missing == 'schema':
        capability['parametersSchema']['additionalProperties'] = True
    else:
        capability['physicalEffects'] = True
    monkeypatch.setattr(service, 'descriptors', lambda: rows)
    _, run, directory, snapshot, child = live_run(client, admitted=False)
    immutable = snapshot.read_bytes()
    response = client.post(f"/api/v1/runs/{run['runId']}/commands", headers={'Idempotency-Key': 'unadmitted'},
                           json={'kind': 'set_parameter', 'expectedStateVersion': run['stateVersion'],
                                 'parameters': {'inputId': 'target', 'expectedValue': 1, 'value': 2}})
    assert response.status_code == 422 and response.json()['code'] == 'CAPABILITY_UNSUPPORTED'
    assert not (directory/'command.json').exists()
    _, cancelled = command(client, run, 'cancel')
    wait_state(client, run['runId'], 'stopped')
    assert_completed(client, cancelled)
    assert child.wait(timeout=5) == 0 and snapshot.read_bytes() == immutable
    assert not any(r['type']=='command.completed' and r['payload'].get('kind')=='set_parameter' for r in records(directory))


@pytest.mark.parametrize('fault,code', [('old_value', 'LIVE_INPUT_CONFLICT'),
    ('bounds', 'LIVE_INPUT_INVALID'), ('principal', 'LIVE_INPUT_AUTHORITY_INVALID'),
    ('state_version', 'COMMAND_STATE_CONFLICT')])
def test_worker_independently_refuses_invalid_owner_signed_live_change(client, monkeypatch, fault, code):
    from xverse_studio.runs import service
    _, run, directory, snapshot, child = live_run(client)
    immutable = snapshot.read_bytes()
    _, pause = command(client, run, 'pause')
    paused = wait_state(client, run['runId'], 'paused')
    assert_completed(client, pause)
    original = service.atomic
    injected = []

    def fault_mailbox(path, body):
        if path == directory/'command.json':
            value = json.loads(body)
            if value['kind'] == 'set_parameter':
                value.pop('signature')
                if fault == 'old_value': value['parameters']['expectedValue'] = 3
                elif fault == 'bounds': value['parameters']['value'] = 101
                elif fault == 'principal': value['principal'] = ''
                else: value['expectedStateVersion'] -= 1
                value['signature'] = hmac.new((directory/'owner.key').read_bytes(), canonical(value).encode(), hashlib.sha256).hexdigest()
                injected.append(value['operationId'])
                return original(path, canonical(value).encode())
        return original(path, body)

    monkeypatch.setattr(service, 'atomic', fault_mailbox)
    response = client.post(f"/api/v1/runs/{run['runId']}/commands", headers={'Idempotency-Key': 'signed-invalid'},
        json={'kind': 'set_parameter', 'expectedStateVersion': paused['stateVersion'],
              'parameters': {'inputId': 'target', 'expectedValue': 1, 'value': 2}})
    assert response.status_code == 202, response.text
    receipt = response.json()
    deadline = time.monotonic()+5
    while time.monotonic()<deadline:
        current = client.get('/api/v1/runs/'+run['runId']).json()
        outcome = client.get('/api/v1/operations/'+receipt['operationId']).json()
        if outcome['status'] == 'failed': break
        time.sleep(.02)
    assert outcome['status'] == 'failed' and outcome['code'] == code
    assert injected == [receipt['operationId']]
    assert current['stateVersion'] == paused['stateVersion'] and current['liveValues']['target'] == 1
    assert current['liveMutationCount'] == 0
    assert any(r['type']=='command.failed' and r['payload']['operationId']==receipt['operationId'] for r in records(directory))
    assert not any(r['type']=='command.completed' and r['payload']['operationId']==receipt['operationId'] for r in records(directory))
    command(client, current, 'cancel')
    wait_state(client, run['runId'], 'stopped')
    assert child.wait(timeout=5) == 0 and snapshot.read_bytes() == immutable


def wait_mutation(client, run, value):
    deadline = time.monotonic()+10
    while time.monotonic() < deadline:
        current = client.get('/api/v1/runs/'+run['runId']).json()
        if current.get('liveValues', {}).get('target') == value:
            return current
        assert current['state'] not in ('failed', 'unknown'), current
        time.sleep(.02)
    raise AssertionError(current)


def test_live_profile_has_authoritative_identity_and_closed_model_input_contract():
    docs = live_documents()
    compiled = XDLAdapter().compile(docs)
    assert compiled['valid'], compiled
    config = reference_configuration(docs, compiled)
    assert config['liveInputs']['target'] == {
        'id': 'target', 'initialParameterId': 'target', 'mutable': True,
        'valueType': 'number', 'unit': '1', 'minimum': -100, 'maximum': 100,
    }
    ordinary = {k: dump_yaml(v) for k,v in reference_resources().items()}
    assert 'liveInputs' not in reference_configuration(ordinary)
    assert compiled['semanticDigest'] != XDLAdapter().compile(ordinary)['semanticDigest']


def test_binding_live_schema_alone_cannot_activate_a_model_input(client):
    project = client.post('/api/v1/projects', json={'name': 'Schema is not a control'}).json()
    entry = next(r for r in client.get('/api/v1/profiles').json()['items'] if r['namespace']=='io.xverse.studio.reference-controls')
    bound = client.post(f"/api/v1/projects/{project['projectId']}/profile-bindings", headers={'If-Match': str(project['revision'])},
        json={'baseRevision': project['revision'], 'profiles': [{k: entry[k] for k in ('profileId','version','schemaDigest','presentationDigest')}]})
    assert bound.status_code == 200, bound.text
    sources = client.app.state.studio.projects.sources(bound.json())
    config = reference_configuration(sources)
    assert 'liveInputs' not in config
    checked = client.post(f"/api/v1/projects/{project['projectId']}/preflights", json={'revision':bound.json()['revision']})
    assert checked.status_code == 200 and checked.json()['status'] == 'ready', checked.text
    assert client.app.state.studio.runs.children == {}


def test_running_live_change_drives_the_next_actual_model_step(client):
    _, run, directory, snapshot, child = live_run(client)
    immutable = snapshot.read_bytes()
    response = client.post(f"/api/v1/runs/{run['runId']}/commands", headers={'Idempotency-Key': 'running-change'},
        json={'kind': 'set_parameter', 'expectedStateVersion': run['stateVersion'],
              'parameters': {'inputId': 'target', 'expectedValue': 1, 'value': 2}})
    assert response.status_code == 202, response.text
    current = wait_mutation(client, run, 2)
    assert current['state'] == 'running' and current['stateVersion'] == run['stateVersion']+1
    deadline = time.monotonic()+5
    while time.monotonic()<deadline:
        samples = [r for r in records(directory) if r['type']=='observation.available' and r['payload']['values']['target']==2]
        if len(samples)>=2: break
        time.sleep(.02)
    assert len(samples)>=2
    first, second = [r['payload']['values'] for r in samples[:2]]
    assert first['control'] == pytest.approx(.8*(2-first['measured']))
    assert second['value'] == pytest.approx(first['value']+first['control']*.1)
    completion = next(r for r in records(directory) if r['type']=='command.completed' and r['payload']['operationId']==response.json()['operationId'])
    assert completion['sourceTime'] == samples[0]['sourceTime']
    command(client, current, 'stop')
    wait_state(client, run['runId'], 'stopped')
    assert child.wait(timeout=5) == 0 and snapshot.read_bytes() == immutable


def test_pending_live_change_serializes_other_commands_and_retains_original_payload(client, monkeypatch):
    from xverse_studio.runs import service
    _, run, directory, snapshot, child = live_run(client)
    immutable = snapshot.read_bytes()
    command(client, run, 'pause')
    paused = wait_state(client, run['runId'], 'paused')
    original = service.atomic
    held = []

    def hold_mailbox(path, body):
        if path == directory/'command.json' and json.loads(body)['kind']=='set_parameter':
            held.append((path,body))
            return
        return original(path,body)

    monkeypatch.setattr(service, 'atomic', hold_mailbox)
    body = {'kind': 'set_parameter', 'expectedStateVersion': paused['stateVersion'],
            'parameters': {'inputId': 'target', 'expectedValue': 1, 'value': 2}}
    headers = {'Idempotency-Key': 'held-live-change'}
    endpoint = f"/api/v1/runs/{run['runId']}/commands"
    accepted = client.post(endpoint, headers=headers, json=body)
    assert accepted.status_code == 202 and len(held)==1
    assert client.post(endpoint, headers=headers, json=body).json()==accepted.json()
    assert len(held)==1
    different = {**body, 'parameters': {**body['parameters'], 'value': 3}}
    conflict = client.post(endpoint, headers=headers, json=different)
    assert conflict.status_code == 409 and conflict.json()['code']=='IDEMPOTENCY_CONFLICT'
    blocked = client.post(endpoint, headers={'Idempotency-Key':'competing-live'}, json=different)
    assert blocked.status_code == 409 and blocked.json()['code']=='STATE_CONFLICT'
    assert client.get('/api/v1/runs/'+run['runId']).json()['liveMutationCount']==0
    operation = client.get('/api/v1/operations/'+accepted.json()['operationId']).json()
    assert operation['parameters']==body['parameters'] and operation['principal']=='local-operator'
    original(*held[0])
    current = wait_mutation(client,run,2)
    assert current['liveMutationCount']==1
    assert client.post(endpoint,headers=headers,json=body).json()==accepted.json()
    assert len(held)==1
    command(client,current,'cancel')
    wait_state(client,run['runId'],'stopped')
    assert child.wait(timeout=5)==0 and snapshot.read_bytes()==immutable


def test_native_live_target_changes_actual_samples_with_provenance_and_immutable_inputs(client, record_property):
    project, run, directory, snapshot, child = live_run(client)
    immutable = snapshot.read_bytes()
    _, paused_receipt = command(client, run, 'pause')
    paused = wait_state(client, run['runId'], 'paused')
    assert_completed(client, paused_receipt)
    payload = {'kind': 'set_parameter', 'expectedStateVersion': paused['stateVersion'],
               'parameters': {'inputId': 'target', 'expectedValue': 1.0, 'value': 2.0}}
    headers = {'Idempotency-Key': 'live-target-once'}
    response = client.post(f"/api/v1/runs/{run['runId']}/commands", headers=headers, json=payload)
    assert response.status_code == 202, response.text
    receipt = response.json()
    changed = wait_mutation(client, run, 2.0)
    assert changed['state'] == 'paused' and changed['stateVersion'] == paused['stateVersion']+1
    assert changed['liveMutationCount'] == 1
    assert client.post(f"/api/v1/runs/{run['runId']}/commands", headers=headers, json=payload).json() == receipt
    op = client.get('/api/v1/operations/'+receipt['operationId']).json()
    assert op['status'] == 'completed'
    mutation = op['result']['mutation']
    assert mutation['inputId'] == 'target' and mutation['oldValue'] == 1.0 and mutation['newValue'] == 2.0
    assert mutation['authority'] == {'principal': 'local-operator', 'scope': 'native-backend-owned', 'physicalEffects': False}
    assert isinstance(mutation['recordedAt'], (int,float)) and mutation['recordedAt'] > 0
    completed = [r for r in records(directory) if r['type']=='command.completed' and r['payload']['operationId']==receipt['operationId']]
    assert len(completed)==1 and completed[0]['payload']['mutation']==mutation
    assert completed[0]['sourceTime']==mutation['sourceTime']
    # A later draft edit cannot replace either the initial configuration or live input.
    edited = client.post(f"/api/v1/projects/{project['projectId']}/edits", headers={'If-Match':str(project['revision'])},
                         json={'baseRevision':project['revision'],'edits':[{'kind':'set_parameter','parameterId':'target','value':3.0}]})
    assert edited.status_code==200, edited.text
    _, resumed = command(client, changed, 'resume')
    running = wait_state(client, run['runId'], 'running')
    assert_completed(client, resumed)
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        samples=[r for r in records(directory) if r['type']=='observation.available' and r['payload']['values']['target']==2.0]
        if samples:break
        time.sleep(.02)
    assert samples and all(r['payload']['values']['target']!=3.0 for r in records(directory) if r['type']=='observation.available')
    projected=client.get(f"/api/v1/runs/{run['runId']}/observations",params={'field':'target'}).json()
    assert projected['integrity']=='verified_prefix' and projected['clockDomain']=='simulation-time'
    assert any(item['values']['target']==2.0 for item in projected['items'])
    _, stopped = command(client, running, 'stop')
    ended = wait_state(client, run['runId'], 'stopped')
    assert_completed(client, stopped)
    assert child.wait(timeout=5)==0 and ended['cleanup']==ended['evidence']=='complete'
    assert client.get(f"/api/v1/runs/{run['runId']}/observations",params={'field':'target'}).json()['integrity']=='valid'
    assert snapshot.read_bytes()==immutable and json.loads(immutable)['configuration']['target']==1.0
    assert ended['liveValues']['target']==2.0 and ended['liveMutationCount']==1
    assert len(client.app.state.studio.store.all('run'))==1
    record_property('owned_live_target',json.dumps(dict(scope='Actual owned native worker; no equipment',pid=child.pid,
        snapshotId=run['snapshotId'],originalArgvBirthOwnerVerified=True,oldValue=1,newValue=2,draftValue=3,
        sameKeyOneMutation=True,unchangedSnapshot=True,appliedSamples=len(samples))))


def test_native_live_target_refuses_unsupported_bounds_old_value_and_stale_state_without_effects(client):
    _, run, directory, _, _ = live_run(client)
    command(client,run,'pause');paused=wait_state(client,run['runId'],'paused')
    before=(directory/'command.json').read_bytes();journal=(directory/'evidence.jsonl').read_bytes()
    op_count=len(client.app.state.studio.store.all('operation'))
    invalid=[{'inputId':'initial','expectedValue':0,'value':1},
             {'inputId':'target','expectedValue':1,'value':101},
             {'inputId':'target','expectedValue':1,'value':True},
             {'inputId':'target','expectedValue':2,'value':3},
             {'inputId':'target','expectedValue':1,'value':2,'authority':'operator-supplied'},
             {'inputId':'target','expectedValue':1,'value':10**400}]
    for i,params in enumerate(invalid):
        r=client.post(f"/api/v1/runs/{run['runId']}/commands",headers={'Idempotency-Key':'invalid-live-'+str(i)},
                      json={'kind':'set_parameter','expectedStateVersion':paused['stateVersion'],'parameters':params})
        assert r.status_code in (409,422),r.text
    r=client.post(f"/api/v1/runs/{run['runId']}/commands",headers={'Idempotency-Key':'stale-live'},
                  json={'kind':'set_parameter','expectedStateVersion':0,'parameters':{'inputId':'target','expectedValue':1,'value':2}})
    assert r.status_code==409
    observed=client.get('/api/v1/runs/'+run['runId']).json()
    assert observed['liveValues']=={'target':1.0} and observed['liveMutationCount']==0
    assert observed['stateVersion']==paused['stateVersion']
    assert len(client.app.state.studio.store.all('operation'))==op_count
    assert (directory/'command.json').read_bytes()==before and (directory/'evidence.jsonl').read_bytes()==journal
    command(client,observed,'cancel');wait_state(client,run['runId'],'stopped')


@pytest.mark.parametrize('fault', ['constant', 'profile_version', 'unsupported_input'])
def test_live_profile_refuses_constant_or_unadmitted_semantics_without_launch(client, monkeypatch, fault):
    from xverse_studio.runs import service as module
    resources=reference_resources(live_controls=True)
    if fault=='constant':
        target=next(p for p in resources['scenario.xdl.yaml']['extensions'][PROFILE_NAMESPACE]['parameters'] if p['id']=='target')
        target['mutability']='constant'
    elif fault=='profile_version':
        resources['live-controls-profile.xdl.yaml']['metadata']['version']='2.0.0'
    else:
        resources['scenario.xdl.yaml']['extensions']['io.xverse.studio.reference-controls']['inputs'][0]['id']='initial'
    studio=client.app.state.studio
    project=studio.projects.create('Unsupported live input',documents={k:dump_yaml(v) for k,v in resources.items()})
    def no_launch(*args,**kwargs):pytest.fail('Unadmitted live semantics cannot launch a worker')
    monkeypatch.setattr(module.subprocess,'Popen',no_launch)
    response=client.post(f"/api/v1/projects/{project['projectId']}/preflights",json={'revision':project['revision']})
    assert response.status_code==200 and response.json()['status']=='blocked'
    assert studio.store.all('run')==[]
    assert studio.projects.read(project['projectId'])==project


def test_native_live_mutation_budget_is_frozen_and_enforced_without_33rd_effect(client):
    _,run,directory,snapshot,child=live_run(client)
    original=snapshot.read_bytes()
    command(client,run,'pause');current=wait_state(client,run['runId'],'paused')
    assert current['controlLimits']['maxLiveMutations']==32
    for index in range(32):
        old=current['liveValues']['target'];value=2.0 if old==1.0 else 1.0
        body={'kind':'set_parameter','expectedStateVersion':current['stateVersion'],
              'parameters':{'inputId':'target','expectedValue':old,'value':value}}
        response=client.post(f"/api/v1/runs/{run['runId']}/commands",headers={'Idempotency-Key':'budget-'+str(index)},json=body)
        assert response.status_code==202,response.text
        current=wait_mutation(client,current,value)
        assert current['liveMutationCount']==index+1
    before=(directory/'command.json').read_bytes();op_count=len(client.app.state.studio.store.all('operation'))
    old=current['liveValues']['target']
    response=client.post(f"/api/v1/runs/{run['runId']}/commands",headers={'Idempotency-Key':'budget-overflow'},
        json={'kind':'set_parameter','expectedStateVersion':current['stateVersion'],
              'parameters':{'inputId':'target','expectedValue':old,'value':3.0}})
    assert response.status_code==422 and response.json()['code']=='LIVE_INPUT_LIMIT'
    assert len(client.app.state.studio.store.all('operation'))==op_count
    assert (directory/'command.json').read_bytes()==before and snapshot.read_bytes()==original
    applied=[e for e in records(directory) if e['type']=='command.completed' and 'mutation' in e['payload']]
    assert len(applied)==32
    command(client,current,'cancel');ended=wait_state(client,run['runId'],'stopped')
    assert child.wait(timeout=5)==0 and ended['liveMutationCount']==32

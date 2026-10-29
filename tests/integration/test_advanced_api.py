"""Actual local HTTP/provider checks. These establish owned reference scope only."""
import time
from io import StringIO

from ruamel.yaml import YAML


def prepared(client):
    response = client.post('/api/v1/projects', json={'name': 'Advanced owned reference', 'blueprintRef': 'reference-process-control'})
    assert response.status_code == 201, response.text
    project = response.json()
    scenario_id, scenario = next((k, v) for k, v in project['documents'].items() if 'scenario' in v['path'])
    yaml = YAML()
    resource = yaml.load(scenario['content'])
    parameters = resource['extensions']['io.xverse.experiment']['parameters']
    next(p for p in parameters if p['id'] == 'duration')['value'] = .2
    resource['extensions']['io.xverse.studio.experiments']['definitions'][0]['window']['endTick'] = '200000'
    stream = StringIO(); yaml.dump(resource, stream)
    saved = client.put(f"/api/v1/projects/{project['projectId']}/documents/{scenario_id}", headers={'If-Match': str(project['revision'])}, json={'content': stream.getvalue(), 'format': 'yaml'})
    assert saved.status_code == 200, saved.text
    project = saved.json()
    pf = client.post(f"/api/v1/projects/{project['projectId']}/preflights", json={'revision': project['revision']})
    assert pf.status_code == 200 and pf.json()['status'] == 'ready', pf.text
    return project, pf.json()


def wait_run(client, rid):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        result = client.get('/api/v1/runs/' + rid)
        assert result.status_code == 200, result.text
        if result.json()['state'] in {'stopped', 'failed', 'unknown'}:
            return result.json()
        time.sleep(.1)
    raise AssertionError('Owned reference worker did not reach terminal state')


def start(client, pf, key='advanced-run'):
    response = client.post('/api/v1/runs', headers={'Idempotency-Key': key}, json={'snapshotId': pf['snapshotId'], 'preflightId': pf['preflightId']})
    assert response.status_code == 202, response.text
    return response.json()['runId']


def test_snapshot_evaluation_api_uses_frozen_definition_and_canonical_evidence(client):
    project, pf = prepared(client)
    rid = start(client, pf)
    result = wait_run(client, rid)
    assert result['state'] == 'stopped', result
    definitions = client.get(f'/api/v1/runs/{rid}/definitions').json()['items']
    assert len(definitions) == 1
    definition = definitions[0]
    payload = {'snapshotId': pf['snapshotId'], 'definitionRef': definition['definitionRef'], 'definitionDigest': definition['definitionDigest'], 'evidenceRefs': [rid + ':reference-journal']}
    response = client.post(f'/api/v1/runs/{rid}/evaluations', headers={'Idempotency-Key': 'evaluation'}, json=payload)
    assert response.status_code == 202, response.text
    row = client.get('/api/v1/evaluations/' + response.json()['evaluationId']).json()
    assert (row['status'], row['verdict']) == ('complete', 'pass'), row
    retry = client.post(f'/api/v1/runs/{rid}/evaluations', headers={'Idempotency-Key': 'evaluation'}, json=payload)
    assert retry.json()['evaluationId'] == row['evaluationId']
    tampered = client.post(f'/api/v1/runs/{rid}/evaluations', headers={'Idempotency-Key': 'tampered'}, json={**payload, 'definitionDigest': 'sha256:wrong'})
    assert tampered.status_code == 422
    wrong_evidence = client.post(f'/api/v1/runs/{rid}/evaluations', headers={'Idempotency-Key': 'wrong-evidence'}, json={**payload, 'evidenceRefs': ['different-run:reference-journal']})
    assert wrong_evidence.status_code == 422


def test_campaign_scheduler_runs_immutable_parameter_children_without_browser_start(client):
    _, pf = prepared(client)
    payload = {'snapshotId': pf['snapshotId'], 'matrix': {'gain': [.8, 1.6]}, 'budget': {'maxRuns': 2, 'maxTotalSeconds': 1}, 'concurrency': 1}
    response = client.post('/api/v1/campaigns', headers={'Idempotency-Key': 'finite-campaign'}, json=payload)
    assert response.status_code == 202, response.text
    cid = response.json()['campaignId']
    retry = client.post('/api/v1/campaigns', headers={'Idempotency-Key': 'finite-campaign'}, json=payload)
    assert retry.json()['campaignId'] == cid
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        state = client.get('/api/v1/campaigns/' + cid).json()
        if state['status'] == 'complete':
            break
        time.sleep(.2)
    assert state['status'] == 'complete', state
    assert [c['state'] for c in state['children']] == ['stopped', 'stopped'], state
    assert len({c['runId'] for c in state['children']}) == 2
    snapshots = [client.get('/api/v1/runs/' + c['runId']).json()['snapshotId'] for c in state['children']]
    assert len(set(snapshots)) == 2 and pf['snapshotId'] not in snapshots
    compare = client.post('/api/v1/comparisons', json={'leftRunId': state['children'][0]['runId'], 'rightRunId': state['children'][1]['runId']})
    assert compare.status_code == 200, compare.text
    assert compare.json()['rerunRequiresFreshAdmission'] is True
    assert any(d['field'] == 'parameters' for d in compare.json()['differences'])


def test_annotations_revision_retention_dependencies_and_empty_lab(client):
    _, pf = prepared(client)
    rid = start(client, pf)
    assert wait_run(client, rid)['state'] == 'stopped'
    body = {'kind': 'comment', 'text': 'Owned reference observation', 'evidenceRefs': [rid + ':reference-journal']}
    response = client.post(f'/api/v1/runs/{rid}/annotations', json=body)
    assert response.status_code == 201, response.text
    annotation = response.json()
    changed = client.put('/api/v1/annotations/' + annotation['annotationId'], headers={'If-Match': '1'}, json={**body, 'text': 'Reviewed observation', 'revision': 1})
    assert changed.status_code == 200 and changed.json()['revision'] == 2
    stale = client.put('/api/v1/annotations/' + annotation['annotationId'], headers={'If-Match': '1'}, json={**body, 'revision': 1})
    assert stale.status_code == 412
    plan = client.post('/api/v1/retention/plans', json={'runIds': [rid]})
    assert plan.status_code == 200, plan.text
    assert plan.json()['removals'] == []
    assert 'ANNOTATION_DEPENDS_ON_EVIDENCE' in plan.json()['protected'][0]['reasons']
    assert client.get('/api/v1/assets').json()['items'] == []
    reservation = client.post('/api/v1/assets/unapproved-device/reservations', headers={'Idempotency-Key': 'no-device'}, json={})
    assert reservation.status_code == 503


def test_stale_retention_and_revisioned_annotation_reference_negatives(client):
    _, pf = prepared(client)
    rid = start(client, pf)
    assert wait_run(client, rid)['state'] == 'stopped'
    plan = client.post('/api/v1/retention/plans', json={'runIds':[rid]}).json()
    annotation = client.post(f'/api/v1/runs/{rid}/annotations', json={'kind':'comment','text':'Protect this evidence'}).json()
    stale = client.post('/api/v1/retention/plans/' + plan['planId'] + '/apply', headers={'Idempotency-Key':'stale-plan'}, json={'fingerprint':plan['fingerprint']})
    assert stale.status_code == 409, stale.text
    invalid = client.put('/api/v1/annotations/' + annotation['annotationId'], headers={'If-Match':'1'}, json={'revision':1,'kind':'comment','text':'Bad reference','evidenceRefs':['other-run:reference-journal']})
    assert invalid.status_code == 422


def test_retention_apply_commits_intent_and_does_not_replay_effects(client):
    _, pf = prepared(client)
    rid = start(client, pf)
    assert wait_run(client,rid)['state'] == 'stopped'
    plan = client.post('/api/v1/retention/plans', json={'runIds':[rid]}).json()
    payload = {'fingerprint':plan['fingerprint']}
    path = '/api/v1/retention/plans/' + plan['planId'] + '/apply'
    response = client.post(path, headers={'Idempotency-Key':'remove-owned-run'}, json=payload)
    assert response.status_code == 202, response.text
    assert response.json()['outcomes'] == [{'runId':rid,'status':'removed','snapshotPreserved':True}]
    assert client.post(path, headers={'Idempotency-Key':'remove-owned-run'},json=payload).json() == response.json()
    assert client.app.state.studio.store.get('snapshot',pf['snapshotId'])['snapshotId'] == pf['snapshotId']
    assert client.app.state.studio.store.get('run',rid)['state'] == 'stopped'


def test_restart_marks_interrupted_evaluation_and_retention_unknown_without_replay(tmp_path):
    from xverse_studio.storage.core import Store
    from xverse_studio.api.app import create_app
    store = Store(tmp_path)
    store.put('evaluation','eval-interrupted',{'evaluationId':'eval-interrupted','operationId':'op-evaluation','status':'running','verdict':None})
    store.put('operation','op-evaluation',{'operationId':'op-evaluation','status':'accepted'})
    store.put('retention','ret-interrupted',{'planId':'ret-interrupted','operationId':'op-retention','status':'applying','outcomes':[{'runId':'owned','status':'removed'}]})
    store.put('operation','op-retention',{'operationId':'op-retention','status':'delegated'})
    store.put('operation','op-cancel',{'operationId':'op-cancel','kind':'campaign_cancel','campaignId':'c','status':'accepted'})
    create_app(tmp_path, allowed_hosts=['testserver'], bootstrap_token='restart-token')
    interrupted = store.get('evaluation','eval-interrupted')
    assert interrupted['status'] == 'error' and interrupted['verdict'] is None
    assert store.get('operation','op-evaluation')['status'] == 'failed'
    assert store.get('retention','ret-interrupted')['status'] == 'unknown'
    assert store.get('operation','op-retention')['status'] == 'unknown'
    assert store.get('operation','op-cancel')['status'] == 'unknown'


def test_snapshot_corruption_cannot_resolve_an_evaluation_definition(client):
    _, pf = prepared(client)
    rid = start(client, pf)
    assert wait_run(client,rid)['state'] == 'stopped'
    store = client.app.state.studio.store
    snapshot = store.get('snapshot',pf['snapshotId'])
    snapshot['configuration']['target'] = 99
    store.put('snapshot',pf['snapshotId'],snapshot)
    result = client.get(f'/api/v1/runs/{rid}/definitions')
    assert result.status_code == 422
    assert result.json()['code'] == 'SNAPSHOT_INTEGRITY_INVALID'


def test_cancelled_campaign_does_not_schedule_pending_children(client):
    _, pf = prepared(client)
    response = client.post('/api/v1/campaigns', headers={'Idempotency-Key':'cancel-campaign'}, json={'snapshotId':pf['snapshotId'],'matrix':{'gain':[.8,1.6,2.4]},'budget':{'maxRuns':3,'maxTotalSeconds':1},'concurrency':1})
    assert response.status_code == 202, response.text
    cid = response.json()['campaignId']
    cancel = client.post('/api/v1/campaigns/' + cid + '/cancel', headers={'Idempotency-Key':'cancel'}, json={})
    assert cancel.status_code == 202, cancel.text
    deadline = time.monotonic()+10
    while time.monotonic() < deadline:
        row = client.get('/api/v1/campaigns/' + cid).json()
        if row['status'] == 'cancelled': break
        time.sleep(.1)
    assert row['status'] == 'cancelled', row
    assert sum(c['state'] == 'cancelled' for c in row['children']) >= 2
    assert not any(c['state'] in {'dispatching','running','pending'} for c in row['children'])


def test_retention_partial_filesystem_failure_does_not_claim_complete(client, monkeypatch):
    import xverse_studio.retention.service as retention_service
    _, pf = prepared(client)
    rid = start(client,pf)
    assert wait_run(client,rid)['state'] == 'stopped'
    plan = client.post('/api/v1/retention/plans',json={'runIds':[rid]}).json()
    def refuse(path): raise OSError('owned injected filesystem refusal')
    monkeypatch.setattr(retention_service.shutil,'rmtree',refuse)
    response = client.post('/api/v1/retention/plans/' + plan['planId'] + '/apply',headers={'Idempotency-Key':'failed-removal'},json={'fingerprint':plan['fingerprint']})
    assert response.status_code == 202, response.text
    assert response.json()['status'] == 'partial'
    assert response.json()['outcomes'][0]['status'] == 'failed'
    assert client.app.state.studio.runs.directory(rid).exists()


def test_corrupted_canonical_evidence_never_yields_pass(client):
    _, pf = prepared(client)
    rid = start(client,pf)
    assert wait_run(client,rid)['state'] == 'stopped'
    definition = client.get(f'/api/v1/runs/{rid}/definitions').json()['items'][0]
    journal = client.app.state.studio.runs.directory(rid) / 'evidence.jsonl'
    journal.write_bytes(journal.read_bytes() + b'corruption\n')
    response = client.post(f'/api/v1/runs/{rid}/evaluations',headers={'Idempotency-Key':'corrupt-evidence'},json={'snapshotId':pf['snapshotId'],'definitionRef':definition['definitionRef'],'definitionDigest':definition['definitionDigest'],'evidenceRefs':[rid+':reference-journal']})
    assert response.status_code == 202, response.text
    result = client.get('/api/v1/evaluations/' + response.json()['evaluationId']).json()
    assert result['status'] == 'complete' and result['verdict'] == 'indeterminate'
    assert result['coverage'] == 'invalid'


def test_campaign_malformed_parameter_values_use_error_envelope(client):
    _,pf = prepared(client)
    response = client.post('/api/v1/campaigns/preview',json={'snapshotId':pf['snapshotId'],'matrix':{'duration':['unsupported']},'budget':{'maxRuns':1}})
    assert response.status_code == 422, response.text
    assert response.json()['code'] == 'INVALID_CAMPAIGN'

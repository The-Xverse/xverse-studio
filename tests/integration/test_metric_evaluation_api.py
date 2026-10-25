"""Actual admitted reference evidence with immutable named metric dependencies."""
from copy import deepcopy
from io import StringIO
import time

import pytest
from ruamel.yaml import YAML

from xverse_studio.assertions import definition_digest


def make_project(client, mode='valid'):
    project=client.post('/api/v1/projects',json={'name':'Metric dependency reference','blueprintRef':'reference-process-control'}).json()
    did,document=next((k,v) for k,v in project['documents'].items() if 'scenario' in v['path'])
    yaml=YAML();resource=yaml.load(document['content'])
    next(p for p in resource['extensions']['io.xverse.experiment']['parameters'] if p['id']=='duration')['value']=.2
    original=resource['extensions']['io.xverse.studio.experiments']['definitions'][0]
    original['window']['endTick']='200000'
    metric={**deepcopy(original),'evaluationId':'peak','kind':'metric','name':'Peak reference state','resultUnit':'1','expression':deepcopy(original['expression']['left'])}
    assertion=deepcopy(original)
    assertion['expression']['left']={'kind':'metric','evaluationRef':{'evaluationId':'peak','version':'1.0','definitionDigest':definition_digest(metric)}}
    if mode=='wrong_pin':assertion['expression']['left']['evaluationRef']['definitionDigest']='sha256:wrong'
    if mode=='missing':assertion['expression']['left']['evaluationRef']['evaluationId']='not-in-snapshot'
    if mode=='wrong_version':assertion['expression']['left']['evaluationRef']['version']='2.0'
    if mode=='cycle':
        other=deepcopy(metric);other['evaluationId']='other-peak';other['expression']={'kind':'metric','evaluationRef':{'evaluationId':'peak','version':'1.0','definitionDigest':'sha256:cycle'}}
        metric['expression']={'kind':'metric','evaluationRef':{'evaluationId':'other-peak','version':'1.0','definitionDigest':'sha256:cycle'}}
        definitions=[metric,other,assertion]
    elif mode=='two':
        second=deepcopy(assertion);second['evaluationId']='second-bound';second['name']='Second bound';second['expression']={'kind':'literal','value':False}
        definitions=[metric,assertion,second]
    elif mode=='chain':
        alias=deepcopy(metric);alias['evaluationId']='peak-alias';alias['expression']={'kind':'metric','evaluationRef':deepcopy(assertion['expression']['left']['evaluationRef'])}
        assertion['expression']['left']['evaluationRef']={'evaluationId':'peak-alias','version':'1.0','definitionDigest':definition_digest(alias)}
        definitions=[metric,alias,assertion]
    else:definitions=[metric,assertion]
    resource['extensions']['io.xverse.studio.experiments']['definitions']=definitions
    stream=StringIO();yaml.dump(resource,stream)
    response=client.put(f"/api/v1/projects/{project['projectId']}/documents/{did}",headers={'If-Match':str(project['revision'])},json={'content':stream.getvalue(),'format':'yaml'})
    assert response.status_code==200,response.text
    project=response.json()
    pf=client.post(f"/api/v1/projects/{project['projectId']}/preflights",json={'revision':project['revision']})
    assert pf.status_code==200,pf.text
    return project,pf.json(),assertion


def start(client,pf):
    result=client.post('/api/v1/runs',headers={'Idempotency-Key':'metric-run'},json={'snapshotId':pf['snapshotId'],'preflightId':pf['preflightId']})
    assert result.status_code==202,result.text
    rid=result.json()['runId'];deadline=time.monotonic()+20
    while time.monotonic()<deadline:
        run=client.get('/api/v1/runs/'+rid).json()
        if run['state'] in ('stopped','failed','unknown'):break
        time.sleep(.1)
    assert run['state']=='stopped',run
    return rid


def evaluate(client,rid,pf,key='metric-evaluation'):
    definitions=client.get(f'/api/v1/runs/{rid}/definitions')
    assert definitions.status_code==200,definitions.text
    selected=next(d for d in definitions.json()['items'] if d['definition']['kind']=='assertion')
    return client.post(f'/api/v1/runs/{rid}/evaluations',headers={'Idempotency-Key':key},json={'snapshotId':pf['snapshotId'],'definitionRef':selected['definitionRef'],'definitionDigest':selected['definitionDigest'],'evidenceRefs':[rid+':reference-journal']})


def test_named_metric_is_evaluated_and_persisted_before_its_assertion(client,monkeypatch):
    import xverse_studio.api.advanced as facade
    original_evaluate=facade.evaluate
    def inspect_then_evaluate(definition,*args,**kwargs):
        rows=client.app.state.studio.store.all('evaluation')
        current=next(r for r in rows if r['definitionRef']==definition['evaluationId'] and r['status']=='running')
        assert current['definitionDigest']==definition_digest(definition)
        assert current['inputEvidenceDigests']
        assert current['evaluatorIdentity']['implementationDigest'].startswith('sha256:')
        return original_evaluate(definition,*args,**kwargs)
    monkeypatch.setattr(facade,'evaluate',inspect_then_evaluate)
    _,pf,_=make_project(client)
    assert pf['status']=='ready',pf
    rid=start(client,pf)
    response=evaluate(client,rid,pf)
    assert response.status_code==202,response.text
    assertion=client.get('/api/v1/evaluations/'+response.json()['evaluationId']).json()
    assert (assertion['status'],assertion['verdict'])==('complete','pass'),assertion
    rows=client.get(f'/api/v1/runs/{rid}/evaluations').json()['items']
    metric=next(row for row in rows if row['definitionRef']=='peak')
    assert metric['status']=='complete' and metric['verdict'] is None and metric['coverage']=='complete'
    assert metric['snapshotId']==assertion['snapshotId']==pf['snapshotId']
    assert metric['evidenceDigests']==assertion['evidenceDigests']
    assert assertion['dependencyResults'][0]['evaluationId']==metric['evaluationId']
    assert assertion['dependencyResults'][0]['definitionDigest']==metric['definitionDigest']
    assert metric['completedAt']<=assertion['completedAt']
    assert metric['evaluatorIdentity']['implementationDigest'].startswith('sha256:')
    assert metric['inputEvidenceDigests']==assertion['inputEvidenceDigests']==metric['evidenceDigests']
    from xverse_studio.storage.core import digest
    assert assertion['dependencyResults'][0]['resultDigest']==digest(metric)
    retry=evaluate(client,rid,pf)
    assert retry.json()['evaluationId']==assertion['evaluationId']
    assert len(client.get(f'/api/v1/runs/{rid}/evaluations').json()['items'])==2
    conflict=client.post(f'/api/v1/runs/{rid}/evaluations',headers={'Idempotency-Key':'metric-evaluation'},json={'snapshotId':pf['snapshotId'],'definitionRef':assertion['definitionRef'],'definitionDigest':'sha256:changed','evidenceRefs':[rid+':reference-journal']})
    assert conflict.status_code==409 and conflict.json()['code']=='IDEMPOTENCY_CONFLICT'


@pytest.mark.parametrize('mode,code',[('wrong_pin','METRIC_IDENTITY_MISMATCH'),('wrong_version','METRIC_IDENTITY_MISMATCH'),('missing','METRIC_REFERENCE_UNRESOLVED'),('cycle','METRIC_DEPENDENCY_CYCLE')])
def test_bad_frozen_metric_graph_rejects_without_evaluation_jobs(client,mode,code):
    _,pf,_=make_project(client,mode)
    if pf['status']=='blocked':
        assert any(d['code'] in {code,'CAPABILITY_UNSUPPORTED'} for d in pf['diagnostics']),pf
        return
    rid=start(client,pf)
    response=client.get(f'/api/v1/runs/{rid}/definitions')
    assert response.status_code==422,response.text
    assert response.json()['code']==code
    assert client.get(f'/api/v1/runs/{rid}/evaluations').json()['items']==[]


def test_invalid_metric_inputs_propagate_indeterminate_not_pass(client):
    _,pf,_=make_project(client)
    rid=start(client,pf)
    path=client.app.state.studio.runs.directory(rid)/'evidence.jsonl'
    path.write_bytes(path.read_bytes()+b'corrupted\n')
    response=evaluate(client,rid,pf)
    assert response.status_code==202,response.text
    assertion=client.get('/api/v1/evaluations/'+response.json()['evaluationId']).json()
    assert assertion['status']=='complete' and assertion['verdict']=='indeterminate'
    metric=next(row for row in client.get(f'/api/v1/runs/{rid}/evaluations').json()['items'] if row['definitionRef']=='peak')
    assert metric['coverage']!='complete' and metric['value'] is None


def test_transitive_metric_dependencies_are_frozen_and_evaluated_in_order(client):
    _,pf,_=make_project(client,'chain')
    rid=start(client,pf)
    response=evaluate(client,rid,pf)
    assert response.status_code==202,response.text
    result=client.get('/api/v1/evaluations/'+response.json()['evaluationId']).json()
    assert result['verdict']=='pass',result
    rows=client.get(f'/api/v1/runs/{rid}/evaluations').json()['items']
    assert len(rows)==3
    peak=next(r for r in rows if r['definitionRef']=='peak')
    alias=next(r for r in rows if r['definitionRef']=='peak-alias')
    assert alias['dependencyResults'][0]['evaluationId']==peak['evaluationId']
    assert result['dependencyResults'][0]['evaluationId']==alias['evaluationId']
    assert peak['completedAt']<=alias['completedAt']<=result['completedAt']


def test_missing_canonical_metric_input_remains_indeterminate(client):
    _,pf,_=make_project(client)
    rid=start(client,pf)
    (client.app.state.studio.runs.directory(rid)/'evidence.jsonl').unlink()
    response=evaluate(client,rid,pf)
    assert response.status_code==202,response.text
    result=client.get('/api/v1/evaluations/'+response.json()['evaluationId']).json()
    assert result['status']=='complete' and result['verdict']=='indeterminate'
    metric=next(row for row in client.get(f'/api/v1/runs/{rid}/evaluations').json()['items'] if row['definitionRef']=='peak')
    assert metric['coverage']!='complete' and metric['value'] is None


def test_run_assessment_projection_before_after_and_latest_error(client):
    _,pf,_=make_project(client)
    rid=start(client,pf)
    before=client.get('/api/v1/runs/'+rid).json()
    assert before['evaluation']=='not_started' and before['verdict'] is None
    response=evaluate(client,rid,pf)
    assert response.status_code==202,response.text
    after=client.get('/api/v1/runs/'+rid).json()
    assert after['evaluation']=='complete' and after['verdict']=='pass',after
    assert after['evaluationSummary']['metricJobs'][0]['status']=='complete'
    assert after['evaluationSummary']['metricJobs'][0]['verdict'] is None
    assert (after['state'],after['cleanup'])==(before['state'],before['cleanup'])
    # A durable interrupted-evaluator fixture verifies latest-result selection;
    # it does not claim an actually running evaluator or provider failure.
    store=client.app.state.studio.store
    latest=deepcopy(store.get('evaluation',response.json()['evaluationId']))
    latest.update(evaluationId='eval-latest-error',createdAt=time.time()+1,status='error',verdict=None,reasons=['EVALUATION_INTERRUPTED'])
    store.put('evaluation',latest['evaluationId'],latest)
    errored=client.get('/api/v1/runs/'+rid).json()
    assert errored['evaluation']=='error' and errored['verdict']=='indeterminate'
    assert (errored['state'],errored['cleanup'])==(before['state'],before['cleanup'])


def test_run_aggregate_missing_required_and_failure_with_running_fixture(client):
    _,pf,_=make_project(client,'two')
    rid=start(client,pf)
    first=evaluate(client,rid,pf)
    assert first.status_code==202,first.text
    partial=client.get('/api/v1/runs/'+rid).json()
    assert partial['verdict']=='indeterminate'
    assert partial['evaluation']!='running'  # No implicit queued evaluator.
    assert partial['evaluationSummary']['counts']['not_started']==1
    selected=next(d for d in client.get(f'/api/v1/runs/{rid}/definitions').json()['items'] if d['definitionRef']=='second-bound')
    failed=client.post(f'/api/v1/runs/{rid}/evaluations',headers={'Idempotency-Key':'second-failure'},json={'snapshotId':pf['snapshotId'],'definitionRef':selected['definitionRef'],'definitionDigest':selected['definitionDigest'],'evidenceRefs':[rid+':reference-journal']})
    assert failed.status_code==202,failed.text
    store=client.app.state.studio.store
    pending=deepcopy(store.get('evaluation',first.json()['evaluationId']))
    pending.update(evaluationId='eval-running-fixture',createdAt=time.time()+1,status='running',verdict=None)
    store.put('evaluation',pending['evaluationId'],pending)
    aggregate=client.get('/api/v1/runs/'+rid).json()
    assert aggregate['evaluation']=='running' and aggregate['verdict']=='fail'
    assert aggregate['evaluationSummary']['counts']['running']==1
    assert aggregate['state']=='stopped' and aggregate['cleanup']=='complete'

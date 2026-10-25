"""Inert evidence exchange over real owned reference execution and hostile fixtures."""
import base64
import io
import json
import stat
import time
import zipfile
from io import StringIO

import pytest
from ruamel.yaml import YAML

from xverse_studio.storage.core import canonical, digest


def archive(files, *, link=None):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,value in files.items():
            z.writestr(name, value.encode() if isinstance(value,str) else value)
        if link:
            info=zipfile.ZipInfo(link); info.create_system=3; info.external_attr=(stat.S_IFLNK|0o777)<<16
            z.writestr(info,'../../outside')
    return stream.getvalue()


def unpack(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        return {n:z.read(n) for n in z.namelist()}


def rehash(files):
    manifest=json.loads(files['manifest.json'])
    manifest['files']={name:digest(value.encode() if isinstance(value,str) else value) for name,value in files.items() if name!='manifest.json'}
    files['manifest.json']=canonical(manifest)
    return files


def import_bundle(client, data):
    return client.post('/api/v1/evidence/imports',json={'archiveBase64':base64.b64encode(data).decode()})


@pytest.fixture
def exported(client):
    project=client.post('/api/v1/projects',json={'name':'Evidence exchange reference','blueprintRef':'reference-process-control'}).json()
    did,document=next((k,v) for k,v in project['documents'].items() if 'scenario' in v['path'])
    yaml=YAML();resource=yaml.load(document['content'])
    next(p for p in resource['extensions']['io.xverse.experiment']['parameters'] if p['id']=='duration')['value']=.2
    resource['extensions']['io.xverse.studio.experiments']['definitions'][0]['window']['endTick']='200000'
    stream=StringIO();yaml.dump(resource,stream)
    project=client.put(f"/api/v1/projects/{project['projectId']}/documents/{did}",headers={'If-Match':str(project['revision'])},json={'content':stream.getvalue(),'format':'yaml'}).json()
    pf=client.post(f"/api/v1/projects/{project['projectId']}/preflights",json={'revision':project['revision']}).json()
    response=client.post('/api/v1/runs',headers={'Idempotency-Key':'exchange-run'},json={'snapshotId':pf['snapshotId'],'preflightId':pf['preflightId']})
    assert response.status_code==202,response.text
    rid=response.json()['runId'];deadline=time.monotonic()+20
    while time.monotonic()<deadline:
        run=client.get('/api/v1/runs/'+rid).json()
        if run['state'] in ('stopped','failed','unknown'):break
        time.sleep(.1)
    assert run['state']=='stopped',run
    definition=client.get(f'/api/v1/runs/{rid}/definitions').json()['items'][0]
    evaluated=client.post(f'/api/v1/runs/{rid}/evaluations',headers={'Idempotency-Key':'exchange-eval'},json={'snapshotId':pf['snapshotId'],'definitionRef':definition['definitionRef'],'definitionDigest':definition['definitionDigest'],'evidenceRefs':[rid+':reference-journal']})
    assert evaluated.status_code==202,evaluated.text
    annotation=client.post(f'/api/v1/runs/{rid}/annotations',json={'kind':'comment','text':'Reference observation'}).json()
    updated=client.put('/api/v1/annotations/'+annotation['annotationId'],headers={'If-Match':'1'},json={'kind':'comment','text':'Reviewed reference observation','revision':1})
    assert updated.status_code==200,updated.text
    client.post(f'/api/v1/runs/{rid}/annotations',json={'kind':'trace_link','target':{'uri':'urn:requirements:owned:1','revision':'rev-1'}})
    exported=client.post(f'/api/v1/runs/{rid}/exports',headers={'Idempotency-Key':'exchange-export'},json={})
    assert exported.status_code==202,exported.text
    result=exported.json()['result']
    response=client.get(result['downloadUrl'])
    assert response.status_code==200,response.text
    return rid,response.content


def test_real_reference_export_import_keeps_derived_records_and_never_creates_run(client,exported):
    rid,data=exported
    files=unpack(data)
    assert {'evaluations.json','annotations.json'}<=files.keys()
    evaluations=json.loads(files['evaluations.json']);annotations=json.loads(files['annotations.json'])
    assert evaluations[0]['verdict']=='pass'
    assert any(a['revision']==2 and len(a['history'])==1 for a in annotations)
    assert any(a['kind']=='trace_link' and a['target']['revision']=='rev-1' for a in annotations)
    before_runs=client.get('/api/v1/runs').json()['items'];before_projects=client.get('/api/v1/projects').json()['items']
    response=import_bundle(client,data)
    assert response.status_code==201,response.text
    bundle=response.json()
    assert bundle['inspection']['integrity']=='valid'
    assert bundle['inspection']['executionAllowed'] is False
    assert bundle['evaluations']==evaluations and bundle['annotations']==annotations
    assert bundle['inspection']['sourceRunId']==rid
    assert len(client.get('/api/v1/runs').json()['items'])==len(before_runs)
    assert len(client.get('/api/v1/projects').json()['items'])==len(before_projects)
    assert client.get('/api/v1/evidence/imports/'+bundle['bundleId']).json()['bundleId']==bundle['bundleId']
    assert client.get('/api/v1/evidence/imports').json()['items'][0]['bundleId']==bundle['bundleId']


def test_manifest_missing_file_and_digest_tamper_reject(client,exported):
    _,data=exported
    files=unpack(data);files.pop('annotations.json')
    assert import_bundle(client,archive(files)).status_code==422
    files=unpack(data);files['report.json']=b'{}'
    assert import_bundle(client,archive(files)).status_code==422


def test_rehashed_manifest_cannot_hide_snapshot_or_plan_tamper(client,exported):
    _,data=exported
    files=unpack(data);snapshot=json.loads(files['snapshot.json']);snapshot['configuration']['target']=99;files['snapshot.json']=canonical(snapshot)
    response=import_bundle(client,archive(rehash(files)))
    assert response.status_code==422,response.text
    files=unpack(data);snapshot=json.loads(files['snapshot.json']);snapshot['plan']['parameters'][0]['value']=999;snapshot.pop('snapshotDigest');snapshot['snapshotDigest']=digest(snapshot);files['snapshot.json']=canonical(snapshot)
    response=import_bundle(client,archive(rehash(files)))
    assert response.status_code==422,response.text


def test_damaged_original_journal_is_inspectable_as_invalid_never_promoted(client,exported):
    _,data=exported
    files=unpack(data);files['evidence/reference.jsonl']+=b'corrupted canonical evidence\n'
    response=import_bundle(client,archive(rehash(files)))
    assert response.status_code==201,response.text
    assert response.json()['inspection']['integrity']=='invalid'
    assert response.json()['inspection']['executionAllowed'] is False


def test_source_declared_invalid_and_partial_stay_degraded(client,exported):
    _,data=exported
    files=unpack(data)
    report=json.loads(files['report.json']);report.update(integrity='invalid',evidenceStatus='partial');files['report.json']=canonical(report)
    manifest=json.loads(files['manifest.json']);manifest.update(integrity='invalid',availability='partial');files['manifest.json']=canonical(manifest)
    response=import_bundle(client,archive(rehash(files)))
    assert response.status_code==201,response.text
    assert response.json()['inspection']['integrity']=='invalid'
    assert response.json()['inspection']['availability']=='partial'


@pytest.mark.parametrize('unsafe',['../escape','/absolute','C:/drive','evidence/CON.json','evidence/reference.jsonl/../other'])
def test_unsafe_names_reject_before_allocating_import(client,unsafe):
    response=import_bundle(client,archive({'manifest.json':'{}',unsafe:'inert'}))
    assert response.status_code==422,response.text
    assert client.get('/api/v1/evidence/imports').json()['items']==[]


def test_symlink_case_collision_and_secret_reject(client,exported):
    _,data=exported;files=unpack(data)
    assert import_bundle(client,archive(files,link='evidence/linked.jsonl')).status_code==422
    files['REPORT.JSON']=files['report.json']
    assert import_bundle(client,archive(files)).status_code==422
    files=unpack(data);annotations=json.loads(files['annotations.json']);annotations[0]['text']='password: do-not-export';files['annotations.json']=canonical(annotations)
    response=import_bundle(client,archive(rehash(files)))
    assert response.status_code==422 and response.json()['code']=='CREDENTIAL_REJECTED',response.text


def test_inline_secret_annotation_blocks_run_export(client,exported):
    rid,_=exported
    client.post(f'/api/v1/runs/{rid}/annotations',json={'kind':'comment','text':'password: do-not-export'})
    response=client.post(f'/api/v1/runs/{rid}/exports',headers={'Idempotency-Key':'secret-export'},json={})
    assert response.status_code==422 and response.json()['code']=='CREDENTIAL_REJECTED',response.text


@pytest.mark.parametrize('raw',[b'{"formatVersion":"1.0","formatVersion":"2.0"}',b'{"value":NaN}',b'{"value":1e999}',b'[]'])
def test_malformed_manifest_json_is_typed_rejection(client,raw):
    files={'manifest.json':raw,'snapshot.json':'{}','run.json':'{}','report.json':'{}'}
    response=import_bundle(client,archive(files))
    assert response.status_code==422,response.text


def test_stored_import_tamper_is_reported_without_rewriting_original_inspection(client,exported):
    _,data=exported
    response=import_bundle(client,data)
    assert response.status_code==201,response.text
    record=response.json()
    store=client.app.state.studio.store
    path=store.root/'evidence-imports'/record['bundleId']/'annotations.json'
    path.write_text('[]')
    inspected=client.get('/api/v1/evidence/imports/'+record['bundleId']).json()
    assert inspected['inspection']['integrity']=='invalid'
    assert store.get('importedEvidence',record['bundleId'])['inspection']['integrity']=='valid'


def test_conflicting_source_availability_never_upgrades_invalid(client,exported):
    _,data=exported
    files=unpack(data);manifest=json.loads(files['manifest.json']);manifest['availability']='invalid';files['manifest.json']=canonical(manifest)
    response=import_bundle(client,archive(files))
    assert response.status_code==201,response.text
    inspection=response.json()['inspection']
    assert inspection['availability']=='invalid'
    assert inspection['declaredAvailability']=='complete' and inspection['manifestAvailability']=='invalid'


def test_source_scope_never_confers_provider_or_device_admission(client,exported):
    _,data=exported
    files=unpack(data);report=json.loads(files['report.json']);report['evidenceScope']='physical-device-claim';files['report.json']=canonical(report)
    response=import_bundle(client,archive(rehash(files)))
    assert response.status_code==201,response.text
    inspection=response.json()['inspection']
    assert inspection['evidenceScope']=='imported_recorded_evidence'
    assert inspection['declaredEvidenceScope']=='physical-device-claim'
    assert inspection['providerAdmission']=='not_conferred_by_import'
    assert inspection['executionAllowed'] is False

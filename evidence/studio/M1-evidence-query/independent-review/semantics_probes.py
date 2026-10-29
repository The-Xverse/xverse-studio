"""Independent positive/negative query semantics; isolated files, no processes."""
from contextlib import contextmanager
from copy import deepcopy
from decimal import Decimal
import hashlib,json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest.mock import patch
from fastapi.testclient import TestClient
from xverse_studio.api.app import create_app
from xverse_studio.evidence import reader
from xverse_studio.evidence.query import HistoryQuery,ObservationQuery,project_evidence,receipt_time,MAX_FACETS
from xverse_studio.storage.core import canonical,digest,Problem
ROOT=Path(__file__).resolve().parents[4];TEMP=ROOT/'.studio-local/review-temp';TEMP.mkdir(parents=True,exist_ok=True)
PATHS=['services/studio-api/src/xverse_studio/evidence/query.py','services/studio-api/src/xverse_studio/evidence/reader.py','services/studio-api/src/xverse_studio/api/app.py']
def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in PATHS}
def row(index,tick,receipt,provider='studio.reference',clock='clock-a',values=None):
 return {'schemaVersion':'1.0','eventId':'fixture:'+str(index),'runId':'fixture','snapshotId':'snapshot','sequence':str(index),'type':'observation.available','recordedAt':receipt,'sourceTime':None if tick is None else {'tick':tick,'clockDomain':clock,'resolution':'nanosecond','uncertainty':0},'source':{'providerId':provider,'version':'1.0.0'},'elementRefs':[],'evidenceClass':'unknown','payload':{'observerRef':'observer','values':values if values is not None else {'value':0,'flag':False},'units':{'value':'1'}}}
def lines(rows):
 previous='0'*64;result=[]
 for original in rows:
  body={**deepcopy(original),'previousDigest':previous};previous=hashlib.sha256(canonical(body).encode()).hexdigest();body['digest']=previous;result.append((canonical(body)+'\n').encode())
 return result
report={'sourceBefore':hashes(),'scope':'Synthetic isolated Linux query/reader fixtures only; process creation forbidden; no Windows/hardware/live-provider evidence'}
records=[row(1,'0',0),row(2,None,None,values={'value':None}),row(3,'bad',False),row(4,'9007199254740993','2026-01-01T01:00:00+01:00'),row(5,'-2',0,provider='unknown-codec',clock='clock-b')]
original=deepcopy(records)
large=project_evidence(records,'valid',ObservationQuery(clockDomain='clock-a',startTick='9007199254740993',endTick='9007199254740994'),'fixture','observations')
assert [r['eventId'] for r in large['items']]==['fixture:4'];assert large['items'][0]['tick']=='9007199254740993'
all_values=project_evidence(records,'valid',ObservationQuery(),'fixture','observations')
assert all_values['items'][0]['values']['value']==0 and type(all_values['items'][0]['values']['value']) is int
assert all_values['items'][0]['values']['flag'] is False
assert all_values['items'][1]['tick'] is None and all_values['items'][1]['values']['value'] is None
assert all_values['items'][2]['tick'] is None
assert all_values['quality']['missingSourceTime']==1 and all_values['quality']['malformedSourceTime']==1
assert receipt_time(records[0])[0]==Decimal(0) and receipt_time(records[2])==(None,None,'unavailable')
assert receipt_time(records[4])==(None,None,'unavailable')
receipt=project_evidence(records,'valid',HistoryQuery(recordedFrom='1970-01-01T00:00:00Z',recordedUntil='1970-01-01T00:00:00.000001Z'),'fixture')
assert [r['eventId'] for r in receipt['items']]==['fixture:1']
first=project_evidence(records,'valid',HistoryQuery(limit=1),'fixture');cursor=first['nextCursor'];second=project_evidence(records,'valid',HistoryQuery(limit=1,cursor=cursor),'fixture')
assert second['items'][0]['eventId']=='fixture:2'
rejections=[]
for query,rid,kind in [(HistoryQuery(cursor=cursor),'other','history'),(HistoryQuery(cursor=cursor,observerRef='changed'),'fixture','history'),(ObservationQuery(cursor=cursor),'fixture','observations')]:
 try:project_evidence(records,'valid',query,rid,kind)
 except Problem as exc:assert exc.code=='CURSOR_INVALID';rejections.append(exc.code)
 else:raise AssertionError('Cross-context cursor accepted')
facets=project_evidence([row(i+1,str(i),'2026-01-01T00:00:00Z',provider='fixture-'+str(i)) for i in range(MAX_FACETS+2)],'valid',ObservationQuery(),'fixture','observations')
assert len(facets['facets']['sourceProviderIds'])==MAX_FACETS and facets['facetsComplete'] is False
assert records==original
assert all_values['tickUnit'] is None and all_values['reportedResolutions']==['nanosecond'] and all_values['mapping'] is None
codec=row(1,'0',0,clock='simulation-time');codec['sourceTime']['resolution']='microsecond'
known=project_evidence([codec],'valid',ObservationQuery(),'fixture','observations',evidence_scope='owned_reference')
assert known['tickUnit']=='microsecond'
unknown=project_evidence([codec],'valid',ObservationQuery(),'fixture','observations')
assert unknown['tickUnit'] is None
report['semantics']={'exactLargeTick':large['items'][0]['tick'],'zeroFalseAndMissingPreserved':True,'receiptZeroNotFalse':True,'cursorContextRejections':rejections,'facetsBound':MAX_FACETS,'rawInputUnchanged':records==original,'resolutionNotInferredAsUnit':True,'knownReferenceUnitRequiresContext':True}
with TemporaryDirectory(dir=TEMP,prefix='independent-evidence-semantics-') as directory:
 base=Path(directory);root=base/'append';root.mkdir();parts=lines([row(1,'0',0),row(2,'1',1)]);path=root/'evidence.jsonl';path.write_bytes(parts[0]);real_open=reader.open_read;appended=[]
 @contextmanager
 def changing(root_arg,path_arg):
  with real_open(root_arg,path_arg) as stream:
   class Wrapper:
    def fileno(self):return stream.fileno()
    def read(self,size):
     data=stream.read(size)
     with path.open('ab') as destination:destination.write(parts[1])
     appended.append(True);return data
   yield Wrapper()
 with patch.object(reader,'open_read',changing):seen,integrity=reader.read_journal(root,{'runId':'fixture','snapshotId':'snapshot','state':'running'})
 assert appended and seen==[] and integrity=='unavailable'
 stable,stable_integrity=reader.read_journal(root,{'runId':'fixture','snapshotId':'snapshot','state':'running'})
 assert len(stable)==2 and stable_integrity=='verified_prefix' and path.read_bytes()==b''.join(parts)
 report['concurrentAppend']={'firstIntegrity':integrity,'retryIntegrity':stable_integrity,'retryRecords':len(stable),'originalPrefixPreserved':path.read_bytes().startswith(parts[0])}
 app=create_app(base/'api',allowed_hosts=['testserver'],bootstrap_token='owned-local-review')
 with patch.object(subprocess,'Popen',side_effect=AssertionError('No process creation')),TestClient(app,base_url='http://testserver',raise_server_exceptions=False) as client:
  client.headers['Origin']='http://testserver';login=client.post('/api/v1/session',json={'bootstrapToken':'owned-local-review'});client.headers['X-CSRF-Token']=login.json()['csrfToken'];store=app.state.studio.store
  runroot=store.root/'runs/fixture';runroot.mkdir(parents=True);raw=b''.join(lines(records));(runroot/'evidence.jsonl').write_bytes(raw)
  store.put('run','fixture',{'runId':'fixture','snapshotId':'snapshot','state':'stopped','cleanup':'complete','evidence':'complete','evidenceScope':'recorded_fixture','journalDigest':digest(raw)})
  try:
   results=[]
   for route,params in [('history',{'startTick':'bad'}),('history',{'startTick':'0','endTick':'1'}),('observations',{'recordedFrom':'2026-01-01T00:00:00'}),('history',{'cursor':'bad'}),('observations',{'limit':'201'}),('observations',{'unknown':'x'})]:
    response=client.get('/api/v1/runs/fixture/'+route,params=params);assert response.status_code==422,(route,response.status_code,response.text);results.append({'route':route,'status':response.status_code,'code':response.json()['code']})
   response=client.get('/api/v1/runs/fixture/observations');assert response.status_code==200 and response.json()['evidenceScope']=='recorded_fixture'
   assert (runroot/'evidence.jsonl').read_bytes()==raw
   report['httpTypedRefusals']=results;report['httpRecordedScopePreserved']=True
  finally:
   with store.tx() as db:db.execute('DELETE FROM records WHERE kind=? AND id=?',('run','fixture'))
report['sourceAfter']=hashes();print(json.dumps(report,indent=2))

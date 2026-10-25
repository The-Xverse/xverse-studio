"""Independent isolated evidence-query probes; no process or large allocation."""
from copy import deepcopy
import hashlib,json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest.mock import patch
from fastapi.testclient import TestClient
from xverse_studio.api.app import create_app
from xverse_studio.evidence.query import ObservationQuery, project_evidence, MAX_GAPS
from xverse_studio.evidence.reader import read_journal
from xverse_studio.storage.core import canonical,Problem
ROOT=Path(__file__).resolve().parents[4];TEMP=ROOT/'.studio-local/review-temp';TEMP.mkdir(parents=True,exist_ok=True)
SOURCES=['services/studio-api/src/xverse_studio/evidence/query.py','services/studio-api/src/xverse_studio/evidence/reader.py','services/studio-api/src/xverse_studio/api/app.py']
def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCES}
def event(identifier='fixture:1',tick='0',clock='clock-a',kind='observation.available'):
 return {'schemaVersion':'1.0','eventId':identifier,'runId':'fixture','snapshotId':'fixture-snapshot','sequence':'1','type':kind,'recordedAt':'2026-01-01T00:00:00Z','sourceTime':{'tick':tick,'clockDomain':clock,'resolution':'nanosecond','uncertainty':0},'source':{'providerId':'fixture','version':'1.0.0'},'elementRefs':[],'evidenceClass':'unknown','payload':{'observerRef':'observer','values':{'value':0,'flag':False},'units':{'value':'1'}}}
def journal(root,row):
 body={**deepcopy(row),'previousDigest':'0'*64};body['digest']=hashlib.sha256(canonical(body).encode()).hexdigest();raw=(canonical(body)+'\n').encode();(root/'evidence.jsonl').write_bytes(raw);return raw
report={'scope':'Isolated synthetic Linux reader/API fixtures; process creation forbidden; no Windows/hardware/actual provider claims','sourceBefore':hashes()}
rows=[event('gap:'+str(i),kind='observation.gap') for i in range(MAX_GAPS)]
result=project_evidence(rows,'invalid',ObservationQuery(),'fixture','observations')
report['gapBound']={'advertised':MAX_GAPS,'returned':len(result['gaps']),'gapCount':result['gapCount'],'gapsComplete':result['gapsComplete']}
known=event();malformed=event('fixture:2','not-a-tick','malformed-other-clock')
try:
 result=project_evidence([known,malformed],'valid',ObservationQuery(startTick='0',endTick='1'),'fixture','observations')
 report['legacyKnownClock']={'outcome':'RETURNED','ids':[r['eventId'] for r in result['items']],'effectiveFilter':result['effectiveFilter'],'quality':result['quality']}
except Problem as exc:report['legacyKnownClock']={'outcome':'REJECTED','code':exc.code}
with TemporaryDirectory(dir=TEMP,prefix='independent-evidence-query-') as directory:
 base=Path(directory);root=base/'direct';root.mkdir();raw=journal(root,event());state={'runId':'fixture','snapshotId':'fixture-snapshot','state':'stopped','journalDigest':[]}
 try:
  rows,integrity=read_journal(root,state);report['malformedDigestDirect']={'outcome':'RETURNED','integrity':integrity}
 except Exception as exc:report['malformedDigestDirect']={'outcome':'RAISED','type':type(exc).__name__}
 report['sourceBytesUnchanged']=root.joinpath('evidence.jsonl').read_bytes()==raw
 app=create_app(base/'api',allowed_hosts=['testserver'],bootstrap_token='owned-local-review')
 with patch.object(subprocess,'Popen',side_effect=AssertionError('No process creation')),TestClient(app,base_url='http://testserver',raise_server_exceptions=False) as client:
  client.headers['Origin']='http://testserver';login=client.post('/api/v1/session',json={'bootstrapToken':'owned-local-review'});client.headers['X-CSRF-Token']=login.json()['csrfToken'];store=app.state.studio.store
  runroot=store.root/'runs/fixture';runroot.mkdir(parents=True);journal(runroot,event())
  store.put('run','fixture',{'runId':'fixture','snapshotId':'fixture-snapshot','projectId':'fixture-project','state':'stopped','cleanup':'complete','evidence':'complete','journalDigest':[]})
  try:
   response=client.get('/api/v1/runs/fixture/history');report['malformedDigestHttp']={'status':response.status_code,'code':response.json().get('code'),'integrity':response.json().get('integrity')}
  finally:
   with store.tx() as db:db.execute('DELETE FROM records WHERE kind=? AND id=?',('run','fixture'))
report['sourceAfter']=hashes();print(json.dumps(report,indent=2))

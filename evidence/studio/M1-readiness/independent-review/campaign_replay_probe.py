"""Read-only API admission regression; all fixtures local, process launch forbidden."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import hashlib,json,subprocess
from fastapi.testclient import TestClient
from xverse_studio.api.app import create_app
paths=['services/studio-api/src/xverse_studio/preflight/__init__.py','services/studio-api/src/xverse_studio/runs/service.py','services/studio-api/src/xverse_studio/api/advanced.py']
def hashes():return {p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}
report={'sourceBefore':hashes(),'scope':'isolated Linux loop10 fixtures; Popen forbidden; no Windows/hardware/external integration'}
ROOT=Path(__file__).resolve().parents[4]
REVIEW_TEMP=ROOT/'.studio-local/review-temp'
REVIEW_TEMP.mkdir(parents=True,exist_ok=True)
with TemporaryDirectory(dir=REVIEW_TEMP,prefix='readiness-independent-replay-') as directory:
    app=create_app(Path(directory),allowed_hosts=['testserver'],bootstrap_token='owned-review-token')
    with patch.object(subprocess,'Popen',side_effect=AssertionError('Read-only review cannot launch processes')), TestClient(app,base_url='http://testserver') as client:
        app.state.studio.campaign_tick=lambda:None
        client.headers['Origin']='http://testserver';login=client.post('/api/v1/session',json={'bootstrapToken':'owned-review-token'});client.headers['X-CSRF-Token']=login.json()['csrfToken']
        project=client.post('/api/v1/projects',json={'name':'Independent replay fixture'}).json()
        pf=client.post(f"/api/v1/projects/{project['projectId']}/preflights",json={'revision':1}).json()
        body={'snapshotId':pf['snapshotId'],'matrix':{'gain':[0.8]},'budget':{'maxRuns':1,'maxTotalSeconds':5},'concurrency':1}
        first=client.post('/api/v1/campaigns',headers={'Idempotency-Key':'replay-owned'},json=body)
        path=app.state.studio.store.root/'snapshots'/pf['snapshotId']/'snapshot.json';held=path.with_suffix('.held');before=path.read_bytes();path.rename(held)
        try:
            replay=client.post('/api/v1/campaigns',headers={'Idempotency-Key':'replay-owned'},json=body)
            conflict=client.post('/api/v1/campaigns',headers={'Idempotency-Key':'replay-owned'},json={**body,'matrix':{'gain':[1.1]}})
            new_intent=client.post('/api/v1/campaigns',headers={'Idempotency-Key':'new-owned-intent'},json=body)
        finally:held.rename(path)
        report.update(firstStatus=first.status_code,replayStatus=replay.status_code,replayCode=replay.json().get('code'),sameOperation=replay.json()==first.json(),conflictStatus=conflict.status_code,conflictCode=conflict.json().get('code'),newIntentStatus=new_intent.status_code,newIntentCode=new_intent.json().get('code'),campaignCount=len(app.state.studio.store.all('campaign')),runCount=len(app.state.studio.store.all('run')),snapshotBytesUnchanged=path.read_bytes()==before)
report['sourceAfter']=hashes();print(json.dumps(report,indent=2))

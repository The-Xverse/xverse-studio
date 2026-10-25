"""Independent owned reference descriptor negatives; no process execution."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from copy import deepcopy
import hashlib,json,subprocess
from fastapi.testclient import TestClient
from xverse_studio.api.app import create_app
from xverse_studio.runs import service
paths=['services/studio-api/src/xverse_studio/preflight/__init__.py','services/studio-api/src/xverse_studio/runs/service.py']
def hashes():return {p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}
report={'sourceBefore':hashes(),'cases':[],'scope':'isolated Linux fixtures; no Windows/hardware/providers launched'}
original=service.descriptors
ROOT=Path(__file__).resolve().parents[4]
REVIEW_TEMP=ROOT/'.studio-local/review-temp'
REVIEW_TEMP.mkdir(parents=True,exist_ok=True)
with TemporaryDirectory(dir=REVIEW_TEMP,prefix='readiness-independent-caps-') as directory:
 app=create_app(Path(directory),allowed_hosts=['testserver'],bootstrap_token='owned-review')
 with patch.object(subprocess,'Popen',side_effect=AssertionError('No process launch')), TestClient(app,base_url='http://testserver') as client:
  client.headers['Origin']='http://testserver';login=client.post('/api/v1/session',json={'bootstrapToken':'owned-review'});client.headers['X-CSRF-Token']=login.json()['csrfToken']
  project=client.post('/api/v1/projects',json={'name':'Independent descriptor fixture'}).json()
  for case in ['start_target_mismatch','unsupported_xdl_version','availability_not_boolean','host_compatibility_not_boolean']:
   rows=deepcopy(original());provider=next(p for p in rows if p['providerId']=='studio.reference')
   if case=='start_target_mismatch':next(c for c in provider['capabilityRecords'] if c['kind']=='start')['targetClass']='unadmitted-target'
   elif case=='unsupported_xdl_version':provider['supportedXdlVersions']=['xverse.io/xdl/unsupported']
   elif case=='availability_not_boolean':provider['available']='unknown'
   else:provider['hostCompatible']='unknown'
   with patch.object(service,'descriptors',lambda:rows):response=client.post(f"/api/v1/projects/{project['projectId']}/preflights",json={'revision':1})
   body=response.json();report['cases'].append({'case':case,'httpStatus':response.status_code,'status':body.get('status'),'capabilities':body.get('readiness',{}).get('capabilities',{}),'target':body.get('readiness',{}).get('target',{}),'configurationPresent':bool(app.state.studio.store.get('snapshot',body['snapshotId'])['configuration']) if 'snapshotId'in body else None})
  report['runCount']=len(app.state.studio.store.all('run'))
report['sourceAfter']=hashes();print(json.dumps(report,indent=2))

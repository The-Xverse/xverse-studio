"""Independent transitive subject-reader probe; no large allocation/processes."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import hashlib,json,subprocess
from fastapi.testclient import TestClient
from xverse_studio.api.app import create_app
ROOT=Path(__file__).resolve().parents[4];TEMP=ROOT/'.studio-local/review-temp';TEMP.mkdir(parents=True,exist_ok=True)
report={'appSourceHash':hashlib.sha256(Path('services/studio-api/src/xverse_studio/api/app.py').read_bytes()).hexdigest(),'scope':'owned local Linux file fixture; no runtime, hardware, Windows or large allocation'}
with TemporaryDirectory(dir=TEMP,prefix='trace-subject-reader-') as directory:
 app=create_app(Path(directory),allowed_hosts=['testserver'],bootstrap_token='owned-review')
 with patch.object(subprocess,'Popen',side_effect=AssertionError('No process launch')), TestClient(app,base_url='http://testserver') as client:
  client.headers['Origin']='http://testserver';login=client.post('/api/v1/session',json={'bootstrapToken':'owned-review'});client.headers['X-CSRF-Token']=login.json()['csrfToken']
  project=client.post('/api/v1/projects',json={'name':'Independent subject reader'}).json();pf=client.post(f"/api/v1/projects/{project['projectId']}/preflights",json={'revision':1}).json()
  store=app.state.studio.store;store.put('run','owned-readonly-fixture',{'runId':'owned-readonly-fixture','snapshotId':pf['snapshotId']})
  snapshot=store.root/'snapshots'/pf['snapshotId']/'snapshot.json';real_read=Path.read_bytes;original_bytes=real_read(snapshot);attempts=[]
  def forbid_unbounded(path):
   if path==snapshot:
    attempts.append(True);raise AssertionError('unbounded_snapshot_read_attempted')
   return real_read(path)
  try:
   with patch.object(Path,'read_bytes',forbid_unbounded):response=client.get('/api/v1/runs/owned-readonly-fixture/snapshot')
   report.update(outcome='RETURNED',status=response.status_code,integrity=response.json().get('integrity'))
  except AssertionError:report.update(outcome='UNBOUNDED_READER_REACHED')
  report['unboundedReadHookExecuted']=bool(attempts);report['snapshotFileBytesPreserved']=real_read(snapshot)==original_bytes
  with store.tx() as db:db.execute('DELETE FROM records WHERE kind=? AND id=?',('run','owned-readonly-fixture'))
report['appSourceHashAfter']=hashlib.sha256(Path('services/studio-api/src/xverse_studio/api/app.py').read_bytes()).hexdigest()
print(json.dumps(report,indent=2))

"""Owner proof of immutable-file boundary using only an owned reference run."""
from pathlib import Path
from tempfile import TemporaryDirectory
from copy import deepcopy
from io import StringIO
import hashlib,json,sys
from fastapi.testclient import TestClient
from ruamel.yaml import YAML
from xverse_studio.api.app import create_app
from xverse_studio.assertions import snapshot_definitions
from xverse_studio.storage.core import digest
sys.path.insert(0,'tests/integration')
from test_advanced_api import prepared,start,wait_run
report={'annotationsDigest':hashlib.sha256(Path('services/studio-api/src/xverse_studio/annotations/__init__.py').read_bytes()).hexdigest(),'scope':'owned Linux reference execution only; no Windows/hardware/external reference fetch'}
ROOT=Path(__file__).resolve().parents[3]
REVIEW_TEMP=ROOT/'.studio-local/review-temp'
REVIEW_TEMP.mkdir(parents=True,exist_ok=True)
with TemporaryDirectory(dir=REVIEW_TEMP,prefix='claim-rehashed-snapshot-') as directory:
 app=create_app(Path(directory),allowed_hosts=['testserver'],bootstrap_token='owned-review')
 with TestClient(app,base_url='http://testserver') as client:
  client.headers['Origin']='http://testserver';login=client.post('/api/v1/session',json={'bootstrapToken':'owned-review'});client.headers['X-CSRF-Token']=login.json()['csrfToken']
  project,pf=prepared(client);rid=start(client,pf,'claim-proof');terminal=wait_run(client,rid);assert terminal['state']=='stopped'
  store=app.state.studio.store;original=deepcopy(store.get('snapshot',pf['snapshotId']));snapshot_file=store.root/'snapshots'/pf['snapshotId']/'snapshot.json';raw=snapshot_file.read_bytes()
  forged=deepcopy(original);path=next(k for k in forged['documents'] if 'scenario' in k);yaml=YAML();resource=yaml.load(forged['documents'][path]);resource['extensions']['io.xverse.studio.experiments']['definitions'][0]['evaluationId']='forged-only-in-metadata';out=StringIO();yaml.dump(resource,out);forged['documents'][path]=out.getvalue();forged.pop('snapshotDigest');forged['snapshotDigest']=digest(forged)
  definition=snapshot_definitions(forged,app.state.studio.adapter)[0];model=app.state.studio.adapter.project(forged['documents'])['elements'][0]['ref']
  store.put('snapshot',pf['snapshotId'],forged)
  try:
   common={'kind':'trace_link','target':{'uri':'urn:test:requirement:reported','revision':'r1','claimStatus':'Externally claimed passed'}}
   model_response=client.post(f'/api/v1/runs/{rid}/annotations',json={**common,'elementRefs':[model]})
   definition_response=client.post(f'/api/v1/runs/{rid}/annotations',json={**common,'definitionRefs':[{'definitionRef':definition['definitionRef'],'definitionDigest':definition['definitionDigest']}]})
   report.update(modelStatus=model_response.status_code,modelCode=model_response.json().get('code'),definitionStatus=definition_response.status_code,definitionCode=definition_response.json().get('code'),annotationCount=len(store.all('annotation')),canonicalSnapshotUnchanged=snapshot_file.read_bytes()==raw,forgedDefinitionAbsentFromCanonical=b'forged-only-in-metadata' not in raw)
  finally:store.put('snapshot',pf['snapshotId'],original)
print(json.dumps(report,indent=2))

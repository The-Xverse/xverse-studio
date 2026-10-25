"""Authenticated source and sidecar reads under an actually executed ancestor swap."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from contextlib import contextmanager
import hashlib
import json
import os
from fastapi.testclient import TestClient
from xverse_studio.api.app import create_app

from pathlib import Path as _ReviewPath
_ReviewPath(".studio-local/review-temp").mkdir(parents=True, exist_ok=True)
_ReviewPath(".studio-local/review-pytest").mkdir(parents=True, exist_ok=True)

paths=['services/studio-api/src/xverse_studio/projects/service.py','services/studio-api/src/xverse_studio/security/managed_io.py']
digests=lambda:{p:'sha256:'+hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}
report={'sourceBefore':digests(),'cases':{}}
@contextmanager
def acquisition_race(target,outside):
    parent=target.parent;held=parent.with_name(parent.name+'-review-held');real_open=os.open;calls=[]
    def race(path,flags,*args,**kwargs):
        directory=kwargs.get('dir_fd')
        hit=Path(path)==target or (directory is not None and str(path)==target.name and os.fstat(directory).st_ino==parent.stat().st_ino)
        if not hit:return real_open(path,flags,*args,**kwargs)
        parent.rename(held);parent.symlink_to(outside,target_is_directory=True);calls.append(True)
        try:return real_open(path,flags,*args,**kwargs)
        finally:parent.unlink();held.rename(parent)
    with patch.object(os,'supports_dir_fd',set(os.supports_dir_fd)|{race}),patch.object(os,'open',race):yield calls

with TemporaryDirectory(dir='.studio-local/review-temp',prefix='project-http-ancestor-review-') as directory:
    base=Path(directory);app=create_app(base/'state',allowed_hosts=['testserver'],bootstrap_token='owned-review-bootstrap')
    with TestClient(app,base_url='http://testserver') as client:
        client.headers['Origin']='http://testserver'
        session=client.post('/api/v1/session',json={'bootstrapToken':'owned-review-bootstrap'})
        client.headers['X-CSRF-Token']=session.json()['csrfToken']
        project=client.post('/api/v1/projects',json={'name':'Owned source acquisition fixture'}).json();pid=project['projectId'];did=next(iter(project['documents']))
        studio=app.state.studio;target=studio.projects.document_path(pid,did);original=target.read_bytes();outside=base/'outside-source';outside.mkdir();(outside/target.name).write_bytes(b'OUTSIDE OWNED SOURCE SENTINEL')
        with acquisition_race(target,outside) as calls:response=client.get('/api/v1/projects/'+pid)
        assert calls and response.status_code==200,response.text
        assert response.json()['documents'][did]['content'].encode()==original
        assert response.json()['sourceIntegrity']=='intact'
        assert target.read_bytes()==original and (outside/target.name).read_bytes()==b'OUTSIDE OWNED SOURCE SENTINEL'
        report['cases']['authenticated_project_read']={'hookExecuted':True,'status':200,'returnedOriginalSource':True,'outsideUnchanged':True}
        profiles=client.get('/api/v1/profiles').json()['items'];locks=[{k:p[k] for k in ('profileId','version','schemaDigest','presentationDigest')} for p in profiles]
        bound=client.post('/api/v1/projects/'+pid+'/profile-bindings',headers={'If-Match':'1'},json={'baseRevision':1,'profiles':locks})
        assert bound.status_code==200,bound.text
        current=studio.projects.read(pid);name=next(n for n in current['supportingFiles'] if n.startswith('profiles/') and n.endswith('.schema.json'))
        sidecar=studio.projects._dir(pid,current['revision'])/name;raw=sidecar.read_bytes();outside=base/'outside-sidecar';outside.mkdir();(outside/sidecar.name).write_bytes(b'OUTSIDE OWNED SIDECAR SENTINEL')
        with acquisition_race(sidecar,outside) as calls:studio.projects.assert_intact(current)
        assert calls and sidecar.read_bytes()==raw and (outside/sidecar.name).read_bytes()==b'OUTSIDE OWNED SIDECAR SENTINEL'
        report['cases']['pinned_profile_sidecar_integrity_read']={'hookExecuted':True,'originalSidecarValidated':True,'outsideUnchanged':True}
report['sourceAfter']=digests();report['sourceStable']=report['sourceBefore']==report['sourceAfter']
print(json.dumps(report,indent=2))

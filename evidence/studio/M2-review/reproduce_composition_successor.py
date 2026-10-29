"""Independent owned composition probes. No run/provider/device start is requested."""
from copy import deepcopy
import base64
import hashlib
from io import BytesIO, StringIO
import json
from pathlib import Path
import tempfile
import time
import platform
import subprocess
import zipfile

from fastapi.testclient import TestClient
from ruamel.yaml import YAML

from xverse_studio.api.app import create_app
from xverse_studio.deployments import Deployments
from xverse_studio.projects.service import Projects
from xverse_studio.storage.core import Store, Problem, canonical, digest
from xverse_studio.xdl import XDLAdapter, examples

CACHE=Path(tempfile.gettempdir())
REVIEWED=['services/studio-api/src/xverse_studio/api/composition.py','services/studio-api/src/xverse_studio/catalog/__init__.py','services/studio-api/src/xverse_studio/profiles/__init__.py','services/studio-api/src/xverse_studio/deployments/__init__.py','services/studio-api/src/xverse_studio/projects/service.py','services/studio-api/src/xverse_studio/runs/service.py','services/studio-api/src/xverse_studio/api/exchange.py','services/studio-api/src/xverse_studio/security/files.py','services/studio-api/src/xverse_studio/api/reruns.py']
def hashes():return {p:'sha256:'+hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in REVIEWED}

def dump(resource):
    stream=StringIO();YAML().dump(resource,stream);return stream.getvalue()

def edited_scenario(source,name):
    value=YAML(typ='safe').load(source)
    value['metadata']['name']=name
    for extension in value.get('extensions',{}).values():
        if isinstance(extension,dict) and isinstance(extension.get('target'),dict) and extension['target'].get('kind')=='Scenario':extension['target']['name']=name
    for definition in value.get('extensions',{}).get('io.xverse.studio.experiments',{}).get('definitions',[]):
        definition['scenarioRef']=f"xdl://{value['metadata']['namespace']}/scenario/{name}"
    return dump(value)

before=hashes();out={'startedAt':time.time(),'candidateCommit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'environment':{'os':platform.system(),'release':platform.release(),'python':platform.python_version(),'filesystem':'loop10'},'scope':'independent Linux-only successor verification of M2-I01 through M2-I05','probes':{}}
with tempfile.TemporaryDirectory(prefix='composition-independent-',dir=CACHE) as temporary:
    root=Path(temporary)
    app=create_app(root/'http',allowed_hosts=['testserver'],bootstrap_token='owned-review-bootstrap')
    with TestClient(app,base_url='http://testserver',raise_server_exceptions=False) as client:
        client.headers['Origin']='http://testserver'
        login=client.post('/api/v1/session',json={'bootstrapToken':'owned-review-bootstrap'})
        assert login.status_code==200,login.text
        client.headers['X-CSRF-Token']=login.json()['csrfToken']
        project=client.post('/api/v1/projects',json={'name':'Independent composition review'}).json();pid=project['projectId']
        compiled_before=client.post(f'/api/v1/projects/{pid}/compilations',json={'revision':1}).json()
        moved=client.put(f'/api/v1/projects/{pid}/layout',headers={'If-Match':'1'},json={'positions':{'controller':{'x':100.0,'y':50.0}}})
        compiled_after=client.post(f'/api/v1/projects/{pid}/compilations',json={'revision':1}).json()
        out['probes']['layout_identity']={'httpStatus':moved.status_code,'sourceRevision':moved.json().get('revision'),'presentationRevision':moved.json().get('presentationRevision'),'samePlanDigest':compiled_before['planDigest']==compiled_after['planDigest'],'sameSemanticDigest':compiled_before['semanticDigest']==compiled_after['semanticDigest']}
        admitted=client.get('/api/v1/profiles').json()['items']
        locks=[{key:entry[key] for key in ('profileId','version','schemaDigest','presentationDigest')} for entry in admitted]
        bound=client.post(f'/api/v1/projects/{pid}/profile-bindings',headers={'If-Match':'1'},json={'baseRevision':1,'profiles':locks})
        assert bound.status_code==200,bound.text
        exported=client.post(f'/api/v1/projects/{pid}/exports',headers={'Idempotency-Key':'review-profile-export'},json={'revision':2})
        out['probes']['project_export_status']={'httpStatus':exported.status_code,'code':exported.json().get('code')}
        if exported.status_code==202:
            archive=client.get(exported.json()['result']['downloadUrl']).content
            with zipfile.ZipFile(BytesIO(archive)) as z:files={name:z.read(name) for name in z.namelist()}
        else:
            # Build the same inert envelope locally so an unrelated export bug
            # cannot conceal the import/admission boundary under review.
            bound_project=bound.json()
            files={name:content.encode() for name,content in bound_project.get('supportingFiles',{}).items()}
            files.update({document['path']:document['content'].encode() for document in bound_project['documents'].values()})
            files['project.studio.json']=canonical(bound_project['manifest']).encode()
            files['layout/model.json']=canonical(bound_project['layout']).encode()
            files.setdefault('artifacts.lock.json',canonical({'formatVersion':'1.0','entries':[]}).encode())
        manifest=json.loads(files['project.studio.json']);lock=manifest['profiles'][0]
        files[lock['schemaPath']]=b'{}';lock['schemaDigest']=digest(b'{}');files['project.studio.json']=canonical(manifest).encode()
        stream=BytesIO()
        with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for name,raw in files.items():z.writestr(name,raw)
        imported=client.post('/api/v1/projects/imports',json={'archiveBase64':base64.b64encode(stream.getvalue()).decode()})
        assert imported.status_code==201,imported.text
        imported_project=imported.json();imported_id=imported_project['projectId']
        preflight=client.post(f'/api/v1/projects/{imported_id}/preflights',json={'revision':1})
        out['probes']['conflicting_imported_profile_lock']={'importStatus':imported.status_code,'preflightHttpStatus':preflight.status_code,'preflight':preflight.json(),'declaredSchemaDigest':lock['schemaDigest'],'admittedRegistrySchemaDigest':next(e['schemaDigest'] for e in admitted if e['namespace']==lock['namespace']),'runCount':len(client.get('/api/v1/runs').json()['items'])}
        artifact=client.post('/api/v1/catalog/artifacts',headers={'Idempotency-Key':'review-inert-artifact'},json={'name':'Inert review artifact','version':'1.0.0','artifactKind':'model','digest':'sha256:'+'a'*64,'originRef':'urn:xverse:review:unavailable-artifact','providerIds':['unadmitted-provider']})
        malformed=client.post('/api/v1/catalog/artifacts',headers={'Idempotency-Key':'review-malformed-uri'},json={'name':'Malformed URI artifact','version':'1.0.0','artifactKind':'model','digest':'sha256:'+'b'*64,'originRef':'https://[broken'})
        out['probes']['artifact_registration']={'normalStatus':artifact.status_code,'executionAllowed':artifact.json().get('executionAllowed'),'availability':artifact.json().get('availability'),'malformedUriStatus':malformed.status_code,'malformedUriCode':malformed.json().get('code'),'malformedUriBody':malformed.text[:300],'runCount':len(client.get('/api/v1/runs').json()['items'])}
        # Unknown payload stays an invalid inspectable draft, never stripped by a
        # known profile binding attempt.
        current=client.get(f'/api/v1/projects/{pid}').json()
        did,doc=next((k,d) for k,d in current['documents'].items() if 'scenario' in d['path'])
        resource=YAML(typ='safe').load(doc['content']);resource.setdefault('extensions',{})['org.review.unknown']={'opaque':'retain-original'}
        saved=client.put(f'/api/v1/projects/{pid}/documents/{did}',headers={'If-Match':str(current['revision'])},json={'content':dump(resource),'format':'yaml'})
        draft=saved.json();binding=client.post(f'/api/v1/projects/{pid}/profile-bindings',headers={'If-Match':str(draft['revision'])},json={'baseRevision':draft['revision'],'profiles':locks})
        retained=client.get(f'/api/v1/projects/{pid}').json()
        out['probes']['unknown_payload_preservation']={'bindingStatus':binding.status_code,'revisionUnchanged':retained['revision']==draft['revision'],'exactSourceUnchanged':retained['documents'][did]['content']==draft['documents'][did]['content']}
    # Generated document-path collision must not corrupt a committed revision.
    store=Store(root/'collision');adapter=XDLAdapter();projects=Projects(store,adapter)
    docs=deepcopy(examples()[0]['documents']);controller=YAML(typ='safe').load(next(source for name,source in docs.items() if 'controller' in name))
    controller['metadata']['name']='unused-helper'
    for endpoint in controller['spec'].get('endpoints',[]):endpoint['ownerId']='unused-helper'
    docs['deployment-review-collision.xdl.yaml']=dump(controller)
    valid=adapter.validate(docs)
    assert valid['valid'],valid['diagnostics']
    project=projects.create('Owned path collision',documents=docs)
    baseline_contents={identifier:document['content'] for identifier,document in project['documents'].items()}
    result=None;collision_error=None
    try:result=Deployments(projects,adapter).create(project['projectId'],1,{'name':'Review collision'})
    except Problem as error:collision_error=error.code
    changed=projects.read(project['projectId']);paths=[d['path'] for d in changed['documents'].values()]
    try:projects.assert_intact(changed);intact=True
    except Problem:intact=False
    out['probes']['variant_document_path_collision']={'sourceFixtureValid':valid['valid'],'reportedError':collision_error,'returnedRevision':result['project']['revision'] if result else None,'afterRevision':changed['revision'],'sourceBytesUnchanged':baseline_contents=={identifier:document['content'] for identifier,document in changed['documents'].items()},'duplicatePaths':len(paths)!=len(set(paths)),'committedProjectIntact':intact,'affectedDocuments':[key for key,d in changed['documents'].items() if digest(d['content'].encode())!=d['digest']]}
    # A post-commit compatibility exception must not masquerade as a rejected edit.
    store=Store(root/'ambiguous-binding');adapter=XDLAdapter();projects=Projects(store,adapter)
    docs=deepcopy(examples()[0]['documents']);scenario=next(source for name,source in docs.items() if 'scenario' in name)
    docs['extra-scenario.xdl.yaml']=edited_scenario(scenario,'extra-scenario')
    valid=adapter.validate(docs);assert valid['valid'],valid['diagnostics']
    project=projects.create('Owned ambiguous compatibility',documents=docs);service=Deployments(projects,adapter);variant=service.list(project['projectId'])['items'][0]
    baseline_contents={identifier:document['content'] for identifier,document in project['documents'].items()}
    error=None
    try:service.update_binding(project['projectId'],1,variant['documentId'],{'bindingId':'plant-binding','targetId':'reference-target'})
    except Problem as e:error=e.code
    changed=projects.read(project['projectId'])
    out['probes']['post_commit_binding_failure']={'sourceFixtureValid':valid['valid'],'reportedError':error,'beforeRevision':1,'afterRevision':changed['revision'],'sourceBytesUnchanged':baseline_contents=={identifier:document['content'] for identifier,document in changed['documents'].items()}}
out['sourceHashesBefore']=before;out['sourceHashesAfter']=hashes();out['reviewedSourcesUnchanged']=before==hashes()
p=out['probes'];lock_probe=p['conflicting_imported_profile_lock'];collision=p['variant_document_path_collision'];binding=p['post_commit_binding_failure']
out['checks']={
 'M2-I01':p['project_export_status']['httpStatus']==202,
 'M2-I02':lock_probe['preflightHttpStatus'] in (409,422) and lock_probe['preflight'].get('code') in ('PROFILE_CONFLICT','PROFILE_UNRESOLVED','REVISION_CONFLICT') and lock_probe['runCount']==0,
 'M2-I03':collision['reportedError']=='PROJECT_PATH_COLLISION' and collision['afterRevision']==1 and collision['sourceBytesUnchanged'] and not collision['duplicatePaths'] and collision['committedProjectIntact'],
 'M2-I04':binding['reportedError']=='SELECTION_AMBIGUOUS' and binding['afterRevision']==1 and binding['sourceBytesUnchanged'],
 'M2-I05':p['artifact_registration']['malformedUriStatus']==422 and p['artifact_registration']['malformedUriCode']=='ARTIFACT_ORIGIN_UNSUPPORTED',
 'layout_identity_retained':p['layout_identity']['samePlanDigest'] and p['layout_identity']['sameSemanticDigest'] and p['layout_identity']['sourceRevision']==1,
 'unknown_source_preserved':all(p['unknown_payload_preservation'][key] for key in ('revisionUnchanged','exactSourceUnchanged')),
 'artifact_metadata_inert':p['artifact_registration']['normalStatus']==201 and p['artifact_registration']['executionAllowed'] is False and p['artifact_registration']['availability']=='unavailable' and p['artifact_registration']['runCount']==0}
out['result']='PASS' if all(out['checks'].values()) and out['reviewedSourcesUnchanged'] else 'FAIL'
out['limitations']=['No runtime start/provider/device effects were requested.','Linux-only verification. Windows installation/testing intentionally NOT_RUN/BLOCKED by explicit user instruction.','This closes the five scoped code findings only; no M2 milestone acceptance claim.']
Path('evidence/studio/M2-review/composition-successor-probes-0dd.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))

raise SystemExit(0 if out['result']=='PASS' else 1)

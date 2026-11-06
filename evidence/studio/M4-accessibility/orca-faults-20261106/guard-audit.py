"""Read-only original fixtures; corrupt only in-memory records or private copies."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import inspect
import io
import json
import shutil
import sqlite3
import tempfile
import traceback
from ruamel.yaml import YAML

root=Path.cwd();local=Path(__file__).resolve().parent
sha=lambda raw:hashlib.sha256(raw).hexdigest()
spec=importlib.util.spec_from_file_location('readback',root/'tests/live/autoverse_orca_authoring_records.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
lines,start=inspect.getsourcelines(module.verify_scenario_history)
semantic_line=start+next(i for i,l in enumerate(lines) if 'assert yaml.load(raw) == states[index]' in l)
results=[];audit=local/'audit';audit.mkdir(mode=0o700,exist_ok=True)
phases=['probe-1','source-probe-1']+[f'final-{name}-{w}' for name in ('fault','source') for w in (1024,1440)]
for phase in phases:
    p=local/phase;data=p/'data';db_path=data/'studio.sqlite';db_hash=sha(db_path.read_bytes())
    context=json.loads((p/'context.private.json').read_bytes());width=context['width'];source_only=context['suite']=='scenario-fault-source'
    before={(k,i):b for k,i,b in json.loads((p/'protected-before.private.json').read_bytes())}
    with sqlite3.connect(db_path.as_uri()+'?mode=ro',uri=True) as db:after={(k,i):b for k,i,b in db.execute("SELECT kind,id,body FROM records WHERE kind!='session'")}
    files_before=json.loads((p/'projects-before-hashes.json').read_bytes())
    def files():return {f.relative_to(data).as_posix():sha(f.read_bytes()) for f in (data/'projects').rglob('*') if f.is_file()}
    files_after=files();baseline=json.loads((p/'project-before.private.json').read_bytes())
    reader=module.verify_fault_source if source_only else module.verify_fault
    def check(a=after,f=files_after,w=width,d=data):return reader(before,a,files_before,f,baseline,d,w,True)
    positive=check();assert positive['acceptedSemanticEdits']==(2 if source_only else 3)
    rejected=[];semantic=[]
    def rejects(name,fn,require_semantic=False):
        try:fn()
        except AssertionError as error:
            if require_semantic:
                assert any(f.name=='verify_scenario_history' and f.lineno==semantic_line for f in traceback.extract_tb(error.__traceback__))
                semantic.append(name)
            else:rejected.append(name)
        else:raise AssertionError('Guard accepted '+name)
    rejects('wrong identifier and opaque intent width',lambda:check(w=1440 if width==1024 else 1024))
    a=copy.deepcopy(after);a.pop(next(k for k in before if k[0]!='project'));rejects('deleted original record',lambda:check(a))
    a=copy.deepcopy(after);a[next(k for k in before if k[0]!='project')]='{}';rejects('changed unrelated record',lambda:check(a))
    a=copy.deepcopy(after);a[('invented','row')]='{}';rejects('unexpected new record',lambda:check(a))
    key=next(k for k in after if k not in before)
    a=copy.deepcopy(after);seal=json.loads(a[key]);seal['origin']['edits']=['incorrect_origin'];a[key]=json.dumps(seal);rejects('wrong edit origin',lambda:check(a))
    a=copy.deepcopy(after);seal=json.loads(a[key]);next(iter(seal['documents'].values()))['digest']='sha256:'+'0'*64;a[key]=json.dumps(seal);rejects('wrong source digest',lambda:check(a))
    f=copy.deepcopy(files_after);f[next(iter(files_before))]='0'*64;rejects('changed previous project byte',lambda:check(f=f))
    f=copy.deepcopy(files_after);f['projects/unexpected.file']='0'*64;rejects('unexpected new project file',lambda:check(f=f))
    f=copy.deepcopy(files_after);f.pop(next(k for k in files_after if k not in files_before));rejects('missing new project file',lambda:check(f=f))
    if phase in ('final-fault-1440','final-source-1440'):
        pid=baseline['projectId'];first=baseline['revision']+1;seal_key=('revision',f'{pid}:{first}');original_seal=json.loads(after[seal_key])
        yaml=YAML(typ='safe');identity=next(i for i,doc in baseline['documents'].items() if yaml.load(doc['content']).get('kind')=='Scenario')
        meta=original_seal['documents'][identity];relative=f'projects/{pid}/revisions/{first}/{meta["path"]}';old_sha=meta['digest'][7:]
        mutations={
            'timed duration changed':lambda fault:fault['extensions']['io.xverse.experiment']['duration'].update(value=3),
            'timed unit changed':lambda fault:fault['extensions']['io.xverse.experiment']['trigger'].update(unit='ms'),
            'clock identity changed':lambda fault:fault['extensions']['io.xverse.experiment'].update(timeDomainId='wrong-clock'),
            'fault target identity changed':lambda fault:fault['extensions']['io.xverse.experiment']['target'].update(element='wrong-element'),
            'maturity promoted':lambda fault:fault.update(maturity='validated'),
            'opaque recovery replaced':lambda fault:fault.update(recovery='discarded opaque intent'),
        }
        for name,mutate in mutations.items():
            with tempfile.TemporaryDirectory(prefix='semantic-',dir=audit) as temporary:
                clone=Path(temporary)
                for revision in range(first,positive['toRevision']+1):
                    folder=Path(f'projects/{pid}/revisions/{revision}');shutil.copytree(data/folder,clone/folder)
                document=yaml.load((clone/relative).read_bytes());fault=document['spec']['faults'][-1];assert fault['id']==f'orca-fault-{width}';mutate(fault)
                output=io.StringIO();yaml.dump(document,output);raw=output.getvalue().encode();(clone/relative).write_bytes(raw);new_sha=sha(raw)
                a=copy.deepcopy(after);seal=copy.deepcopy(original_seal);seal['documents'][identity]['digest']='sha256:'+new_sha;a[seal_key]=json.dumps(seal)
                f=copy.deepcopy(files_after);f[relative]=new_sha;f.pop(f'projects/{pid}/objects/{old_sha}');f[f'projects/{pid}/objects/{new_sha}']=new_sha
                obj=clone/f'projects/{pid}/objects/{new_sha}';obj.parent.mkdir(parents=True);obj.write_bytes(raw)
                rejects(name,lambda:check(a,f,d=clone),True)
    assert files()==files_after and sha(db_path.read_bytes())==db_hash
    results.append({'phase':phase,'width':width,'sourceOnly':source_only,'accepted':positive,'negativeCasesRejected':rejected,'semanticCasesRejectedAtExactComparison':semantic,'originalFixturesUnchanged':True,'afterDatabaseSha256':db_hash,'inputSha256':{n:sha((p/n).read_bytes()) for n in ('protected-before.private.json','projects-before-hashes.json','project-before.private.json','source-inputs.json')}})
report={'positiveFixtures':len(results),'recordAndFileCorruptionsRejected':sum(len(r['negativeCasesRejected']) for r in results),'hashConsistentSemanticCorruptionsRejected':sum(len(r['semanticCasesRejectedAtExactComparison']) for r in results),'semanticFailureLine':semantic_line,'verifierSha256':sha((root/'tests/live/autoverse_orca_authoring_records.py').read_bytes()),'fixtures':results}
(local/'guard-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='fixtures'}))

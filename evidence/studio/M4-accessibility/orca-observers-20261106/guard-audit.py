"""Read-only fault injection against the actual saved copy-local AT revisions."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import sqlite3

root=Path.cwd();local=Path(__file__).resolve().parent
sha=lambda raw:hashlib.sha256(raw).hexdigest()
spec=importlib.util.spec_from_file_location('readback',root/'tests/live/autoverse_orca_authoring_records.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
results=[]
for phase in ('probe-1','final-observers-1024','final-observers-1440'):
    p=local/phase;data=p/'data';db_path=data/'studio.sqlite';db_before=sha(db_path.read_bytes())
    width=json.loads((p/'context.private.json').read_text())['width']
    before={(k,i):body for k,i,body in json.loads((p/'protected-before.private.json').read_text())}
    with sqlite3.connect(db_path.as_uri()+'?mode=ro',uri=True) as db:
        after={(k,i):body for k,i,body in db.execute("SELECT kind,id,body FROM records WHERE kind!='session'")}
    files_before=json.loads((p/'projects-before-hashes.json').read_text())
    def files():return {f.relative_to(data).as_posix():sha(f.read_bytes()) for f in (data/'projects').rglob('*') if f.is_file()}
    files_after=files();baseline=json.loads((p/'project-before.private.json').read_text())
    def check(a=after,f=files_after,w=width,passed=False):
        return module.verify_observer_metric(before,a,files_before,f,baseline,data,w,passed)
    accepted=check(passed=True);assert accepted['acceptedSemanticEdits']==4
    rejected=[]
    def rejects(name,fn):
        try:fn()
        except AssertionError:rejected.append(name)
        else:raise AssertionError('Guard accepted '+name)
    rejects('wrong authored identifier and intent width',lambda:check(w=1440 if width==1024 else 1024))
    a=copy.deepcopy(after);a.pop(next(k for k in before if k[0]!='project'));rejects('deleted original record',lambda:check(a))
    a=copy.deepcopy(after);a[next(k for k in before if k[0]!='project')]='{}';rejects('changed unrelated record',lambda:check(a))
    a=copy.deepcopy(after);a[('invented','row')]='{}';rejects('unexpected new record',lambda:check(a))
    seal_key=next(k for k in after if k not in before)
    a=copy.deepcopy(after);seal=json.loads(a[seal_key]);seal['origin']['edits']=['incorrect_origin'];a[seal_key]=json.dumps(seal);rejects('wrong recorded edit origin',lambda:check(a))
    a=copy.deepcopy(after);seal=json.loads(a[seal_key]);next(iter(seal['documents'].values()))['digest']='sha256:'+'0'*64;a[seal_key]=json.dumps(seal);rejects('wrong source digest',lambda:check(a))
    f=copy.deepcopy(files_after);f[next(iter(files_before))]='0'*64;rejects('changed previous project byte',lambda:check(f=f))
    f=copy.deepcopy(files_after);f['projects/unexpected.file']='0'*64;rejects('unexpected new project file',lambda:check(f=f))
    f=copy.deepcopy(files_after);f.pop(next(k for k in files_after if k not in files_before));rejects('missing required new file',lambda:check(f=f))
    assert files()==files_after and sha(db_path.read_bytes())==db_before
    results.append({'phase':phase,'width':width,'accepted':accepted,'negativeCasesRejected':rejected,'readOnlyFixtureVerified':True,'fixtureSha256':{n:sha((p/n).read_bytes()) for n in ('protected-before.private.json','projects-before-hashes.json','project-before.private.json','source-inputs.json')},'afterDatabaseSha256':db_before})
report={'fixtures':results,'positiveCases':len(results),'negativeCasesRejected':sum(len(r['negativeCasesRejected']) for r in results),'sourceSha256':sha((root/'tests/live/autoverse_orca_authoring_records.py').read_bytes())}
(local/'guard-probe.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='fixtures'}))

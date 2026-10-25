"""Author verification for additive annotation claim metadata, Linux only."""
from pathlib import Path
import hashlib,json,os,platform,subprocess,sys,time
ROOT = Path(__file__).resolve().parents[3]
FILES = ['services/studio-api/src/xverse_studio/annotations/__init__.py','tests/integration/test_trace_claim_status.py','services/studio-api/src/xverse_studio/assertions/evaluation-v1.schema.json','services/studio-api/src/xverse_studio/assertions/evaluator.py','services/studio-api/src/xverse_studio/assertions/snapshot.py']
def sha(raw):return hashlib.sha256(raw).hexdigest()
def sources():
    result = {p:sha((ROOT/p).read_bytes()) for p in FILES}
    models=(ROOT/'services/studio-api/src/xverse_studio/api/models.py').read_text()
    advanced=(ROOT/'services/studio-api/src/xverse_studio/api/advanced.py').read_text()
    result['models.Annotation+AnnotationUpdate']=sha(models[models.index('class Annotation(Body):'):models.index('class Retention(Body):')].encode())
    result['advanced.annotations_block']=sha(advanced[advanced.index('    @app.get("/api/v1/runs/{runId}/annotations")'):advanced.index('    from xverse_studio.retention.service import RetentionService')].encode())
    return result
REVIEW_TEMP=ROOT/'.studio-local/review-temp'
REVIEW_TEMP.mkdir(parents=True,exist_ok=True)
command=[sys.executable,'-m','pytest','tests/integration/test_trace_claim_status.py','tests/integration/test_advanced_api.py','tests/integration/test_exchange_and_retention.py','-k','trace or annotation or reported','-q','-o','cache_dir='+str(REVIEW_TEMP/'pytest'),'--basetemp='+str(REVIEW_TEMP/'trace-claim-final')]
env=os.environ.copy();env.update(PYTHONPATH='services/studio-api/src',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',TMPDIR=str(REVIEW_TEMP))
before=sources();started=time.time();result=subprocess.run(command,cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
receipt={'scope':'Linux owned reference only; no Windows, external references fetched, hardware or companion repository writes','python':sys.version,'platform':platform.platform(),'command':command,'startedAt':started,'elapsedSeconds':time.time()-started,'sourceBefore':before,'sourceAfter':sources(),'scopeNote':'advanced.py/models.py are shared ownership; hash owned annotation blocks only, evaluator/schema/snapshot full files retained to show no change','exitCode':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'independentReview':'pending separate read-only reviewer'}
raw=ROOT/'.studio-local/evidence-raw/readiness-claims';raw.mkdir(parents=True,exist_ok=True)
(raw/('backend-verification-'+str(int(started*1000))+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
def sanitize(value):
    if isinstance(value,str):return value.replace(str(ROOT),'<workspace>')
    if isinstance(value,list):return [sanitize(item) for item in value]
    if isinstance(value,dict):return {key:sanitize(item) for key,item in value.items()}
    return value
receipt=sanitize(receipt)
receipt['redactionNotes']=['Workspace prefixes normalized; raw receipt retained locally outside Git.','Outcomes and source hashes are unchanged.']
Path(__file__).with_name('backend-verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(result.stdout);print(result.stderr);sys.exit(result.returncode)

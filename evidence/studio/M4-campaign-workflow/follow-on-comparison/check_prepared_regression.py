from pathlib import Path
import hashlib,json,os,subprocess,time
root=Path(__file__).resolve().parents[2];base=root/'.studio-local/comparison-next';checkout=base/'isolated-source';out=base/'prepared-regression';out.mkdir(exist_ok=False)
relative='tests/integration/test_comparison.py';original=(root/relative).read_text();target=checkout/relative
assert target.read_text()==original
target.write_text(original+(base/'test-addition.py.txt').read_text())
script=out/'invoke.py';script.write_bytes((base/'isolated-successor/invoke.py').read_bytes())
cmd=[str(root/'.venv/bin/python'),'-I',str(script),str(checkout/'services/studio-api/src'),str(target),'-q','--tb=short','--junitxml='+str(out/'junit.xml'),'--basetemp='+str(out/'tmp')]
env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',TMPDIR=str(root.parent/'.xverse-studio-cache/tmp'));start=time.monotonic()
with (out/'pytest.log').open('w') as f:r=subprocess.run(cmd,cwd=checkout,env=env,stdout=f,stderr=subprocess.STDOUT)
assert (root/relative).read_text()==original
(out/'exact-test.py.txt').write_bytes(target.read_bytes())
s={'command':cmd,'exitCode':r.returncode,'seconds':round(time.monotonic()-start,3),'mainComparisonSourceUnchanged':True,'proposedTestSha256':hashlib.sha256(target.read_bytes()).hexdigest(),'scope':'Proposed tracked public regression plus3 existing comparison cases under the isolated source repair; not applied to main candidate.'}
(out/'summary.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps(s),flush=True)
raise SystemExit(r.returncode)

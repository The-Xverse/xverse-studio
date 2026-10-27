from pathlib import Path
import hashlib,json,os,subprocess,sys,time
root=Path.cwd().resolve();base=root/'.studio-local/comparison-next';out=base/'snapshot-integrity-red';out.mkdir(exist_ok=False)
paths=json.loads((root/'.studio-local/campaign-workflow/final-targeted/source-before.json').read_text())
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in paths.items())
(out/'source-before.json').write_text(json.dumps(paths,indent=2)+'\n')
source=base/'test_snapshot_integrity_probe.py';(out/'exact-test.py.txt').write_bytes(source.read_bytes())
env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',TMPDIR=str(root.parent/'.xverse-studio-cache/tmp'))
cmd=[str(root/'.venv/bin/python'),'-I','-m','pytest',str(source),'-q','--tb=short','--junitxml='+str(out/'junit.xml'),'--basetemp='+str(out/'tmp')]
start=time.monotonic()
with (out/'pytest.log').open('w') as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
after={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in paths};(out/'source-after.json').write_text(json.dumps(after,indent=2)+'\n')
s={'baseCandidate':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'command':cmd,'exitCode':r.returncode,'seconds':round(time.monotonic()-start,3),'sourceUnchanged':paths==after,'probeTestSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scope':'Independent next-scope probe outside the frozen campaign input map; not part of the880 backend or379 browser gate.'}
(out/'summary.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps(s),flush=True)
raise SystemExit(r.returncode or int(paths!=after))

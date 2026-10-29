from pathlib import Path
import hashlib,json,os,subprocess,sys,time
root=Path(__file__).resolve().parents[2];base=root/'.studio-local/comparison-next';checkout=base/'isolated-source';out=base/'isolated-successor';out.mkdir(exist_ok=False)
control=json.loads((base/'isolated-source-control.json').read_text());mainmap=json.loads((root/'.studio-local/campaign-workflow/final-targeted/source-before.json').read_text());assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in mainmap.items())
script=out/'invoke.py';script.write_text('''import sys\nfrom pathlib import Path\nsys.path.insert(0,sys.argv[1])\nimport xverse_studio.api.advanced as advanced\nassert Path(advanced.__file__).resolve().is_relative_to(Path(sys.argv[1]).resolve())\nimport pytest\nraise SystemExit(pytest.main(sys.argv[2:]))\n''')
args=[str(root/'.venv/bin/python'),'-I',str(script),str(checkout/'services/studio-api/src'),str(base/'test_snapshot_integrity_probe.py'),str(root/'tests/integration/test_campaign_presentation.py'),str(root/'tests/integration/test_campaigns.py'),str(root/'tests/integration/test_advanced_api.py'),'-q','--tb=short','--junitxml='+str(out/'junit.xml'),'--basetemp='+str(out/'tmp')]
env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',TMPDIR=str(root.parent/'.xverse-studio-cache/tmp'))
start=time.monotonic()
with (out/'pytest.log').open('w') as f:r=subprocess.run(args,cwd=checkout,env=env,stdout=f,stderr=subprocess.STDOUT)
after={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in mainmap};assert mainmap==after
(out/'main-source-before.json').write_text(json.dumps(mainmap,indent=2)+'\n');(out/'main-source-after.json').write_text(json.dumps(after,indent=2)+'\n')
projection=checkout/'.studio-local/comparison-next/actual-public-projection.json'
if projection.is_file():(out/'actual-public-projection.json').write_bytes(projection.read_bytes())
s={'command':args,'exitCode':r.returncode,'seconds':round(time.monotonic()-start,3),'mainFrozenSourceUnchanged':True,'scope':'Isolated Studio API source with one verification call; not the main campaign candidate or its880/379 gates. Owned reference worker implementation unchanged.'}
(out/'summary.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps(s),flush=True)
raise SystemExit(r.returncode)

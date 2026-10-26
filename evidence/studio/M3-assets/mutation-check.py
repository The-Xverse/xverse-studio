from pathlib import Path
import json,os,subprocess,sys
root=Path.cwd();out=root/'.studio-local/t072'
mutations=[
 ('private-allowlist','assets','return {\n        "assetId": asset["assetId"],','return {\n        **asset,\n        "assetId": asset["assetId"],','inventory_public_allowlist'),
 ('canonical-interface','bindings','asset["interfaces"].get(k) == v','True','unknown_identity_unavailable_and_mismatched_contracts'),
 ('active-authority','bindings','"activeReady": False,','"activeReady": True,','inventory_admission_text'),
 ('source-validation','bindings','if not validation["valid"]:','if False:','invalid_or_external_source'),
 ('inventory-completeness','assets','"complete": not diagnostics and len(providers) <= MAX_PROVIDERS,','"complete": True,','partial_yielded_results'),
]
results=[]
for name,module,old,new,selector in mutations:
 source=(root/f'services/studio-api/src/xverse_studio/lab/{module}.py').read_text();assert old in source,name
 codes=[]
 for label,changed in [('control',source),('mutation',source.replace(old,new))]:
  code=f'''import importlib,pytest
assets=importlib.import_module("xverse_studio.lab.assets")
bindings=importlib.import_module("xverse_studio.lab.bindings")
advanced=importlib.import_module("xverse_studio.api.advanced")
mod=importlib.import_module("xverse_studio.lab.{module}")
exec(compile({changed!r},mod.__file__,"exec"),mod.__dict__)
bindings.inventory_observation=assets.inventory_observation
advanced.inventory_observation=assets.inventory_observation
advanced.resolve_physical_bindings=bindings.resolve_physical_bindings
raise SystemExit(pytest.main(["tests/integration/test_lab_assets.py","-q","--tb=short","-k",{selector!r},"--basetemp=.studio-local/t072/red-tmp/{name}-{label}"]))
'''
  r=subprocess.run([sys.executable,'-I','-B','-c',code],env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',TMPDIR=str(out)),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  (out/f'{name}-{label}.log').write_text(r.stdout);codes.append(r.returncode)
 results.append({'mutation':name,'module':module,'selector':selector,'controlExitCode':codes[0],'mutationExitCode':codes[1],'detected':codes==[0,1]})
 print(name,codes,flush=True)
(out/'red-checks.json').write_text(json.dumps(results,indent=2)+'\n')
assert all(r['detected'] for r in results)

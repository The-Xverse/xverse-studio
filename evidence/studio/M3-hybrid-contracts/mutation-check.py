from pathlib import Path
import json
import os
import subprocess
import sys

root=Path.cwd();out=root/'.studio-local/t076'
mutations=[
 ('receipt-as-source','time_quality','"sourceTick": observation.get("sourceTick")','"sourceTick": observation.get("sourceTick") or observation.get("recordedAt")','missing_clock_evidence'),
 ('unsupported-restore','recovery','if policy != "request_stop":','if False:','unadvertised_physical_recovery'),
 ('failed-restore-cleanup','recovery','elif observed.get("cleanupObserved") == "failed":\n            result["cleanup"] = "failed"','elif observed.get("cleanupObserved") == "failed":\n            result["cleanup"] = "complete"','provider_reported_restore_failure'),
]
results=[]
for name,module,old,new,selector in mutations:
 source=(root/f'services/studio-api/src/xverse_studio/lab/{module}.py').read_text();assert source.count(old)==1
 statuses=[]
 for label,code_source in [('control',source),('mutation',source.replace(old,new))]:
  code=f'''import importlib,pytest
import xverse_studio.lab as lab
mod=importlib.import_module("xverse_studio.lab.{module}")
exec(compile({code_source!r},mod.__file__,"exec"),mod.__dict__)
lab.handle_disconnect=importlib.import_module("xverse_studio.lab.recovery").handle_disconnect
lab.assess_time_quality=importlib.import_module("xverse_studio.lab.time_quality").assess_time_quality
raise SystemExit(pytest.main(["tests/integration/test_hybrid_time_and_loss.py","-q","--tb=short","-k",{selector!r},"--basetemp=.studio-local/t076/red-tmp/{name}-{label}"]))
'''
  run=subprocess.run([sys.executable,'-I','-B','-c',code],env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',TMPDIR=str(out)),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  (out/f'{name}-{label}.log').write_text(run.stdout);statuses.append(run.returncode)
 results.append({'mutation':name,'module':module,'selector':selector,'controlExitCode':statuses[0],'mutationExitCode':statuses[1],'detected':statuses==[0,1]})
 print(name,statuses,flush=True)
(out/'red-checks.json').write_text(json.dumps(results,indent=2)+'\n')
assert all(r['detected'] for r in results)

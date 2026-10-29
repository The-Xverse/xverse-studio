from pathlib import Path
import json
import os
import subprocess
import sys

root=Path.cwd();out=root/'.studio-local/t023-identity'
source=(root/'services/studio-api/src/xverse_studio/runs/service.py').read_text()
mutations=[
 ('birth-check','abs(process.create_time() - observed["createTime"]) > 0.001','False','reused_birth'),
 ('inspection-errors','except (OSError, ValueError, psutil.Error):','except (OSError, ValueError):','missing or denied'),
 ('unknown-shutdown','if run["state"] == "running":','if run["state"] in {"running", "unknown"}:','restart_rejects'),
]
results=[]
for name,old,new,selector in mutations:
 assert source.count(old)==1,(name,source.count(old))
 codes=[]
 for label,text in [('control',source),('mutation',source.replace(old,new))]:
  code=f'''import importlib, pytest
mod=importlib.import_module("xverse_studio.runs.service")
exec(compile({text!r},mod.__file__,"exec"),mod.__dict__)
raise SystemExit(pytest.main(["tests/platform/test_reconciliation_identity.py","-q","--tb=short","-k",{selector!r},"--basetemp=.studio-local/t023-identity/red-tmp/{name}-{label}"]))
'''
  result=subprocess.run([sys.executable,'-I','-B','-c',code],env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',TMPDIR=str(out)),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  (out/f'{name}-{label}.log').write_text(result.stdout);codes.append(result.returncode)
 results.append({'mutation':name,'selector':selector,'controlExitCode':codes[0],'mutationExitCode':codes[1],'detected':codes==[0,1]})
 print(name,codes,flush=True)
(out/'red-checks.json').write_text(json.dumps(results,indent=2)+'\n')
assert all(r['detected'] for r in results)

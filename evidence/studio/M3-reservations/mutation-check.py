from pathlib import Path
import json
import os
import subprocess
import sys

root=Path.cwd();out=root/'.studio-local/t073'
source=(root/'services/studio-api/src/xverse_studio/lab/reservations.py').read_text()
intent='self.records[reservation_id] = rec\n            self._save()\n            try:'
owner='and observed.get("owner") == rec["owner"]'
fence='(initial or observed["fencingIdentity"] == rec["fencingIdentity"])'
grant='if rec["scope"] != "observe" and rec["scope"] not in granted_scopes:'
release_start=source.index('    def release(');release_end=source.index('    def reconcile(',release_start)
release=source[release_start:release_end]
assert release.count('if rec["status"] != "owned":')==1
mutations=[
 ('intent-before-delegation',source.replace(intent,intent.replace('            self._save()\n',''),1),'persistence_failure_before_reserve'),
 ('owner-proof',source.replace(owner,'',1),'malformed_reservation_ack or renewal_cannot_change'),
 ('fence-proof',source.replace(fence,'True',1),'renewal_cannot_change'),
 ('revoked-grant',source.replace(grant,'if False:',1),'revoked_active_grant'),
 ('repeat-uncertain-release',source[:release_start]+release.replace('if rec["status"] != "owned":','if False:',1)+source[release_end:],'lost_release_ack_and_restart'),
]
results=[]
for name,mutated,selector in mutations:
 assert source!=mutated
 statuses=[]
 for label,selected_source in [('control',source),('mutation',mutated)]:
  code=f'''import importlib,pytest
import xverse_studio.lab as lab
mod=importlib.import_module("xverse_studio.lab.reservations")
exec(compile({selected_source!r},mod.__file__,"exec"),mod.__dict__)
lab.LabError=mod.LabError
lab.LabRegistry=mod.LabRegistry
raise SystemExit(pytest.main(["tests/integration/test_lab_reservations.py","-q","--tb=short","-k",{selector!r},"--basetemp=.studio-local/t073/red-tmp/{name}-{label}"]))
'''
  run=subprocess.run([sys.executable,'-I','-B','-c',code],env=dict(os.environ,PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',TMPDIR=str(out)),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  (out/f'{name}-{label}.log').write_text(run.stdout);statuses.append(run.returncode)
 results.append({'mutation':name,'selector':selector,'controlExitCode':statuses[0],'mutationExitCode':statuses[1],'detected':statuses==[0,1]})
 print(name,statuses,flush=True)
(out/'red-checks.json').write_text(json.dumps(results,indent=2)+'\n')
assert all(r['detected'] for r in results)

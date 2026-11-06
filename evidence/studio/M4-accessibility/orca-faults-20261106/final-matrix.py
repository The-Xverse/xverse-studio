from pathlib import Path
import json
import subprocess
import sys

local=Path(__file__).resolve().parent
cases=[(f'final-{name}-{w}',w,suite) for name,suite in [('fault','scenario-fault'),('source','scenario-fault-source'),('stimulus','scenario-stimulus')] for w in (1024,1440)]
completed=[]
for phase,width,suite in cases:
    result=subprocess.run([sys.executable,'-I',str(local/'run.py'),phase,str(width),suite],check=False)
    v=json.loads((local/phase/'verification.private.json').read_bytes())
    assert result.returncode==0 and v['isolatedExit']==0,phase
    assert v['copyMutationReadbackError'] is None and v['before']==v['after'],phase
    assert all(v[k] for k in ('originalRecordingUnchanged','copiedCanonicalUnchanged','sourceInputsUnchanged','uiInputsUnchanged','originalRootReleased')),phase
    completed.append({'phase':phase,'exit':result.returncode})
    (local/'matrix.private.json').write_text(json.dumps(completed,indent=2)+'\n')
    print(json.dumps(completed[-1]),flush=True)

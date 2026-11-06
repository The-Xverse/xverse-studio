from pathlib import Path
import json
import subprocess
import sys

local=Path(__file__).resolve().parent
cases=[(f'final-{name}-{width}',width,suite) for name,suite in [('observers','scenario-observer-metric'),('stimulus','scenario-stimulus'),('retained','retained-results')] for width in (1024,1440)]
completed=[]
for phase,width,suite in cases:
    argv=[sys.executable,'-I',str(local/'run.py'),phase,str(width),suite]
    if suite=='scenario-stimulus':argv.append('close-button')
    result=subprocess.run(argv,check=False)
    v=json.loads((local/phase/'verification.private.json').read_bytes())
    assert result.returncode==0 and v['isolatedExit']==0,phase
    assert v['copyMutationReadbackError'] is None and v['before']==v['after'],phase
    assert all(v[k] for k in ('originalRecordingUnchanged','copiedCanonicalUnchanged','sourceInputsUnchanged','uiInputsUnchanged','originalRootReleased')),phase
    completed.append({'phase':phase,'exit':result.returncode})
    (local/'matrix.private.json').write_text(json.dumps(completed,indent=2)+'\n')
    print(json.dumps(completed[-1]),flush=True)

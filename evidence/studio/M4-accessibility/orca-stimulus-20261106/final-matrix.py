from pathlib import Path
import json
import subprocess
import sys

local = Path(__file__).resolve().parent
cases = [(f'final-stimulus-{w}', w, 'scenario-stimulus', 'close-button', 0) for w in (1024,1440)]
cases += [(f'escape-{w}', w, 'scenario-stimulus', 'escape', 1) for w in (1024,1440)]
cases += [(f'final-{name}-{w}', w, suite, 'escape', 0) for name,suite in [('conditions','scenario-conditions'),('inventory','lab-inventory'),('retained','retained-results')] for w in (1024,1440)]
completed=[]
for phase,width,suite,exit_method,expected in cases:
    argv=[sys.executable,'-I',str(local/'run.py'),phase,str(width),suite]
    if suite=='scenario-stimulus':argv.append(exit_method)
    r=subprocess.run(argv,check=False)
    v=json.loads((local/phase/'verification.private.json').read_bytes())
    assert r.returncode==expected and v['isolatedExit']==expected, phase
    assert v['copyMutationReadbackError'] is None and v['before']==v['after'], phase
    assert all(v[k] for k in ('originalRecordingUnchanged','copiedCanonicalUnchanged','sourceInputsUnchanged','uiInputsUnchanged','originalRootReleased')),phase
    if expected:
        error=(local/phase/'browser.log').read_text()
        assert 'Actual Orca SSIP utterance deadline: View source for step' in error
        assert v['copyMutationReadback']['acceptedSemanticEdits']==1
    completed.append({'phase':phase,'expectedExit':expected,'actualExit':r.returncode})
    (local/'matrix.private.json').write_text(json.dumps(completed,indent=2)+'\n')
    print(json.dumps(completed[-1]),flush=True)

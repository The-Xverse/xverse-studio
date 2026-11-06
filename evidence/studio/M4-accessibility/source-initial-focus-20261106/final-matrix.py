from pathlib import Path
import json
import subprocess
import sys

local=Path(__file__).resolve().parent
cases=[('baseline-current-tools-1440',1440,'escape',1,'run-baseline.py')]
cases += [(f'final-{mode}-{width}',width,mode,0,'run.py') for mode in ('escape','close-button') for width in (1024,1440)]
completed=[]
for phase,width,mode,expected,runner in cases:
    argv=[sys.executable,'-I',str(local/runner),phase,str(width),'scenario-stimulus',mode]
    r=subprocess.run(argv,check=False)
    v=json.loads((local/phase/'verification.private.json').read_bytes())
    assert r.returncode==expected and v['isolatedExit']==expected,phase
    assert v['copyMutationReadbackError'] is None and v['before']==v['after'],phase
    assert all(v[k] for k in ('originalRecordingUnchanged','copiedCanonicalUnchanged','sourceInputsUnchanged','uiInputsUnchanged','originalRootReleased')),phase
    if expected:
        assert 'Actual Orca SSIP utterance deadline: View source for step' in (local/phase/'browser.log').read_text()
        assert v['copyMutationReadback']['acceptedSemanticEdits']==1
    completed.append({'phase':phase,'exit':r.returncode,'baselineExpectedFailure':bool(expected)})
    (local/'matrix.private.json').write_text(json.dumps(completed,indent=2)+'\n')
    print(json.dumps(completed[-1]),flush=True)
r=subprocess.run([sys.executable,'-I',str(local/'native.py'),'final-native'],check=False)
assert r.returncode==0
completed.append({'phase':'final-native','exit':r.returncode})
(local/'matrix.private.json').write_text(json.dumps(completed,indent=2)+'\n')
print(json.dumps(completed[-1]),flush=True)

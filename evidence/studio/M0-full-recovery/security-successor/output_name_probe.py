"""Owned local fixture: pinned output must still name caller's target on success."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import hashlib,json,os
from xverse_studio.storage.core import Store
from xverse_studio.host.recovery import backup_full

from pathlib import Path as _ReviewPath
_ReviewPath(".studio-local/review-temp").mkdir(parents=True, exist_ok=True)
_ReviewPath(".studio-local/review-pytest").mkdir(parents=True, exist_ok=True)
sources=['services/studio-api/src/xverse_studio/host/recovery.py','services/studio-api/src/xverse_studio/security/managed_io.py']
report={'sourceDigests':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources}}
with TemporaryDirectory(dir='.studio-local/review-temp',prefix='recovery-final-name-') as directory:
    base=Path(directory);source=base/'source';Store(source).put('project','owned',{'projectId':'owned'})
    target=base/'target';held=base/'held-output';foreign=base/'foreign';foreign.mkdir();(foreign/'sentinel').write_bytes(b'owned outside fixture')
    real_open=os.open;swaps=[]
    def race(name,flags,*args,**kwargs):
        if name=='manifest.json' and flags&os.O_CREAT and kwargs.get('dir_fd') is not None and not swaps:
            target.rename(held);foreign.rename(target);swaps.append(True)
        return real_open(name,flags,*args,**kwargs)
    try:
        with patch.object(os,'open',race):result=backup_full(source,target)
        report.update(outcome='RETURNED',integrity=result.get('integrity'))
    except Exception as exc:report.update(outcome='REJECTED',errorType=type(exc).__name__,code=str(exc))
    report.update(hookExecuted=bool(swaps),requestedTargetHasManifest=(target/'manifest.json').exists(),movedOriginalHasManifest=(held/'manifest.json').exists(),visibleForeignBytesUnchanged=(target/'sentinel').read_bytes()==b'owned outside fixture')
print(json.dumps(report,indent=2))

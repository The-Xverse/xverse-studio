"""A valid private backup/restore result must still name the reserved output root."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import hashlib
import json
import os
from xverse_studio.host.recovery import backup_full,restore_full
from xverse_studio.storage.core import Store

from pathlib import Path as _ReviewPath
_ReviewPath(".studio-local/review-temp").mkdir(parents=True, exist_ok=True)
_ReviewPath(".studio-local/review-pytest").mkdir(parents=True, exist_ok=True)

report={'sourceDigest':'sha256:'+hashlib.sha256(Path('services/studio-api/src/xverse_studio/host/recovery.py').read_bytes()).hexdigest(),'cases':{}}
for mode in ('backup','restore'):
    with TemporaryDirectory(dir='.studio-local/review-temp',prefix='recovery-output-binding-review-') as directory:
        base=Path(directory);source=base/'source';Store(source).put('project','owned-source',{'projectId':'owned-source'})
        saved=base/'saved';target=saved if mode=='backup' else base/'restored'
        if mode=='restore':backup_full(source,saved)
        foreign=base/'foreign';foreign.mkdir();(foreign/'outside-marker').write_bytes(b'OUTSIDE OWNED FIXTURE')
        held=base/'held-output';real_open=os.open;real_unlink=os.unlink;swaps=[]
        def swap():
            target.rename(held);foreign.rename(target);swaps.append(True)
        def raced_open(path,flags,*args,**kwargs):
            fd=kwargs.get('dir_fd')
            if mode=='backup' and not swaps and fd is not None and str(path)=='manifest.json' and os.fstat(fd).st_ino==target.stat().st_ino:swap()
            return real_open(path,flags,*args,**kwargs)
        def raced_unlink(path,*args,**kwargs):
            fd=kwargs.get('dir_fd')
            if mode=='restore' and not swaps and fd is not None and str(path)=='.recovery-incomplete' and os.fstat(fd).st_ino==target.stat().st_ino:swap()
            return real_unlink(path,*args,**kwargs)
        try:
            with patch.object(os,'supports_dir_fd',set(os.supports_dir_fd)|{raced_open,raced_unlink}),patch.object(os,'open',raced_open),patch.object(os,'unlink',raced_unlink):
                result=backup_full(source,target) if mode=='backup' else restore_full(saved,target)
            outcome={'result':'RETURNED','status':result.get('status'),'integrity':result.get('integrity')}
        except Exception as exc:outcome={'result':'REJECTED','errorType':type(exc).__name__,'detail':str(exc).replace(str(base),'<owned-fixture>')}
        outcome.update(hookExecuted=bool(swaps),requestedOutputHasDatabase=(target/'studio.sqlite').exists() if mode=='restore' else (target/'files/studio.sqlite').exists(),movedOwnedOutputHasDatabase=(held/'studio.sqlite').exists() if mode=='restore' else (held/'files/studio.sqlite').exists(),movedRestoreIncomplete=(held/'.recovery-incomplete').exists(),foreignSentinelUnchanged=(target/'outside-marker').read_bytes()==b'OUTSIDE OWNED FIXTURE' if swaps else (foreign/'outside-marker').read_bytes()==b'OUTSIDE OWNED FIXTURE')
        report['cases'][mode]=outcome
print(json.dumps(report,indent=2))

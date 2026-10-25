"""Owned fixture: late input namespace change must not leave unmarked failed restore."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import hashlib,json,os
from xverse_studio.storage.core import Store
from xverse_studio.host.recovery import backup_full,restore_full

from pathlib import Path as _ReviewPath
_ReviewPath(".studio-local/review-temp").mkdir(parents=True, exist_ok=True)
_ReviewPath(".studio-local/review-pytest").mkdir(parents=True, exist_ok=True)
report={'recoveryDigest':hashlib.sha256(Path('services/studio-api/src/xverse_studio/host/recovery.py').read_bytes()).hexdigest()}
with TemporaryDirectory(dir='.studio-local/review-temp',prefix='recovery-input-final-name-') as directory:
    base=Path(directory);source=base/'source';Store(source).put('project','owned',{'projectId':'owned'})
    backup=base/'backup';backup_full(source,backup);held=base/'held-backup';target=base/'target';swaps=[];original=os.unlink
    def race(name,*args,**kwargs):
        if name=='.recovery-incomplete' and kwargs.get('dir_fd') is not None and not swaps:
            backup.rename(held);swaps.append(True)
        return original(name,*args,**kwargs)
    try:
        with patch.object(os,'unlink',race):result=restore_full(backup,target)
        report.update(outcome='RETURNED',result=result)
    except Exception as exc:report.update(outcome='REJECTED',type=type(exc).__name__,code=str(exc))
    report.update(hookExecuted=bool(swaps),restoredDatabasePresent=(target/'studio.sqlite').exists(),incompleteMarkerPresent=(target/'.recovery-incomplete').exists())
print(json.dumps(report,indent=2))

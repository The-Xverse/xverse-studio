"""Owned-fixture namespace replacement must not change the already locked root."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import hashlib
import json
import os
import sqlite3
from xverse_studio.storage.core import Store
from xverse_studio.host.recovery import backup_full

from pathlib import Path as _ReviewPath
_ReviewPath(".studio-local/review-temp").mkdir(parents=True, exist_ok=True)
_ReviewPath(".studio-local/review-pytest").mkdir(parents=True, exist_ok=True)

paths=['services/studio-api/src/xverse_studio/host/recovery.py','services/studio-api/src/xverse_studio/security/managed_io.py']
report={'sourceDigests':{p:'sha256:'+hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}}
with TemporaryDirectory(dir='.studio-local/review-temp',prefix='recovery-root-replacement-review-') as directory:
    base=Path(directory);source=base/'source';foreign=base/'foreign';held=base/'held-original';saved=base/'backup'
    Store(source).put('project','owned-source',{'projectId':'owned-source'})
    Store(foreign).put('project','foreign-fixture',{'projectId':'foreign-fixture'})
    original=source.joinpath('studio.sqlite').read_bytes();outside=foreign.joinpath('studio.sqlite').read_bytes();real_open=os.open;calls=[];swaps=[]
    def race(path,flags,*args,**kwargs):
        descriptor=kwargs.get('dir_fd')
        component=descriptor is not None and str(path)=='source' and os.fstat(descriptor).st_ino==base.stat().st_ino
        leaf=descriptor is not None and str(path)=='studio.sqlite' and os.fstat(descriptor).st_ino==source.stat().st_ino
        if component:calls.append(True)
        attack=(component and len(calls)==2) or leaf
        if not attack or swaps:return real_open(path,flags,*args,**kwargs)
        source.rename(held);foreign.rename(source);swaps.append(True)
        try:return real_open(path,flags,*args,**kwargs)
        finally:source.rename(foreign);held.rename(source)
    try:
        with patch.object(os,'supports_dir_fd',set(os.supports_dir_fd)|{race}),patch.object(os,'open',race):result=backup_full(source,saved)
        with sqlite3.connect(saved/'files/studio.sqlite') as db:copied=sorted(row[0] for row in db.execute("SELECT id FROM records WHERE kind='project'"))
        report.update(result='RETURNED',integrity=result.get('integrity'),backupProjectIds=copied)
    except Exception as exc:report.update(result='REJECTED',errorType=type(exc).__name__,detail=str(exc).replace(str(base),'<owned-fixture>'))
    report.update(hookExecuted=bool(swaps),sourceDirectoryAcquisitions=len(calls),originalDatabaseUnchanged=source.joinpath('studio.sqlite').read_bytes()==original,foreignDatabaseUnchanged=foreign.joinpath('studio.sqlite').read_bytes()==outside)
print(json.dumps(report,indent=2))

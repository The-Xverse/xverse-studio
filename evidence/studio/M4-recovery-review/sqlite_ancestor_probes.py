"""Owned fixtures only: race source/target namespace during SQLite acquisition."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import hashlib
import json
import sqlite3
from xverse_studio.storage.core import Store
from xverse_studio.host.recovery import backup_full

from pathlib import Path as _ReviewPath
_ReviewPath(".studio-local/review-temp").mkdir(parents=True, exist_ok=True)
_ReviewPath(".studio-local/review-pytest").mkdir(parents=True, exist_ok=True)

original_connect=sqlite3.connect
report={'sourceDigest':'sha256:'+hashlib.sha256(Path('services/studio-api/src/xverse_studio/host/recovery.py').read_bytes()).hexdigest(),'cases':{}}
def projects(path):
    with original_connect(path) as db:
        return sorted(row[0] for row in db.execute("SELECT id FROM records WHERE kind='project'"))
for mode in ('source','destination'):
    with TemporaryDirectory(dir='.studio-local/review-temp',prefix='sqlite-ancestor-review-') as directory:
        root=Path(directory);source=root/'source';outside=root/'outside';saved=root/'backup'
        Store(source).put('project','owned-source',{'projectId':'owned-source'})
        Store(outside).put('project','outside-fixture',{'projectId':'outside-fixture'})
        original_outside=(outside/'studio.sqlite').read_bytes();calls=[];swaps=[]
        def race(path,*args,**kwargs):
            name=str(path)
            if mode=='source' and name.startswith((source/'studio.sqlite').as_uri()):
                calls.append(name)
                attack=len(calls)==2
                parent=source
            else:
                attack=mode=='destination' and name==str(saved/'files/studio.sqlite')
                parent=saved/'files'
            if not attack:return original_connect(path,*args,**kwargs)
            held=parent.with_name(parent.name+'-review-held')
            parent.rename(held);parent.symlink_to(outside,target_is_directory=True);swaps.append(True)
            try:return original_connect(path,*args,**kwargs)
            finally:parent.unlink();held.rename(parent)
        try:
            with patch.object(sqlite3,'connect',side_effect=race):
                result=backup_full(source,saved)
            outcome={'result':'RETURNED','integrity':result.get('integrity'),'backupProjects':projects(saved/'files/studio.sqlite')}
        except Exception as exc:
            outcome={'result':'ERROR','errorType':type(exc).__name__,'detail':str(exc).replace(str(root),'<owned-fixture>')}
        outcome.update(ancestorSwapTriggered=bool(swaps),sourceProjects=projects(source/'studio.sqlite'),outsideProjects=projects(outside/'studio.sqlite'),outsideBytesUnchanged=(outside/'studio.sqlite').read_bytes()==original_outside)
        report['cases'][mode]=outcome
print(json.dumps(report,indent=2))

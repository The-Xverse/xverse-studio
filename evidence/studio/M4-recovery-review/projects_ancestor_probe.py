"""Deterministic owned-fixture parent-link race; no outside user data is accessed."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import hashlib
import json
import os
from xverse_studio.projects.service import Projects
from xverse_studio.storage.core import Store
from xverse_studio.xdl import XDLAdapter

from pathlib import Path as _ReviewPath
_ReviewPath(".studio-local/review-temp").mkdir(parents=True, exist_ok=True)
_ReviewPath(".studio-local/review-pytest").mkdir(parents=True, exist_ok=True)

source = Path('services/studio-api/src/xverse_studio/projects/service.py')
report = {'sourceDigest':'sha256:'+hashlib.sha256(source.read_bytes()).hexdigest()}
with TemporaryDirectory(dir='.studio-local/review-temp',prefix='project-ancestor-review-') as directory:
    root = Path(directory)
    projects=Projects(Store(root/'state'),XDLAdapter())
    project=projects.create('Owned parent race fixture')
    docid=next(iter(project['documents']))
    target=projects.document_path(project['projectId'],docid)
    original=target.read_bytes()
    outside=root/'outside-fixture';outside.mkdir()
    sentinel=b'OUTSIDE OWNED FIXTURE CONTENT MUST NEVER BE RETURNED'
    (outside/target.name).write_bytes(sentinel)
    parent=target.parent;held=parent.with_name(parent.name+'-review-held');original_open=os.open;swapped=[]
    def race(path,flags,*args,**kwargs):
        directory = kwargs.get('dir_fd')
        absolute_target = Path(path) == target
        anchored_leaf = (directory is not None and str(path) == target.name
                         and os.fstat(directory).st_ino == parent.stat().st_ino)
        if not absolute_target and not anchored_leaf:
            return original_open(path,flags,*args,**kwargs)
        parent.rename(held);parent.symlink_to(outside,target_is_directory=True);swapped.append(True)
        try:return original_open(path,flags,*args,**kwargs)
        finally:parent.unlink();held.rename(parent)
    try:
        # Preserve the actual Linux capability while instrumenting the syscall.
        with patch.object(os,'supports_dir_fd',set(os.supports_dir_fd)|{race}), patch.object(os,'open',race):
            result=projects._read_file(target)
        report.update(result='RETURNED',returnedOutsideSentinel=result==sentinel,returnedOriginalSource=result==original)
    except Exception as exc:
        report.update(result='REJECTED',errorType=type(exc).__name__,detail=str(exc))
    report.update(ancestorSwapTriggered=bool(swapped),originalBytesRestored=target.read_bytes()==original,outsideFixtureUnchanged=(outside/target.name).read_bytes()==sentinel)
print(json.dumps(report,indent=2))

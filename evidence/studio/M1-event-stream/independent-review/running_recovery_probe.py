"""Emit the actual production resync response for a disposable running prefix."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from xverse_studio.events import EventStreams
from xverse_studio.storage.core import Store
ROOT=Path(__file__).resolve().parents[4]
FILES=['services/studio-api/src/xverse_studio/events/__init__.py','apps/studio-web/src/features/runs/sessionProtocol.ts','apps/studio-web/src/features/runs/session.ts','apps/studio-web/src/app/App.tsx']
def hashes(): return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES}
spec=importlib.util.spec_from_file_location('running_fixture',ROOT/'tests/fixtures/evidence/stream_fixtures.py');fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
if __name__=='__main__':
    before=hashes()
    with tempfile.TemporaryDirectory(prefix='running-recovery-',dir=ROOT/'.studio-local/review-temp') as d:
        base=Path(d);source=fixture.AdvancingJournal(base/'journal');source.append(3);raw=source.path.read_bytes()
        class Runs:
            def read(self,rid): return {**source.read(rid),'stateVersion':1}
            def directory(self,rid): return source.directory(rid)
        response=EventStreams(Store(base/'store'),Runs()).resync(source.run_id)
        result={'sourceBefore':before,'sourceAfter':hashes(),'response':response,'originalJournalUnchanged':source.path.read_bytes()==raw,'scope':'Actual EventStreams.resync on a new running hash-verified prefix; no runtime launched.'}
    print(json.dumps(result,indent=2))

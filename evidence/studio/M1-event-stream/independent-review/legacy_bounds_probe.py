"""Independent legacy contiguous-prefix and oversized-boundary checks."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from xverse_studio.events import EventStreams
from xverse_studio.storage.core import Store,Problem
ROOT=Path(__file__).resolve().parents[4]
FILES=['services/studio-api/src/xverse_studio/events/__init__.py','services/studio-api/src/xverse_studio/api/app.py']
def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES}
spec=importlib.util.spec_from_file_location('legacy_bounds_fixture',ROOT/'tests/fixtures/evidence/stream_fixtures.py');fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
def rejection(fn):
 try:fn()
 except Problem as error:return {'code':error.code,'status':error.status,'hasRecoveryRoutes':all(key in error.details for key in ['stateUrl','historyUrl','resyncUrl'])}
 raise AssertionError('Expected typed frame refusal')
if __name__=='__main__':
 before=hashes()
 with tempfile.TemporaryDirectory(prefix='legacy-bounds-',dir=ROOT/'.studio-local/review-temp') as d:
  base=Path(d);source=fixture.AdvancingJournal(base/'pressure');source.append(5,message='☀'*700);source.state='stopped';original=source.path.read_bytes()
  manager=EventStreams(Store(base/'store'),source,pending_bytes=8192,max_frame_bytes=4096,poll_interval=0)
  state=manager.prepare(source.run_id,version='1.0');sequences=[];batch_sizes=[]
  for _ in range(10):
   batch,ended,resync=manager._batch(source.run_id,state)
   assert not resync
   batch_sizes.append(sum(len(frame.encode()) for frame,_,_ in batch))
   for frame,q,proof in batch:
    sequences.append(q);state.update(sequence=q,digest=proof)
   if ended:break
  assert sequences==[1,2,3,4,5] and max(batch_sizes)<=8192-4096
  assert original==source.path.read_bytes()
  huge=fixture.AdvancingJournal(base/'huge');huge.append(message='☀'*5000);huge.state='stopped';huge_raw=huge.path.read_bytes()
  big_manager=EventStreams(Store(base/'big-store'),huge,pending_bytes=8192,max_frame_bytes=2048)
  early=rejection(lambda:big_manager.prepare(huge.run_id,version='1.0'));assert early['status']==413 and early['hasRecoveryRoutes']
  later=fixture.AdvancingJournal(base/'later');later.append(message='Small first original record');later.append(message='☀'*5000);later.state='stopped';later_raw=later.path.read_bytes()
  later_manager=EventStreams(Store(base/'later-store'),later,pending_bytes=8192,max_frame_bytes=2048)
  p=later_manager.prepare(later.run_id,version='1.0');batch,_,_=later_manager._batch(later.run_id,p)
  assert [q for _,q,_ in batch]==[1]
  _,q,proof=batch[-1];p.update(sequence=q,digest=proof)
  after_prefix=rejection(lambda:later_manager._batch(later.run_id,p));reconnect=rejection(lambda:later_manager.prepare(later.run_id,'1','1.0'))
  assert after_prefix['status']==reconnect['status']==413
  assert huge.path.read_bytes()==huge_raw and later.path.read_bytes()==later_raw
  result={'sourceBefore':before,'sourceAfter':hashes(),'legacyBytePressure':{'deliveredSequences':sequences,'batchBytes':batch_sizes,'sourceUnchanged':True},'firstOversizedPrepare':early,'laterOversized':{'precedingPrefix':[1],'nextBatch':after_prefix,'reconnectPrepare':reconnect,'sourcesUnchanged':True},'scope':'Direct production prepare/batch on new synthetic fixture journals; no API/server/browser/runtime launch.'}
 print(json.dumps(result,indent=2))

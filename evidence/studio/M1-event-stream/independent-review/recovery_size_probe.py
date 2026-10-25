"""Compare actual recovery JSON bytes with the browser's advertised read cap."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from xverse_studio.events import EventStreams
from xverse_studio.storage.core import Store,Problem,canonical
ROOT=Path(__file__).resolve().parents[4]
FILES=['services/studio-api/src/xverse_studio/events/__init__.py','apps/studio-web/src/features/runs/session.ts','apps/studio-web/src/features/runs/sessionProtocol.ts']
def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES}
spec=importlib.util.spec_from_file_location('size_fixture',ROOT/'tests/fixtures/evidence/stream_fixtures.py');fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
if __name__=='__main__':
 before=hashes()
 with tempfile.TemporaryDirectory(prefix='recovery-size-',dir=ROOT/'.studio-local/review-temp') as d:
  base=Path(d);source=fixture.AdvancingJournal(base/'journal');source.append(200,message='x'*5000);source.state='stopped';raw=source.path.read_bytes()
  summary={'requiredAssertions':32,'attemptedDefinitions':0,'counts':{'not_started':32},'definitions':[{'definitionRef':'assertion-'+str(i)+'x'*240,'definitionDigest':'sha256:'+'a'*64,'evaluationId':None,'status':'not_started','verdict':None,'coverage':None,'reasons':[]} for i in range(32)],'metricDefinitions':0,'metricJobs':[],'diagnostics':[]}
  class Runs:
   def read(self,rid):return {**source.read(rid),'stateVersion':1,'evaluation':'not_started','verdict':None,'evaluationSummary':summary}
   def directory(self,rid):return source.directory(rid)
  response=EventStreams(Store(base/'store'),Runs()).resync(source.run_id)
  try:
   EventStreams(Store(base/'small-store'),Runs(),pending_bytes=8192,max_frame_bytes=4096).resync(source.run_id)
  except Problem as error:
   metadata_refusal={'limitBytes':8192,'code':error.code,'status':error.status,'retrievalRoutes':all(k in error.details for k in ['stateUrl','historyUrl','resyncUrl'])}
  else: raise AssertionError('Metadata alone must refuse rather than exceed configured response budget')
  result={'metadataAloneRefusal':metadata_refusal,'sourceBefore':before,'sourceAfter':hashes(),'encodedResponseBytes':len(canonical(response).encode()),'browserRecoveryBytes':1048576,'encodedHistoryItemsBytes':sum(len(canonical(r).encode()) for r in response['history']['items']),'encodedRunBytes':len(canonical(response['run']).encode()),'returnedHistoryRecords':len(response['history']['items']),'omittedRecords':response['history']['omittedRecords'],'readerIntegrity':response['history']['integrity'],'originalJournalUnchanged':source.path.read_bytes()==raw,'scope':'Production resync over synthetic valid log journal and realistic32-definition summary shape; no actual project32-definition admission or runtime/browser execution claimed.'}
 print(json.dumps(result,indent=2))

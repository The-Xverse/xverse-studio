"""Disposable fork checks legacy inspection vs proof-bearing stream versions."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from xverse_studio.events import EventStreams,encode_cursor
from xverse_studio.storage.core import Store,Problem,canonical
ROOT=Path(__file__).resolve().parents[4]
FILES=['services/studio-api/src/xverse_studio/events/__init__.py','services/studio-api/src/xverse_studio/api/app.py']
def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES}
spec=importlib.util.spec_from_file_location('legacy_fixture',ROOT/'tests/fixtures/evidence/stream_fixtures.py');fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
if __name__=='__main__':
 before=hashes()
 with tempfile.TemporaryDirectory(prefix='legacy-proof-',dir=ROOT/'.studio-local/review-temp') as d:
  base=Path(d);source=fixture.AdvancingJournal(base/'journal');source.append(2);streams=EventStreams(Store(base/'store'),source)
  old_digest=source.records[0]['digest'];old_cursor=encode_cursor(source.run_id,source.snapshot_id,1,old_digest)
  source.records[0]['payload']['message']='New owned internally valid generation'
  previous='0'*64
  for row in source.records:
   row.pop('digest',None);row['previousDigest']=previous;previous=hashlib.sha256(canonical(row).encode()).hexdigest();row['digest']=previous
  source.path.write_text(''.join(canonical(r)+'\n' for r in source.records),encoding='utf-8');raw=source.path.read_bytes()
  outcomes=[]
  for version,cursor in [('1.0','1'),('1.1','1'),('1.1',source.run_id+':1'),('1.1',old_cursor)]:
   try:
    accepted=streams.prepare(source.run_id,cursor,version)
    outcomes.append({'version':version,'cursorKind':'proof' if cursor.startswith('st1.') else 'legacy','accepted':True,'sequence':accepted['sequence'],'usesNewGenerationProof':accepted['digest']==source.records[0]['digest']})
   except Problem as error:outcomes.append({'version':version,'cursorKind':'proof' if cursor.startswith('st1.') else 'legacy','accepted':False,'code':error.code,'status':error.status})
  result={'sourceBefore':before,'sourceAfter':hashes(),'cases':outcomes,'oldAndNewFirstDigestDiffer':old_digest!=source.records[0]['digest'],'originalJournalUnchangedByInspection':source.path.read_bytes()==raw,'scope':'Synthetic valid-chain replacement with production prepare; not a native/browser/runtime recovery claim.'}
 print(json.dumps(result,indent=2))

"""Hash-consistent malformed identity fixtures; no live evidence claim."""
from copy import deepcopy
import hashlib,json
from pathlib import Path
from tempfile import TemporaryDirectory
from xverse_studio.evidence.reader import read_journal
from xverse_studio.evidence.query import project_evidence,HistoryQuery
from xverse_studio.storage.core import canonical,digest
ROOT=Path(__file__).resolve().parents[4];TEMP=ROOT/'.studio-local/review-temp';TEMP.mkdir(parents=True,exist_ok=True)
paths=['services/studio-api/src/xverse_studio/evidence/reader.py','services/studio-api/src/xverse_studio/evidence/query.py']
def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
def row(identifier,sequence,receipt):return {'schemaVersion':'1.0','eventId':identifier,'runId':'fixture','snapshotId':'snapshot','sequence':sequence,'type':'observation.available','recordedAt':receipt,'sourceTime':{'tick':'0','clockDomain':'fixture-clock','resolution':'nanosecond'},'source':{'providerId':'fixture','version':'1.0.0'},'elementRefs':[],'evidenceClass':'unknown','payload':{'observerRef':'observer','values':{'value':0,'flag':False},'units':{'value':'1'}}}
def read(root,rows):
 previous='0'*64;lines=[]
 for original in rows:
  body={**deepcopy(original),'previousDigest':previous};previous=hashlib.sha256(canonical(body).encode()).hexdigest();body['digest']=previous;lines.append(canonical(body)+'\n')
 raw=''.join(lines).encode();root.mkdir();(root/'evidence.jsonl').write_bytes(raw);records,integrity=read_journal(root,{'runId':'fixture','snapshotId':'snapshot','state':'stopped','journalDigest':digest(raw)})
 return records,integrity,root.joinpath('evidence.jsonl').read_bytes()==raw
report={'sourceBefore':hashes(),'scope':'Synthetic hash-consistent reader metadata; no processes, physical devices, Windows or live provider claim'}
with TemporaryDirectory(dir=TEMP,prefix='independent-evidence-identities-') as directory:
 base=Path(directory)
 originals=[row('same-id','1','2026-01-01T00:00:00Z'),row('same-id','2','2026-01-02T00:00:00Z')]
 records,integrity,unchanged=read(base/'duplicate',originals)
 result=project_evidence(records,integrity,HistoryQuery(),'fixture','history')
 report['duplicateEventIds']={'integrity':integrity,'returnedRecords':len(records),'rawReceiptTimes':[r['recordedAt'] for r in result['items']],'presentationCount':len(result['presentation']),'firstProjectedReceipt':result['presentation'].get('same-id',{}).get('recordedAtUtc'),'sourceBytesUnchanged':unchanged}
 report['malformedSequences']=[]
 for index,value in enumerate([True,1.5,'01','+1',' 1 ']):
  records,integrity,unchanged=read(base/('sequence-'+str(index)),[row('event',value,'2026-01-01T00:00:00Z')])
  report['malformedSequences'].append({'sequence':value,'integrity':integrity,'returnedRecords':len(records),'sourceBytesUnchanged':unchanged})
report['sourceAfter']=hashes();print(json.dumps(report,indent=2))

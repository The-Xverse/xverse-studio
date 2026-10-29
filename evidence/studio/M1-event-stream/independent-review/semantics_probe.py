"""Finite synthetic-journal independent transport probes, no runtime operations."""
import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from xverse_studio.events import EventStreams, encode_cursor
from xverse_studio.evidence.reader import read_journal
from xverse_studio.storage.core import Store, Problem, canonical, digest
ROOT=Path(__file__).resolve().parents[4]
FILES=['services/studio-api/src/xverse_studio/events/__init__.py','services/studio-api/src/xverse_studio/api/app.py','services/studio-api/src/xverse_studio/evidence/reader.py']
def hashes(): return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES}
spec=importlib.util.spec_from_file_location('independent_fixture',ROOT/'tests/fixtures/evidence/stream_fixtures.py')
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
def rehash(source):
    previous='0'*64
    for row in source.records:
        row.pop('digest',None);row['previousDigest']=previous
        previous=hashlib.sha256(canonical(row).encode()).hexdigest();row['digest']=previous
    source.previous=previous
    source.path.write_text(''.join(canonical(r)+'\n' for r in source.records),encoding='utf-8')
def parsed(frame):
    return [json.loads(line[6:]) for line in frame.splitlines() if line.startswith('data: ')]
async def probe(base):
    outcomes=[]
    source=fixture.AdvancingJournal(base/'normal');source.append(12,message='☀'*700)
    original=source.path.read_bytes()
    streams=EventStreams(Store(base/'store'),source,pending_events=4,pending_bytes=8192,max_frame_bytes=4096,poll_interval=0)
    prepared=streams.prepare(source.run_id,version='1.1')
    frames,ended,resync=streams._batch(source.run_id,prepared)
    bodies=[parsed(f[0])[0] for f in frames]
    gap=bodies[0]
    canonical_rows=[r for r in bodies if r['type']!='stream.gap']
    assert gap['firstMissingSequence']=='1' and int(gap['lastMissingSequence'])+1==int(canonical_rows[0]['sequence'])
    assert gap['missingCount']==int(gap['lastMissingSequence'])
    assert sum(len(f[0].encode()) for f in frames)<=8192
    assert len(canonical_rows)<=4 and all(len(f[0].encode())<=4096 for f in frames)
    outcomes.append({'case':'unicode_record_byte_pressure','result':'PASS','gap':{k:gap[k] for k in ('firstMissingSequence','lastMissingSequence','missingCount','reason')},'batchBytes':sum(len(f[0].encode()) for f in frames),'canonicalFrames':len(canonical_rows)})
    recovery=streams.resync(source.run_id)
    assert recovery['watermark']['sequence']=='12' and recovery['watermark']['digest']==source.records[-1]['digest']
    assert recovery['history']['omittedRecords']==12-len(recovery['history']['items'])
    outcomes.append({'case':'resync_omissions_keep_exact_source_watermark','result':'PASS','omittedRecords':recovery['history']['omittedRecords']})
    ack=streams.prepare(source.run_id,encode_cursor(source.run_id,source.snapshot_id,1,source.records[0]['digest']),'1.1')
    source.records[0]['payload']['message']='New owned fork';rehash(source)
    fork_frames,_,need_resync=streams._batch(source.run_id,ack)
    fork=parsed(fork_frames[0][0])[0]
    assert need_resync and fork['type']=='stream.resync_required' and fork['missingCount'] is None
    outcomes.append({'case':'valid_hashchain_fork_after_ack','result':'PASS','reason':fork['reason'],'missingCount':fork['missingCount']})
    # Restore only our new fixture, then acknowledge all records in unknown state.
    source.path.write_bytes(original)
    source.state='unknown'
    records,integrity=read_journal(source.root,source.read(source.run_id))
    assert integrity=='verified_prefix'
    prepared=streams.prepare(source.run_id,encode_cursor(source.run_id,source.snapshot_id,len(records),records[-1]['digest']),'1.1')
    lease=streams.reserve(source.run_id)
    iterator=streams.iterate(source.run_id,prepared,lease)
    heartbeat=await anext(iterator)
    assert heartbeat==': heartbeat\n\n'
    await iterator.aclose();assert not streams.leases
    outcomes.append({'case':'unknown_is_live_and_iterator_close_releases','result':'PASS','integrity':integrity,'heartbeatOnly':True})
    assert source.path.read_bytes()==original
    # Malformed event kind in a new, internally hash-valid fixture.
    malformed=fixture.AdvancingJournal(base/'malformed-kind');malformed.append()
    malformed.records[0]['type']='log.appended\ndata: {"injected":true}'
    rehash(malformed)
    malformed.state='stopped';raw=malformed.path.read_bytes()
    manager=EventStreams(Store(base/'kind-store'),malformed)
    try:
        p=manager.prepare(malformed.run_id,version='1.1')
        emitted,_,_=manager._batch(malformed.run_id,p)
        body=emitted[0][0]
        outcome={'case':'embedded_newline_event_kind','transportDataLineCount':sum(line.startswith('data: ') for line in body.splitlines()),'typedRejection':False}
    except Problem as error:
        outcome={'case':'embedded_newline_event_kind','typedRejection':True,'code':error.code,'status':error.status,'integrity':error.details.get('integrity')}
    outcome.update(readerIntegrity=read_journal(malformed.root,malformed.read(malformed.run_id))[1],originalJournalUnchanged=malformed.path.read_bytes()==raw)
    outcomes.append(outcome)
    return {'cases':outcomes,'normalSourceUnchanged':source.path.read_bytes()==original,'scope':'Direct production EventStreams with newly created synthetic fixture journals; no process/device/browser operations.'}
if __name__=='__main__':
    before=hashes()
    with tempfile.TemporaryDirectory(prefix='event-semantics-',dir=ROOT/'.studio-local/review-temp') as directory:
        result=asyncio.run(asyncio.wait_for(probe(Path(directory)),timeout=15))
    print(json.dumps({'sourceBefore':before,'sourceAfter':hashes(),**result},indent=2))

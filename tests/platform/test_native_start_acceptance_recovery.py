"""Native backend death after real Start acceptance, before any worker launch.

The initial backend has a labelled test-only gate. Acceptance, files, SQLite,
HTTP and the restart remain real; no run/operation/owner record is rewritten.
The successor uses the ordinary native launcher. No equipment is involved.
"""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import sys
import time

import httpx
import psutil
import pytest

from test_native_recovery import eventually


GATE_SOURCE = '''from pathlib import Path
import json,os,sys,time
from xverse_studio.runs import service
from xverse_studio.host.launcher import main

mode=sys.argv.pop(1)
assert mode in ('before_private_files','before_worker_launch')
root=Path(sys.argv[sys.argv.index('--data-dir')+1])
marker=root/'accepted-start-gate.fixture.json'
def gate(rid):
    with marker.open('x') as stream:
        json.dump({'scope':'Test-only pause after actual durable Start acceptance, before any worker launch',
                   'backendPid':os.getpid(),'runId':rid,'boundary':mode},stream)
        stream.flush();os.fsync(stream.fileno())
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:time.sleep(.02)
    raise RuntimeError('Owned native crash fixture deadline expired before fault delivery')
if mode=='before_private_files':
    original=service.Runs._dispatch
    def dispatch(self,rid):
        gate(rid)
        return original(self,rid)
    service.Runs._dispatch=dispatch
else:
    original=service.subprocess.Popen
    def launch(argv,*args,**kwargs):
        directory=Path(argv[-1])
        assert argv==[sys.executable,'-I','-m','xverse_studio.providers.worker',str(directory)]
        assert directory.parent==root/'runs'
        gate(directory.name)
        return original(argv,*args,**kwargs)
    service.subprocess.Popen=launch
main()
'''


def disk_record(root, kind, identity):
    import sqlite3

    with sqlite3.connect((root/'studio.sqlite').as_uri()+'?mode=ro',uri=True) as db:
        row=db.execute('SELECT body FROM records WHERE kind=? AND id=?',(kind,identity)).fetchone()
    assert row is not None
    return json.loads(row[0])


@pytest.mark.parametrize('boundary', ['before_private_files','before_worker_launch'])
def test_native_start_acceptance_survives_backend_crash_without_blind_dispatch(
    tmp_path, record_property, boundary
):
    root=tmp_path/'Native accepted Start Ω with spaces'
    gate=tmp_path/'accepted_start_gate.py'
    gate.write_text(GATE_SOURCE)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        port=sock.getsockname()[1]
    url=f'http://127.0.0.1:{port}'
    tail=['--data-dir',str(root),'--port',str(port)]
    initial=[sys.executable,'-I',str(gate),boundary,*tail]
    successor=[sys.executable,'-I','-m','xverse_studio.host.launcher',*tail]
    process=None
    process_birth=None
    expected=None
    client=httpx.Client(base_url=url,headers={'Origin':url},timeout=10)
    pending_client=None
    pool=ThreadPoolExecutor(max_workers=1)

    def launch(argv):
        child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        return child,psutil.Process(child.pid).create_time()

    def original_backend():
        observed=psutil.Process(process.pid)
        assert process.poll() is None and observed.create_time()==process_birth
        assert observed.cmdline()==expected and observed.ppid()==psutil.Process().pid
        return observed

    def response(method,path,**kwargs):
        result=client.request(method,'/api/v1'+path,**kwargs)
        assert result.status_code in (200,201,202),result.text
        return result.json()

    try:
        expected=initial
        process,process_birth=launch(expected)
        eventually(lambda:client.get('/api/v1/session').status_code==401)
        boot=json.loads((root/'bootstrap.json').read_text())
        session=response('POST','/session',json={'bootstrapToken':boot['bootstrapToken']})
        client.headers['X-CSRF-Token']=session['csrfToken']
        project=response('POST','/projects',json={'name':'Owned accepted Start crash'})
        preflight=response('POST',f"/projects/{project['projectId']}/preflights",json={'revision':project['revision']})
        assert preflight['status']=='ready'
        snapshot=root/'snapshots'/preflight['snapshotId']/'snapshot.json'
        immutable=snapshot.read_bytes()
        body={'snapshotId':preflight['snapshotId'],'preflightId':preflight['preflightId']}
        headers={'Idempotency-Key':'native-accepted-once'}
        pending_client=httpx.Client(base_url=url,headers=dict(client.headers),cookies=client.cookies,timeout=20)
        pending=pool.submit(pending_client.post,'/api/v1/runs',headers=headers,json=body)
        marker=root/'accepted-start-gate.fixture.json'
        captured=eventually(lambda:json.loads(marker.read_text()))
        assert captured['boundary']==boundary and captured['backendPid']==process.pid
        rid=captured['runId']
        run=disk_record(root,'run',rid)
        operation=disk_record(root,'operation',run['operationId'])
        before_state='requested' if boundary=='before_private_files' else 'preparing'
        before_operation='accepted' if boundary=='before_private_files' else 'delegated'
        assert run['state']==before_state and operation['status']==before_operation
        assert 'pid' not in run and 'createTime' not in run
        native=original_backend()
        assert native.children(recursive=True)==[]
        directory=root/'runs'/rid
        retained={p.name:p.read_bytes() for p in directory.iterdir() if p.is_file()} if directory.exists() else {}
        if boundary=='before_private_files':
            assert not directory.exists() and retained=={}
        else:
            from xverse_studio.storage.core import digest
            argv=[sys.executable,'-I','-m','xverse_studio.providers.worker',str(directory)]
            assert run['launchArgvDigest']==digest(argv)
            assert run['ownerDigest']==digest((directory/'owner.key').read_bytes())
            request=json.loads((directory/'request.json').read_text())
            assert request['snapshot']['planDigest']==preflight['planDigest']
            assert (directory/'tmp').is_dir()
        # A second real HTTP request observes the committed fingerprint/result
        # while the original request is still paused before launch.
        retry=client.post('/api/v1/runs',headers=headers,json=body)
        assert retry.status_code==202,retry.text
        receipt=retry.json()
        assert receipt=={'runId':rid,'operationId':run['operationId'],'stateVersion':0}
        assert not pending.done() and original_backend().children(recursive=True)==[]
        process.kill()  # Only the exact Popen/birth/argv-verified test backend.
        process.wait(timeout=5)
        with pytest.raises(httpx.TransportError):
            pending.result(timeout=5)
        pending_client.close()
        pending_client=None

        expected=successor
        process,process_birth=launch(expected)
        eventually(lambda:client.get('/api/v1/session').status_code==200)
        original_backend()
        recovered=response('GET','/runs/'+rid)
        assert recovered['state']=='unknown' and recovered['reason']=='OWNERSHIP_UNKNOWN'
        assert recovered['cleanup']=='unknown' and recovered['evidence']=='partial'
        assert recovered['verdict'] is None and recovered['evidenceAvailability']=='unavailable'
        assert response('GET','/operations/'+run['operationId'])['status']=='unknown'
        assert client.post('/api/v1/runs',headers=headers,json=body).json()==receipt
        conflict=client.post('/api/v1/runs',headers=headers,json={**body,'preflightId':preflight['preflightId']+'-changed'})
        assert conflict.status_code==409 and conflict.json()['code']=='IDEMPOTENCY_CONFLICT'
        denied=client.post(f'/api/v1/runs/{rid}/commands',headers={'Idempotency-Key':'native-uncertain-stop'},json={'kind':'stop','expectedStateVersion':recovered['stateVersion']})
        assert denied.status_code==409 and denied.json()['code']=='STATE_CONFLICT'
        assert len(response('GET','/runs')['items'])==1
        assert original_backend().children(recursive=True)==[]
        assert 'pid' not in disk_record(root,'run',rid)
        assert snapshot.read_bytes()==immutable
        assert response('GET','/projects/'+project['projectId'])==project
        if boundary=='before_private_files':
            assert not directory.exists()
        else:
            assert {p.name:p.read_bytes() for p in directory.iterdir() if p.is_file()}==retained
            assert not (directory/'state.json').exists() and not (directory/'evidence.jsonl').exists()
        record_property('native_start_acceptance_recovery',json.dumps(dict(boundary=boundary,
            scope='Actual native backend death at labelled pre-launch fixture gate; ordinary native restart; no equipment',
            actualHost=sys.platform,backendPidBirthArgvVerified=True,initialState=before_state,
            initialOperation=before_operation,recoveredState='unknown',recoveredOperation='unknown',
            originalReceiptPreserved=True,immutableSnapshot=True,workerLaunchesObserved=0,
            noBlindDispatch=True,retainedPrivateBytesUnchanged=True)))
    finally:
        if process is not None and process.poll() is None:
            original_backend()
            process.terminate()
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                original_backend()
                process.kill()
                process.wait(timeout=5)
        if pending_client is not None:pending_client.close()
        pool.shutdown(wait=True)
        client.close()

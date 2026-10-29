"""Bounded read-only target tracing and failure capture before fixture teardown."""
from collections import deque
import hashlib
import json
import os
from pathlib import Path
import threading
import time

import pytest

TARGET='test_native_late_command_outcome_preserves_natural_completion_and_exact_retry'
events=deque(maxlen=12000)
dropped=0
case=None
case_index=0
output=Path(os.environ['COMMAND_HANDOFF_OUTPUT'])
output.mkdir()

def active():
    return case is not None and TARGET in case

def record(kind,**fields):
    global dropped
    if not active():return
    if len(events)==events.maxlen:dropped+=1
    events.append(dict(case=case,at=time.time(),monotonic=time.monotonic(),
                       thread=threading.get_ident(),kind=kind,
                       **json.loads(json.dumps(fields))))

def pytest_configure(config):
    import httpx
    from xverse_studio.runs.service import Runs
    from xverse_studio.storage.core import Store
    global originals
    originals=(Runs.read,Runs._reconcile_command,Runs._terminal_after_exit,
               Store.get,Store.put,Path.read_text,httpx.Response.json)
    read_run,reconcile,terminal,get,put,read_text,response_json=originals
    def observed_run(self,rid):
        record('run-read-entry',runId=rid)
        value=read_run(self,rid)
        record('run-read-return',body=value)
        return value
    def observed_reconcile(self,run,observed):
        record('reconcile-entry',run=run,observed=observed)
        value=reconcile(self,run,observed)
        record('reconcile-return',run=run)
        return value
    def observed_terminal(path,run):
        value=terminal(path,run)
        record('terminal-reacquisition',body=value)
        return value
    def observed_get(self,kind,identity,db=None):
        value=get(self,kind,identity,db)
        if db is None and kind in ('operation','run'):
            record('store-get',recordKind=kind,body=value)
        return value
    def observed_put(self,kind,identity,body,db=None):
        value=put(self,kind,identity,body,db)
        if db is None and kind in ('operation','run'):
            record('store-put',recordKind=kind,body=body)
        return value
    def observed_text(path,*args,**kwargs):
        value=read_text(path,*args,**kwargs)
        if active() and path.name=='state.json':
            record('state-file-read',body=json.loads(value),sha256=hashlib.sha256(value.encode()).hexdigest())
        return value
    def observed_json(self,*args,**kwargs):
        value=response_json(self,*args,**kwargs)
        if active():
            try:path=self.request.url.path
            except RuntimeError:path=''
            if path.startswith('/api/v1/operations/'):
                record('operation-response',body=value,status=self.status_code)
        return value
    Runs.read,Runs._reconcile_command=observed_run,observed_reconcile
    Runs._terminal_after_exit=staticmethod(observed_terminal)
    Store.get,Store.put,Path.read_text,httpx.Response.json=observed_get,observed_put,observed_text,observed_json

def pytest_runtest_logstart(nodeid,location):
    global case,case_index
    case=nodeid+'#'+str(case_index)
    case_index+=1
    record('case-start')

def capture(item):
    client=item.funcargs.get('client')
    if client is None:
        record('capture-unavailable',reason='No live client fixture')
        return
    studio=client.app.state.studio
    destination=output/('failed-'+str(case_index))
    destination.mkdir()
    with studio.store.lock:
        runs=studio.store.all('run')
        operations=studio.store.all('operation')
    (destination/'metadata.private.json').write_text(json.dumps(dict(runs=runs,operations=operations),indent=2)+'\n')
    for run in runs:
        directory=studio.runs.directory(run['runId'])
        saved=destination/run['runId']
        saved.mkdir()
        observations=[]
        # Explicit allowlist excludes owner.key, bootstrap/session files and DB.
        for name in ['state.json','evidence.jsonl','request.json','command.json']:
            path=directory/name
            try:
                before=path.stat()
                if before.st_size>64*1024*1024:
                    observations.append(dict(name=name,outcome='over-limit'))
                    continue
                data=path.read_bytes()
                after=path.stat()
                (saved/name).write_bytes(data)
                observations.append(dict(name=name,outcome='copied',bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),
                    stableAcquisition=(before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns)))
            except OSError as exc:
                observations.append(dict(name=name,outcome='unavailable',error=type(exc).__name__))
        snapshot=studio.store.root/'snapshots'/run['snapshotId']/'snapshot.json'
        try:(saved/'snapshot.json').write_bytes(snapshot.read_bytes())
        except OSError as exc:observations.append(dict(name='snapshot.json',outcome='unavailable',error=type(exc).__name__))
        (saved/'acquisition.private.json').write_text(json.dumps(dict(capturedBeforeFixtureTeardown=True,
            observedAt=time.time(),runId=run['runId'],observations=observations),indent=2)+'\n')
    record('failure-captured',runs=len(runs),beforeFixtureTeardown=True)

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item,call):
    outcome=yield
    report=outcome.get_result()
    if active() and report.when=='call':
        record('case-result',outcome=report.outcome,detail=report.longreprtext)
        if report.failed:
            try:capture(item)
            except Exception as exc:record('capture-error',error=type(exc).__name__,detail=str(exc))

def pytest_unconfigure(config):
    import httpx
    from xverse_studio.runs.service import Runs
    from xverse_studio.storage.core import Store
    Runs.read,Runs._reconcile_command,terminal,Store.get,Store.put,Path.read_text,httpx.Response.json=originals
    Runs._terminal_after_exit=staticmethod(terminal)
    with (output/'trace.private.json').open('x') as stream:
        json.dump(dict(scope='Read-only backend observations; original functions and native worker unchanged; observer timing effects possible',
                       eventBound=events.maxlen,droppedEvents=dropped,events=list(events)),stream,indent=2)

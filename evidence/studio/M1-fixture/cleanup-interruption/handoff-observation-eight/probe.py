"""Read-only instrumentation of actual owned command reconciliation; no outcome changes."""
import json
import os
from pathlib import Path
import time

events=[]
case=None
output=Path(os.environ['COMMAND_HANDOFF_TRACE'])

def pytest_configure(config):
    from xverse_studio.runs.service import Runs
    from xverse_studio.storage.core import Store
    global original_reconcile,original_put,original_read
    original_reconcile,original_put,original_read=Runs._reconcile_command,Store.put,Path.read_text
    def record(kind,**fields):
        events.append(dict(case=case,at=time.time(),kind=kind,**fields))
    def reconcile(self,run,observed):
        oid=run.get('pendingCommandId')
        before=self.store.get('operation',oid) if oid else None
        if oid:record('reconcile-before',runId=run['runId'],runState=run['state'],operation=before,observed=observed)
        result=original_reconcile(self,run,observed)
        if oid:record('reconcile-after',operation=self.store.get('operation',oid),pending=run.get('pendingCommandId'))
        return result
    def put(self,kind,identity,body,db=None):
        result=original_put(self,kind,identity,body,db)
        if kind=='operation':record('put-operation',body=json.loads(json.dumps(body)),transaction=db is not None)
        return result
    def read(path,*args,**kwargs):
        body=original_read(path,*args,**kwargs)
        if path.name=='state.json':
            try:record('actual-state-read',body=json.loads(body))
            except ValueError:record('malformed-state-read')
        return body
    Runs._reconcile_command,Store.put,Path.read_text=reconcile,put,read

def pytest_runtest_logstart(nodeid,location):
    global case
    case=nodeid+'#'+str(sum(e['kind']=='case-start' for e in events))
    events.append(dict(case=case,at=time.time(),kind='case-start'))

def pytest_collection_finish(session):
    events.append(dict(case=None,at=time.time(),kind='collection',selected=len(session.items)))

def pytest_runtest_logreport(report):
    if report.when=='call':events.append(dict(case=case,at=time.time(),kind='case-result',outcome=report.outcome,detail=report.longreprtext))

def pytest_unconfigure(config):
    from xverse_studio.runs.service import Runs
    from xverse_studio.storage.core import Store
    Runs._reconcile_command,Store.put,Path.read_text=original_reconcile,original_put,original_read
    with output.open('x') as stream:json.dump(events,stream,indent=2)

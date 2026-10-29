"""Actual owned-child failure cleanup; no CARLA/container acceptance substitution."""
from pathlib import Path
import selectors
import subprocess
import sys
import psutil
import pytest
from xverse_studio.providers.autoverse.worker import Demo, finish
from xverse_studio.storage.core import digest


def workload(tmp_path):
    process = subprocess.Popen([sys.executable,'-I','-c','import time; time.sleep(120)'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    owner=psutil.Process(process.pid)
    demo=Demo.__new__(Demo)
    demo.root=tmp_path
    demo.request={'runId':'run-test','snapshot':{}}
    demo.snapshot={'snapshotId':'snap-test'}
    demo.processes={'owned':{'process':process,'pid':process.pid,'createTime':owner.create_time(),'argvDigest':digest(owner.cmdline())}}
    demo.containers={};demo.lock=None;demo.selector=selectors.DefaultSelector()
    demo.state={'state':'running','stateVersion':2,'cleanup':'not_started','commandResults':{},'runtimeStatus':{}}
    demo.stop_command={'operationId':'op-stop'};demo.count=demo.journal_bytes=0;demo.previous='0'*64
    demo.journal=(tmp_path/'evidence.jsonl').open('xb',buffering=0)
    return demo,process


def test_failed_state_storage_cannot_prevent_real_owned_child_cleanup(tmp_path):
    demo,process=workload(tmp_path)
    def unavailable(): raise OSError('simulated storage failure')
    demo.save=unavailable
    try:
        assert finish(demo,False)==1
        assert process.poll() is not None
        assert demo.state['cleanup']=='complete'
        assert demo.state['evidence']=='partial'
        assert demo.state['evidenceFailure']=='AUTOVERSE_EVIDENCE_IO_FAILED'
        assert demo.journal.closed
    finally:
        if process.poll() is None: process.terminate();process.wait(timeout=5)


def test_birth_identity_mismatch_never_signals_an_unconfirmed_process(tmp_path):
    demo,process=workload(tmp_path)
    demo.processes['owned']['createTime']+=100
    try:
        demo.cleanup()
        assert process.poll() is None
        assert demo.state['cleanup']=='unknown'
        assert demo.state['cleanupResources']==[{'resourceId':'owned','kind':'process','status':'unknown'}]
    finally:
        process.terminate();process.wait(timeout=5);demo.journal.close()

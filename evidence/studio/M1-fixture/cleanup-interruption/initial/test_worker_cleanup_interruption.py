"""Real Linux x86-64 cleanup interruption in the original owned native worker.

The test parent traces only its verified child. It observes the actual rmdir
entry, queues SIGINT and detaches at its signal-delivery stop. No worker code,
register, return value, state file or clock is replaced. ptrace is contributor
fault tooling, never an application dependency or a Windows result.

Kernel ABI / signal-delivery semantics:
https://man7.org/linux/man-pages/man2/ptrace.2.html
"""

import ctypes
import hashlib
import json
import os
import platform
import signal
import sys
import time

import psutil
import pytest

from test_native_command_terminal_boundaries import (
    assert_original_process, journal, native_run, wait_actual_sample,
)
from xverse_studio.storage.core import canonical, digest


class OwnedCleanupTrace:
    # Linux UAPI: PTRACE_GET_SYSCALL_INFO (kernel >=5.3), x86-64 rmdir.
    SEIZE, INTERRUPT, GET_INFO = 0x4206, 0x4207, 0x420E
    SYSCALL, CONT, DETACH, PEEKDATA = 24, 7, 17, 2
    TRACESYSGOOD, EVENT_STOP, X86_64, RMDIR = 1, 128, 0xC000003E, 84

    class Info(ctypes.Structure):
        _fields_ = [('op', ctypes.c_uint8), ('pad', ctypes.c_uint8 * 3),
                    ('arch', ctypes.c_uint32), ('ip', ctypes.c_uint64),
                    ('sp', ctypes.c_uint64), ('nr', ctypes.c_uint64),
                    ('args', ctypes.c_uint64 * 6)]

    def __init__(self, child, directory, known):
        self.child, self.pid, self.directory, self.known = child, child.pid, directory, known
        self.call = ctypes.CDLL(None, use_errno=True).ptrace
        self.call.argtypes = [ctypes.c_uint, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]
        self.call.restype = ctypes.c_long
        self.attached, self.stopped = False, False

    def ptrace(self, request, address=0, data=0):
        ctypes.set_errno(0)
        result = self.call(request, self.pid, address, data)
        error = ctypes.get_errno()
        if result == -1 and error:
            raise OSError(error, 'Owned native ptrace fault prerequisite/operation failed')
        return result

    def wait_stop(self, deadline):
        while time.monotonic() < deadline:
            observed, status = os.waitpid(self.pid, os.WNOHANG | 0x40000000)  # __WALL
            if observed:
                assert observed == self.pid
                if os.WIFEXITED(status) or os.WIFSIGNALED(status):
                    self.child.returncode = os.waitstatus_to_exitcode(status)
                    self.attached = False
                    raise AssertionError('Original worker exited before the required cleanup stop')
                assert os.WIFSTOPPED(status), status
                self.stopped = True
                return status
            time.sleep(.001)
        raise AssertionError('Owned native cleanup trace exceeded its bounded deadline')

    def resume(self, request, delivered_signal=0):
        self.ptrace(request, data=delivered_signal)
        self.stopped = False

    def path_at(self, address):
        value = b''
        width = ctypes.sizeof(ctypes.c_long)
        while len(value) < 4096:
            word = self.ptrace(self.PEEKDATA, address + len(value))
            value += ctypes.c_ulong(word).value.to_bytes(width, sys.byteorder)
            if b'\0' in value:
                return os.fsdecode(value.split(b'\0', 1)[0])
        raise AssertionError('Owned rmdir pathname exceeded the read bound')

    def deliver_at_cleanup(self):
        assert_original_process(self.child, self.known, self.directory)
        deadline = time.monotonic() + 10
        original = (self.directory / 'tmp').stat()
        assert (self.directory / 'tmp').is_dir() and not (self.directory / 'tmp').is_symlink()
        observed_stops = 0
        try:
            self.ptrace(self.SEIZE, data=self.TRACESYSGOOD)
            self.attached = True
            self.ptrace(self.INTERRUPT)
            status = self.wait_stop(deadline)
            assert status >> 16 == self.EVENT_STOP
            self.resume(self.SYSCALL)
            while time.monotonic() < deadline and observed_stops < 4096:
                status = self.wait_stop(deadline)
                observed_stops += 1
                assert os.WSTOPSIG(status) == signal.SIGTRAP | 0x80, status
                info = self.Info()
                size = self.ptrace(self.GET_INFO, ctypes.sizeof(info), ctypes.byref(info))
                assert info.arch == self.X86_64 and info.op in (1, 2)
                if info.op == 1 and info.nr == self.RMDIR:
                    assert size >= ctypes.sizeof(info)
                    path = self.path_at(info.args[0])
                    assert path == str(self.directory / 'tmp'), path
                    current = (self.directory / 'tmp').stat()
                    assert (current.st_dev, current.st_ino) == (original.st_dev, original.st_ino)
                    # Do not call Popen.poll while tracing: waitpid owns these
                    # stops, which are not process exit notifications.
                    process = psutil.Process(self.pid)
                    assert process.create_time() == self.known['createTime']
                    assert digest(process.cmdline()) == self.known['launchArgvDigest']
                    state = json.loads((self.directory / 'state.json').read_text())
                    assert state['pid'] == self.pid and state['createTime'] == self.known['createTime']
                    assert state['ownerDigest'] == digest((self.directory / 'owner.key').read_bytes()) == self.known['ownerDigest']
                    # A signal argument at a syscall stop may be ignored.
                    # Queue a real signal, observe its delivery stop, then pass
                    # that same signal through normal kernel delivery.
                    process.send_signal(signal.SIGINT)
                    self.resume(self.CONT)
                    delivered = self.wait_stop(deadline)
                    assert os.WSTOPSIG(delivered) == signal.SIGINT and delivered >> 16 == 0
                    self.resume(self.DETACH, signal.SIGINT)
                    self.attached = False
                    return dict(syscall='rmdir', syscallNumber=self.RMDIR,
                        exactOwnedPathAndDirectoryIdentityVerified=True,
                        originalPidBirthArgvOwnerVerified=True,
                        realSignal='SIGINT', signalDeliveryStopObserved=True,
                        syscallStopsObserved=observed_stops)
                self.resume(self.SYSCALL)
            raise AssertionError('No actual owned rmdir entry observed within the trace bounds')
        finally:
            # Always release this original tracee, including assertion failures.
            # This affects no other process and supplies no invented outcome.
            if self.attached:
                if not self.stopped:
                    self.ptrace(self.INTERRUPT)
                    self.wait_stop(time.monotonic() + 5)
                self.resume(self.DETACH)
                self.attached = False


@pytest.mark.skipif(sys.platform != 'linux' or platform.machine() != 'x86_64',
                    reason='Linux x86-64 kernel>=5.3 owned syscall fault lane; no native Windows result')
@pytest.mark.parametrize('kind', ['duration', 'stop', 'cancel'])
def test_native_interrupt_at_owned_directory_release_preserves_known_stop_and_unknown_cleanup(
    client, record_property, kind
):
    project, preflight, start_body, start_receipt, run, directory, child, known, snapshot = native_run(client)
    studio = client.app.state.studio
    immutable, request = snapshot.read_bytes(), (directory / 'request.json').read_bytes()
    wait_actual_sample(directory, child)
    assert_original_process(child, known, directory)
    operation = None
    if kind != 'duration':
        body = {'kind': kind, 'expectedStateVersion': run['stateVersion']}
        headers = {'Idempotency-Key': 'cleanup-interrupted-' + kind}
        response = client.post(f"/api/v1/runs/{run['runId']}/commands", headers=headers, json=body)
        assert response.status_code == 202, response.text
        operation = response.json()
    witness = OwnedCleanupTrace(child, directory, known).deliver_at_cleanup()
    assert child.wait(timeout=10) == 1
    state = json.loads((directory / 'state.json').read_text())
    observed = client.get('/api/v1/runs/' + run['runId']).json()
    for result in [state, observed]:
        assert result['state'] == 'stopped'
        assert result['cleanup'] == 'unknown' and result['evidence'] == 'partial'
        assert result['reason'] == 'REFERENCE_CLEANUP_INTERRUPTED'
        assert result['cleanupResources'] == [{'resourceId': run['runId'] + ':temporary-directory',
            'kind': 'temporary-directory', 'status': 'unknown',
            'code': 'TEMPORARY_DIRECTORY_RELEASE_INTERRUPTED'}]
        assert 'journalDigest' not in result and 'eventCount' not in result
    assert observed['verdict'] is None and observed['effectivePlanDigest'] == preflight['planDigest']
    rows = journal(directory)
    assert any(row['type'] == 'observation.available' for row in rows)
    assert not any(row['type'] in ('cleanup.updated', 'evidence.updated') for row in rows)
    failures = [row for row in rows if row['type'] == 'log.appended' and row['payload'].get('code') == 'REFERENCE_CLEANUP_INTERRUPTED']
    assert len(failures) == 1
    previous = '0' * 64
    for sequence, original in enumerate(rows, 1):
        row = dict(original)
        signature = row.pop('digest')
        assert row['sequence'] == str(sequence) and row['previousDigest'] == previous
        assert hashlib.sha256(canonical(row).encode()).hexdigest() == signature
        previous = signature
    assert client.get(f"/api/v1/runs/{run['runId']}/history").json()['integrity'] == 'verified_prefix'
    sealed = (directory / 'evidence.jsonl').read_bytes()
    if operation:
        completed = client.get('/api/v1/operations/' + operation['operationId']).json()
        assert completed['status'] == 'completed'
        assert client.post(f"/api/v1/runs/{run['runId']}/commands", headers=headers, json=body).json() == operation
        assert sum(row['type'] == 'command.delegated' and row['payload']['operationId'] == operation['operationId'] for row in rows) == 1
    assert client.post('/api/v1/runs', headers={'Idempotency-Key': 'native-boundary-start'}, json=start_body).json() == start_receipt
    assert snapshot.read_bytes() == immutable and (directory / 'request.json').read_bytes() == request
    assert studio.projects.read(project['projectId']) == project
    assert len(studio.store.all('run')) == 1 and len(studio.store.all('operation')) == (2 if operation else 1)
    assert (directory / 'evidence.jsonl').read_bytes() == sealed
    record_property('native_cleanup_interruption', json.dumps(dict(kind=kind, witness=witness,
        lifecycle=observed['state'], cleanup=observed['cleanup'], evidence=observed['evidence'],
        originalWorkerExit=child.returncode, immutableInputs=True, noReplayOrRespawn=True,
        scope='Actual Linux x86-64 owned child interrupted at original rmdir; parent-only ptrace; no equipment')))

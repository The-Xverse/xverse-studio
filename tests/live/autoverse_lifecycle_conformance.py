"""Explicit native Autoverse lifecycle/restart cases for T021.

Uses the actual enrolled complete-demo target. Startup cancellation and loss are
negative executions, not complete-demo success. No project selects commands or
faults. Signals use original native handles verified against this run's owner.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import select
import signal
import socket
import sqlite3
import subprocess
import sys
import time
import uuid

import httpx
import psutil
from ruamel.yaml import YAML

from xverse_studio.blueprints.autoverse import documents, NAMESPACE
from xverse_studio.evidence.reader import read_journal
from xverse_studio.host.ownership import own_root, RootOwnedError
from xverse_studio.providers.autoverse.installation import container_fact
from xverse_studio.security.managed_io import create_directory
from xverse_studio.storage.core import atomic, canonical, digest
from xverse_studio.xdl.examples import dump_yaml

ROOT = Path(__file__).resolve().parents[2]
CASES = ['restart-natural', 'cancel-startup', 'component-loss']


def checked(response, status=200):
    assert response.status_code == status, (response.status_code, response.text[:1600])
    return response.json()


def wait(read, predicate, timeout=30):
    deadline, value = time.monotonic() + timeout, None
    while time.monotonic() < deadline:
        value = read()
        if predicate(value):
            return value
        time.sleep(0.1)
    raise AssertionError(('Native Autoverse observation deadline', value))


def private_record(data, kind, identity):
    with sqlite3.connect((data / 'studio.sqlite').as_uri() + '?mode=ro', uri=True) as db:
        row = db.execute('SELECT body FROM records WHERE kind=? AND id=?', (kind, identity)).fetchone()
        assert row is not None
        return json.loads(row[0])


class OriginalProcess:
    """An original Linux pidfd plus native birth/argv/owner witnesses."""

    def __init__(self, pid, birth, argv_digest, *, parent=None):
        p = psutil.Process(pid)
        assert p.uids().real == os.getuid() and p.create_time() == birth
        assert digest(p.cmdline()) == argv_digest
        if parent is not None:
            assert p.ppid() == parent
        self.process, self.pid, self.birth, self.argv_digest = p, pid, birth, argv_digest
        self.fd = os.pidfd_open(pid, 0)
        try:
            self.verify()
        except Exception:
            os.close(self.fd)
            raise

    def verify(self):
        p = self.process
        assert p.uids().real == os.getuid() and p.create_time() == self.birth
        assert digest(p.cmdline()) == self.argv_digest and not self.exited()

    def exited(self):
        return bool(select.select([self.fd], [], [], 0)[0])

    def send(self, number):
        self.verify()
        signal.pidfd_send_signal(self.fd, number, None, 0)

    def close(self):
        os.close(self.fd)


class NativeHost:
    def __init__(self, data, output, receipt, backend, static, *, host_arguments=(), register_provider=True, binding_timing=False, binding_profile=False):
        self.data, self.output, self.receipt = data, output, receipt
        self.backend, self.static = backend, static
        self.host_arguments = tuple(host_arguments)
        self.register_provider = register_provider
        assert not binding_timing or not register_provider
        self.binding_timing = binding_timing
        assert not binding_profile or binding_timing
        self.binding_profile = binding_profile
        self.child, self.log, self.number = None, None, 0
        with socket.socket() as s:
            s.bind(('127.0.0.1', 0))
            self.port = s.getsockname()[1]
        self.url = f'http://127.0.0.1:{self.port}'
        self.observations = []

    def start(self):
        assert self.child is None or self.child.poll() is not None
        self.number += 1
        argv = [str(self.backend), '-I', str(ROOT / 'tests/live/autoverse_admission_host.py'),
                '--receipt', str(self.receipt), '--data-dir', str(self.data),
                '--static-dir', str(self.static), '--port', str(self.port), '--fault', 'valid', *self.host_arguments]
        if not self.register_provider:
            assert not self.host_arguments
            argv = [str(self.backend), '-I', '-m', 'xverse_studio.host.launcher',
                    '--data-dir', str(self.data), '--port', str(self.port)]
            if self.binding_timing:
                argv = [str(self.backend), '-I', str(ROOT / 'tests/live/autoverse_binding_timing_host.py'),
                        '--data-dir', str(self.data), '--port', str(self.port)]
                if self.binding_profile:
                    argv += ['--profile-bindings']
            if self.static is not None:
                argv += ['--static-dir', str(self.static)]
        self.log = (self.output / f'host-{self.number}.log').open('xb')
        self.child = subprocess.Popen(argv, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=self.log, stderr=subprocess.STDOUT)
        p = psutil.Process(self.child.pid)
        # Retain this new original handle/identity before any acknowledgement
        # check. A failed second launch must never reuse the first owner's facts.
        self.owner = {'pid': p.pid, 'birth': p.create_time(), 'argv': argv, 'argvVerified': False}
        command = self.output / f'host-{self.number}-command.private.json'
        command.open('x').write(json.dumps(self.owner, indent=2) + '\n')
        def identity_acknowledged():
            assert self.child.poll() is None, 'Original backend exited before native identity acknowledgement'
            observation = {'birth': p.create_time(), 'parent': p.ppid(), 'uid': p.uids().real, 'argv': p.cmdline()}
            (self.output / f'host-{self.number}-identity.private.json').write_text(json.dumps(observation, indent=2) + '\n')
            return (observation['birth'] == self.owner['birth'] and observation['parent'] == os.getpid()
                    and observation['uid'] == os.getuid() and observation['argv'] == argv)
        wait(identity_acknowledged, bool, timeout=3)
        self.owner['argvVerified'] = True
        command.write_text(json.dumps(self.owner, indent=2) + '\n')
        def ready():
            assert self.child.poll() is None, 'Original Autoverse backend exited before readiness'
            try:
                return httpx.get(self.url + '/api/v1/session', timeout=1).status_code
            except httpx.HTTPError:
                return None
        wait(ready, lambda value: value == 401, timeout=45)
        return self.child.pid

    def stop(self, *, crash=False):
        child = self.child
        if child is None:
            return
        if child.poll() is None:
            p = psutil.Process(child.pid)
            assert p.create_time() == self.owner['birth'] and p.uids().real == os.getuid()
            if self.owner['argvVerified']:
                assert p.cmdline() == self.owner['argv']
            else:
                # This still is our unreaped native child, retained immediately
                # from Popen. No provider/foreign process may use this branch.
                assert p.ppid() == os.getpid()
            child.kill() if crash else child.terminate()
        child.wait(timeout=90)
        self.observations.append({'launch': self.number, 'originalIdentityVerified': True,
                                  'termination': 'original-handle SIGKILL' if crash else 'original-handle SIGTERM',
                                  'exit': child.returncode})
        assert child.returncode in (0, -signal.SIGKILL if crash else -signal.SIGTERM)
        self.log.close()
        self.child = None


def login(host):
    api = httpx.Client(base_url=host.url, headers={'Origin': host.url}, timeout=30)
    token = json.loads((host.data / 'bootstrap.json').read_bytes())['bootstrapToken']
    value = checked(api.post('/api/v1/session', json={'bootstrapToken': token}))
    api.headers['X-CSRF-Token'] = value['csrfToken']
    return api


def author(api):
    p = checked(api.post('/api/v1/projects', json={'name': 'Owned Autoverse lifecycle', 'blueprintRef': 'autoverse-classic'}), 201)
    variant = documents('studio-browser')
    source = YAML(typ='safe').load(variant['scenario.xdl.yaml'])
    source['extensions'][NAMESPACE]['durationSeconds'] = 30
    variant['scenario.xdl.yaml'] = dump_yaml(source)
    for identity, document in list(p['documents'].items()):
        content = variant[Path(document['path']).name]
        if content != document['content']:
            p = checked(api.put(f"/api/v1/projects/{p['projectId']}/documents/{identity}",
                               headers={'If-Match': str(p['revision'])}, json={'content': content, 'format': 'yaml'}))
    pf = checked(api.post(f"/api/v1/projects/{p['projectId']}/preflights", json={'revision': p['revision'], 'providerId': 'autoverse.demo'}))
    assert pf['status'] == 'ready', pf
    return p, pf


def verify_released(data, rid, *, input_loss_clock=False, assessment_clock=False):
    directory = data / 'runs' / rid
    state = json.loads((directory / 'state.json').read_bytes())
    processes = json.loads((directory / 'resources.private.json').read_bytes())
    for entry in processes.values():
        try:
            p = psutil.Process(entry['pid'])
            assert p.create_time() != entry['createTime'] or p.status() == psutil.STATUS_ZOMBIE
        except psutil.NoSuchProcess:
            pass
    containers = json.loads((directory / 'containers.private.json').read_bytes()) if (directory / 'containers.private.json').exists() else {}
    for entry in containers.values():
        actual = json.loads(subprocess.check_output(['docker', 'inspect', entry['identity']['id']]))[0]
        assert container_fact(actual) == entry['identity'] and actual['State']['StartedAt'] == entry['startedAt']
        assert actual['State']['Running'] is False
    records, integrity = read_journal(directory, state)
    assert integrity == 'valid' and state['cleanup'] == 'complete'
    terminal = [r for r in records if r['type'] == 'run.state_changed'][-1]
    assert terminal['payload']['cleanupResources'] == state['cleanupResources']
    frozen_provider = json.loads((directory / 'request.json').read_bytes())['snapshot']['providerIdentity']
    for record in records:
        if input_loss_clock and record['type'].startswith('fault.'):
            assert record['source'] == {'providerId':'autoverse.demo','version':frozen_provider['providerVersion']}
            assert record['payload']['clockCodec'] == 'autoverse.host-elapsed-microseconds.v1'
            assert record['sourceTime'] == {'tick':record['payload']['actualTick'], 'clockDomain':'host-runtime', 'resolution':'microsecond'}
            assert record['payload']['effectScope'] == 'driver-bridge-publication-lease'
            assert record['payload']['vehicleEffect'] == 'not_attested'
        elif assessment_clock and record['type'] == 'assessment.coverage':
            payload = record['payload']
            assert record['source'] == {'providerId':'autoverse.demo','version':frozen_provider['providerVersion']}
            assert payload['coverageScope'] == 'recorded-events-only' and payload['complete'] is True
            assert payload['prefixDigest'] == record['previousDigest'] and payload['prefixSequence'] == str(int(record['sequence']) - 1)
            assert record['sourceTime'] == {'tick':str(int(payload['endTick']) - 1), 'clockDomain':'host-runtime', 'resolution':'microsecond'}
            assert payload['sampleCounts'] == {'activationObserved':sum(r['type'] == 'fault.activation_observed' for r in records), 'recoveryObserved':sum(r['type'] == 'fault.recovery_observed' for r in records)}
        else:
            assert record['sourceTime'] is None
    return {'originalProcessInstancesExited': len(processes), 'exactStoppedContainers': len(containers),
            'originalResourceRoles': sorted(processes), 'containerRoles': sorted(containers),
            'journalIntegrity': integrity, 'journalDigest': state['journalDigest'],
            'terminalCleanupFactsMatchCanonicalJournal': True, 'recordCount': len(records),
            'observations': sum(r['type'] == 'observation.available' for r in records)}


def run_case(case, out, args):
    output = out / case
    output.mkdir()
    data = ROOT / '.studio-local/browser-tests' / ('lifecycle-' + case + '-' + uuid.uuid4().hex)
    with create_directory(Path('/'), data.absolute(), parents=True):
        pass
    host = NativeHost(data, output, args.receipt, args.backend_python, args.static_dir)
    result = {'case': case, 'scope': 'actual native Autoverse complete-demo target; startup negatives are partial executions', 'outcome': 'failed'}
    api, worker, component, rid, frozen_path, frozen = None, None, None, None, None, None
    try:
        original_backend_pid = host.start()
        api = login(host)
        p, pf = author(api)
        frozen_path = data / 'snapshots' / pf['snapshotId'] / 'snapshot.json'
        frozen = frozen_path.read_bytes()
        payload = {k: pf[k] for k in ['snapshotId', 'preflightId']}
        def retry():
            with httpx.Client(base_url=host.url, cookies=api.cookies, headers={'Origin': host.url, 'X-CSRF-Token': api.headers['X-CSRF-Token']}, timeout=30) as other:
                return checked(other.post('/api/v1/runs', headers={'Idempotency-Key': 'original-lifecycle-start'}, json=payload), 202)
        with ThreadPoolExecutor(max_workers=2) as pool:
            first_receipts = list(pool.map(lambda _: retry(), range(2)))
        receipt = first_receipts[0]
        assert first_receipts == [receipt, receipt]
        result['concurrentInitialStartUsesOneReceipt'] = True
        rid = receipt['runId']
        print(case, 'RUN', rid, flush=True)
        route = '/api/v1/runs/' + rid
        phases = []
        def read():
            value = checked(api.get(route))
            phase = {'state': value['state'], 'phase': value.get('runtimeStatus', {}).get('phase')}
            if not phases or phase != phases[-1]:
                phases.append(phase)
                print(case, 'OBSERVED', phase, flush=True)
            return value
        result['observedPhases'] = phases
        def owned():
            value = private_record(data, 'run', rid)
            return value if value.get('pid') and (data / 'runs' / rid / 'state.json').exists() else None
        native = wait(owned, bool)
        assert digest((data / 'runs' / rid / 'owner.key').read_bytes()) == native['ownerDigest']
        worker = OriginalProcess(native['pid'], native['createTime'], native['launchArgvDigest'], parent=original_backend_pid)
        result.update(runId=rid, snapshotId=pf['snapshotId'], planDigest=pf['planDigest'], semanticDigest=pf['semanticDigest'],
                      originalWorker={'pid': worker.pid, 'birth': worker.birth, 'argvDigest': worker.argv_digest,
                                      'nativePidfdCaptured': True, 'originalParentVerified': True, 'privateOwnerVerified': True})
        assert_root_owned(data)
        result['secondRootOwnerRefused'] = True
        # Distinct HTTP clients share the same authenticated session scope.
        with ThreadPoolExecutor(max_workers=2) as pool:
            assert list(pool.map(lambda _: retry(), range(2))) == [receipt, receipt]
        conflict = api.post('/api/v1/runs', headers={'Idempotency-Key': 'original-lifecycle-start'}, json={**payload, 'snapshotId': 'different-snapshot'})
        assert conflict.status_code == 409 and conflict.json()['code'] == 'IDEMPOTENCY_CONFLICT'
        result['concurrentHttpStartRetriesReturnOriginalReceipt'] = True
        result['changedStartPayloadRefused'] = True
        if case == 'restart-natural':
            running = wait(read, lambda v: v['state'] == 'running', timeout=540)
            assert running['effectivePlanDigest'] == pf['planDigest']
            assert running['runtimeStatus']['components']['android'] == 'booted_apk_started'
            wait(read, lambda v: v.get('inputTelemetry', {}).get('items', {}).get('speed', {}).get('status') == 'observed')
            command_path = data / 'runs' / rid / 'command.json'
            for kind in ['pause', 'resume', 'step', 'reset', 'set_parameter']:
                response = api.post(route + '/commands', headers={'Idempotency-Key': 'unsupported-' + kind}, json={'kind': kind, 'expectedStateVersion': read()['stateVersion']})
                assert response.status_code == 422 and response.json()['code'] == 'CAPABILITY_UNSUPPORTED'
                assert not command_path.exists()
            # A closed native report fault, never an application fault switch.
            # Briefly suspend only this original worker while replacing/restoring
            # its mutable report. The external simulator is not paused by this.
            state_path = data / 'runs' / rid / 'state.json'
            worker.send(signal.SIGSTOP)
            native_report = None
            try:
                wait(lambda: worker.process.status(), lambda v: v == psutil.STATUS_STOPPED)
                native_report = state_path.read_bytes()
                changed_report = json.loads(native_report)
                assert changed_report['pid'] == worker.pid and changed_report['createTime'] == worker.birth
                assert changed_report['ownerDigest'] == native['ownerDigest']
                changed_report['ownerDigest'] = 'sha256:' + '0' * 64
                atomic(state_path, canonical(changed_report).encode())
                unknown = read()
                assert unknown['state'] == 'unknown' and unknown['cleanup'] == 'unknown'
                assert unknown['reason'] == 'OWNERSHIP_UNKNOWN'
                denied = api.post(route + '/commands', headers={'Idempotency-Key': 'unknown-owner-stop'}, json={'kind': 'stop', 'expectedStateVersion': unknown['stateVersion']})
                assert denied.status_code == 409 and denied.json()['code'] == 'STATE_CONFLICT'
                assert not command_path.exists()
            finally:
                try:
                    if native_report is not None:
                        atomic(state_path, native_report)
                        assert state_path.read_bytes() == native_report
                finally:
                    if not worker.exited():
                        worker.send(signal.SIGCONT)
            recovered = wait(read, lambda v: v['state'] == 'running')
            assert recovered['runId'] == rid and recovered['snapshotId'] == pf['snapshotId']
            assert recovered.get('reason') != 'OWNERSHIP_UNKNOWN'
            result['unknownOwnershipBlocksControlUntilOriginalReportRestored'] = True
            result['originalReportBytesRestoredBeforeWorkerResume'] = True
            original_sources = {d['path']: d['content'] for d in p['documents'].values()}
            doc_id, scenario = next((i, d) for i, d in p['documents'].items() if Path(d['path']).name == 'scenario.xdl.yaml')
            draft = YAML(typ='safe').load(scenario['content'])
            draft['extensions'][NAMESPACE]['durationSeconds'] = 31
            edited = checked(api.put(f"/api/v1/projects/{p['projectId']}/documents/{doc_id}", headers={'If-Match': str(p['revision'])}, json={'content': dump_yaml(draft), 'format': 'yaml'}))
            compilation = checked(api.post(f"/api/v1/projects/{p['projectId']}/compilations", json={'revision': edited['revision'], 'providerId': 'autoverse.demo'}))
            assert compilation['valid'] and compilation['planDigest'] != pf['planDigest'] and compilation['semanticDigest'] != pf['semanticDigest']
            assert frozen_path.read_bytes() == frozen
            assert json.loads(frozen)['projectDocuments'] == original_sources
            assert read()['planDigest'] == pf['planDigest']
            stale = api.post('/api/v1/runs', headers={'Idempotency-Key': 'new-key-old-snapshot'}, json=payload)
            assert stale.status_code == 409 and stale.json()['code'] == 'PREFLIGHT_STALE'
            result['activeDraftChangesDoNotMutateFrozenRun'] = True
            result['unsupportedControlsRefusedBeforeMailbox'] = True
            worker.verify()
            host.stop(crash=True)
            worker.verify()
            result['originalWorkerSurvivesBackendCrash'] = True
            api.close()
            host.start()
            api = login(host)
            restored = read()
            assert restored['state'] == 'running' and restored['runId'] == rid and restored['snapshotId'] == pf['snapshotId']
            same = checked(api.post('/api/v1/runs', headers={'Idempotency-Key': 'original-lifecycle-start'}, json=payload), 202)
            assert same == receipt
            worker.verify()
            unavailable = next(v for v in checked(api.get('/api/v1/providers'))['items'] if v['providerId'] == 'autoverse.demo')
            assert unavailable['available'] is False and unavailable['operations'] == []
            result['restartFreshEnrollmentUnavailableWhileOriginalRunReconciles'] = True
            result['restartStartRetryDoesNotRespawn'] = True
            result['originalRunContinuesAcrossHttpDisconnect'] = True
        else:
            resources_path = data / 'runs' / rid / 'resources.private.json'
            def partial():
                state = read()
                resources = json.loads(resources_path.read_bytes()) if resources_path.exists() else {}
                return (state, resources) if state['state'] == 'preparing' and state.get('runtimeStatus', {}).get('phase') == 'simulator' and 'carla' in resources and 'vcu' not in resources else None
            state, resources = wait(partial, bool, timeout=60)
            carla = resources['carla']
            component = OriginalProcess(carla['pid'], carla['createTime'], carla['argvDigest'], parent=worker.pid)
            result['faultBoundary'] = 'simulator startup; actual router and original CARLA child acquired, no VCU/containers yet'
            if case == 'cancel-startup':
                body = {'kind': 'cancel', 'expectedStateVersion': state['stateVersion']}
                first = checked(api.post(route + '/commands', headers={'Idempotency-Key': 'original-startup-cancel'}, json=body), 202)
                assert checked(api.post(route + '/commands', headers={'Idempotency-Key': 'original-startup-cancel'}, json=body), 202) == first
                changed = api.post(route + '/commands', headers={'Idempotency-Key': 'original-startup-cancel'}, json={**body, 'kind': 'stop'})
                assert changed.status_code == 409 and changed.json()['code'] == 'IDEMPOTENCY_CONFLICT'
                result['originalCancelReceipt'] = first
            else:
                component.send(signal.SIGKILL)
                wait(component.exited, bool)
                result['componentLoss'] = {'role': 'carla', 'originalPidfdSignal': 'SIGKILL', 'originalParentVerified': True, 'nativeExitObserved': True}
        terminal = wait(read, lambda v: v['state'] in ('stopped', 'failed'), timeout=100)
        wait(worker.exited, bool, timeout=30)
        assert terminal['cleanup'] == 'complete' and terminal['verdict'] is None
        if case == 'component-loss':
            assert terminal['state'] == 'failed' and terminal['evidence'] == 'partial'
            assert terminal['reason'] == 'AUTOVERSE_CARLA_NOT_READY'
        else:
            assert terminal['state'] == 'stopped' and terminal['evidence'] == 'available'
        result['terminal'] = {k: terminal.get(k) for k in ['state', 'cleanup', 'evidence', 'reason', 'verdict']}
        assert frozen_path.read_bytes() == frozen
        result['frozenSnapshotUnchanged'] = True
        result['cleanup'] = verify_released(data, rid)
        if case == 'restart-natural':
            assert result['cleanup']['exactStoppedContainers'] == 3 and result['cleanup']['observations'] >= 1
            assert json.loads((data / 'runs' / rid / 'state.json').read_bytes())['commandResults'] == {}
            result['normalDurationCompletionWithoutStopCommand'] = True
        if case == 'cancel-startup':
            operation = checked(api.get('/api/v1/operations/' + result['originalCancelReceipt']['operationId']))
            assert operation['status'] == 'completed'
            assert checked(api.post(route + '/commands', headers={'Idempotency-Key': 'original-startup-cancel'}, json=body), 202) == first
            result['cancelCompletedAndTerminalRetryUnchanged'] = True
        assert len(checked(api.get('/api/v1/runs'))['items']) == 1
        assert checked(api.post('/api/v1/runs', headers={'Idempotency-Key': 'original-lifecycle-start'}, json=payload), 202) == receipt
        result['oneOriginalRunOnly'] = True
        host.stop()
        with own_root(data):
            pass
        result['originalRootLockReleased'] = True
        result['outcome'] = 'passed'
    finally:
        try:
            host.stop()
            if worker is not None and not worker.exited():
                # Only the previously captured original pidfd is eligible.
                if worker.process.status() == psutil.STATUS_STOPPED:
                    worker.send(signal.SIGCONT)
                worker.send(signal.SIGTERM)
                wait(worker.exited, bool, timeout=90)
        except Exception as error:
            result['outcome'] = 'failed'
            result['cleanupInspectionFailure'] = type(error).__name__
            raise
        finally:
            if worker is not None:
                result['originalWorkerExited'] = worker.exited()
                worker.close()
            if component is not None:
                component.close()
            if api is not None:
                api.close()
            result['nativeBackendObservations'] = host.observations
            (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(case, result['outcome'], result['terminal'], flush=True)
    return result


def assert_root_owned(data):
    try:
        with own_root(data):
            raise AssertionError('A second owner acquired the original backend root')
    except RootOwnedError:
        pass


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--receipt', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--backend-python', type=Path, default=Path(sys.executable))
    p.add_argument('--static-dir', type=Path, default=ROOT / '.studio-local/linux-capabilities-review/ui')
    p.add_argument('--cases', choices=CASES, nargs='+', default=CASES)
    args = p.parse_args()
    args.backend_python = args.backend_python.absolute()
    args.receipt = args.receipt.absolute()
    args.static_dir = args.static_dir.absolute()
    assert len(args.cases) == len(set(args.cases)) and sys.platform == 'linux'
    args.output.mkdir(parents=True)
    results = [run_case(case, args.output, args) for case in args.cases]
    summary = {'scope': 'T021 actual native Autoverse target; no reference/Lite/platform/physical execution claim', 'outcome': 'passed',
               'cases': len(results), 'allOriginalWorkersExited': all(r['originalWorkerExited'] for r in results),
               'allOriginalRootLocksReleased': all(r['originalRootLockReleased'] for r in results)}
    (args.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()

"""Own native Autoverse/Playwright handles for the explicit T025 browser lane."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

import psutil

from xverse_studio.blueprints.autoverse import documents, NAMESPACE
from xverse_studio.host.ownership import own_root
from xverse_studio.security.managed_io import create_directory
from xverse_studio.storage.core import digest
from xverse_studio.xdl.examples import dump_yaml
from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('owned_autoverse_lifecycle', Path(__file__).with_name('autoverse_lifecycle_conformance.py'))
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--receipt', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--node', type=Path, required=True)
    p.add_argument('--playwright-cli', type=Path, required=True)
    p.add_argument('--browser-cache', type=Path, required=True)
    p.add_argument('--static-dir', type=Path, required=True)
    p.add_argument('--case', choices=['startup-failure', 'runtime-failure'], default='startup-failure')
    args = p.parse_args()
    args.output.mkdir(parents=True)
    data = ROOT / '.studio-local/browser-tests' / ('browser-recovery-' + uuid.uuid4().hex)
    with create_directory(Path('/'), data.absolute(), parents=True):
        pass
    sources = documents('studio-browser')
    scenario = YAML(typ='safe').load(sources['scenario.xdl.yaml'])
    scenario['extensions'][NAMESPACE]['durationSeconds'] = 180 if args.case == 'runtime-failure' else 30
    sources['scenario.xdl.yaml'] = dump_yaml(scenario)
    (data / 'author-inputs.private.json').write_text(json.dumps(sources))
    host = native.NativeHost(data, args.output, args.receipt.absolute(), Path(sys.executable), args.static_dir.absolute())
    node, worker, component = None, None, None
    rid, injected = None, False
    report = {'scope': 'Actual native Autoverse and browser command-failure evidence', 'case': args.case, 'outcome': 'failed'}
    try:
        host.start()
        env = dict(os.environ, STUDIO_BASE_URL=host.url, STUDIO_BROWSER_DATA=str(data), STUDIO_AUTOVERSE_RECONNECT_CASE=args.case, STUDIO_BROWSER_REPORT=str(args.output.absolute() / 'browser.json'), STUDIO_BROWSER_OUTPUT=str(args.output.absolute() / 'browser-artifacts'), PLAYWRIGHT_BROWSERS_PATH=str(args.browser_cache.absolute()))
        argv = [str(args.node.absolute()), str(args.playwright_cli.absolute()), 'test', '--config', 'tests/live/autoverse-reconnect.config.ts']
        (args.output / 'browser-command.private.json').write_text(json.dumps({'argv': argv, 'dataRoot': str(data)}, indent=2) + '\n')
        with (args.output / 'browser.log').open('xb') as log:
            node = subprocess.Popen(argv, cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
            original_node = psutil.Process(node.pid)
            browser_birth = original_node.create_time()
            native.wait(lambda: original_node.ppid() == os.getpid() and original_node.uids().real == os.getuid()
                        and original_node.create_time() == browser_birth and original_node.cmdline() == argv, bool, timeout=3)
            report['originalBrowserDriver'] = {'pid': node.pid, 'birth': browser_birth, 'argvDigest': digest(argv), 'nativeParentAndUidVerified': True}
            deadline = time.monotonic() + (720 if args.case == 'runtime-failure' else 180)
            while node.poll() is None and time.monotonic() < deadline:
                context = data / 'browser-run.private.json'
                if context.exists():
                    value = json.loads(context.read_bytes())
                    rid = value['runId']
                    r = native.private_record(data, 'run', rid)
                    directory = data / 'runs' / rid
                    if worker is None and r.get('pid') and (directory / 'state.json').exists():
                        assert digest((directory / 'owner.key').read_bytes()) == r['ownerDigest']
                        worker = native.OriginalProcess(r['pid'], r['createTime'], r['launchArgvDigest'], parent=host.child.pid)
                        report.update(runId=rid, snapshotId=value['snapshotId'], operationId=value['operationId'], originalWorkerPidfdCaptured=True)
                    state_path = directory / 'state.json'
                    resource_path = directory / 'resources.private.json'
                    if not injected and worker is not None and state_path.exists() and resource_path.exists():
                        state = json.loads(state_path.read_bytes())
                        resources = json.loads(resource_path.read_bytes())
                        partial = state['state'] == 'preparing' and state['runtimeStatus']['phase'] == 'simulator' and 'vcu' not in resources
                        active = state['state'] == 'running' and (data / 'browser-observed-running.private.json').exists()
                        if 'carla' in resources and (partial if args.case == 'startup-failure' else active):
                            original = resources['carla']
                            component = native.OriginalProcess(original['pid'], original['createTime'], original['argvDigest'], parent=worker.pid)
                            component.send(signal.SIGKILL)
                            injected = True
                            report['originalCarlaPidfdLoss'] = 'startup' if args.case == 'startup-failure' else 'after_observed_running'
                time.sleep(0.1)
            if node.poll() is None:
                assert original_node.create_time() == browser_birth and original_node.cmdline() == argv
                node.terminate()
            node.wait(timeout=30)
        report['browserExit'] = node.returncode
        assert injected and rid is not None and worker is not None
        native.wait(worker.exited, bool, timeout=90)
        report['cleanup'] = native.verify_released(data, rid)
        assert report['cleanup']['exactStoppedContainers'] == (0 if args.case == 'startup-failure' else 3)
        assert node.returncode == 0, 'Actual browser scenario failed; retain its original report'
        report['outcome'] = 'passed'
    finally:
        try:
            if node is not None and node.poll() is None:
                node.terminate()
                node.wait(timeout=30)
            host.stop()
            if worker is not None and not worker.exited():
                worker.send(signal.SIGTERM)
                native.wait(worker.exited, bool, timeout=90)
        finally:
            if worker is not None:
                report['originalWorkerExited'] = worker.exited()
                worker.close()
            if component is not None:
                component.close()
            with own_root(data):
                report['originalRootLockReleased'] = True
            report['nativeBackendObservations'] = host.observations
            (args.output / 'native-result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()

"""Read/validate only an existing isolated browser workload; never starts a provider."""
from __future__ import annotations
import json
from pathlib import Path
import socket
import subprocess
import sys
import time
import httpx

repository = Path(__file__).resolve().parents[2]
roots = [root for root in (repository / '.studio-local/browser-tests').iterdir() if root.is_dir() and (root / 'studio.sqlite').is_file()]
data = max(roots, key=lambda root: root.stat().st_mtime_ns)
with socket.socket() as sock:
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
url = f'http://127.0.0.1:{port}'
process = subprocess.Popen([sys.executable, '-I', '-m', 'xverse_studio.host.launcher', '--data-dir', str(data), '--port', str(port)], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
client = httpx.Client(base_url=url, headers={'Origin': url}, timeout=15)
try:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            if client.get('/api/v1/session').status_code == 401:
                break
        except httpx.HTTPError:
            pass
        time.sleep(.1)
    else:
        raise RuntimeError('The isolated diagnostic backend did not start.')
    bootstrap = json.loads((data / 'bootstrap.json').read_text())
    login = client.post('/api/v1/session', json={'bootstrapToken': bootstrap['bootstrapToken']})
    login.raise_for_status()
    client.headers['X-CSRF-Token'] = login.json()['csrfToken']
    projects = client.get('/api/v1/projects').json()['items']
    project = next(project for project in projects if project['name'].startswith('Performance reference'))
    loads, validations = [], []
    for _ in range(5):
        started = time.perf_counter()
        response = client.get('/api/v1/projects/' + project['projectId'])
        response.raise_for_status()
        loads.append((time.perf_counter() - started) * 1000)
        started = time.perf_counter()
        response = client.post('/api/v1/projects/' + project['projectId'] + '/validations', json={'revision': project['revision']})
        response.raise_for_status()
        assert response.json()['valid'] is True
        validations.append((time.perf_counter() - started) * 1000)
    summary = {'scope': 'diagnostic HTTP timing for existing isolated valid 200-element/400-flow inputs', 'requests': 5, 'projectGetMilliseconds': loads, 'authoritativeValidationMilliseconds': validations, 'sourceBytesChanged': False, 'providerStarts': 0}
    target = repository / 'evidence/studio/M2-review/performance-failure-before-repair/backend-request-timings.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
finally:
    client.close()
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)

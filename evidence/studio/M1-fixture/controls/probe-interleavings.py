from pathlib import Path
import argparse
import hashlib
import json
import os
import sys
import time

import pytest

parser = argparse.ArgumentParser()
parser.add_argument('mode', choices=['capability', 'journal'])
parser.add_argument('label')
parser.add_argument('--expected', type=int, required=True)
args = parser.parse_args()
root = Path.cwd().resolve()
out = root / '.studio-local/fixture-matrix' / args.label
out.mkdir()
cache = root.parent / '.xverse-studio-cache' / 'tmp'
os.environ.update(TMPDIR=str(cache), TMP=str(cache), TEMP=str(cache), PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', SPECIFY_FEATURE_DIRECTORY='specs/001-industry-agnostic-studio')
import tempfile
tempfile.tempdir = None
source_map = json.loads((root / '.studio-local/fixture-matrix/io-boundaries-full/inputs-before.json').read_text())
inputs = lambda: {n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in source_map}
before = inputs()
(out/'inputs-before.json').write_text(json.dumps(before,indent=2)+'\n')
witness = dict(mode=args.mode, scope='Controlled scheduling of actual owned native model and genuine metadata; no equipment or manufactured responses', triggered=0, observations=[])

class Interleaving:
    @pytest.hookimpl(hookwrapper=True)
    def pytest_fixture_setup(self, fixturedef, request):
        result = yield
        if fixturedef.argname != 'client':
            return
        client = result.get_result()
        studio = client.app.state.studio
        if args.mode == 'capability':
            original = client.post
            def post(url, *values, **options):
                response = original(url, *values, **options)
                body = options.get('json') or {}
                if str(url).endswith('/commands') and body.get('kind') == 'pause' and response.status_code == 422:
                    rid = str(url).split('/')[-2]
                    child = studio.runs.children[rid]
                    assert child.wait(timeout=20) == 0
                    state = json.loads((studio.runs.directory(rid)/'state.json').read_text())
                    witness['triggered'] += 1
                    witness['observations'].append(dict(stage='after unsupported denial, before next test action',state=state['state'],stateVersion=state['stateVersion'],cleanup=state['cleanup'],evidence=state['evidence']))
                if str(url).endswith('/commands') and body.get('kind') == 'cancel':
                    witness['observations'].append(dict(stage='cleanup Cancel',expectedStateVersion=body['expectedStateVersion'],status=response.status_code,code=response.json().get('code')))
                return response
            client.post = post
        else:
            original = studio.runs.read
            def read(rid):
                record = original(rid)
                if witness['triggered'] == 0 and record['state'] == 'preparing':
                    journal = studio.runs.directory(rid)/'evidence.jsonl'
                    deadline = time.monotonic()+15
                    while time.monotonic() < deadline:
                        if journal.is_file():
                            lines=journal.read_bytes().splitlines(keepends=True)
                            records=[json.loads(line) for line in lines if line.endswith(b'\n')]
                            if any(r['type']=='observation.available' for r in records):
                                state=json.loads((journal.parent/'state.json').read_text())
                                witness['triggered'] += 1
                                witness['observations'].append(dict(stage='held genuine preparing response until actual sample',returnedState=record['state'],workerState=state['state'],actualSample=True))
                                break
                        time.sleep(.01)
                    else:
                        raise AssertionError('Controlled actual sample did not arrive')
                return record
            studio.runs.read = read

node = ('tests/integration/test_reference_pause.py::test_pause_requires_the_frozen_scoped_nonphysical_capability[operation]' if args.mode=='capability' else 'tests/integration/test_worker_evidence_io.py::test_native_evidence_io_failure_preserves_known_lifecycle_and_cleanup[journal_finalize]')
code = pytest.main([node,'-q','--tb=short','--junitxml='+str(out/'junit.private.xml')],plugins=[Interleaving()])
after=inputs()
(out/'inputs-after.json').write_text(json.dumps(after,indent=2)+'\n')
(out/'witness.private.json').write_text(json.dumps(witness,indent=2)+'\n')
proof=dict(command=[sys.executable,'-I',str(Path(__file__).resolve()),args.mode,args.label,'--expected',str(args.expected)],probeSourceSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),exitCode=int(code),expectedExitCode=args.expected,inputsIdentical=before==after,selectedInputs=len(before),witness=witness)
(out/'verification.private.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof),flush=True)
assert witness['triggered']==1 and before==after and int(code)==args.expected

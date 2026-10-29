"""Canonical load/compile contracts; no launch or actual demo claim."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from xverse_studio.blueprints.autoverse import documents, resources, ROLES, NAMESPACE
from xverse_studio.xdl import XDLAdapter, XDLRejected, reference_configuration
from xverse_studio.xdl.examples import dump_yaml, examples


def test_complete_demo_is_canonical_xdl_with_distinct_roles_realizations_and_communication():
    source = documents()
    before = deepcopy(source)
    compiled = XDLAdapter().compile(source)
    assert compiled['valid'], compiled['diagnostics']
    assert source == before
    projected = XDLAdapter().project(source)
    assert {r['ref'].rsplit('#',1)[-1] for r in projected['elements'] if r['kind'] != 'nodes'} == set(ROLES)
    assert {b['logicalRef']['element'] for b in compiled['plan']['bindings']} == set(ROLES)
    assert {b['realizationClass'] for b in compiled['plan']['bindings']} == {'simulated','virtual'}
    assert len(projected['connections']) >= 14
    # The owned scalar reference is not silently substituted for this demo.
    with pytest.raises(XDLRejected):
        reference_configuration(source, compiled)


def test_public_cli_and_library_agree_for_complete_demo(tmp_path):
    source = documents()
    inputs = []
    for name, content in source.items():
        p = tmp_path/name; p.write_text(content,encoding='utf-8'); inputs.append(str(p))
    adapter = XDLAdapter()
    schemas = [value for path in adapter.profile_schema_paths for value in ('--profile-schema',path)]
    result = subprocess.run([sys.executable,'-I','-m','xverse_xdl','experiment','compile','--format','json',*schemas,*inputs],
                            text=True,capture_output=True,timeout=20)
    assert result.returncode == 0,result.stdout+result.stderr
    assert json.loads(result.stdout)['plan'] == adapter.compile(source)['plan']


def test_discovery_loading_and_compilation_have_no_runtime_side_effect(client):
    entries = examples()
    selected = next(e for e in entries if e['id']=='autoverse-classic')
    assert selected['providerId']=='autoverse.demo' and selected['scope']=='external_demo'
    created = client.post('/api/v1/projects',json={'name':'Load complete Autoverse','blueprintRef':selected['id']})
    assert created.status_code == 201,created.text
    project = created.json()
    compiled = client.post(f"/api/v1/projects/{project['projectId']}/compilations",json={'revision':project['revision']})
    assert compiled.status_code == 200 and compiled.json()['valid'],compiled.text
    assert client.app.state.studio.runs.children == {}
    assert client.get('/api/v1/runs',params={'projectId':project['projectId']}).json()['items']==[]
    checked = client.post(f"/api/v1/projects/{project['projectId']}/preflights",json={'revision':project['revision']})
    assert checked.status_code == 200 and checked.json()['status']=='blocked',checked.text
    assert client.app.state.studio.runs.children == {}


@pytest.mark.parametrize('value',[True,0,29,1801,float('inf'),'600'])
def test_declared_runtime_bounds_are_authoritatively_validated(value):
    source = resources()
    source['scenario.xdl.yaml']['extensions'][NAMESPACE]['durationSeconds'] = value
    report = XDLAdapter().compile({name:dump_yaml(value) for name,value in source.items()})
    assert not report['valid'] and report['plan'] is None


def test_blueprint_and_contract_contain_no_machine_paths_or_imported_commands():
    source = documents()
    text = json.dumps(source)
    assert '/home/' not in text and '/media/' not in text
    assert 'run_autoverse.py' not in text and 'shell' not in text
    contract = Path(__file__).parents[2]/'services/studio-api/src/xverse_studio/blueprints/autoverse-contract.json'
    assert json.loads(contract.read_text())['physicalEffects'] is False

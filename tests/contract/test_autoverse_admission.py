"""Provider admission and driver authorization tests; no live-demo acceptance claim."""
from copy import deepcopy
import json
from pathlib import Path
import time
import pytest
from xverse_studio.blueprints.autoverse import documents, NAMESPACE
from xverse_studio.providers.autoverse.adapter import configuration, EXTERNAL_CONTRACT
from xverse_studio.providers.autoverse.input import input_request
from xverse_studio.connections import admit_connections, admission_diagnostics
from xverse_studio.storage.core import Problem, atomic, canonical
from xverse_studio.xdl import XDLAdapter


def test_exact_source_admission_accepts_project_paths_and_rejects_extra_semantics():
    source = documents()
    adapter = XDLAdapter()
    compiled = adapter.compile(source)
    assert configuration(source, compiled)['durationSeconds'] == 600
    assert configuration({'xdl/'+k:v for k,v in source.items()}, compiled)
    assert configuration({**source,'other/system.xdl.yaml':source['system.xdl.yaml']}, compiled) is None
    yaml = __import__('ruamel.yaml', fromlist=['YAML']).YAML(typ='safe')
    value = yaml.load(source['scenario.xdl.yaml'])
    value['extensions'][NAMESPACE]['durationSeconds'] = 30
    from xverse_studio.xdl.examples import dump_yaml
    source['scenario.xdl.yaml'] = dump_yaml(value)
    assert configuration(source, adapter.compile(source))['durationSeconds'] == 30
    value['spec']['initialConditions']['unknownBehavior'] = True
    source['scenario.xdl.yaml'] = dump_yaml(value)
    assert configuration(source, adapter.compile(source)) is None


def test_external_feedback_requires_matching_installed_provider_contract():
    source = documents()
    base = {'providerId':'autoverse.demo','connectionContracts':{'externalRuntime':EXTERNAL_CONTRACT}}
    report = admit_connections(source, {'diagnostics':[]}, base)
    assert report['cycles'] and not admission_diagnostics(report)
    for provider in (None, {**base,'providerId':'other'}, {**base,'connectionContracts':{}}, {**base,'connectionContracts':{'externalRuntime':{**EXTERNAL_CONTRACT,'version':'99'}}}):
        assert admission_diagnostics(admit_connections(source,{'diagnostics':[]},provider))


@pytest.fixture
def channel(tmp_path, monkeypatch):
    now = [100.0]
    import xverse_studio.providers.autoverse.input as module
    monkeypatch.setattr(module.time,'monotonic',lambda:now[0])
    atomic(tmp_path/'owner.key',b'x'*32)
    atomic(tmp_path/'state.json',canonical({'updatedAt':time.time(),'inputTelemetry':{'items':{
        'speed':{'value':20,'status':'observed','ageSeconds':0},
        'reverseEngaged':{'value':False,'status':'observed','ageSeconds':0},
        'cruiseEngaged':{'value':False,'status':'observed','ageSeconds':0},
    }}}).encode())
    return tmp_path,now


def send(root,lease,seq=1,**fields):
    return input_request(root,'frame',{**lease,'frame':{'sequence':seq,'throttle':0,'brake':0,'steer':0,**fields}},'session-a')


def test_exclusive_lease_expiry_fencing_and_sequence_retries(channel):
    root,now=channel
    lease=input_request(root,'acquire',{},'session-a')
    lease={k:lease[k] for k in ('leaseToken','generation')}
    with pytest.raises(Problem,match='Another browser'):
        input_request(root,'acquire',{},'session-b')
    assert send(root,lease)['status']=='staged'
    before=(root/'input.json').read_bytes()
    now[0]+=.1
    assert send(root,lease)['status']=='duplicate'
    assert (root/'input.json').read_bytes()==before
    with pytest.raises(Problem): send(root,lease,throttle=.5)
    with pytest.raises(Problem): input_request(root,'release',lease,'session-b')
    now[0]+=.7
    with pytest.raises(Problem): send(root,lease,2)
    second=input_request(root,'acquire',{},'session-a')
    assert second['generation']>lease['generation']
    with pytest.raises(Problem): send(root,lease,2)
    send(root,{k:second[k] for k in ('leaseToken','generation')},2)
    assert json.loads((root/'input.json').read_text())['frame']['sequence']==2


def test_pending_discrete_request_cannot_be_overwritten_or_replayed(channel):
    root,now=channel
    acquired=input_request(root,'acquire',{},'session-a')
    lease={k:acquired[k] for k in ('leaseToken','generation')}
    assert send(root,lease,cruise=True)['status']=='staged'
    before=(root/'input.json').read_bytes()
    now[0]+=.1
    assert send(root,lease,2)['status']=='publication_pending'
    assert (root/'input.json').read_bytes()==before
    assert send(root,lease,cruise=True)['status']=='duplicate'
    state=json.loads((root/'state.json').read_text());state['inputTelemetry']['lastPublishedSequence']=1
    atomic(root/'state.json',canonical(state).encode())
    assert send(root,lease,2)['status']=='staged'
    assert json.loads((root/'input.json').read_text())['frame']['sequence']==2


@pytest.mark.parametrize('frame',[{'cruise':True,'brake':1},{'reverse':True},{'deltaSpeed':5},{'sequence':True},{'throttle':2},{'throttle':.5,'brake':.2},{'unknown':1}])
def test_backend_rejects_invalid_or_unobserved_controls(channel,frame):
    root,now=channel
    acquired=input_request(root,'acquire',{},'session-a')
    lease={k:acquired[k] for k in ('leaseToken','generation')}
    with pytest.raises(Problem):send(root,lease,**frame)
    assert not (root/'input.json').exists()


def test_release_requests_brake_and_stops_renewal(channel):
    root,now=channel
    acquired=input_request(root,'acquire',{},'session-a')
    lease={k:acquired[k] for k in ('leaseToken','generation')}
    input_request(root,'release',lease,'session-a')
    frame=json.loads((root/'input.json').read_text())['frame']
    assert frame['brake']==1 and frame['throttle']==0 and frame['cruise'] is False
    with pytest.raises(Problem):send(root,lease,2)


def test_forward_request_is_also_gated_by_speed_in_backend(channel):
    root,now=channel
    acquired=input_request(root,'acquire',{},'session-a')
    lease={k:acquired[k] for k in ('leaseToken','generation')}
    with pytest.raises(Problem):send(root,lease,reverse=False)


def test_reacquiring_driver_does_not_reinitialize_gear_selection(channel):
    root,now=channel
    acquired=input_request(root,'acquire',{},'session-a')
    lease={k:acquired[k] for k in ('leaseToken','generation')}
    send(root,lease)
    now[0]+=1
    acquired=input_request(root,'acquire',{},'session-a')
    lease={k:acquired[k] for k in ('leaseToken','generation')}
    send(root,lease)
    assert 'reverse' not in json.loads((root/'input.json').read_text())['frame']

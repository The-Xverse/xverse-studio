"""Real Argus writer/reader interoperability; owned evidence fixtures, not live Maestro/X-COM."""
from pathlib import Path
import hashlib

import pytest
from xverse.argus import EvidenceStore
from xverse_studio.platform_observability.argus import ArgusBinding, ArgusSources
from xverse_studio.storage.core import Problem
from xverse_studio.xdl import XDLAdapter
from xverse_studio.xdl.examples import examples


@pytest.fixture
def argus_source(tmp_path):
    compiled=XDLAdapter().compile(examples()[0]['documents'])
    assert compiled['valid']
    root=tmp_path/'argus-run'
    run=EvidenceStore.open_run(root,run_id='actual-argus-fixture',plan=compiled['plan'])
    run.append_event(event_id='command-1',producer_id='owned-reader-fixture',event_kind='annotation',correlation_id='request-1')
    run.append_event(event_id='result-1',producer_id='owned-reader-fixture',event_kind='annotation',correlation_id='request-1',causation_id='command-1')
    run.finalize()
    return root,compiled


def bind(root, compiled, source='source-a', run='actual-argus-fixture', plan=None):
    return ArgusBinding(source,root,run,plan or compiled['planDigest'])


def hashes(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}


def test_actual_argus_records_clocks_correlation_and_verdicts_survive_read_only(argus_source):
    root,compiled=argus_source
    before=hashes(root)
    source=ArgusSources((bind(root,compiled),))
    result=source.read('source-a')
    original=EvidenceStore.read_run(root)
    assert result['items']==original.records()
    assert result['evidence']['assessed']==original.assessed_evidence_status
    assert result['evidence']['recorded']==original.recorded_evidence_status
    assert result['planDigest']==compiled['planDigest']
    assert result['inputSemanticDigest'] is None  # Never conflate two digests.
    assert result['identityVerified'] is True
    event=next(r for r in result['items'] if r['eventId']=='result-1')
    assert event['correlationId']=='request-1' and event['causationId']=='command-1'
    assert hashes(root)==before


@pytest.mark.parametrize('which,code',[('run','ARGUS_RUN_IDENTITY_MISMATCH'),('plan','ARGUS_PLAN_IDENTITY_MISMATCH')])
def test_other_run_or_plan_is_not_joined(argus_source,which,code):
    root,compiled=argus_source
    binding=bind(root,compiled,run='another-run' if which=='run' else 'actual-argus-fixture',plan='sha256:'+'f'*64 if which=='plan' else None)
    with pytest.raises(Problem) as caught:ArgusSources((binding,)).read('source-a')
    assert caught.value.code==code


def test_original_corruption_verdict_is_not_upgraded_or_repaired(argus_source):
    root,compiled=argus_source
    stream=root/'events.jsonl'
    manifest=EvidenceStore.read_run(root).manifest
    # Read the public manifest's declared stream rather than assuming a format.
    stream_name=manifest['eventStream']['path']
    stream=root/stream_name
    stream.write_bytes(stream.read_bytes()[:-5])
    before=hashes(root)
    original=EvidenceStore.read_run(root)
    result=ArgusSources((bind(root,compiled),)).read('source-a')
    assert result['evidence']['assessed']==original.assessed_evidence_status=='incomplete'
    assert result['evidence']['recorded']==original.recorded_evidence_status
    assert result['diagnostics'] and hashes(root)==before
    assert str(root) not in str(result['diagnostics'])


def test_page_identity_cannot_cross_source_and_changed_evidence(argus_source):
    root,compiled=argus_source
    sources=ArgusSources((bind(root,compiled),bind(root,compiled,source='source-b')))
    page=sources.read('source-a',limit=1)
    assert page['nextCursor']
    following=sources.read('source-a',limit=1,cursor=page['nextCursor'])
    assert following['items'][0]!=page['items'][0]
    with pytest.raises(Problem,match='identity changed'):
        sources.read('source-b',cursor=page['nextCursor'])
    manifest=root/'manifest.json';manifest.write_bytes(manifest.read_bytes()+b' ')
    with pytest.raises(Problem):sources.read('source-a',cursor=page['nextCursor'])


def test_host_registry_and_replaced_root_fail_closed(argus_source):
    root,compiled=argus_source
    sources=ArgusSources((bind(root,compiled),))
    with pytest.raises(Problem):sources.read(str(root))
    root.rename(root.with_name('old'));root.mkdir()
    with pytest.raises(Problem) as caught:sources.read('source-a')
    assert caught.value.code=='ARGUS_SOURCE_CHANGED'
    with pytest.raises(ValueError):ArgusSources((bind(root,compiled),bind(root,compiled)))
    for limit in (True,0,201):
        with pytest.raises(Problem):sources.read('source-a',limit=limit)


def test_declared_byte_budget_rejects_before_actual_reader(argus_source,monkeypatch):
    import json
    root,compiled=argus_source
    path=root/'manifest.json';manifest=json.loads(path.read_text())
    manifest['artifacts']=[{'bytes':65*1024*1024}]
    path.write_text(json.dumps(manifest))
    monkeypatch.setattr(EvidenceStore,'read_run',lambda *_args,**_kwargs:pytest.fail('Oversized source reached SDK'))
    with pytest.raises(Problem) as caught:ArgusSources((bind(root,compiled),)).read('source-a')
    assert caught.value.code=='ARGUS_SOURCE_LIMIT'


def test_missing_manifest_never_manufactures_observed_run_identity(argus_source):
    root,compiled=argus_source
    source=ArgusSources((bind(root,compiled),))
    (root/'manifest.json').unlink()
    original=EvidenceStore.read_run(root)
    result=source.read('source-a')
    assert result['identityVerified'] is False
    assert result['runId'] is None and result['planDigest'] is None
    assert result['expectedIdentity']['runId']=='actual-argus-fixture'
    assert result['evidence']['assessed']==original.assessed_evidence_status
    assert result['diagnostics']


def test_unsupported_host_reports_actionable_integration_limit(argus_source,monkeypatch):
    import xverse_studio.platform_observability.argus as module
    root,compiled=argus_source
    source=ArgusSources((bind(root,compiled),))
    monkeypatch.setattr(module.sys,'platform','win32')
    with pytest.raises(Problem) as caught:source.read('source-a')
    assert caught.value.code=='ARGUS_READER_OS_UNSUPPORTED'
    assert 'native Linux' in caught.value.message

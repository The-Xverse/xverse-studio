"""Campaign read projection; scheduler is held only for read immutability checks."""
from copy import deepcopy

from test_advanced_api import prepared


def test_campaign_preview_and_retained_history_identify_verified_frozen_inputs(client, monkeypatch):
    monkeypatch.setattr(client.app.state.studio, 'campaign_tick', lambda: None)
    project, pf = prepared(client)
    body = {'snapshotId': pf['snapshotId'], 'matrix': {'gain': [.5, .8]},
            'budget': {'maxRuns': 2, 'maxTotalSeconds': 1}, 'concurrency': 1,
            'stopPolicy': 'stop_on_failure'}
    before = client.get('/api/v1/campaigns').json()
    preview = client.post('/api/v1/campaigns/preview', json=body)
    assert preview.status_code == 200, preview.text
    result = preview.json()
    assert result['campaignVersion'] == '1.0'
    base = result['baseInput']
    assert base['status'] == 'verified'
    assert base['projectId'] == project['projectId'] and base['revision'] == project['revision']
    assert base['snapshotId'] == pf['snapshotId'] and base['snapshotDigest'] == pf['snapshotDigest']
    assert base['selection'] == pf['selection'] and base['providerId'] == 'studio.reference'
    assert client.get('/api/v1/campaigns').json() == before
    assert client.get('/api/v1/runs').json()['items'] == []
    response = client.post('/api/v1/campaigns', headers={'Idempotency-Key': 'presentation'}, json=body)
    assert response.status_code == 202, response.text
    cid = response.json()['campaignId']
    store = client.app.state.studio.store
    original = deepcopy(store.get('campaign', cid))
    detail = client.get('/api/v1/campaigns/' + cid).json()
    listed = next(r for r in client.get('/api/v1/campaigns?limit=20').json()['items'] if r['campaignId'] == cid)
    assert detail == listed
    assert detail['baseInput'] == base and detail['campaignVersion'] == '1.0'
    assert detail['children'] == original['children']
    assert 'principal' not in detail and 'baseSnapshot' not in detail
    assert store.get('campaign', cid) == original


def test_unverifiable_campaign_base_remains_unknown_without_hiding_child_states(client, monkeypatch):
    monkeypatch.setattr(client.app.state.studio, 'campaign_tick', lambda: None)
    _, pf = prepared(client)
    body = {'snapshotId': pf['snapshotId'], 'matrix': {'gain': [.8]}, 'budget': {'maxRuns': 1}}
    accepted = client.post('/api/v1/campaigns', headers={'Idempotency-Key': 'unknown-base'}, json=body)
    assert accepted.status_code == 202, accepted.text
    cid = accepted.json()['campaignId']
    store = client.app.state.studio.store
    original = store.get('campaign', cid)
    snapshot = store.root / 'snapshots' / pf['snapshotId'] / 'snapshot.json'
    snapshot.write_bytes(snapshot.read_bytes() + b' ')
    response = client.get('/api/v1/campaigns/' + cid)
    assert response.status_code == 200, response.text
    public = response.json()
    assert public['baseInput'] == {'status': 'unavailable', 'reason': 'SNAPSHOT_INTEGRITY'}
    assert public['children'] == original['children'] and public['status'] == original['status']
    assert store.get('campaign', cid) == original

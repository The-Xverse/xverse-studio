from copy import deepcopy

from xverse_studio.comparison import compare_runs


def run():
    # The original healthy-control assertions now carry explicit provenance/window facts.
    from test_comparison_report import fixture_run
    return fixture_run()


def test_configuration_differences_precede_interpretation():
    left, right = run(), run(); right["runId"] = "other"; right["snapshot"]["configuration"]["gain"] = 2
    out = compare_runs(left, right)
    assert out["differences"][0]["field"] == "parameters"
    assert out["compatible"] is True
    assert out["mode"] == "recorded_observation_comparison"
    assert out["rerunRequiresFreshAdmission"] is True


def test_unit_identity_mismatch_and_clock_uncertainty_block_numeric_overlay():
    for key, value in [("unitDefinitionDigest", "other"), ("clockDomainRef", "device"), ("quantity", "distance")]:
        left, right = run(), run(); right["observations"][0][key] = value
        out = compare_runs(left, right)
        assert out["compatible"] is False


def test_missing_gapped_invalid_evidence_cannot_be_compared_as_complete():
    left, right = run(), run(); right["observations"][0]["coverage"]["gaps"] = [[1, 2]]
    assert compare_runs(left, right)["compatible"] is False
    right = run(); right["evidence"]["integrity"] = "invalid"
    assert compare_runs(left, right)["compatible"] is False


def test_public_comparison_refuses_unverified_frozen_snapshot(client):
    from test_advanced_api import prepared, start, wait_run

    project, left_pf = prepared(client)
    left = start(client, left_pf, key='comparison-left')
    assert wait_run(client, left)['state'] == 'stopped'
    right_pf = client.post(f"/api/v1/projects/{project['projectId']}/preflights", json={'revision': project['revision']})
    assert right_pf.status_code == 200 and right_pf.json()['status'] == 'ready', right_pf.text
    right = start(client, right_pf.json(), key='comparison-right')
    assert wait_run(client, right)['state'] == 'stopped'
    assert left_pf['snapshotId'] != right_pf.json()['snapshotId']
    payload = {'leftRunId': left, 'rightRunId': right}
    healthy = client.post('/api/v1/comparisons', json=payload)
    assert healthy.status_code == 200 and healthy.json()['compatible'] is True, healthy.text
    store = client.app.state.studio.store
    original = store.get('snapshot', left_pf['snapshotId'])
    snapshot_file = store.root / 'snapshots' / left_pf['snapshotId'] / 'snapshot.json'
    original_bytes = snapshot_file.read_bytes()
    changed = deepcopy(original)
    changed['artifactIdentities'] = [{'artifactId': 'owned-tampered-claim', 'digest': 'sha256:' + '0' * 64}]
    store.put('snapshot', left_pf['snapshotId'], changed)
    try:
        refused = client.post('/api/v1/comparisons', json=payload)
        assert refused.status_code == 422, refused.text
        assert refused.json()['code'] == 'SNAPSHOT_INTEGRITY'
        assert snapshot_file.read_bytes() == original_bytes
    finally:
        store.put('snapshot', left_pf['snapshotId'], original)

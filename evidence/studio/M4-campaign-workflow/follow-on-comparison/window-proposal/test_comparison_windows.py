"""Labelled contract fixtures: no native run or live provider acceptance claim."""
from copy import deepcopy
import pytest
from xverse_studio.comparison import compare_runs


def pair():
    left = {
        'runId': 'fixture-left',
        'snapshot': {'semanticDigest': 'model', 'planDigest': 'plan', 'parameters': {'gain': 1}, 'providerIdentity': {'id': 'owned'}, 'clockDomainRef': 'simulation-time'},
        'evidence': {'integrity': 'valid', 'status': 'complete'},
        'observations': [{'observerRef': 'fixture-observer', 'field': 'state', 'unit': '1', 'quantity': 'dimensionless', 'unitDefinitionDigest': 'one', 'clockDomainRef': 'simulation-time', 'coverage': {'verified': True, 'complete': True, 'startTick': 0, 'endTick': 10, 'gaps': []}}],
    }
    right = deepcopy(left)
    right['runId'] = 'fixture-right'
    return left, right


def test_equal_known_windows_remain_comparable():
    left, right = pair()
    assert compare_runs(left, right)['compatible'] is True


def test_complete_flag_without_window_bounds_does_not_establish_equivalence():
    left, right = pair()
    for value in (left, right):
        del value['observations'][0]['coverage']['startTick']
        del value['observations'][0]['coverage']['endTick']
    assert compare_runs(left, right)['compatible'] is False


def test_distinct_complete_windows_are_not_like_for_like():
    left, right = pair()
    right['observations'][0]['coverage']['endTick'] = 20
    assert compare_runs(left, right)['compatible'] is False


@pytest.mark.parametrize('start,end', [(11, 10), (float('nan'), 10), (0, float('inf')), (False, 10)])
def test_invalid_window_is_not_like_for_like(start, end):
    left, right = pair()
    right['observations'][0]['coverage'].update(startTick=start, endTick=end)
    assert compare_runs(left, right)['compatible'] is False


def test_missing_observer_identity_is_not_provenance_equivalence():
    left, right = pair()
    for value in (left, right):
        del value['observations'][0]['observerRef']
    assert compare_runs(left, right)['compatible'] is False

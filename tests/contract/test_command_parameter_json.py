"""Command input must be canonicalizable before lookup, fingerprinting or effects."""

import pytest

from xverse_studio.api.models import Command


@pytest.mark.parametrize('token', ['NaN', 'Infinity', '-Infinity', '1e999'])
@pytest.mark.parametrize('position', ['value', 'nested'])
def test_nonfinite_command_json_is_rejected_before_runtime_or_fingerprinting(client, monkeypatch, token, position):
    studio = client.app.state.studio
    before = studio.store.all('operation')
    called = []

    def forbidden(*args, **kwargs):
        called.append(True)
        raise AssertionError('Nonfinite JSON must not reach runtime command dispatch')

    monkeypatch.setattr(studio.runs, 'command', forbidden)
    parameters = ('{"inputId":"target","expectedValue":1,"value":' + token + '}' if position == 'value'
        else '{"inputId":"target","expectedValue":1,"value":2,"extra":{"values":[' + token + ']}}')
    body = '{"kind":"set_parameter","expectedStateVersion":1,"parameters":' + parameters + '}'
    response = client.post('/api/v1/runs/never-look-up-this-run/commands',
        headers={'Idempotency-Key': 'invalid-json', 'Content-Type': 'application/json'}, content=body)
    assert response.status_code == 422 and response.json()['code'] == 'REQUEST_INVALID', response.text
    assert called == [] and studio.store.all('operation') == before


def test_command_json_requires_encodable_unicode_before_fingerprinting(client, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Unencodable JSON must not reach runtime command dispatch')

    monkeypatch.setattr(client.app.state.studio.runs, 'command', forbidden)
    response = client.post('/api/v1/runs/never-look-up-this-run/commands',
        headers={'Idempotency-Key': 'invalid-unicode', 'Content-Type': 'application/json'},
        content=r'{"kind":"set_parameter","expectedStateVersion":1,"parameters":{"inputId":"\ud800"}}')
    assert response.status_code == 422 and response.json()['code'] == 'REQUEST_INVALID', response.text


def test_finite_command_json_preserves_opaque_payload_and_reaches_normal_lookup(client):
    parameters = {'value': 1.25, 'metadata': {'unit': '1', 'label': 'Ω', 'nested': [None, True, 2]}}
    body = {'kind': 'set_parameter', 'expectedStateVersion': 1, 'parameters': parameters}
    assert Command.model_validate(body).model_dump()['parameters'] == parameters
    response = client.post('/api/v1/runs/missing-finite-json-run/commands',
        headers={'Idempotency-Key': 'finite-lookup'}, json=body)
    assert response.status_code == 404 and response.json()['code'] == 'NOT_FOUND', response.text

import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient


def pytest_addoption(parser):
    parser.addoption('--owned-failure-dir', default=None,
                     help='Diagnostic output for explicitly marked owned native failures.')


def pytest_configure(config):
    from studio_native_failure_capture import NativeFailureCapture

    config.addinivalue_line('markers', 'capture_owned_native_failure: retain bounded owned run diagnostics on failure')
    output = config.getoption('--owned-failure-dir') or config.rootpath / 'test-results' / 'native-failures'
    config._studio_owned_failure_capture = NativeFailureCapture(output)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if not report.failed or report.when not in ('setup', 'call') or not item.get_closest_marker('capture_owned_native_failure'):
        return
    client = item.funcargs.get('client')
    if client is None:
        report.sections.append(('Owned native diagnostics', 'Unavailable: no live client fixture.'))
        return
    try:
        result = item.config._studio_owned_failure_capture.capture(client.app.state.studio, item.nodeid)
        message = 'Capture status: ' + result['status'] + '; ' + result.get('captureId', result.get('code', ''))
    except Exception as exc:
        # A failed diagnostic write must preserve the original test failure.
        message = 'Capture unavailable: ' + type(exc).__name__
    report.sections.append(('Owned native diagnostics', message))


# Contributor test files stay on the user's chosen loop10 filesystem.
@pytest.fixture
def client(tmp_path):
    from xverse_studio.api.app import create_app

    app = create_app(
        tmp_path, allowed_hosts=["testserver"], bootstrap_token="test-bootstrap"
    )
    with TestClient(app, base_url="http://testserver") as c:
        c.headers["Origin"] = "http://testserver"
        response = c.post("/api/v1/session", json={"bootstrapToken": "test-bootstrap"})
        assert response.status_code == 200, response.text
        c.headers["X-CSRF-Token"] = response.json()["csrfToken"]
        yield c

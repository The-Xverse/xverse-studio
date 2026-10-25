import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient


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

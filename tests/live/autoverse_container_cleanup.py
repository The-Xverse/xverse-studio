"""Native readback negatives against the actual enrolled stopped Autoverse target.

Only returned observations/claims are faulted. Docker mutation is forbidden in
these cases; complete-demo Stop and acknowledgement loss have separate live proof.
"""

from copy import deepcopy
import json
import os
from pathlib import Path
import time

import pytest

from xverse_studio.providers.autoverse import cleanup
from xverse_studio.providers.autoverse.installation import container_fact, inspect


@pytest.fixture
def enrolled(monkeypatch):
    path = os.environ.get("STUDIO_AUTOVERSE_TEST_INSTALLATION")
    assert path, "An explicit actual Autoverse installation is required"
    installation = json.loads(Path(path).read_bytes())["classic"]
    expected = installation["containers"]["android"]
    row = inspect(installation["docker"], expected["id"])
    assert container_fact(row) == expected and row["State"]["Running"] is False
    claim = {"identity": deepcopy(expected), "startedAt": row["State"]["StartedAt"]}
    original = cleanup.subprocess.run
    calls = []

    def read_only(argv, **options):
        assert argv == [installation["docker"], "inspect", expected["id"]], (
            "A stopped-target readback case must not dispatch a mutation"
        )
        calls.append("actual enrolled container inspection")
        return original(argv, **options)

    monkeypatch.setattr(cleanup.subprocess, "run", read_only)
    return installation, claim, row, calls


def test_actual_stopped_autoverse_target_has_current_owner_readback(enrolled):
    installation, claim, _, calls = enrolled
    assert cleanup.cleanup_container(installation, "android", claim) == {
        "resourceId": "android",
        "kind": "container",
        "status": "released",
    }
    assert len(calls) == 2


@pytest.mark.parametrize(
    "fault", ["missing-start", "changed-start", "changed-configuration"]
)
def test_autoverse_unknown_claim_never_dispatches_cleanup(enrolled, fault):
    installation, claim, _, calls = enrolled
    if fault == "missing-start":
        claim["startedAt"] = None
    elif fault == "changed-start":
        claim["startedAt"] = "unverified-native-start"
    else:
        claim["identity"]["configurationDigest"] = "sha256:" + "0" * 64
    result = cleanup.cleanup_container(installation, "android", claim)
    assert result["status"] == "unknown"
    assert result["diagnostics"] == ["AUTOVERSE_CONTAINER_OWNERSHIP_UNKNOWN"]
    assert len(calls) == 1


@pytest.mark.parametrize("fault", ["unavailable", "malformed"])
def test_autoverse_inspection_failure_is_coded_without_private_echo(
    enrolled, monkeypatch, fault
):
    installation, claim, row, calls = enrolled

    def failed(*args, **options):
        if fault == "unavailable":
            raise OSError("owned-private-marker: " + "x" * 4096)
        result = deepcopy(row)
        result["State"] = None
        return result

    monkeypatch.setattr(cleanup, "inspect", failed)
    result = cleanup.cleanup_container(installation, "android", claim)
    assert result["status"] == "unknown"
    assert result["diagnostics"] == ["AUTOVERSE_CONTAINER_INSPECTION_UNAVAILABLE"]
    assert "owned-private-marker" not in json.dumps(result)
    assert len(json.dumps(result)) < 512 and not calls


@pytest.mark.parametrize(
    "fault", ["start", "configuration", "unavailable", "running", "running-type"]
)
def test_autoverse_final_readback_cannot_release_a_changed_or_unconfirmed_target(
    enrolled, monkeypatch, fault
):
    installation, claim, row, calls = enrolled
    count = []
    actual_inspect = cleanup.inspect

    def later(*args, **options):
        count.append(True)
        if len(count) == 1:
            return actual_inspect(*args, **options)
        result = deepcopy(row)
        if fault == "unavailable":
            raise OSError("owned-private-marker")
        if fault == "start":
            result["State"]["StartedAt"] = "another-start-observation"
        elif fault == "configuration":
            result["Config"]["Image"] = "unverified-configuration"
        elif fault == "running":
            result["State"]["Running"] = True
        else:
            result["State"]["Running"] = "false"
        return result

    monkeypatch.setattr(cleanup, "inspect", later)
    result = cleanup.cleanup_container(installation, "android", claim)
    assert result["status"] == "unknown"
    expected = (
        "AUTOVERSE_CONTAINER_INSPECTION_UNAVAILABLE"
        if fault == "unavailable"
        else "AUTOVERSE_CONTAINER_STOP_UNCONFIRMED"
        if fault == "running"
        else "AUTOVERSE_CONTAINER_OWNERSHIP_UNKNOWN"
    )
    assert result["diagnostics"] == [expected]
    assert len(count) == 2 and len(calls) == 1


def test_autoverse_expired_cleanup_budget_performs_no_inspection_or_mutation(enrolled):
    installation, claim, _, calls = enrolled
    result = cleanup.cleanup_container(
        installation, "android", claim, deadline=time.monotonic() - 1
    )
    assert result["status"] == "unknown"
    assert result["diagnostics"] == ["AUTOVERSE_CLEANUP_DEADLINE"]
    assert not calls

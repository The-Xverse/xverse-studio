"""Actual backend interruption at declared fixture-controlled lease boundaries.

Only timing is injected; production writes and HTTP routes are not substituted.
Provider effects use a test-only durable JSON fixture, never actual equipment.
"""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import signal
import sqlite3
import sys
import time
from contextlib import closing

import httpx
import pytest

from test_lab_native_restart import identity, login, ROOT
import selectors
import subprocess

pytestmark = pytest.mark.skipif(
    sys.platform != "linux",
    reason="Linux process-identity crash probe; Windows held separately.",
)


def start(data, boundary, phase):
    args = [
        sys.executable,
        "-I",
        str(ROOT / "tests/fixtures/providers/physical/interruption_host.py"),
        "--data",
        str(data),
        "--boundary",
        boundary,
        "--phase",
        phase,
    ]
    with (data.parent / (phase + "-stderr.private.log")).open("wb") as log:
        child = subprocess.Popen(
            args, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=log
        )
    try:
        proof = identity(child, args)
        with selectors.DefaultSelector() as selector:
            selector.register(child.stdout, selectors.EVENT_READ)
            assert selector.select(15), "Owned interruption startup timed out"
            message = child.stdout.readline(4097)
        assert len(message) <= 4096 and message.endswith(b"\n")
        origin = json.loads(message)["origin"]
        assert origin.startswith("http://127.0.0.1:")
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            try:
                if httpx.get(origin + "/api/v1/session", timeout=1).status_code == 401:
                    return child, args, proof, origin
            except httpx.HTTPError:
                pass
            time.sleep(0.02)
        raise AssertionError("Owned interruption host did not reach HTTP readiness")
    except BaseException:
        if child.poll() is None:
            identity(child, args)
            child.kill()
        child.wait(timeout=15)
        raise


def durable_records(data):
    uri = (data / "studio.sqlite").resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True, timeout=1)) as db:
        return {
            kind: [
                json.loads(row[0])
                for row in db.execute("SELECT body FROM records WHERE kind=?", (kind,))
            ]
            for kind in ("operation", "lab_registry")
        }


@pytest.mark.parametrize(
    "boundary", ["before-delegation", "after-provider-effect", "before-final-receipt"]
)
def test_native_interruption_never_replays_original_reservation(tmp_path, boundary):
    data = tmp_path / "owned interrupted backend Ω"
    marker, effect = (
        tmp_path / "boundary.private.json",
        tmp_path / "provider-effect.private.json",
    )
    key, route = (
        "owned-interrupted-reservation",
        "/api/v1/assets/fixture:bench-sensor/reservations",
    )
    children, proofs = [], []
    try:
        child, args, proof, origin = start(data, boundary, "initial")
        children.append((child, args))
        proofs.append(proof)
        with (
            closing(login(data, origin)) as client,
            ThreadPoolExecutor(max_workers=1) as pool,
        ):
            pending = pool.submit(
                client.post,
                route,
                headers={"Idempotency-Key": key},
                json={"durationSeconds": 300},
            )
            deadline = time.monotonic() + 10
            while not marker.exists() and time.monotonic() < deadline:
                assert child.poll() is None
                time.sleep(0.005)
            assert marker.exists(), (
                "Actual operation did not enter its declared fixture pause"
            )
            phase = json.loads(marker.read_text())
            assert phase["boundary"] == boundary and phase["phase"] == "initial"
            before = durable_records(data)
            operations = [
                row for row in before["operation"] if row["kind"] == "lab_reserve"
            ]
            assert len(operations) == 1
            operation = operations[0]
            rid = operation["reservationId"]
            assert operation["status"] == (
                "accepted" if boundary == "before-delegation" else "delegated"
            )
            records = (
                before["lab_registry"][0]["records"] if before["lab_registry"] else []
            )
            expected_effects = 0 if boundary == "before-delegation" else 1
            assert phase["reservationEffects"] == expected_effects
            if boundary == "before-delegation":
                assert (
                    records == []
                    and not effect.exists()
                    and phase["calls"].count("reserve") == 0
                )
            else:
                assert len(records) == 1 and records[0]["reservationId"] == rid
                assert records[0]["status"] == (
                    "owned" if boundary == "before-final-receipt" else "unknown"
                )
                assert bool(records[0]["fencingIdentity"]) == (
                    boundary == "before-final-receipt"
                )
                assert phase["calls"].count("reserve") == 1
            provider_before = effect.read_bytes() if effect.exists() else None
            assert identity(child, args) == proof
            child.send_signal(signal.SIGKILL)
            assert child.wait(timeout=15) == -signal.SIGKILL
            with pytest.raises(httpx.TransportError):
                pending.result(timeout=10)
        assert not (tmp_path / "initial-observation.json").exists()
        child, args, proof, origin = start(data, boundary, "restart")
        children.append((child, args))
        proofs.append(proof)
        with closing(login(data, origin)) as client:
            replay = client.post(
                route, headers={"Idempotency-Key": key}, json={"durationSeconds": 300}
            )
            assert replay.status_code == 202
            receipt = replay.json()
            assert (
                receipt["operationId"] == operation["operationId"]
                and receipt["reservationId"] == rid
            )
            assert (
                receipt["status"] == "unknown"
                and receipt["code"] == "LAB_OPERATION_INTERRUPTED"
            )
            assert (
                client.post(
                    route,
                    headers={"Idempotency-Key": key},
                    json={"durationSeconds": 300},
                ).json()
                == receipt
            )
            assert (
                client.get("/api/v1/operations/" + operation["operationId"]).json()
                == receipt
            )
            observed = client.get("/api/v1/reservations/" + rid)
            if boundary == "before-delegation":
                assert observed.status_code == 404
            else:
                assert (
                    observed.status_code == 200
                    and observed.json()["status"] == "unknown"
                )
                for field in [
                    "reservationId",
                    "assetId",
                    "providerId",
                    "owner",
                    "scope",
                    "expiry",
                    "fencingIdentity",
                ]:
                    assert observed.json()[field] == records[0][field]
            fence = records[0]["fencingIdentity"] if records else None
            refused = client.post(
                "/api/v1/reservations/" + rid + "/renewals",
                headers={"Idempotency-Key": "owned-interrupted-renew"},
                json={
                    "durationSeconds": 300,
                    "fencingIdentity": fence or "unconfirmed-fixture-fence",
                },
            )
            assert refused.status_code == (
                404 if boundary == "before-delegation" else 422
            )
            if boundary != "before-delegation":
                assert refused.json()["code"] == "OWNERSHIP_UNCERTAIN"
            checked = client.post(
                "/api/v1/reservations/" + rid + "/reconciliations",
                headers={"Idempotency-Key": "owned-interrupted-inspect"},
                json={},
            )
            assert checked.status_code == (
                404 if boundary == "before-delegation" else 202
            )
            if boundary != "before-delegation":
                restored = client.get("/api/v1/reservations/" + rid).json()
                assert restored["status"] == (
                    "owned" if boundary == "before-final-receipt" else "unknown"
                )
                assert restored["fencingIdentity"] == fence
            assert (
                client.post(
                    route,
                    headers={"Idempotency-Key": key},
                    json={"durationSeconds": 300},
                ).json()
                == receipt
            )
            assert client.get("/api/v1/runs").json()["items"] == []
            caps = client.get("/api/v1/capabilities").json()["labReservations"]
            assert (
                caps["runtimeAdmission"] == "unavailable"
                and caps["physicalCommands"] == []
            )
        after = durable_records(data)
        assert (
            len([row for row in after["operation"] if row["kind"] == "lab_reserve"])
            == 1
        )
        assert (effect.read_bytes() if effect.exists() else None) == provider_before
        assert identity(child, args) == proof
        child.terminate()
        assert child.wait(timeout=15) in (0, -signal.SIGTERM)
        observer = json.loads((tmp_path / "restart-observation.json").read_text())
        assert observer["calls"] == (
            []
            if boundary == "before-delegation"
            else ["inventory", "inventory", "inventory", "inspect"]
        )
        assert (
            observer["reservationEffects"] == observer["heldLeases"] == expected_effects
        )
        (tmp_path / "interruption-result.private.json").write_text(
            json.dumps(
                {
                    "boundary": boundary,
                    "outcome": "passed",
                    "processes": proofs,
                    "durableBefore": before,
                    "durableAfter": after,
                    "pauseObservation": phase,
                    "restartObservation": observer,
                    "effectSha256": hashlib.sha256(provider_before).hexdigest()
                    if provider_before
                    else None,
                    "scope": "Actual Linux backend crash at timing-only fixture boundary; provider continuity is a durable JSON fixture, not an actual external provider/device.",
                },
                indent=2,
            )
            + "\n"
        )
    finally:
        for child, args in children:
            if child.poll() is None:
                identity(child, args)
                child.terminate()
                try:
                    child.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    identity(child, args)
                    child.kill()
                    child.wait(timeout=5)

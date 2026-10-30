"""Actual native Autoverse input admission/cleanup; metadata faults only.

The explicit native fixture supplies the real enrolled classic adapter. This
driver edits only its owned descriptor-fault file and its newly created snapshot
for an integrity negative. No provider lifecycle, telemetry or outcome is faked.
"""

import argparse
import json
from pathlib import Path
import re
import statistics
import time

import httpx

from xverse_studio.blueprints.autoverse import documents
from xverse_studio.storage.core import atomic, canonical, digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--url", required=True)
    args = parser.parse_args()
    root = args.data_dir.resolve()
    if (
        root.parent.name != "browser-tests"
        or not re.fullmatch(r"http://127\.0\.0\.1:[0-9]{1,5}", args.url)
        or any((root / "runs").glob("*"))
        or (root / "active-control-verification.json").exists()
    ):
        parser.error(
            "A fresh owned native Autoverse fixture and exact loopback URL are required"
        )
    report = {
        "scope": "actual complete native Autoverse classic demo, studio-browser input variant",
        "outcome": "failed",
        "inputResults": [],
        "finiteJsonResults": [],
        "authenticationResults": [],
        "failures": [],
    }
    rid = None
    snapshot_file = None
    snapshot_raw = None
    timings = []
    fault_file = root / "descriptor-fault.txt"

    def fault(value):
        atomic(fault_file, value.encode())

    def check(condition, message):
        if not condition:
            report["failures"].append(message)

    with httpx.Client(
        base_url=args.url, headers={"Origin": args.url}, timeout=30
    ) as api:
        token = json.loads((root / "bootstrap.json").read_bytes())["bootstrapToken"]
        login = api.post("/api/v1/session", json={"bootstrapToken": token})
        assert login.status_code == 200
        api.headers["X-CSRF-Token"] = login.json()["csrfToken"]
        create = api.post(
            "/api/v1/projects",
            json={
                "name": "Autoverse active provider admission",
                "blueprintRef": "autoverse-classic",
            },
        )
        assert create.status_code == 201, create.text
        p = create.json()
        # Select the complete supported browser-input variant through ordinary
        # source authoring. Default/current user projects remain Pygame projects.
        variant = documents("studio-browser")
        for docid, doc in list(p["documents"].items()):
            content = variant[Path(doc["path"]).name]
            if doc["content"] != content:
                saved = api.put(
                    f"/api/v1/projects/{p['projectId']}/documents/{docid}",
                    headers={"If-Match": str(p["revision"])},
                    json={"content": content, "format": "yaml"},
                )
                assert saved.status_code == 200, saved.text
                p = saved.json()
        pf = api.post(
            f"/api/v1/projects/{p['projectId']}/preflights",
            json={"revision": p["revision"], "providerId": "autoverse.demo"},
        )
        assert pf.status_code == 200 and pf.json()["status"] == "ready", pf.text
        snapshot_file = root / "snapshots" / pf.json()["snapshotId"] / "snapshot.json"
        snapshot_raw = snapshot_file.read_bytes()
        start = api.post(
            "/api/v1/runs",
            headers={"Idempotency-Key": "actual-active-autoverse"},
            json={key: pf.json()[key] for key in ("snapshotId", "preflightId")},
        )
        assert start.status_code == 202, start.text
        rid = start.json()["runId"]
        print("RUN", rid, flush=True)
        runroot = root / "runs" / rid
        route = f"/api/v1/runs/{rid}"

        def run():
            r = api.get(route)
            assert r.status_code == 200, r.text
            return r.json()

        def send(action, body):
            before = time.monotonic()
            r = api.post(route + "/input/" + action, json=body)
            timings.append(time.monotonic() - before)
            return r

        def lease():
            got = send("acquire", {})
            assert got.status_code == 200, got.text
            return {key: got.json()[key] for key in ("leaseToken", "generation")}

        def mailbox():
            return {
                name: (runroot / name).read_bytes()
                if (runroot / name).exists()
                else None
                for name in ["input-owner.json", "input.json"]
            }

        try:
            deadline = time.monotonic() + 540
            previous = None
            while time.monotonic() < deadline:
                value = run()
                phase = (value["state"], value.get("runtimeStatus", {}).get("phase"))
                if phase != previous:
                    print("OBSERVED", phase, flush=True)
                    previous = phase
                if value["state"] == "running":
                    break
                assert value["state"] not in ("stopped", "failed"), value
                time.sleep(1)
            assert (
                value["state"] == "running"
                and value["inputSurface"]["kind"] == "normalized-driver"
            ), value
            positive = lease()
            frame = {"sequence": 1, "throttle": 0, "brake": 1, "steer": 0}
            staged = send("frame", {**positive, "frame": frame})
            assert staged.status_code == 200, staged.text
            publication = staged.json()["publicationSequence"]
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if (
                    run().get("inputTelemetry", {}).get("lastPublishedSequence", 0)
                    >= publication
                ):
                    report["actualNativePublicationObserved"] = True
                    break
                time.sleep(0.1)
            assert report.get("actualNativePublicationObserved")
            # The complete actual demo remains running while invalid callers
            # attempt both input publication and owned Stop. Never replay an
            # uncertain mutation; each negative has its own transport.
            for invalid in [
                "missing-session",
                "missing-origin",
                "wrong-origin",
                "missing-csrf",
                "wrong-csrf",
                "nonascii-csrf",
            ]:
                headers = dict(api.headers)
                cookies = api.cookies
                if invalid == "missing-session":
                    cookies = {}
                elif invalid == "missing-origin":
                    headers.pop("origin", None)
                elif invalid == "wrong-origin":
                    headers["origin"] = "http://foreign.invalid"
                elif invalid == "missing-csrf":
                    headers.pop("x-csrf-token", None)
                else:
                    headers["x-csrf-token"] = "invalid"
                encoded_headers = [
                    (k.encode("ascii"), v.encode("ascii")) for k, v in headers.items()
                ]
                if invalid == "nonascii-csrf":
                    encoded_headers = [
                        (k, v) for k, v in encoded_headers if k != b"x-csrf-token"
                    ]
                    encoded_headers.append((b"x-csrf-token", b"\xff"))
                for action in ["frame", "stop"]:
                    original = mailbox()
                    command_file = runroot / "command.json"
                    command_before = (
                        command_file.read_bytes() if command_file.exists() else None
                    )
                    body = (
                        {**positive, "frame": {**frame, "sequence": 2}}
                        if action == "frame"
                        else {
                            "kind": "stop",
                            "expectedStateVersion": run()["stateVersion"],
                        }
                    )
                    endpoint = route + (
                        "/input/frame" if action == "frame" else "/commands"
                    )
                    with httpx.Client(
                        base_url=args.url,
                        headers=encoded_headers,
                        cookies=cookies,
                        timeout=30,
                    ) as refused:
                        response = refused.post(
                            endpoint,
                            json=body,
                            headers={"Idempotency-Key": "denied-autoverse-" + invalid},
                        )
                    expected = 401 if invalid == "missing-session" else 403
                    report["authenticationResults"].append(
                        {
                            "case": invalid,
                            "action": action,
                            "status": response.status_code,
                        }
                    )
                    check(
                        response.status_code == expected,
                        f"{invalid}/{action}: expected authentication refusal",
                    )
                    check(
                        mailbox() == original,
                        f"{invalid}/{action}: changed original input mailbox",
                    )
                    check(
                        (command_file.read_bytes() if command_file.exists() else None)
                        == command_before,
                        f"{invalid}/{action}: delegated an unauthorized command",
                    )
                    check(
                        run()["state"] == "running",
                        f"{invalid}/{action}: changed actual running lifecycle",
                    )
            # Expired ownership is never silently renewed by a read observation.
            time.sleep(0.8)

            for name in ["invalid", "changed", "unavailable", "host", "broken"]:
                fault("valid")
                owner = lease()
                baseline = send("frame", {**owner, "frame": frame})
                assert baseline.status_code == 200, baseline.text
                time.sleep(0.06)
                original = mailbox()
                fault(name)
                replacement = owner
                for action, body in [
                    ("frame", {**owner, "frame": {**frame, "sequence": 2}}),
                    ("release", owner),
                    ("acquire", {}),
                ]:
                    reply = send(action, body)
                    code = reply.json().get("code")
                    report["inputResults"].append(
                        {
                            "fault": name,
                            "action": action,
                            "status": reply.status_code,
                            "code": code,
                        }
                    )
                    check(
                        reply.status_code == 409
                        and code == "PROVIDER_ADMISSION_CHANGED",
                        f"{name}/{action}: expected provider refusal, got {reply.status_code}/{code}",
                    )
                    check(
                        "owned-private-marker" not in reply.text,
                        "Native describe exception was exposed",
                    )
                    check(
                        mailbox() == original,
                        f"{name}/{action}: original input/mailbox changed",
                    )
                    if action == "acquire" and reply.status_code == 200:
                        replacement = {
                            key: reply.json()[key]
                            for key in ("leaseToken", "generation")
                        }
                fault("valid")
                released = send("release", replacement)
                assert released.status_code in (200, 409), released.text
                time.sleep(0.8)

            fault("valid")
            owner = lease()
            original = mailbox()
            for label, literal in [
                ("nan", "NaN"),
                ("infinity", "Infinity"),
                ("negative-infinity", "-Infinity"),
                ("overflow", "1e999"),
            ]:
                body = json.dumps({**owner, "frame": frame}).replace(
                    '"throttle": 0', '"throttle": ' + literal
                )
                # A real500 can close its keep-alive connection. Give each
                # malformed request an independent transport; never replay a
                # mutation to conceal an uncertain acknowledgement.
                with httpx.Client(
                    base_url=args.url,
                    headers=dict(api.headers),
                    cookies=api.cookies,
                    timeout=30,
                ) as invalid_client:
                    reply = invalid_client.post(
                        route + "/input/frame",
                        content=body,
                        headers={"Content-Type": "application/json"},
                    )
                report["finiteJsonResults"].append(
                    {"case": label, "status": reply.status_code}
                )
                check(
                    reply.status_code == 422,
                    f"{label}: nonfinite request did not reject as422",
                )
                check(
                    mailbox() == original,
                    f"{label}: invalid JSON changed the input mailbox",
                )
            send("release", owner)
            time.sleep(0.8)

            original = mailbox()
            snapshot_file.write_bytes(snapshot_raw + b"\n")
            broken = send("acquire", {})
            report["snapshotIntegrity"] = {
                "status": broken.status_code,
                "code": broken.json().get("code"),
            }
            check(
                broken.status_code == 422
                and broken.json().get("code") == "SNAPSHOT_INTEGRITY",
                "Changed sealed snapshot allowed input acquisition",
            )
            check(
                mailbox() == original,
                "Changed snapshot request mutated the input owner",
            )
            # Original ownership cleanup must still work while fresh admission is
            # unavailable and the independent frozen-file negative remains active.
            fault("invalid")
            stop_body = {"kind": "stop", "expectedStateVersion": run()["stateVersion"]}
            stopped = api.post(
                route + "/commands",
                headers={"Idempotency-Key": "actual-stop-under-invalid-descriptor"},
                json=stop_body,
            )
            assert stopped.status_code == 202, stopped.text
            receipt = stopped.json()
            deadline = time.monotonic() + 120
            while time.monotonic() < deadline:
                value = run()
                if value["state"] in ("stopped", "failed"):
                    break
                time.sleep(1)
            assert value["state"] == "stopped" and value["cleanup"] == "complete", value
            retry = api.post(
                route + "/commands",
                headers={"Idempotency-Key": "actual-stop-under-invalid-descriptor"},
                json=stop_body,
            )
            assert retry.status_code == 202 and retry.json() == receipt, retry.text
            report.update(
                ownedStopWhileAdmissionInvalid=True,
                sameStopReceiptAfterTerminal=True,
                terminal={
                    key: value.get(key) for key in ("state", "cleanup", "evidence")
                },
            )
            report["outcome"] = "passed" if not report["failures"] else "failed"
        finally:
            if rid:
                current = run()
                if current["state"] in ("running", "preparing", "ready"):
                    api.post(
                        route + "/commands",
                        headers={"Idempotency-Key": "owned-active-check-final-stop"},
                        json={
                            "kind": "stop",
                            "expectedStateVersion": current["stateVersion"],
                        },
                    )
                    deadline = time.monotonic() + 120
                    while time.monotonic() < deadline and run()["state"] not in (
                        "stopped",
                        "failed",
                    ):
                        time.sleep(1)
            if snapshot_file and snapshot_raw is not None:
                snapshot_file.write_bytes(snapshot_raw)
                report["originalSnapshotRestored"] = digest(
                    snapshot_file.read_bytes()
                ) == digest(snapshot_raw)
            if timings:
                report["apiRequestSeconds"] = {
                    "count": len(timings),
                    "median": statistics.median(timings),
                    "max": max(timings),
                }
            atomic(
                root / "active-control-verification.json", canonical(report).encode()
            )
    print(
        "ACTIVE_CONTROL_OUTCOME",
        report["outcome"],
        "failures",
        len(report["failures"]),
        flush=True,
    )
    return 0 if report["outcome"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Owned disposable evidence only: no runtime/device ownership or private stream."""

import asyncio
import base64
import builtins
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import zipfile

import pytest

from xverse_studio.evidence.reader import read_journal
from xverse_studio.storage.core import Store
from xverse_studio.storage.core import canonical, digest


def load_fixture(name):
    path = Path(__file__).resolve().parents[1] / "fixtures/evidence" / name
    spec = importlib.util.spec_from_file_location(name.replace(".", "_"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_recorded = load_fixture("create_recorded_evidence.py")
_stream = load_fixture("stream_fixtures.py")


def cursor(run_id, snapshot_id, sequence="0", record_digest="0" * 64):
    payload = json.dumps(
        {"r": run_id, "s": snapshot_id, "q": sequence, "d": record_digest},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return "st1." + base64.urlsafe_b64encode(payload).decode().rstrip("=")


def run_async(awaitable):
    async def bounded():
        return await asyncio.wait_for(awaitable, timeout=10)

    return asyncio.run(bounded())


def frames(text):
    if isinstance(text, bytes):
        text = text.decode()
    result = []
    for block in text.replace("\r\n", "\n").split("\n\n"):
        fields = {}
        for line in block.splitlines():
            if not line or line.startswith(":"):
                continue
            key, _, value = line.partition(":")
            fields[key] = value.lstrip(" ")
        if "data" in fields:
            fields["data"] = json.loads(fields["data"])
            result.append(fields)
    return result


@pytest.fixture
def recorded(client):
    project = client.post(
        "/api/v1/projects", json={"name": "New stream fixture"}
    ).json()
    studio = client.app.state.studio
    return _recorded.create_recorded_evidence(
        studio.store, studio.projects, studio.runs, project["projectId"], noise=0
    )


def test_v11_source_proof_resume_and_resync_watermark_are_read_only(client, recorded):
    rid, sid = recorded["runId"], recorded["snapshotId"]
    studio = client.app.state.studio
    root = studio.runs.directory(rid)
    original = (root / "evidence.jsonl").read_bytes()
    expected, integrity = read_journal(root, studio.runs.read(rid))
    response = client.get(f"/api/v1/runs/{rid}/events", params={"streamVersion": "1.1"})
    assert response.status_code == 200, response.text
    delivered = frames(response.text)
    events = [
        frame for frame in delivered if frame.get("event") != "studio.stream_control"
    ]
    assert [item["data"] for item in events] == expected
    assert all(item["id"].startswith("st1.") for item in events)
    second = client.get(
        f"/api/v1/runs/{rid}/events",
        params={"streamVersion": "1.1", "after": events[1]["id"]},
    )
    assert second.status_code == 200, second.text
    assert [
        item["data"]
        for item in frames(second.text)
        if item.get("event") != "studio.stream_control"
    ] == expected[2:]
    response = client.get(f"/api/v1/runs/{rid}/resync")
    assert response.status_code == 200, response.text
    resync = response.json()
    assert resync["streamVersion"] == "1.1" and resync["snapshotId"] == sid
    assert resync["watermark"] == {
        "sequence": expected[-1]["sequence"],
        "digest": expected[-1]["digest"],
    }
    assert resync["history"]["items"] == expected[-200:]
    assert resync["history"]["integrity"] == integrity
    assert resync["history"]["nextCursor"] is None
    resumed = client.get(
        f"/api/v1/runs/{rid}/events",
        params={"streamVersion": "1.1", "after": resync["resumeCursor"]},
    )
    assert resumed.status_code == 200, resumed.text
    assert not [
        item
        for item in frames(resumed.text)
        if item.get("event") != "studio.stream_control"
    ]
    assert (root / "evidence.jsonl").read_bytes() == original


def test_v11_digest_fork_requires_resynchronization_not_empty_success(client, recorded):
    rid, sid = recorded["runId"], recorded["snapshotId"]
    response = client.get(
        f"/api/v1/runs/{rid}/events",
        params={"streamVersion": "1.1", "after": cursor(rid, sid, "1", "f" * 64)},
    )
    assert response.status_code == 410, response.text
    error = response.json()
    assert error["code"] == "STREAM_RESYNC_REQUIRED"
    for key in ("stateUrl", "historyUrl", "resyncUrl"):
        assert rid in error[key]
    assert error.get("missingCount") is None


def test_v11_expired_replay_reports_exact_range_and_fresh_resync(client):
    project = client.post(
        "/api/v1/projects", json={"name": "New expired stream fixture"}
    ).json()
    studio = client.app.state.studio
    recorded = _recorded.create_recorded_evidence(
        studio.store, studio.projects, studio.runs, project["projectId"], noise=1005
    )
    rid, sid = recorded["runId"], recorded["snapshotId"]
    path = studio.runs.directory(rid) / "evidence.jsonl"
    original = path.read_bytes()
    response = client.get(
        f"/api/v1/runs/{rid}/events",
        params={"streamVersion": "1.1", "after": cursor(rid, sid)},
    )
    assert response.status_code == 410, response.text
    error = response.json()
    assert error["code"] == "CURSOR_EXPIRED"
    details = error
    omitted = recorded["recordCount"] - 1000
    assert details["firstMissingSequence"] == "1"
    assert details["lastMissingSequence"] == str(omitted)
    assert details["missingCount"] == omitted

    def decode(token):
        assert token.startswith("st1.")
        encoded = token[4:]
        return json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))

    assert decode(details["earliestCursor"])["q"] == str(omitted)
    assert decode(details["earliestAvailableCursor"])["q"] == str(omitted + 1)
    resync = client.get(details["resyncUrl"])
    assert resync.status_code == 200, resync.text
    body = resync.json()
    assert len(body["history"]["items"]) <= 200
    assert body["history"]["omittedRecords"] == recorded["recordCount"] - len(
        body["history"]["items"]
    )
    assert body["watermark"]["sequence"] == str(recorded["recordCount"])
    assert path.read_bytes() == original


@pytest.mark.parametrize(
    "kind,status,code",
    [
        ("missing", 503, "STREAM_SOURCE_UNAVAILABLE"),
        ("invalid", 422, "EVIDENCE_INVALID"),
    ],
)
def test_v11_unavailable_and_invalid_never_look_like_empty_valid_stream(
    client, recorded, kind, status, code
):
    studio = client.app.state.studio
    rid = recorded["runId"]
    path = studio.runs.directory(rid) / "evidence.jsonl"
    if kind == "missing":
        path.rename(path.with_name("owned-fixture-missing-source.jsonl"))
    else:
        # Only this newly allocated disposable fixture is corrupted.
        path.write_bytes(path.read_bytes() + b"bad-new-fixture-tail\n")
    response = client.get(f"/api/v1/runs/{rid}/events", params={"streamVersion": "1.1"})
    assert response.status_code == status, response.text
    assert response.json()["code"] == code


def test_only_admitted_public_redacted_journal_is_read_or_exported(
    client, recorded, tmp_path, monkeypatch
):
    """No invented redaction: provider has already redacted its admitted output."""
    private, secret = _stream.private_backing_fixture(
        tmp_path / "new-excluded-provider"
    )
    root = client.app.state.studio.runs.directory(recorded["runId"])
    protected_in_run = root / "provider-private-stderr.log"
    protected_in_run.write_bytes(private.read_bytes())
    public = (root / "evidence.jsonl").read_bytes()
    private_before = hashlib.sha256(private.read_bytes()).hexdigest()
    original_open, original_builtin, original_os = io.open, builtins.open, os.open
    private_reads = []

    def refuse_private(file):
        if isinstance(file, (str, Path)) and (
            Path(file).absolute() in {private.absolute(), protected_in_run.absolute()}
            or Path(file).name in {private.name, protected_in_run.name}
        ):
            private_reads.append(str(file))
            raise AssertionError("An excluded private backing stream was opened")

    def guarded_open(file, *args, **kwargs):
        refuse_private(file)
        return original_open(file, *args, **kwargs)

    def guarded_builtin(file, *args, **kwargs):
        refuse_private(file)
        return original_builtin(file, *args, **kwargs)

    def guarded_os(file, *args, **kwargs):
        refuse_private(file)
        return original_os(file, *args, **kwargs)

    monkeypatch.setattr(io, "open", guarded_open)
    monkeypatch.setattr(builtins, "open", guarded_builtin)
    monkeypatch.setattr(os, "open", guarded_os)
    # Keep the actual dir_fd capability under the observation wrapper.
    if original_os in os.supports_dir_fd:
        monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {guarded_os})
    rid = recorded["runId"]
    exposed = []
    for endpoint in ("history", "observations", "evidence", "events?streamVersion=1.1"):
        response = client.get(f"/api/v1/runs/{rid}/{endpoint}")
        assert response.status_code == 200, response.text
        exposed.append(response.content)
    exported = client.post(
        f"/api/v1/runs/{rid}/exports",
        headers={"Idempotency-Key": "public-stream-only"},
        json={},
    )
    assert exported.status_code == 202, exported.text
    bundle = client.get(exported.json()["result"]["downloadUrl"])
    assert bundle.status_code == 200
    with zipfile.ZipFile(io.BytesIO(bundle.content)) as archive:
        assert not any("private" in name for name in archive.namelist())
        exposed.extend(archive.read(name) for name in archive.namelist())
    assert private_reads == []
    assert all(secret.encode() not in body for body in exposed)
    assert (root / "evidence.jsonl").read_bytes() == public
    monkeypatch.undo()
    assert hashlib.sha256(private.read_bytes()).hexdigest() == private_before
    assert protected_in_run.read_bytes() == secret.encode()


def test_advancing_producer_slow_consumer_gets_bounded_explicit_gap(tmp_path):
    from xverse_studio.events import EventStreams

    source = _stream.AdvancingJournal(tmp_path / "new-advancing-journal")
    source.append()
    assert read_journal(source.root, source.read(source.run_id)) == (
        source.records,
        "verified_prefix",
    )
    streams = EventStreams(
        Store(tmp_path / "new-stream-store"),
        source,
        replay_window=1000,
        pending_events=3,
        pending_bytes=8192,
        max_frame_bytes=2048,
        poll_interval=0,
    )
    prepared = streams.prepare(source.run_id, version="1.1")
    lease = streams.reserve(source.run_id)

    async def consume():
        iterator = streams.iterate(source.run_id, prepared, lease)
        first = await anext(iterator)
        # The client holds the first yielded frame while producer advances.
        source.append(20)
        source.state = "stopped"
        rest = []
        async for frame in iterator:
            rest.append(frame)
        return [first, *rest]

    raw_frames = run_async(consume())
    delivered = [frame for raw in raw_frames for frame in frames(raw)]
    controls = [f for f in delivered if f.get("event") == "studio.stream_control"]
    gap = next(f for f in controls if f["data"]["type"] == "stream.gap")
    assert "id" not in gap
    assert gap["data"]["firstMissingSequence"] == "2"
    assert gap["data"]["lastMissingSequence"] == "18"
    assert gap["data"]["missingCount"] == 17
    records = [
        f["data"] for f in delivered if f.get("event") != "studio.stream_control"
    ]
    assert [row["sequence"] for row in records] == ["1", "19", "20", "21"]
    assert all(
        len(raw.encode() if isinstance(raw, str) else raw) <= 8192 for raw in raw_frames
    )
    retained, integrity = read_journal(source.root, source.read(source.run_id))
    assert integrity == "valid" and retained == source.records
    assert len(retained) == 21  # delivery loss never deletes canonical evidence
    streams.release(lease)


def test_oversized_delivery_frame_is_skipped_with_gap_not_canonical_truncation(
    tmp_path,
):
    from xverse_studio.events import EventStreams

    source = _stream.AdvancingJournal(tmp_path / "new-large-frame-journal")
    source.append(message="Public large record " + "☀" * 5000)
    source.append(message="Next bounded public log")
    source.state = "stopped"
    original = source.path.read_bytes()
    streams = EventStreams(
        Store(tmp_path / "new-large-frame-store"),
        source,
        pending_events=3,
        pending_bytes=8192,
        max_frame_bytes=2048,
        poll_interval=0,
    )
    prepared = streams.prepare(source.run_id, version="1.1")
    lease = streams.reserve(source.run_id)

    async def consume():
        return [
            frame async for frame in streams.iterate(source.run_id, prepared, lease)
        ]

    raw = run_async(consume())
    delivered = [frame for chunk in raw for frame in frames(chunk)]
    gaps = [
        frame
        for frame in delivered
        if frame.get("event") == "studio.stream_control"
        and frame["data"]["type"] == "stream.gap"
    ]
    assert len(gaps) == 1 and "id" not in gaps[0]
    assert gaps[0]["data"]["firstMissingSequence"] == "1"
    assert gaps[0]["data"]["lastMissingSequence"] == "1"
    assert gaps[0]["data"]["missingCount"] == 1
    originals = [
        frame for frame in delivered if frame.get("event") != "studio.stream_control"
    ]
    assert [frame["data"] for frame in originals] == [source.records[1]]
    assert all(
        len(chunk.encode() if isinstance(chunk, str) else chunk) <= 8192
        for chunk in raw
    )
    assert source.path.read_bytes() == original
    assert read_journal(source.root, source.read(source.run_id)) == (
        source.records,
        "valid",
    )
    streams.release(lease)


def test_subscription_admission_is_bounded_before_any_iteration(tmp_path):
    from xverse_studio.events import EventStreams
    from xverse_studio.storage.core import Problem

    source = _stream.AdvancingJournal(tmp_path / "new-subscriber-journal")
    source.append()
    sources = {source.run_id: source}
    for name in ("second-isolated-run", "third-isolated-run"):
        journal = _stream.AdvancingJournal(tmp_path / name, run_id=name)
        journal.append()
        sources[name] = journal

    class JournalCollection:
        def read(self, run_id):
            return sources[run_id].read(run_id)

        def directory(self, run_id):
            return sources[run_id].directory(run_id)

    streams = EventStreams(
        Store(tmp_path / "new-subscriber-store"),
        JournalCollection(),
        global_subscribers=2,
        per_run_subscribers=1,
    )
    first = streams.reserve(source.run_id)
    with pytest.raises(Problem) as per_run:
        streams.reserve(source.run_id)
    assert per_run.value.status == 429
    second = streams.reserve("second-isolated-run")
    with pytest.raises(Problem) as global_limit:
        streams.reserve("third-isolated-run")
    assert global_limit.value.status == 429
    streams.release(first)
    replacement = streams.reserve(source.run_id)
    streams.release(replacement)
    streams.release(second)


@pytest.mark.parametrize(
    "failure,integrity", [("missing", "unavailable"), ("invalid", "invalid")]
)
def test_source_read_failure_after_headers_has_explicit_control(
    tmp_path, failure, integrity
):
    from xverse_studio.events import EventStreams

    source = _stream.AdvancingJournal(tmp_path / "new-after-headers-journal")
    source.append()
    streams = EventStreams(
        Store(tmp_path / "new-after-headers-store"), source, poll_interval=0
    )
    prepared = streams.prepare(source.run_id, version="1.1")
    lease = streams.reserve(source.run_id)

    async def consume():
        iterator = streams.iterate(source.run_id, prepared, lease)
        first = await anext(iterator)
        if failure == "missing":
            source.path.rename(source.path.with_suffix(".fixture-missing"))
        else:
            with source.path.open("ab") as output:
                output.write(b"bad-disposable-fixture-tail\n")
        rest = [frame async for frame in iterator]
        return [first, *rest]

    delivered = [frame for chunk in run_async(consume()) for frame in frames(chunk)]
    originals = [
        f["data"] for f in delivered if f.get("event") != "studio.stream_control"
    ]
    assert originals == source.records
    controls = [f for f in delivered if f.get("event") == "studio.stream_control"]
    assert controls and controls[-1]["data"]["type"] in {
        "stream.error",
        "stream.resync_required",
    }
    assert controls[-1]["data"]["integrity"] == integrity
    assert "id" not in controls[-1]
    assert not any(f["data"]["type"] == "stream.end" for f in controls)
    streams.release(lease)


def test_new_unknown_transport_fixture_has_no_runtime_authority_or_terminal_claim(
    client,
):
    fixture = load_fixture("create_stream_recovery_fixture.py")
    project = client.post(
        "/api/v1/projects", json={"name": "New unknown transport fixture"}
    ).json()
    studio = client.app.state.studio
    created = fixture.create_stream_recovery_fixture(
        studio.store, studio.projects, studio.runs, project["projectId"]
    )
    run = studio.runs.read(created["runId"])
    assert run["state"] == "unknown" and run["capabilities"] == []
    assert run["evidenceScope"] == "recorded_fixture"
    assert not run.get("pid") and not run.get("owner")
    path = studio.runs.directory(created["runId"]) / "evidence.jsonl"
    original = path.read_bytes()
    manager = studio.events
    prepared = manager.prepare(created["runId"], version="1.1")
    lease = manager.reserve(created["runId"])

    class DisconnectAfterBatch:
        calls = 0

        async def is_disconnected(self):
            self.calls += 1
            return self.calls > 1

    async def consume():
        return [
            frame
            async for frame in manager.iterate(
                created["runId"], prepared, lease, request=DisconnectAfterBatch()
            )
        ]

    delivered = [frame for chunk in run_async(consume()) for frame in frames(chunk)]
    controls = [
        f["data"] for f in delivered if f.get("event") == "studio.stream_control"
    ]
    assert any(f["type"] == "stream.gap" for f in controls)
    assert not any(f["type"] == "stream.end" for f in controls)
    assert path.read_bytes() == original
    manager.release(lease)


def test_application_restart_resumes_verified_source_without_new_run(tmp_path):
    from fastapi.testclient import TestClient
    from xverse_studio.api.app import create_app

    def authenticate(client):
        client.headers["Origin"] = "http://testserver"
        response = client.post(
            "/api/v1/session", json={"bootstrapToken": "fixture-bootstrap"}
        )
        assert response.status_code == 200, response.text
        client.headers["X-CSRF-Token"] = response.json()["csrfToken"]

    def application():
        return create_app(
            tmp_path / "new-restarted-application",
            allowed_hosts=["testserver"],
            bootstrap_token="fixture-bootstrap",
        )

    with TestClient(application(), base_url="http://testserver") as first:
        authenticate(first)
        project = first.post(
            "/api/v1/projects", json={"name": "Restart fixture"}
        ).json()
        studio = first.app.state.studio
        created = _recorded.create_recorded_evidence(
            studio.store, studio.projects, studio.runs, project["projectId"], noise=0
        )
        rid = created["runId"]
        path = studio.runs.directory(rid) / "evidence.jsonl"
        original = path.read_bytes()
        response = first.get(
            f"/api/v1/runs/{rid}/events", params={"streamVersion": "1.1"}
        )
        assert response.status_code == 200, response.text
        original_events = [
            frame
            for frame in frames(response.text)
            if frame.get("event") != "studio.stream_control"
        ]
        acknowledged = original_events[3]["id"]
        expected = [frame["data"] for frame in original_events[4:]]

    # Actual application lifespan shutdown/recreate; no original process handles exist.
    with TestClient(application(), base_url="http://testserver") as second:
        authenticate(second)
        response = second.get(
            f"/api/v1/runs/{rid}/events",
            params={"streamVersion": "1.1", "after": acknowledged},
        )
        assert response.status_code == 200, response.text
        resumed = [
            frame["data"]
            for frame in frames(response.text)
            if frame.get("event") != "studio.stream_control"
        ]
        assert resumed == expected
        assert [run["runId"] for run in second.get("/api/v1/runs").json()["items"]] == [
            rid
        ]
        assert path.read_bytes() == original


@pytest.mark.parametrize("failure", ["oserror", "cancelled"])
def test_api_header_send_failure_releases_lease_before_iterator_entry(
    client, recorded, failure
):
    from starlette.requests import Request
    from starlette.requests import ClientDisconnect

    studio = client.app.state.studio
    rid = recorded["runId"]
    path = studio.runs.directory(rid) / "evidence.jsonl"
    original = path.read_bytes()
    endpoint = next(
        route.endpoint
        for route in client.app.routes
        if getattr(route, "path", "") == "/api/v1/runs/{runId}/events"
    )
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.4"},
        "method": "GET",
        "scheme": "http",
        "path": f"/api/v1/runs/{rid}/events",
        "raw_path": f"/api/v1/runs/{rid}/events".encode(),
        "root_path": "",
        "query_string": b"streamVersion=1.1",
        "headers": [],
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 1),
    }
    calls = []

    async def invoke():
        response = await endpoint(rid, Request(scope), streamVersion="1.1")
        assert len(studio.events.leases) == 1

        async def send(message):
            calls.append(message["type"])
            assert message["type"] == "http.response.start"
            if failure == "oserror":
                raise OSError("Disposable disconnected response transport")
            raise asyncio.CancelledError()

        async def receive():
            return {"type": "http.disconnect"}

        with pytest.raises((ClientDisconnect, OSError, asyncio.CancelledError)):
            await response(scope, receive, send)
        assert len(studio.events.leases) == 0
        # Closing a never-entered generator is not the admission cleanup mechanism.
        await response.body_iterator.aclose()
        assert len(studio.events.leases) == 0

    run_async(invoke())
    assert calls == ["http.response.start"]
    assert path.read_bytes() == original


@pytest.mark.parametrize(
    "kind",
    [
        'log.appended\ndata: {"injected":true}',
        "log.appended\rdata: malformed",
        "future.unregistered_event",
        "studio.stream_control",
    ],
)
def test_hash_valid_unsupported_event_kind_rejects_transport_without_rewriting_evidence(
    client, recorded, kind
):
    studio = client.app.state.studio
    rid = recorded["runId"]
    path = studio.runs.directory(rid) / "evidence.jsonl"
    rows = [json.loads(line) for line in path.read_bytes().splitlines()]
    rows[0]["type"] = kind
    previous, encoded = "0" * 64, []
    for row in rows:
        row.pop("digest")
        row["previousDigest"] = previous
        previous = hashlib.sha256(canonical(row).encode()).hexdigest()
        row["digest"] = previous
        encoded.append((canonical(row) + "\n").encode())
    # Allocate this deliberately malformed source solely within its new fixture.
    original = b"".join(encoded)
    path.write_bytes(original)
    with studio.store.tx() as db:
        run = studio.store.get("run", rid, db)
        run["journalDigest"] = digest(original)
        studio.store.put("run", rid, run, db)
    assert read_journal(path.parent, studio.runs.read(rid)) == (rows, "valid")
    response = client.get(f"/api/v1/runs/{rid}/events", params={"streamVersion": "1.1"})
    assert response.status_code == 422, response.text
    assert response.json()["code"] == "STREAM_ENVELOPE_UNSUPPORTED"
    assert response.json()["integrity"] == "valid"
    history = client.get(f"/api/v1/runs/{rid}/history")
    assert history.status_code == 200 and history.json()["integrity"] == "valid"
    assert history.json()["items"][0]["type"] == kind
    assert path.read_bytes() == original


def test_legacy_byte_budget_delivers_every_consecutive_record_without_silent_drop(
    tmp_path,
):
    from xverse_studio.events import EventStreams

    source = _stream.AdvancingJournal(tmp_path / "new-legacy-byte-journal")
    source.append(5, message="x" * 800)
    source.state = "stopped"
    original = source.path.read_bytes()
    manager = EventStreams(
        Store(tmp_path / "new-legacy-byte-store"),
        source,
        pending_events=10,
        pending_bytes=8192,
        max_frame_bytes=2048,
        poll_interval=0,
    )
    prepared = manager.prepare(source.run_id, version="1.0")
    lease = manager.reserve(source.run_id)

    async def consume():
        return [
            frame async for frame in manager.iterate(source.run_id, prepared, lease)
        ]

    chunks = run_async(consume())
    delivered = [frame for chunk in chunks for frame in frames(chunk)]
    assert all(frame.get("event") != "studio.stream_control" for frame in delivered)
    assert [frame["data"] for frame in delivered] == source.records
    assert [frame["id"] for frame in delivered] == [
        f"{source.run_id}:{i}" for i in range(1, 6)
    ]
    assert all(
        len(chunk.encode() if isinstance(chunk, str) else chunk) <= 8192
        for chunk in chunks
    )
    assert read_journal(source.root, source.read(source.run_id)) == (
        source.records,
        "valid",
    )
    assert source.path.read_bytes() == original
    manager.release(lease)


def test_legacy_oversized_first_record_refuses_before_headers(client, recorded):
    studio = client.app.state.studio
    rid = recorded["runId"]
    path = studio.runs.directory(rid) / "evidence.jsonl"
    rows = [json.loads(line) for line in path.read_bytes().splitlines()]
    rows[0]["payload"]["largePublicFixture"] = "x" * (300 * 1024)
    previous, encoded = "0" * 64, []
    for row in rows:
        row.pop("digest")
        row["previousDigest"] = previous
        previous = hashlib.sha256(canonical(row).encode()).hexdigest()
        row["digest"] = previous
        encoded.append((canonical(row) + "\n").encode())
    original = b"".join(encoded)
    path.write_bytes(original)
    with studio.store.tx() as db:
        run = studio.store.get("run", rid, db)
        run["journalDigest"] = digest(original)
        studio.store.put("run", rid, run, db)
    assert read_journal(path.parent, studio.runs.read(rid)) == (rows, "valid")
    response = client.get(f"/api/v1/runs/{rid}/events", params={"streamVersion": "1.0"})
    assert response.status_code == 413, response.text
    assert response.json()["code"] == "STREAM_FRAME_TOO_LARGE"
    assert not studio.events.leases
    assert path.read_bytes() == original


def test_legacy_index_requires_explicit_resync_in_v11_but_remains_v10_compatible(
    tmp_path,
):
    from xverse_studio.events import EventStreams
    from xverse_studio.storage.core import Problem

    source = _stream.AdvancingJournal(tmp_path / "new-legacy-context-journal")
    source.append(8)
    source.state = "stopped"
    original = source.path.read_bytes()
    manager = EventStreams(
        Store(tmp_path / "new-legacy-context-store"),
        source,
        replay_window=3,
        poll_interval=0,
    )
    with pytest.raises(Problem) as rejected:
        manager.prepare(source.run_id, cursor="2", version="1.1")
    assert rejected.value.status == 410
    assert rejected.value.code == "STREAM_RESYNC_REQUIRED"
    assert rejected.value.details["reason"] == "LEGACY_CURSOR_WITHOUT_SOURCE_PROOF"
    prepared = manager.prepare(source.run_id, cursor="2", version="1.0")
    lease = manager.reserve(source.run_id)

    async def consume():
        return [
            frame async for frame in manager.iterate(source.run_id, prepared, lease)
        ]

    delivered = [frame for chunk in run_async(consume()) for frame in frames(chunk)]
    assert [frame["data"] for frame in delivered] == source.records[2:]
    assert source.path.read_bytes() == original
    manager.release(lease)


def summary_runs(source):
    """Synthetic summary shape only; no 32-definition project/run admission claim."""
    summary = {
        "requiredAssertions": 32,
        "attemptedDefinitions": 0,
        "counts": {"not_started": 32},
        "definitions": [
            {
                "definitionRef": "assertion-" + str(i) + "x" * 240,
                "definitionDigest": "sha256:" + "a" * 64,
                "evaluationId": None,
                "status": "not_started",
                "verdict": None,
                "coverage": None,
                "reasons": [],
            }
            for i in range(32)
        ],
        "metricDefinitions": 0,
        "metricJobs": [],
        "diagnostics": [],
    }

    class SyntheticSummaryRuns:
        def read(self, run_id):
            return {
                **source.read(run_id),
                "stateVersion": 1,
                "evaluation": "not_started",
                "verdict": None,
                "evaluationSummary": summary,
            }

        def directory(self, run_id):
            return source.directory(run_id)

    return SyntheticSummaryRuns()


@pytest.mark.parametrize("budget", [16 * 1024, 1024 * 1024])
def test_whole_resync_response_including_run_metadata_obeys_utf8_budget(
    tmp_path, budget
):
    from xverse_studio.events import EventStreams

    source = _stream.AdvancingJournal(tmp_path / "new-whole-recovery-journal")
    source.append(200, message="x" * 5000)
    source.state = "stopped"
    original = source.path.read_bytes()
    manager = EventStreams(
        Store(tmp_path / "new-whole-recovery-store"),
        summary_runs(source),
        pending_bytes=budget,
    )
    response = manager.resync(source.run_id)
    assert len(canonical(response).encode("utf-8")) <= budget
    assert response["history"]["integrity"] == "valid"
    assert response["watermark"] == {
        "sequence": "200",
        "digest": source.records[-1]["digest"],
    }
    assert len(response["history"]["items"]) <= 200
    assert response["history"]["omittedRecords"] == 200 - len(
        response["history"]["items"]
    )
    assert response["run"]["evaluationSummary"]["requiredAssertions"] == 32
    assert len(response["run"]["evaluationSummary"]["definitions"]) == 32
    assert source.path.read_bytes() == original
    assert read_journal(source.root, source.read(source.run_id)) == (
        source.records,
        "valid",
    )


def test_resync_metadata_alone_over_budget_refuses_with_typed413(tmp_path):
    from xverse_studio.events import EventStreams
    from xverse_studio.storage.core import Problem

    source = _stream.AdvancingJournal(tmp_path / "new-metadata-recovery-journal")
    source.append()
    source.state = "stopped"
    original = source.path.read_bytes()
    manager = EventStreams(
        Store(tmp_path / "new-metadata-recovery-store"),
        summary_runs(source),
        pending_bytes=8192,
    )
    with pytest.raises(Problem) as error:
        manager.resync(source.run_id)
    assert error.value.status == 413
    assert error.value.code == "STREAM_RECOVERY_TOO_LARGE"
    assert source.path.read_bytes() == original
    assert read_journal(source.root, source.read(source.run_id)) == (
        source.records,
        "valid",
    )

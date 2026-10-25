"""Read-only bounded presentation transport, independent of execution ownership."""

import asyncio
import base64
from collections import deque
import json
import re
import threading
from urllib.parse import quote

from xverse_studio.evidence.reader import read_journal
from xverse_studio.storage.core import Problem, canonical, uid

REPLAY_WINDOW = 1000
PENDING_EVENTS = 200
PENDING_BYTES = 1024 * 1024
MAX_FRAME_BYTES = 256 * 1024
GLOBAL_SUBSCRIBERS = 16
PER_RUN_SUBSCRIBERS = 4
POLL_INTERVAL = 0.2
CONTROL_RESERVE = 4096
ZERO_DIGEST = "0" * 64
SEQUENCE = re.compile(r"(?:0|[1-9][0-9]*)\Z", re.ASCII)
HEX = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
EVENT_KINDS = frozenset(
    {
        "command.accepted",
        "command.delegated",
        "command.completed",
        "command.rejected",
        "command.failed",
        "command.unknown",
        "run.state_changed",
        "run.reconciling",
        "run.ownership_unknown",
        "element.state_changed",
        "readiness.observed",
        "connection.observed",
        "log.appended",
        "observation.available",
        "observation.gap",
        "fault.activation_requested",
        "fault.activation_observed",
        "fault.recovery_observed",
        "cleanup.updated",
        "evidence.updated",
        "evaluation.updated",
        "stream.gap",
        "stream.resync_required",
        "capabilities.changed",
    }
)


def encode_cursor(run_id, snapshot_id, sequence, digest):
    data = {"r": run_id, "s": snapshot_id, "q": str(sequence), "d": digest}
    return "st1." + base64.urlsafe_b64encode(canonical(data).encode()).decode().rstrip(
        "="
    )


def _closed_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate cursor field")
        result[key] = value
    return result


def decode_cursor(value, run_id, snapshot_id):
    if (
        not isinstance(value, str)
        or not 0 < len(value) <= 2048
        or not value.startswith("st1.")
    ):
        raise Problem("CURSOR_INVALID", "The event cursor encoding is invalid.")
    try:
        raw = value[4:]
        body = json.loads(
            base64.b64decode(
                raw + "=" * (-len(raw) % 4), altchars=b"-_", validate=True
            ),
            object_pairs_hook=_closed_pairs,
        )
        if not isinstance(body, dict) or set(body) != {"r", "s", "q", "d"}:
            raise ValueError()
        if body["r"] != run_id or body["s"] != snapshot_id:
            raise ValueError()
        if (
            not isinstance(body["q"], str)
            or len(body["q"]) > 32
            or not SEQUENCE.fullmatch(body["q"])
        ):
            raise ValueError()
        if not isinstance(body["d"], str) or not HEX.fullmatch(body["d"]):
            raise ValueError()
        sequence = int(body["q"])
        if sequence > 100000 or sequence == 0 and body["d"] != ZERO_DIGEST:
            raise ValueError()
        if value != encode_cursor(run_id, snapshot_id, sequence, body["d"]):
            raise ValueError()
        return sequence, body["d"]
    except (ValueError, TypeError, KeyError, UnicodeError):
        raise Problem(
            "CURSOR_INVALID",
            "The event cursor is malformed or belongs to another run/snapshot.",
        ) from None


class _LargeFrame(ValueError):
    pass


def _bounded_json(value, limit, *, max_nodes=10000):
    # Refuse a very large primitive before JSON escaping can allocate its full
    # serialized representation. All source objects already have reader bounds.
    stack, nodes = [value], 0
    while stack:
        item = stack.pop()
        nodes += 1
        if nodes > max_nodes:
            raise _LargeFrame()
        if isinstance(item, str) and len(item) > limit:
            raise _LargeFrame()
        if isinstance(item, dict):
            stack.extend(item.keys())
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    pieces, size = [], 0
    encoder = json.JSONEncoder(
        sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    for piece in encoder.iterencode(value):
        size += len(piece.encode("utf-8"))
        if size > limit:
            raise _LargeFrame()
        pieces.append(piece)
    return "".join(pieces)


class EventStreams:
    def __init__(
        self,
        store,
        runs,
        *,
        replay_window=REPLAY_WINDOW,
        pending_events=PENDING_EVENTS,
        pending_bytes=PENDING_BYTES,
        max_frame_bytes=MAX_FRAME_BYTES,
        global_subscribers=GLOBAL_SUBSCRIBERS,
        per_run_subscribers=PER_RUN_SUBSCRIBERS,
        poll_interval=POLL_INTERVAL,
    ):
        self.store, self.runs = store, runs
        for name, value in {
            "replay_window": replay_window,
            "pending_events": pending_events,
            "pending_bytes": pending_bytes,
            "max_frame_bytes": max_frame_bytes,
            "global_subscribers": global_subscribers,
            "per_run_subscribers": per_run_subscribers,
        }.items():
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
            setattr(self, name, value)
        if (
            pending_bytes < CONTROL_RESERVE
            or pending_events > 100000
            or replay_window > 100000
        ):
            raise ValueError(
                "Presentation limits exceed the supported control/source bounds"
            )
        if not isinstance(poll_interval, (int, float)) or not 0 <= poll_interval <= 10:
            raise ValueError("poll_interval must be within 0–10 seconds")
        self.poll_interval = poll_interval
        self.lock = threading.RLock()
        self.leases = {}
        self.closed = False

    def reserve(self, run_id):
        with self.lock:
            if self.closed:
                raise Problem(
                    "STREAM_SOURCE_UNAVAILABLE",
                    "The presentation service is stopping.",
                    503,
                    retryable=True,
                )
            if (
                len(self.leases) >= self.global_subscribers
                or sum(r == run_id for r in self.leases.values())
                >= self.per_run_subscribers
            ):
                raise Problem(
                    "STREAM_SUBSCRIBER_LIMIT",
                    "The bounded presentation subscription budget is occupied.",
                    429,
                    retryable=True,
                    retryAfterMs=500,
                )
            lease = uid("sub-")
            self.leases[lease] = run_id
            return lease

    def release(self, lease):
        with self.lock:
            self.leases.pop(lease, None)

    def close(self):
        with self.lock:
            self.closed = True
            self.leases.clear()

    def _urls(self, run_id, total=0):
        root = "/api/v1/runs/" + quote(run_id, safe="")
        start = max(0, total - PENDING_EVENTS)
        return {
            "stateUrl": root,
            "historyUrl": root + f"/history?cursor={start}&limit=200",
            "resyncUrl": root + "/resync",
            "evidenceUrl": root + "/evidence",
        }

    def _read(self, run_id):
        run = self.runs.read(run_id)
        snapshot_id = run.get("snapshotId")
        if (
            not isinstance(snapshot_id, str)
            or not 0 < len(snapshot_id) <= 128
            or len(run_id) > 128
        ):
            raise Problem(
                "STREAM_CONTEXT_UNSUPPORTED",
                "This stream context exceeds its declared bounds.",
            )
        records, integrity = read_journal(self.runs.directory(run_id), run)
        details = {
            **self._urls(run_id, len(records)),
            "runId": run_id,
            "snapshotId": snapshot_id,
            "streamVersion": "1.1",
            "integrity": integrity,
        }
        if integrity == "unavailable":
            raise Problem(
                "STREAM_SOURCE_UNAVAILABLE",
                "The source cannot currently be acquired; the acknowledged position has not changed.",
                503,
                retryable=True,
                retryAfterMs=500,
                **details,
            )
        if integrity == "invalid":
            raise Problem(
                "EVIDENCE_INVALID",
                "The original evidence cannot establish a continuous event stream.",
                422,
                **details,
            )
        if any(record["type"] not in EVENT_KINDS for record in records):
            raise Problem(
                "STREAM_ENVELOPE_UNSUPPORTED",
                "An original event kind is outside the admitted v1 transport registry; inspect retained evidence without reinterpreting it.",
                422,
                **details,
            )
        return run, records, integrity

    @staticmethod
    def _proof(records, sequence):
        return ZERO_DIGEST if sequence == 0 else records[sequence - 1]["digest"]

    def _recovery(
        self,
        run_id,
        run,
        records,
        integrity,
        *,
        sequence=None,
        reason="PRESENTATION_WINDOW_EXPIRED",
    ):
        last = len(records)
        boundary = max(0, last - self.replay_window)
        sid = run["snapshotId"]
        missing_known = (
            sequence is not None
            and sequence <= boundary
            and reason == "PRESENTATION_WINDOW_EXPIRED"
        )
        return {
            "streamVersion": "1.1",
            "runId": run_id,
            "snapshotId": sid,
            "reason": reason,
            "integrity": integrity,
            **self._urls(run_id, last),
            "earliestCursor": encode_cursor(
                run_id, sid, boundary, self._proof(records, boundary)
            ),
            "resumeAfterCursor": encode_cursor(
                run_id, sid, boundary, self._proof(records, boundary)
            ),
            "earliestAvailableCursor": encode_cursor(
                run_id, sid, boundary + 1, self._proof(records, boundary + 1)
            )
            if boundary < last
            else None,
            "firstMissingSequence": str(sequence + 1)
            if missing_known and sequence < boundary
            else None,
            "lastMissingSequence": str(boundary)
            if missing_known and sequence < boundary
            else None,
            "missingCount": boundary - sequence if missing_known else None,
        }

    def prepare(self, run_id, cursor=None, version="1.1"):
        if version not in {"1.0", "1.1"}:
            raise Problem(
                "STREAM_VERSION_UNSUPPORTED",
                "Select an advertised event stream version.",
                426,
            )
        run, records, integrity = self._read(run_id)
        sid = run["snapshotId"]
        sequence, proof = 0, ZERO_DIGEST
        if cursor:
            if cursor.startswith("st1."):
                sequence, proof = decode_cursor(cursor, run_id, sid)
                if sequence > len(records) or self._proof(records, sequence) != proof:
                    raise Problem(
                        "STREAM_RESYNC_REQUIRED",
                        "The prior source watermark cannot be verified; obtain a current state/history view.",
                        410,
                        **self._recovery(
                            run_id,
                            run,
                            records,
                            integrity,
                            reason="SOURCE_DISCONTINUITY",
                        ),
                    )
            else:
                # Compatibility only: legacy positions are indices, not proof of
                # an unchanged source generation across a backend restart.
                raw = (
                    cursor[len(run_id) + 1 :]
                    if cursor.startswith(run_id + ":")
                    else cursor
                )
                if (
                    not isinstance(raw, str)
                    or len(raw) > 32
                    or not SEQUENCE.fullmatch(raw)
                ):
                    raise Problem(
                        "CURSOR_INVALID",
                        "The legacy event cursor is malformed or belongs to another run.",
                    )
                sequence = int(raw)
                if sequence > len(records):
                    raise Problem(
                        "CURSOR_INVALID",
                        "The cursor is ahead of the available source.",
                        409,
                    )
                if version == "1.1":
                    raise Problem(
                        "STREAM_RESYNC_REQUIRED",
                        "A legacy index cannot establish historical source continuity; recover state/history before using a proof-bound cursor.",
                        410,
                        **self._recovery(
                            run_id,
                            run,
                            records,
                            integrity,
                            reason="LEGACY_CURSOR_WITHOUT_SOURCE_PROOF",
                        ),
                    )
                proof = self._proof(records, sequence)
            if version == "1.1" and sequence < max(
                0, len(records) - self.replay_window
            ):
                raise Problem(
                    "CURSOR_EXPIRED",
                    "The presentation replay window no longer covers this acknowledged position.",
                    410,
                    **self._recovery(
                        run_id, run, records, integrity, sequence=sequence
                    ),
                )
        if version == "1.0" and sequence < len(records):
            # Legacy clients have no negotiated gap control. Refuse an
            # undeliverable next record before committing SSE response headers.
            try:
                self._data_frame(run_id, sid, records[sequence], version)
            except _LargeFrame:
                raise self._legacy_frame_error(run_id, len(records)) from None
        return {
            "runId": run_id,
            "snapshotId": sid,
            "sequence": sequence,
            "digest": proof,
            "version": version,
        }

    def resync(self, run_id):
        run, records, integrity = self._read(run_id)
        sid, last = run["snapshotId"], len(records)
        public_run = {
            key: value
            for key, value in run.items()
            if key not in {"pid", "createTime", "ownerDigest"}
        }
        response = {
            "streamVersion": "1.1",
            "runId": run_id,
            "snapshotId": sid,
            "run": public_run,
            "history": {
                "items": [],
                "nextCursor": None,
                "integrity": integrity,
                "omittedRecords": last,
                "oversizedOrBudgetOmissions": 0,
            },
            "resumeCursor": encode_cursor(
                run_id, sid, last, self._proof(records, last)
            ),
            "watermark": {"sequence": str(last), "digest": self._proof(records, last)},
            **self._urls(run_id, last),
        }
        try:
            base_size = len(_bounded_json(response, self.pending_bytes).encode("utf-8"))
        except _LargeFrame:
            raise self._recovery_size_error(run_id, last) from None
        # Charge the whole envelope and current run metadata, not only history.
        # The reserve also covers separators and changing omission-count digits.
        history_budget = max(0, self.pending_bytes - base_size - CONTROL_RESERVE)
        tail, size = deque(), 0
        skipped = 0
        for item in reversed(records[-PENDING_EVENTS:]):
            try:
                encoded = _bounded_json(
                    item,
                    min(self.max_frame_bytes, history_budget),
                )
            except _LargeFrame:
                skipped += 1
                continue
            amount = len(encoded.encode("utf-8"))
            if size + amount > history_budget:
                skipped += 1
                continue
            tail.appendleft(item)
            size += amount
        response["history"].update(
            items=list(tail),
            omittedRecords=last - len(tail),
            oversizedOrBudgetOmissions=skipped,
        )
        try:
            # Each item and metadata was already bounded independently. Permit
            # their combined node count while enforcing the actual JSON bytes.
            _bounded_json(
                response,
                self.pending_bytes,
                max_nodes=10000 * (len(tail) + 1),
            )
        except _LargeFrame:
            raise self._recovery_size_error(run_id, last) from None
        return response

    def _recovery_size_error(self, run_id, total):
        return Problem(
            "STREAM_RECOVERY_TOO_LARGE",
            "Recovery metadata exceeds the presentation budget; inspect current state and paged retained history.",
            413,
            **self._urls(run_id, total),
        )

    def _control(self, run_id, snapshot_id, kind, **details):
        body = {
            "streamVersion": "1.1",
            "type": kind,
            "runId": run_id,
            "snapshotId": snapshot_id,
            "firstMissingSequence": None,
            "lastMissingSequence": None,
            "missingCount": None,
            **self._urls(run_id),
            **details,
        }
        encoded = _bounded_json(body, CONTROL_RESERVE - 64)
        return "event: studio.stream_control\ndata: " + encoded + "\n\n"

    def _legacy_frame_error(self, run_id, total):
        return Problem(
            "STREAM_FRAME_TOO_LARGE",
            "Use the versioned stream recovery view for this retained record.",
            413,
            **self._urls(run_id, total),
        )

    def _data_frame(self, run_id, snapshot_id, item, version):
        seq = int(item["sequence"])
        cursor = (
            encode_cursor(run_id, snapshot_id, seq, item["digest"])
            if version == "1.1"
            else f"{run_id}:{seq}"
        )
        payload = _bounded_json(
            item, self.max_frame_bytes - len(cursor.encode()) - 128
        )
        frame = f"id: {cursor}\nevent: {item['type']}\ndata: {payload}\n\n"
        amount = len(frame.encode("utf-8"))
        if (
            amount > self.max_frame_bytes
            or amount > self.pending_bytes - CONTROL_RESERVE
        ):
            raise _LargeFrame()
        return frame, amount

    def _batch(self, run_id, state):
        run, records, integrity = self._read(run_id)
        sequence, proof = state["sequence"], state["digest"]
        sid, last = run["snapshotId"], len(records)
        if (
            sid != state["snapshotId"]
            or sequence > last
            or self._proof(records, sequence) != proof
        ):
            info = self._recovery(
                run_id, run, records, integrity, reason="SOURCE_DISCONTINUITY"
            )
            return (
                [
                    (
                        self._control(
                            run_id,
                            sid,
                            "stream.resync_required",
                            **{
                                k: v
                                for k, v in info.items()
                                if k not in {"runId", "snapshotId", "streamVersion"}
                            },
                        ),
                        sequence,
                        proof,
                    )
                ],
                False,
                True,
            )
        if sequence == last and run["state"] in {"stopped", "failed"}:
            frame = self._control(
                run_id, sid, "stream.end", reason="TERMINAL_SOURCE", integrity=integrity
            )
            return (
                [(frame, sequence, proof)] if state["version"] == "1.1" else [],
                True,
                False,
            )
        floor = (
            max(sequence, last - self.pending_events)
            if state["version"] == "1.1"
            else sequence
        )
        reason = "SLOW_CONSUMER"
        frames, size = deque(), 0
        stop = min(last, floor + self.pending_events)
        for item in records[floor:stop]:
            seq = int(item["sequence"])
            try:
                frame, amount = self._data_frame(
                    run_id, sid, item, state["version"]
                )
            except _LargeFrame:
                if state["version"] == "1.0":
                    if frames:
                        break
                    raise self._legacy_frame_error(run_id, last) from None
                frames.clear()
                size, floor = 0, seq
                reason = "FRAME_LIMIT"
                continue
            if (
                state["version"] == "1.0"
                and size + amount > self.pending_bytes - CONTROL_RESERVE
            ):
                # Keep a consecutive prefix; the next batch resumes after it.
                break
            frames.append((frame, seq, item["digest"]))
            size += amount
            while size > self.pending_bytes - CONTROL_RESERVE:
                removed = frames.popleft()
                size -= len(removed[0].encode("utf-8"))
                floor = removed[1]
                reason = "PENDING_BYTE_LIMIT"
        result = list(frames)
        if floor > sequence and state["version"] == "1.1":
            digest = self._proof(records, floor)
            control = self._control(
                run_id,
                sid,
                "stream.gap",
                reason=reason,
                integrity=integrity,
                firstMissingSequence=str(sequence + 1),
                lastMissingSequence=str(floor),
                missingCount=floor - sequence,
                resumeAfterCursor=encode_cursor(run_id, sid, floor, digest),
                **self._urls(run_id, last),
            )
            result.insert(0, (control, floor, digest))
        return result, False, False

    async def iterate(self, run_id, prepared, lease, request=None):
        state = dict(prepared)
        try:
            while not self.closed:
                with self.lock:
                    if self.leases.get(lease) != run_id:
                        return
                if request is not None and await request.is_disconnected():
                    return
                try:
                    frames, ended, resync = await asyncio.to_thread(
                        self._batch, run_id, state
                    )
                except Problem as exc:
                    if state["version"] == "1.1":
                        info = {
                            k: v
                            for k, v in exc.details.items()
                            if k not in {"runId", "snapshotId", "streamVersion"}
                        }
                        yield self._control(
                            run_id,
                            state["snapshotId"],
                            "stream.error",
                            reason=exc.code,
                            message=exc.message,
                            **info,
                        )
                    return
                for frame, sequence, proof in frames:
                    yield frame
                    state.update(sequence=sequence, digest=proof)
                if ended or resync:
                    return
                if not frames:
                    yield ": heartbeat\n\n"
                await asyncio.sleep(self.poll_interval)
        finally:
            self.release(lease)

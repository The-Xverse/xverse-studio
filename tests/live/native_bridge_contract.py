"""Opt-in actual native artifact contract tests, without full Autoverse claims.

Invoke this file explicitly with XVERSE_STUDIO_NATIVE_BRIDGE set to the admitted
host-built binary. Missing artifacts fail; no mock or skip substitutes for native.
"""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest
from xverse.argus import EvidenceStore
from xverse.maestro.execution import NativeObservationBatch

from xverse_studio.blueprints.autoverse import documents
from xverse_studio.providers.autoverse.native_protocol import collection_interval, native_configuration
from xverse_studio.providers.autoverse.preparation import prepare_snapshot
from xverse_studio.storage.core import digest
from xverse_studio.xdl import XDLAdapter


@pytest.fixture(scope="module")
def native():
    binary = Path(os.environ["XVERSE_STUDIO_NATIVE_BRIDGE"]).resolve(strict=True)
    source = documents()
    compiled = XDLAdapter().compile(source)
    assert compiled["valid"]
    installation = {"identityDigest": digest({"scope": "owned-native-contract-boundary",
        "binarySha256": hashlib.sha256(binary.read_bytes()).hexdigest()})}
    preparation = prepare_snapshot("native-contract", {"documents": source, "plan": compiled["plan"],
        "planDigest": compiled["planDigest"], "semanticDigest": compiled["semanticDigest"]},
        installation=installation, host_id="owned-native-contract")
    config, transports = native_configuration(preparation.prepared, operation_id="original-native-operation",
        correlation_id="original-run-start-request", provider_id="autoverse.demo")
    return binary, preparation, config, transports


def execute(native, messages, *, configuration=None):
    binary, _, config, _ = native
    packet = b"".join((json.dumps(value, separators=(",", ":")) + "\n").encode()
                      for value in [configuration or config, *messages])
    result = subprocess.run([str(binary)], input=packet, capture_output=True, timeout=10)
    assert not result.stderr
    return result.returncode, [json.loads(line) for line in result.stdout.splitlines()]


def test_every_vcu_boundary_payload_uses_actual_native_submit_receive(native):
    _, _, config, transports = native
    assert len(config["routes"]) == len(transports) == 11
    messages = [{"kind": "ingress", "requestId": i + 1, "route": i,
                 "payloadHex": ("0." + str(i)).encode().hex()} for i in range(11)]
    messages.append({"kind": "stop", "requestId": 12})
    code, replies = execute(native, messages)
    assert code == 0 and replies[0]["kind"] == "ready"
    for request, reply in zip(messages[:-1], replies[1:-1], strict=True):
        assert reply["kind"] == "delivered" and reply["payloadHex"] == request["payloadHex"]
        assert reply["route"] == request["route"]
    assert replies[-1]["routesReleased"] is True
    assert all(row["accepted"] == row["received"] == 1 for row in replies[-1]["traffic"])


def test_original_native_batch_imports_through_actual_argus_with_gap_verdict(native, tmp_path):
    _, preparation, config, _ = native
    messages = [{"kind": "ingress", "requestId": i + 1, "route": 4, "payloadHex": str(i).encode().hex()}
                for i in range(16)]
    messages.append({"kind": "stop", "requestId": 17})
    code, replies = execute(native, messages)
    assert code == 0
    raw = replies[-1]["projectionJson"].encode()
    (tmp_path / "original-native-projection.json").write_bytes(raw)
    batch = NativeObservationBatch("autoverse.demo", 1, raw)
    original = batch.validate_identity(preparation.prepared, preparation.prepared.providers[0])
    observed = original["records"][0]
    inputs = original["extensions"]["io.xverse.native.inputs"]
    snapshots = original["extensions"]["io.xverse.native.snapshots"]
    assert observed["visibleBytesHex"] == b"15".hex()
    assert observed["counters"]["coalesced"] == snapshots[0]["coalesced"] == 15
    assert observed["causationId"] == inputs[0]["eventId"]
    assert inputs[0]["upstreamCausationId"] is None
    assert snapshots[0]["intervalProvenance"]["closure"] == "closed"
    root = tmp_path / "actual-argus"
    writer = EvidenceStore.open_run(root, run_id=preparation.prepared.submission.run_id,
        plan=preparation.prepared.inspection.to_data()["plan"],
        clocks={"native": {"domain": config["identity"]["clockDomain"], "unit": "ns", "value": 0}})
    writer.append_event(event_id=config["identity"]["correlationId"], producer_id="owned-host-contract",
                        event_kind="annotation")
    for fact in inputs:
        writer.append_event(event_id=fact["eventId"], producer_id=fact["producerId"], event_kind="annotation",
            correlation_id=fact["correlationId"], causation_id=fact["upstreamCausationId"],
            clocks={"source": fact["sourceClock"]}, extensions={"io.xverse.native.input": fact})
    ordinals = writer.import_observation(original)
    for snapshot in snapshots:
        writer.import_snapshot(snapshot)
    writer.finalize()
    reader = EvidenceStore.read_run(root)
    records = reader.records()
    assert ordinals and reader.assessed_evidence_status == "incomplete"
    assert any(r.get("causationId") == inputs[0]["eventId"] for r in records)
    assert any(r.get("extensions", {}).get("io.xverse.native.input") == inputs[0] for r in records)
    # The canonical evidence remains actual Argus data; collection loss is not
    # upgraded because every native payload was received successfully.


def test_native_batches_keep_original_sequence_and_distinct_ingress_causes(native):
    code, replies = execute(native, [
        {"kind": "ingress", "requestId": 1, "route": 4, "payloadHex": "31"},
        {"kind": "collect", "requestId": 2},
        {"kind": "ingress", "requestId": 3, "route": 4, "payloadHex": "32"},
        {"kind": "stop", "requestId": 4}])
    assert code == 0
    first, second = (json.loads(replies[i]["projectionJson"]) for i in (2, 4))
    assert first["extensions"]["io.xverse.maestro.execution"]["batchSequence"] == 1
    assert second["extensions"]["io.xverse.maestro.execution"]["batchSequence"] == 2
    assert first["records"][0]["causationId"] != second["records"][0]["causationId"]
    assert first["records"][0]["correlationId"] == second["records"][0]["correlationId"]


@pytest.mark.parametrize("message", [
    {"kind": "ingress", "requestId": 1, "route": 99, "payloadHex": "31"},
    {"kind": "ingress", "requestId": 1, "route": 0, "payloadHex": "00" * 129},
    {"kind": "ingress", "requestId": 1, "route": 0, "payloadHex": "bad"},
    {"kind": "ingress", "requestId": 1, "route": 0, "payloadHex": "31", "command": "untrusted"},
    {"kind": "collect", "requestId": True},
    {"kind": "collect", "requestId": 2},
    {"kind": "run-project-command", "requestId": 1},
])
def test_invalid_native_input_stops_without_claiming_delivery(native, message):
    code, replies = execute(native, [message])
    assert code == 2 and len(replies) == 1 and replies[0]["kind"] == "ready"


def test_duplicate_route_is_rejected_before_readiness(native):
    config = deepcopy(native[2])
    config["routes"][1]["routeId"] = config["routes"][0]["routeId"]
    code, replies = execute(native, [], configuration=config)
    assert code == 2 and replies == []


def test_collection_budget_scales_to_advertised_duration_without_hiding_loss():
    assert collection_interval(600) == 2.5
    assert collection_interval(1800) == 7.2
    assert 1800 / collection_interval(1800) <= 250

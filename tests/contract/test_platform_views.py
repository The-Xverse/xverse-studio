"""Actual Argus read captures and HTTP policies; fixtures do not prove live integration."""

from copy import deepcopy
from dataclasses import replace

import pytest
from xverse.argus import EvidenceStore
from xverse_studio.platform_observability.argus import ArgusBinding
from xverse_studio.platform_observability.views import (
    PlatformEvidenceBinding,
    PlatformQuery,
    PlatformViews,
    project_capture,
)
from xverse_studio.storage.core import Problem, atomic, canonical, digest
from xverse_studio.xdl import XDLAdapter
from xverse_studio.xdl.examples import examples


@pytest.fixture
def source(tmp_path):
    compiled = XDLAdapter().compile(examples()[0]["documents"])
    root = tmp_path / "source"
    writer = EvidenceStore.open_run(
        root, run_id="owned-view-run", plan=compiled["plan"]
    )
    extension = {
        "schemaVersion": "1.0",
        "runId": "owned-view-run",
        "planDigest": compiled["planDigest"],
        "inputSemanticDigest": compiled["semanticDigest"],
        "kind": "run-running",
        "operationId": "actual-operation",
        "logicalId": "xdl://owned/system#element",
        "observation": {"privateLog": "/private/SECRET", "cleanup": "released"},
    }
    writer.append_event(
        event_id="start",
        producer_id="maestro-public-execution",
        event_kind="annotation",
        correlation_id="actual-correlation",
        extensions={"io.xverse.maestro.execution": extension},
    )
    writer.append_event(
        event_id="result",
        producer_id="owned-view-test",
        event_kind="annotation",
        correlation_id="actual-correlation",
        causation_id="start",
        extensions={"private-log": {"text": "/private/SECRET"}},
    )
    binding = PlatformEvidenceBinding(
        ArgusBinding("owned-source", root, "owned-view-run", compiled["planDigest"]),
        compiled["semanticDigest"],
        "owned-provider",
        "sha256:" + "1" * 64,
        "sha256:" + "2" * 64,
        (("endpoint", "xdl://owned/system#element"),),
        (("schema", "utf8-finite-number"),),
    )
    yield binding, writer, compiled
    writer.finalize()


def test_actual_capture_is_shared_across_views_and_stable_while_writer_appends(source):
    binding, writer, _ = source
    views = PlatformViews()
    first = views.read(binding, PlatformQuery(view="evidence", limit=1))
    writer.append_event(
        event_id="later", producer_id="owned-view-test", event_kind="annotation"
    )
    following = views.read(
        binding,
        PlatformQuery(
            view="evidence",
            snapshot=first["snapshotId"],
            limit=1,
            cursor=first["nextCursor"],
        ),
    )
    assert following["items"][0]["eventId"] == "result"
    assert following["counts"]["retained"] == first["counts"]["retained"] == 2
    orchestration = views.read(binding, PlatformQuery(snapshot=first["snapshotId"]))
    assert orchestration["sourceWitness"] == first["sourceWitness"]
    assert orchestration["items"][0]["maestro"]["operationId"] == "actual-operation"
    assert orchestration["identityVerified"]["maestroInputs"] is True
    refreshed = views.read(binding, PlatformQuery(view="evidence"))
    assert refreshed["counts"]["retained"] == 3
    assert refreshed["sourceWitness"] != first["sourceWitness"]
    assert "SECRET" not in canonical(first) + canonical(orchestration)
    assert "private-log" not in canonical(following)


def test_pages_bind_run_view_filters_limit_and_snapshot(source):
    binding, _, _ = source
    views = PlatformViews()
    first = views.read(binding, PlatformQuery(view="evidence", limit=1))
    for changed in (
        {"view": "communications"},
        {"correlationId": "other"},
        {"limit": 2},
        {"order": "newest"},
    ):
        args = {
            "view": "evidence",
            "limit": 1,
            "snapshot": first["snapshotId"],
            "cursor": first["nextCursor"],
            **changed,
        }
        with pytest.raises(Problem) as caught:
            views.read(binding, PlatformQuery(**args))
        assert caught.value.code == "PLATFORM_CURSOR_INVALID"
    with pytest.raises(Problem):
        views.read(binding, PlatformQuery(view="evidence", cursor=first["nextCursor"]))
    with pytest.raises(Problem):
        views.read(
            replace(binding, provider_id="another-provider"),
            PlatformQuery(snapshot=first["snapshotId"]),
        )
    cause = views.read(
        binding,
        PlatformQuery(view="evidence", snapshot=first["snapshotId"], eventId="start"),
    )
    assert [r["eventId"] for r in cause["items"]] == ["start"]
    correlated = views.read(
        binding,
        PlatformQuery(snapshot=first["snapshotId"], correlationId="actual-correlation"),
    )
    assert len(correlated["items"]) == 1
    missing = views.read(
        binding,
        PlatformQuery(view="communications", snapshot=first["snapshotId"],
                      correlationId="actual-correlation"),
    )
    assert missing["matchedCount"] == 0


def test_newest_order_uses_original_ordinals_and_pinned_pages(source):
    binding, writer, _ = source
    for i in range(70):
        writer.append_event(event_id=f"new-{i}", producer_id="owned-ordered-source", event_kind="annotation")
    views = PlatformViews()
    newest = views.read(binding, PlatformQuery(view="evidence", order="newest", limit=50))
    assert newest["order"] == "newest"
    assert newest["items"][0]["eventId"] == "new-69"
    ordinals = [r["ingestionOrdinal"] for r in newest["items"]]
    assert ordinals == sorted(ordinals, reverse=True)
    writer.append_event(event_id="after-capture", producer_id="owned-ordered-source", event_kind="annotation")
    page = views.read(binding, PlatformQuery(view="evidence", order="newest", limit=50,
                                             snapshot=newest["snapshotId"], cursor=newest["nextCursor"]))
    assert page["snapshotId"] == newest["snapshotId"]
    assert page["sourceWitness"] == newest["sourceWitness"]
    assert not {r["eventId"] for r in page["items"]} & {r["eventId"] for r in newest["items"]}
    assert page["items"][-1]["eventId"] == "start"
    assert "after-capture" not in {r["eventId"] for r in page["items"] + newest["items"]}
    with pytest.raises(Problem) as wrong_order:
        views.read(binding, PlatformQuery(view="evidence", order="oldest", limit=50,
                                          snapshot=newest["snapshotId"], cursor=newest["nextCursor"]))
    assert wrong_order.value.code == "PLATFORM_CURSOR_INVALID"
    oldest = views.read(binding, PlatformQuery(view="evidence", snapshot=newest["snapshotId"]))
    assert oldest["order"] == "oldest" and oldest["items"][0]["eventId"] == "start"
    refreshed = views.read(binding, PlatformQuery(view="evidence", order="newest"))
    assert refreshed["items"][0]["eventId"] == "after-capture"


def test_capture_limits_expiry_and_eviction_are_explicit(source, monkeypatch):
    import xverse_studio.platform_observability.views as module

    binding, _, _ = source
    now = [0]
    views = PlatformViews(clock=lambda: now[0])
    first = views.read(binding, PlatformQuery())
    second = views.read(binding, PlatformQuery())
    third = views.read(binding, PlatformQuery())
    with pytest.raises(Problem):
        views.read(binding, PlatformQuery(snapshot=first["snapshotId"]))
    assert (
        views.read(binding, PlatformQuery(snapshot=second["snapshotId"]))["snapshotId"]
        == second["snapshotId"]
    )
    now[0] = 300
    with pytest.raises(Problem) as caught:
        views.read(binding, PlatformQuery(snapshot=third["snapshotId"]))
    assert caught.value.code == "PLATFORM_SNAPSHOT_EXPIRED"
    monkeypatch.setattr(module, "MAX_CAPTURE_BYTES", 1)
    with pytest.raises(Problem) as caught:
        views.read(binding, PlatformQuery())
    assert caught.value.code == "PLATFORM_VIEW_LIMIT"


def capture(binding):
    return {
        "sourceWitness": "witness",
        "reader": {"service": "argus"},
        "identityVerified": True,
        "evidence": {
            "recorded": "incomplete",
            "assessed": "incomplete",
            "recordedReasons": ["/private/SECRET"],
        },
        "diagnostics": [{"code": "ARGUS2-LOSS-KNOWN-DROP"}],
        "items": [
            {
                "eventId": "native",
                "eventKind": "observation",
                "ingestionOrdinal": 1,
                "runId": binding.source.run_id,
                "producerId": "native-tap",
                "correlationId": "correlation",
                "causationId": "ingress",
                "clocks": {
                    "source": {"domain": "unmapped", "unit": "ns", "value": 2**63}
                },
                "observation": {
                    "schemaId": "schema",
                    "endpointId": "endpoint",
                    "routeId": "route",
                    "sourcePayloadSize": 3,
                    "visibleByteCount": 3,
                    "payloadViewState": "complete",
                    "visibleBytesHex": "312e35",
                    "counters": {"coalesced": 20, "dropped": 0, "queued": 1},
                },
                "privateLog": "/private/SECRET",
            }
        ],
    }


def test_scalar_policy_original_clocks_causes_and_counters_preserved(source):
    binding, _, _ = source
    original = capture(binding)
    result = project_capture(original, binding)
    row = result["items"][0]
    assert row["clocks"]["source"]["value"] == str(2**63)
    assert row["clocks"]["source"]["domain"] == "unmapped"
    assert row["causationId"] == "ingress" and row["correlationId"] == "correlation"
    assert row["logicalId"] == "xdl://owned/system#element"
    assert row["communication"]["payload"]["value"] == "1.5"
    assert "sequence" not in row["communication"]
    assert row["communication"]["counters"] == {
        "coalesced": 20,
        "dropped": 0,
        "queued": 1,
    }
    assert result["evidence"]["assessed"] == "incomplete"
    assert result["evidence"]["recordedReasonsWithheld"] == 1
    assert "SECRET" not in canonical(result) and "visibleBytesHex" not in canonical(
        result
    )
    assert original["items"][0]["clocks"]["source"]["value"] == 2**63


@pytest.mark.parametrize(
    "payload", ["NaN", "Infinity", "/private/SECRET", "1e999", "01", "1 " * 65]
)
def test_unknown_or_unsafe_payload_is_never_forwarded(source, payload):
    binding, _, _ = source
    original = capture(binding)
    row = original["items"][0]["observation"]
    row.update(
        sourcePayloadSize=len(payload),
        visibleByteCount=len(payload),
        visibleBytesHex=payload.encode().hex(),
    )
    result = project_capture(original, binding)
    assert result["items"][0]["communication"]["payload"]["value"] is None
    assert "SECRET" not in canonical(result)
    row["schemaId"] = "not-host-admitted"
    assert (
        project_capture(original, binding)["items"][0]["communication"]["payload"][
            "policy"
        ]
        == "metadata-only"
    )


def test_mismatched_original_inputs_fail_instead_of_joining(source):
    from xverse_studio.platform_observability.argus import ArgusSources

    binding, _, _ = source
    captured = ArgusSources((binding.source,)).capture(binding.source.source_id)
    for field in ("runId", "planDigest", "inputSemanticDigest"):
        changed = deepcopy(captured)
        changed["items"][0]["extensions"]["io.xverse.maestro.execution"][field] = (
            "other"
        )
        with pytest.raises(Problem):
            project_capture(changed, binding)


def test_http_auth_strict_query_and_host_bound_source(client, source):
    from types import SimpleNamespace

    binding, _, compiled = source
    studio = client.app.state.studio
    # Exact immutable snapshot storage, no run launch or activation.
    snap = {
        "snapshotId": "snap-owned-platform",
        "providerIdentity": {},
        "planDigest": compiled["planDigest"],
    }
    snap["snapshotDigest"] = digest(snap)
    studio.store.put("snapshot", snap["snapshotId"], snap)
    atomic(
        studio.store.root / "snapshots" / snap["snapshotId"] / "snapshot.json",
        canonical(snap).encode(),
    )
    studio.store.put(
        "run",
        binding.source.run_id,
        {
            "runId": binding.source.run_id,
            "snapshotId": snap["snapshotId"],
            "providerId": "owned-provider",
            "state": "stopped",
            "evidence": "unavailable",
            "cleanup": "complete",
        },
    )
    url = "/api/v1/runs/owned-view-run/platform"
    assert client.get(url).status_code == 404  # No source from a journal alone.
    studio.runs.installed_providers["owned-provider"] = SimpleNamespace(
        platform_evidence_binding=lambda run, snapshot: binding
    )
    response = client.get(url)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["identity"]["runId"] == binding.source.run_id
    for query in (
        "?root=/private",
        "?view=invalid",
        "?limit=101",
        "?view=evidence&view=orchestration",
        "?snapshot=unknown",
    ):
        assert client.get(url + query).status_code in (409, 422)
    client.cookies.clear()
    assert client.get(url).status_code == 401


def test_extensible_annotations_cannot_smuggle_nested_browser_metadata(source):
    from xverse_studio.platform_observability.argus import ArgusSources

    binding, _, _ = source
    captured = ArgusSources((binding.source,)).capture(binding.source.source_id)
    captured["items"][0]["extensions"]["io.xverse.maestro.execution"]["operationId"] = {
        "privateLog": "/private/SECRET"
    }
    with pytest.raises(Problem) as caught:
        project_capture(captured, binding)
    assert caught.value.code == "PLATFORM_RECORD_UNSUPPORTED"


def test_native_input_extension_cannot_forward_arbitrary_nested_clock_metadata(source):
    binding, _, _ = source
    original = capture(binding)
    original["items"][0]["extensions"] = {
        "io.xverse.native.input": {
            "eventId": "ingress",
            "sourceClock": {
                "domain": "native",
                "unit": "ns",
                "value": 1,
                "privateLog": "/private/SECRET",
            },
        }
    }
    with pytest.raises(Problem) as caught:
        project_capture(original, binding)
    assert caught.value.code == "PLATFORM_RECORD_UNSUPPORTED"

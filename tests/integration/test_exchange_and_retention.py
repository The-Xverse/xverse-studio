"""Derived metadata and retention invariants; archive tests are owned by exchange."""
from copy import deepcopy
import pytest
from xverse_studio.annotations import create_annotation, revise_annotation, AnnotationError
from xverse_studio.retention import plan_retention, check_plan


def test_annotations_keep_history_and_never_mutate_original_record():
    body = {"kind": "comment", "text": "Observed fixture", "evidenceRefs": ["run:journal"]}
    original = create_annotation("run", body, author="operator")
    revised = revise_annotation(original, {**body, "text": "Correction"}, expected_revision=1, author="operator")
    assert original["text"] == "Observed fixture" and original["revision"] == 1
    assert revised["history"][0]["text"] == original["text"]
    assert revised["revision"] == 2
    with pytest.raises(AnnotationError, match="REVISION_CONFLICT"):
        revise_annotation(revised, body, expected_revision=1, author="operator")
    tombstone = revise_annotation(revised, {}, expected_revision=2, author="operator", delete=True)
    assert tombstone["deleted"] and len(tombstone["history"]) == 2


@pytest.mark.parametrize("uri", ["javascript:alert(1)", "file:///etc/passwd", "https://name:password@example.com/r", "https://example.com/?token=secret", "http://[broken", "https://example.com/\nnext"])
def test_trace_targets_are_inert_and_credential_free(uri):
    with pytest.raises(AnnotationError):
        create_annotation("run", {"kind": "trace_link", "target": {"uri": uri, "revision": "unknown"}}, author="operator")


def test_trace_links_pin_revision_without_claiming_target_validity():
    row = create_annotation("run", {"kind": "trace_link", "target": {"uri": "urn:test:requirement:12", "revision": "rev-1"}}, author="operator")
    assert row["target"]["revision"] == "rev-1"
    assert "verdict" not in row


def test_retention_is_read_only_and_protects_active_and_derived_dependencies():
    state = {"runs": [{"runId": "active", "state": "unknown"}, {"runId": "done", "state": "stopped"}, {"runId": "derived", "state": "stopped"}], "evaluations": [{"runId": "derived"}]}
    before = deepcopy(state)
    plan = plan_retention(["active", "done", "derived"], state)
    assert [r["runId"] for r in plan["removals"]] == ["done"]
    assert state == before
    assert check_plan(plan, state, plan["fingerprint"]) == plan["removals"]
    state["runs"][1]["state"] = "running"
    with pytest.raises(ValueError, match="RETENTION_PLAN_STALE"):
        check_plan(plan, state, plan["fingerprint"])

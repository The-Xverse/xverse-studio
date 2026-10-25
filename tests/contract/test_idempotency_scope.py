"""Durable operation identity is scoped by authenticated owner and resource route."""

import pytest

from xverse_studio.storage.core import Store, Problem, uid


def test_principal_route_and_payload_scopes_survive_reopen_without_extra_effects(
    tmp_path,
):
    store = Store(tmp_path)
    callbacks = []

    def accept(db):
        operation = {"operationId": uid("op-")}
        callbacks.append(operation["operationId"])
        store.put("owned-effect", operation["operationId"], operation, db)
        return operation

    original, created = store.idempotent(
        "operator-a", "POST /runs/system-a", "retry-key", {"input": 1}, accept
    )
    assert created
    replay, created = store.idempotent(
        "operator-a", "POST /runs/system-a", "retry-key", {"input": 1}, accept
    )
    assert not created and replay == original
    other_owner, created = store.idempotent(
        "operator-b", "POST /runs/system-a", "retry-key", {"input": 2}, accept
    )
    assert created and other_owner != original
    other_route, created = store.idempotent(
        "operator-a", "POST /runs/system-b", "retry-key", {"input": 3}, accept
    )
    assert created and other_route not in [original, other_owner]
    with pytest.raises(Problem) as conflict:
        store.idempotent(
            "operator-a", "POST /runs/system-a", "retry-key", {"input": 99}, accept
        )
    assert (
        conflict.value.code == "IDEMPOTENCY_CONFLICT" and conflict.value.status == 409
    )
    store = Store(tmp_path)
    replay, created = store.idempotent(
        "operator-a", "POST /runs/system-a", "retry-key", {"input": 1}, accept
    )
    assert not created and replay == original
    assert len(callbacks) == 3
    assert {row["operationId"] for row in store.all("owned-effect")} == set(callbacks)

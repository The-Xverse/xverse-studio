"""Owned adapter contract only; these are not live Autoverse acceptance cases."""
import pytest

from xverse_studio.providers.autoverse.controls import (
    ControlRejected, DriverLease, LatestTelemetry, driver_frame, wire_messages,
    DRIVER_SIGNALS, TELEMETRY_SIGNALS, decode_telemetry, MAX_DRIVER_LEASE_SECONDS,
)


def frame(**changes):
    return {"sequence": 1, "throttle": 0, "brake": 0, "steer": 0, **changes}


def test_existing_manual_control_topic_and_wire_contract():
    messages = dict(wire_messages(frame(throttle=.4, steer=-.5, cruise=True, reverse=False, deltaSpeed=1)))
    assert messages == {
        "vehicle/command/acc_pedal_sts": b"0.4", "vehicle/command/brake_pedal_sts": b"0.0",
        "vehicle/command/steer_sts": b"-0.5", "vehicle/control/cc_engage_req": b"true",
        "vehicle/control/reverse_req": b"false", "vehicle/control/delta_speed": b"1.0",
    }
    assert dict(wire_messages(frame(deltaSpeed=0))) == {
        "vehicle/command/acc_pedal_sts": b"0.0", "vehicle/command/brake_pedal_sts": b"0.0", "vehicle/command/steer_sts": b"0.0"}


@pytest.mark.parametrize("field,value", [
    ("throttle", True), ("throttle", 1.01), ("throttle", -1), ("brake", float("nan")),
    ("brake", float("inf")), ("steer", 1.01), ("steer", -1.01),
    ("cruise", 1), ("cruise", "true"), ("reverse", 0), ("deltaSpeed", 21),
    ("deltaSpeed", -21), ("sequence", True), ("sequence", -1), ("sequence", 2**53),
    ("command", "arbitrary shell text"),
])
def test_invalid_or_unknown_input_is_rejected_without_mutation(field, value):
    source = frame(**{field: value})
    original = source.copy()
    with pytest.raises(ControlRejected):
        driver_frame(source)
    assert source.keys() == original.keys()
    assert all(source[key] is original[key] for key in original)


def test_pedal_conflict_and_partial_analog_state_are_not_silently_reinterpreted():
    with pytest.raises(ControlRejected, match="PEDAL_CONFLICT"):
        driver_frame(frame(throttle=.5, brake=.5))
    value = frame(); value.pop("steer")
    with pytest.raises(ControlRejected, match="FRAME_INVALID"):
        driver_frame(value)


def test_retry_does_not_extend_control_lease_or_republish_delta():
    lease = DriverLease()
    original = frame(throttle=.4, deltaSpeed=1)
    assert lease.accept(original, 10) == {"accepted": True, "duplicate": False, "sequence": 1}
    assert lease.accept(original, 10.5)["duplicate"] is True
    assert lease.requested(10.5)["active"]
    expired = lease.requested(10 + MAX_DRIVER_LEASE_SECONDS)
    assert expired["active"] is False
    assert expired["frame"] == frame(sequence=0, brake=1.0, cruise=False)
    assert "reverse" not in expired["frame"] and "deltaSpeed" not in expired["frame"]
    # The publishing loop excludes one-shot requests after their accepted frame.
    continuous = dict(wire_messages(original, include_requests=False))
    assert DRIVER_SIGNALS["deltaSpeed"].topic not in continuous
    assert lease.accept(frame(sequence=2), 11)["duplicate"] is False


def test_conflicting_sequence_or_clock_cannot_overwrite_last_accepted_frame():
    lease = DriverLease(); lease.accept(frame(throttle=.2), 10)
    for value, now in [(frame(throttle=.3), 10.1), (frame(sequence=0), 10.1), (frame(sequence=2), 9)]:
        with pytest.raises(ControlRejected): lease.accept(value, now)
    assert lease.requested(10.1)["frame"]["throttle"] == .2
    assert lease.requested(9)["active"] is False


@pytest.mark.parametrize("text", [b"nan", b"inf", b"-1", b"261", b"1; run()", b"{}", b"\xff", b"1"*257])
def test_invalid_speed_or_oversize_wire_payload_is_not_known_data(text):
    with pytest.raises(ControlRejected):
        decode_telemetry(TELEMETRY_SIGNALS["speed"].topic, text)


def test_unknown_topic_does_not_acquire_control_or_observation_scope():
    with pytest.raises(ControlRejected): decode_telemetry("arbitrary/private/topic", b"1")


def test_measured_zero_missing_and_stale_values_remain_distinct():
    view = LatestTelemetry()
    assert all(item["value"] is None and item["status"] == "unknown" for item in view.snapshot(10)["items"].values())
    assert view.receive(TELEMETRY_SIGNALS["speed"].topic, b"0", 10)
    current = view.snapshot(10.1)
    assert current["items"]["speed"]["value"] == 0 and current["items"]["speed"]["status"] == "observed"
    assert current["items"]["cruiseEngaged"]["value"] is None
    assert view.snapshot(12)["items"]["speed"]["status"] == "stale"
    assert view.snapshot(9)["items"]["speed"]["status"] == "unknown"
    assert view.snapshot(12)["simulationTime"] is None


def test_invalid_payload_preserves_previous_sample_and_bounded_projection():
    view = LatestTelemetry()
    topic = TELEMETRY_SIGNALS["cruiseEngaged"].topic
    assert view.receive(topic, b"true", 10)
    assert not view.receive(topic, b"definitely", 10.1)
    assert view.snapshot(10.2)["items"]["cruiseEngaged"]["value"] is True
    assert view.snapshot(10.2)["invalidPayloads"] == 1
    assert len(view.snapshot(10.2)["items"]) == len(TELEMETRY_SIGNALS)


def test_new_driver_after_expiry_preserves_gear_desire_but_does_not_reengage_cruise():
    lease=DriverLease()
    lease.accept({'sequence':1,'throttle':0,'brake':0,'steer':0,'reverse':True,'cruise':True},100)
    assert 'reverse' not in lease.requested(101)['frame']
    lease.accept({'sequence':2,'throttle':0,'brake':1,'steer':0},101)
    state=lease.requested(101.1)['frame']
    assert state['reverse'] is True and state['cruise'] is False

import pytest
from test_native_command_terminal_boundaries import test_native_late_command_outcome_preserves_natural_completion_and_exact_retry as native_workflow

@pytest.mark.capture_owned_native_failure
def test_deliberate_capture_control(client,monkeypatch,record_property):
    native_workflow(client,monkeypatch,record_property,'stop','after_final_poll')
    raise AssertionError('OWNED_CAPTURE_CONTROL: original native workflow assertions passed')

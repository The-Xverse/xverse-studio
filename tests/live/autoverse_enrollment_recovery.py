"""Private receipt boundary on actual enrolled data; no runtime operation."""

from copy import deepcopy
import json
import os
from pathlib import Path

import pytest

from xverse_studio.providers.autoverse.installation import InstallationError


@pytest.fixture
def receipt():
    return json.loads(
        Path(os.environ["STUDIO_AUTOVERSE_TEST_INSTALLATION"]).read_bytes()
    )["classic"]


def test_private_first_enrollment_then_restart_reuses_only_original_identity(
    receipt, tmp_path, monkeypatch
):
    from xverse_studio.providers.autoverse import enrollment

    calls = []

    def enroll(root):
        calls.append(("cold", str(root)))
        return deepcopy(receipt)

    def identity(value):
        assert value == receipt
        calls.append(("identity", value["identityDigest"]))

    monkeypatch.setattr(enrollment, "enroll", enroll)
    monkeypatch.setattr(enrollment, "verify_identity", identity)
    first = enrollment.load_or_enroll(tmp_path, Path(receipt["root"]))
    assert first == receipt and calls == [("cold", str(Path(receipt["root"])))]
    file = tmp_path / "autoverse-installation.private.json"
    assert file.stat().st_mode & 0o077 == 0
    second = enrollment.load_or_enroll(tmp_path, Path(receipt["root"]))
    assert second == first and calls[-1] == ("identity", receipt["identityDigest"])


@pytest.mark.parametrize(
    "case",
    [
        "symlink",
        "public-mode",
        "malformed",
        "digest",
        "wrong-root",
        "changed-identity",
        "oversized",
        "directory",
        "hard-link",
        "duplicate-key",
    ],
)
def test_untrusted_or_changed_private_receipt_never_triggers_fresh_enrollment(
    receipt, tmp_path, monkeypatch, case
):
    from xverse_studio.providers.autoverse import enrollment

    monkeypatch.setattr(enrollment, "enroll", lambda root: deepcopy(receipt))
    enrollment.load_or_enroll(tmp_path, Path(receipt["root"]))
    file = tmp_path / "autoverse-installation.private.json"
    if case == "symlink":
        original = tmp_path / "original.private.json"
        file.rename(original)
        file.symlink_to(original)
    elif case == "public-mode":
        file.chmod(0o644)
    elif case == "malformed":
        file.write_text("not-json")
    elif case == "oversized":
        file.write_bytes(b" " * (enrollment.MAX_BYTES + 1))
    elif case == "directory":
        file.unlink()
        file.mkdir()
    elif case == "hard-link":
        os.link(file, tmp_path / "aliased-private-receipt")
    elif case == "duplicate-key":
        text = file.read_text()
        file.write_text(
            text.replace('"version":"1.0"', '"version":"1.0","version":"1.0"', 1)
        )
    elif case == "digest":
        value = json.loads(file.read_text())
        value["installation"]["files"]["untrusted"] = "sha256:" + "0" * 64
        file.write_text(json.dumps(value))
    elif case == "wrong-root":
        value = json.loads(file.read_text())
        value["root"] = str(tmp_path / "other-root")
        file.write_text(json.dumps(value))

    def forbidden(root):
        pytest.fail("An unsafe or changed receipt was silently re-enrolled")

    def identity(value):
        if case == "changed-identity":
            raise InstallationError("AUTOVERSE_INSTALLATION_CHANGED")
        pytest.fail("Untrusted private receipt reached identity verification")

    monkeypatch.setattr(enrollment, "enroll", forbidden)
    monkeypatch.setattr(enrollment, "verify_identity", identity)
    with pytest.raises(InstallationError):
        enrollment.load_or_enroll(tmp_path, Path(receipt["root"]))


def test_actual_immutable_identity_probe_keeps_full_readiness_separate(receipt):
    from xverse_studio.providers.autoverse.installation import verify_identity

    # Real file/SDK/container/artifact/gateway reads; no reservation or process.
    assert verify_identity(receipt) is True


@pytest.mark.parametrize("case", ["tool-retarget", "container-retarget"])
def test_cached_data_cannot_select_new_probe_executables_or_container_names(
    receipt, monkeypatch, case
):
    from xverse_studio.providers.autoverse import installation

    changed = deepcopy(receipt)
    if case == "tool-retarget":
        changed["docker"] = "/unadmitted/never-execute"
    else:
        changed["containers"]["score"]["name"] = "/unadmitted-container"

    def forbidden(*args, **kwargs):
        pytest.fail("Retargeted cached data reached an external command")

    monkeypatch.setattr(installation, "command", forbidden)
    with pytest.raises(InstallationError, match="AUTOVERSE_ENROLLMENT_BINDING_CHANGED"):
        installation.verify_identity(changed)

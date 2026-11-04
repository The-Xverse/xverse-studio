"""Filesystem guards for new Autoverse environments; no simulated live acceptance."""
import hashlib
import importlib.util
import os
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("autoverse_asset_staging", Path(__file__).resolve().parents[2] / "scripts/stage_autoverse_assets.py")
assets = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(assets)


def package(root):
    runtime = root / "aaos_digital_cluster/cuttlefish_emulator/runtime"
    (runtime / "bin").mkdir(parents=True)
    for name in ["bin/launch_cvd", "bin/stop_cvd", "boot.img", "super.img"]:
        p = runtime / name
        p.write_bytes(b"Explicit non-executable filesystem fixture\n")
        p.chmod(0o755 if name.startswith("bin/") else 0o644)
    userdata = runtime / "userdata.img"
    with userdata.open("wb") as stream:
        stream.truncate(8 * 1024 * 1024)
        stream.seek(-1, os.SEEK_END)
        stream.write(b"x")
    apk = runtime.parent / "apk/digital-cluster-app-debug.apk"
    apk.parent.mkdir()
    apk.write_bytes(b"Inert fixture; never install or execute")
    return runtime


def test_sparse_assets_are_independent_and_existing_guest_state_is_excluded(tmp_path):
    root = tmp_path / "existing"
    runtime = package(root)
    (runtime / "cvd-state").mkdir()
    (runtime / "cvd-state/private-sentinel").write_text("must remain original")
    (runtime / "generated-user-state.img").write_text("not an admitted base image")
    target = tmp_path / "new"
    report = assets.stage(root, target)
    original, staged = runtime / "userdata.img", target / "android-runtime/userdata.img"
    assert staged.stat().st_ino != original.stat().st_ino
    assert hashlib.sha256(staged.read_bytes()).hexdigest() == hashlib.sha256(original.read_bytes()).hexdigest()
    assert staged.stat().st_blocks * 512 < staged.stat().st_size
    assert not (target / "android-runtime/cvd-state").exists()
    assert not (target / "android-runtime/generated-user-state.img").exists()
    assert report["guestStateCopied"] is False and not (target / ".incomplete").exists()
    with staged.open("r+b") as stream:
        stream.write(b"new instance")
    assert original.read_bytes().startswith(bytes(12))


def test_existing_or_original_destinations_are_refused_without_overwrite(tmp_path):
    root = tmp_path / "existing"
    package(root)
    target = tmp_path / "already-there"
    target.mkdir()
    sentinel = target / "sentinel"
    sentinel.write_text("original")
    for path in [target, root / "new-inside-original"]:
        with pytest.raises(ValueError, match="DESTINATION_MUST_BE_NEW"):
            assets.stage(root, path)
    alias = tmp_path / "alias"
    alias.symlink_to(root, target_is_directory=True)
    with pytest.raises(ValueError, match="DESTINATION_MUST_BE_NEW"):
        assets.stage(root, alias / "new-inside-original")
    assert sentinel.read_text() == "original" and not (root / "new-inside-original").exists()


def test_internal_link_escape_fails_with_only_an_incomplete_new_root(tmp_path):
    root = tmp_path / "existing"
    runtime = package(root)
    outside = tmp_path / "outside"
    outside.write_text("private sentinel")
    (runtime / "bin/launch_cvd").unlink()
    (runtime / "bin/launch_cvd").symlink_to(outside)
    target = tmp_path / "new"
    with pytest.raises(ValueError, match="LINK_ESCAPE"):
        assets.stage(root, target)
    assert (target / ".incomplete").exists() and not (target / "asset-manifest.json").exists()
    assert outside.read_text() == "private sentinel"


def test_changing_source_is_not_published_as_verified_assets(tmp_path, monkeypatch):
    root = tmp_path / "existing"
    runtime = package(root)
    source = runtime / "boot.img"
    original = assets.os.pread
    changed = False
    def mutate(fd, amount, offset):
        nonlocal changed
        content = original(fd, amount, offset)
        if not changed and os.fstat(fd).st_ino == source.stat().st_ino:
            source.write_bytes(b"concurrent replacement of source bytes")
            changed = True
        return content
    monkeypatch.setattr(assets.os, "pread", mutate)
    target = tmp_path / "new"
    with pytest.raises(ValueError, match="ASSET_CHANGED_DURING_READ"):
        assets.stage(root, target)
    assert (target / ".incomplete").exists() and not (target / "asset-manifest.json").exists()

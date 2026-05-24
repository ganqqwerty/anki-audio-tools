from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from scripts import release_asset_common, release_assets, release_sherpa_assets

from tests.release_assets_helpers import (
    write_spleeter_smoke_outputs as _write_spleeter_smoke_outputs,
)
from tests.release_assets_helpers import (
    write_verified_target_sources as _write_verified_target_sources,
)
from tests.release_assets_helpers import (
    write_verified_target_tracked_files as _write_verified_target_tracked_files,
)


def test_lock_contains_supported_target_and_tool_matrix() -> None:
    lock = release_assets.load_lock()

    assert release_assets.lock_targets(lock) == [
        "macos-arm64",
        "macos-x86_64",
        "windows-x86_64",
    ]
    assert release_assets.lock_tools(lock, "macos-arm64") == [
        "deep-filter",
        "ffmpeg",
        "ffprobe",
        "rnnoise-cli",
        "sherpa-spleeter",
        "dpdfnet",
    ]
    assert release_assets.lock_tools(lock, "macos-x86_64") == [
        "deep-filter",
        "ffmpeg",
        "ffprobe",
        "rnnoise-cli",
        "sherpa-spleeter",
        "dpdfnet",
    ]
    assert release_assets.lock_tools(lock, "windows-x86_64") == [
        "deep-filter",
        "ffmpeg",
        "ffprobe",
        "rnnoise-cli",
        "sherpa-spleeter",
        "dpdfnet",
    ]
    for target in release_assets.lock_targets(lock):
        sherpa_files = release_assets.tool_runtime_files(lock, target, "sherpa-spleeter")
        assert sherpa_files
    assert release_assets.lock_shared_files(lock) == [
        "spleeter-vocals",
        "spleeter-accompaniment",
    ]
    assert any("DPDFNet Lite CLI" in notice for notice in lock["notices"])


def test_release_ready_lock_requires_every_binary_checksum() -> None:
    lock = release_assets.load_lock()
    release_ready_lock = copy.deepcopy(lock)
    release_ready_lock["release_ready"] = True
    release_ready_lock["targets"]["macos-arm64"]["tools"]["ffmpeg"].pop("sha256", None)

    with pytest.raises(release_assets.ReleaseAssetError, match="macos-arm64/ffmpeg.*sha256"):
        release_assets.validate_lock(release_ready_lock)


def test_release_ready_lock_requires_runtime_file_checksums() -> None:
    lock = release_assets.load_lock()
    release_ready_lock = copy.deepcopy(lock)
    release_ready_lock["release_ready"] = True
    runtime_file = release_ready_lock["targets"]["macos-arm64"]["tools"]["sherpa-spleeter"]["runtime_files"][0]
    runtime_file.pop("sha256", None)

    with pytest.raises(release_assets.ReleaseAssetError, match="macos-arm64/sherpa-spleeter.*sha256"):
        release_assets.validate_lock(release_ready_lock)


def test_verify_target_reports_missing_tracked_runtime_binary(tmp_path: Path) -> None:
    lock = release_assets.load_lock()

    result = release_assets.verify_assets(
        lock,
        cache_dir=tmp_path,
        addon_bin_dir=tmp_path / "addon-bin",
        target_keys=["macos-arm64"],
        run_diagnostics=False,
    )

    assert result.ok is False
    assert "macos-arm64/deep-filter" in "\n".join(result.errors)


def test_verify_target_reports_missing_cached_ffmpeg_binary(tmp_path: Path) -> None:
    lock = release_assets.load_lock()
    addon_bin_dir = tmp_path / "addon-bin"
    _write_verified_target_tracked_files(lock, addon_bin_dir, "macos-arm64")

    result = release_assets.verify_assets(
        lock,
        cache_dir=tmp_path / "cache",
        addon_bin_dir=addon_bin_dir,
        target_keys=["macos-arm64"],
        run_diagnostics=False,
    )

    assert result.ok is False
    assert "macos-arm64/ffmpeg" in "\n".join(result.errors)


def test_verify_target_reports_checksum_mismatch(tmp_path: Path) -> None:
    lock = release_assets.load_lock()
    locked = copy.deepcopy(lock)
    entry = locked["targets"]["macos-arm64"]["tools"]["deep-filter"]
    entry["sha256"] = hashlib.sha256(b"expected").hexdigest()
    binary = tmp_path / "addon-bin" / "macos-arm64" / "deep-filter"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"actual")

    result = release_assets.verify_assets(
        locked,
        cache_dir=tmp_path,
        addon_bin_dir=tmp_path / "addon-bin",
        target_keys=["macos-arm64"],
        run_diagnostics=False,
    )

    assert result.ok is False
    assert "checksum mismatch" in "\n".join(result.errors)


def test_verify_runs_current_sherpa_spleeter_smoke(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lock = copy.deepcopy(release_assets.load_lock())
    current_target = "macos-arm64"
    _write_verified_target_sources(lock, tmp_path / "cache", tmp_path / "addon-bin", current_target)
    monkeypatch.setattr(release_assets, "current_target_key", lambda: current_target)
    monkeypatch.setattr(release_assets, "_append_diagnostic_report", lambda *_args: None)
    commands: list[tuple[str, ...]] = []

    def fake_run(
        command: list[str],
        capture_output: bool,
        text: bool,
        timeout: int,
        check: bool,
    ) -> SimpleNamespace:
        commands.append(tuple(command))
        if command[0].endswith("ffmpeg"):
            Path(command[-1]).write_bytes(b"input wav")
        elif command[0].endswith("sherpa-spleeter"):
            _write_spleeter_smoke_outputs(command)
        else:  # pragma: no cover - protects the test if a new command is added
            raise AssertionError(command)
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(release_sherpa_assets.subprocess, "run", fake_run)

    result = release_assets.verify_assets(
        lock,
        cache_dir=tmp_path / "cache",
        addon_bin_dir=tmp_path / "addon-bin",
        target_keys=[current_target],
        run_diagnostics=True,
    )

    assert result.ok is True
    assert commands[1][-1] == "--num-threads=1"
    assert any("sherpa-spleeter: smoke ok" in report for report in result.reports)


def test_cmd_verify_skips_diagnostics_by_default(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(release_assets, "load_lock", lambda: {"schema_version": 1})
    seen: dict[str, object] = {}

    def fake_verify_assets(
        lock: dict,
        *,
        target_keys: list[str] | None,
        run_diagnostics: bool,
    ) -> release_asset_common.VerificationResult:
        seen["lock"] = lock
        seen["target_keys"] = target_keys
        seen["run_diagnostics"] = run_diagnostics
        return release_asset_common.VerificationResult(errors=[], reports=["ok"])

    monkeypatch.setattr(release_assets, "verify_assets", fake_verify_assets)
    monkeypatch.setattr(release_assets, "_target_selection", lambda value: [value])

    exit_code = release_assets._cmd_verify(SimpleNamespace(target="current", diagnostics=False))

    assert exit_code == 0
    assert seen["target_keys"] == ["current"]
    assert seen["run_diagnostics"] is False
    assert capsys.readouterr().out.strip() == "ok"


def test_cmd_verify_enables_diagnostics_when_requested(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(release_assets, "load_lock", lambda: {"schema_version": 1})
    seen: dict[str, object] = {}

    def fake_verify_assets(
        lock: dict,
        *,
        target_keys: list[str] | None,
        run_diagnostics: bool,
    ) -> release_asset_common.VerificationResult:
        seen["lock"] = lock
        seen["target_keys"] = target_keys
        seen["run_diagnostics"] = run_diagnostics
        return release_asset_common.VerificationResult(errors=[], reports=[])

    monkeypatch.setattr(release_assets, "verify_assets", fake_verify_assets)
    monkeypatch.setattr(release_assets, "_target_selection", lambda value: [value])

    exit_code = release_assets._cmd_verify(SimpleNamespace(target="current", diagnostics=True))

    assert exit_code == 0
    assert seen["target_keys"] == ["current"]
    assert seen["run_diagnostics"] is True


def test_stage_rejects_path_traversal_from_lock(tmp_path: Path) -> None:
    lock = release_assets.load_lock()
    unsafe = copy.deepcopy(lock)
    unsafe["targets"]["macos-arm64"]["tools"]["ffmpeg"]["executable"] = "../ffmpeg"

    with pytest.raises(release_assets.ReleaseAssetError, match="unsafe executable path"):
        release_assets.stage_assets(
            unsafe,
            cache_dir=tmp_path,
            destination=tmp_path / "stage",
            target_keys=["macos-arm64"],
        )


def test_stage_copies_verified_runtime_binary(tmp_path: Path) -> None:
    lock = release_assets.load_lock()
    locked = copy.deepcopy(lock)
    binary = tmp_path / "cache" / "bin" / "macos-arm64" / "ffmpeg"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"ffmpeg")
    locked["targets"]["macos-arm64"]["tools"]["ffmpeg"]["sha256"] = hashlib.sha256(b"ffmpeg").hexdigest()

    staged = release_assets.stage_assets(
        locked,
        cache_dir=tmp_path / "cache",
        addon_bin_dir=tmp_path / "addon-bin",
        destination=tmp_path / "stage",
        target_keys=["macos-arm64"],
        tool_names=["ffmpeg"],
    )

    assert staged == [tmp_path / "stage" / "macos-arm64" / "ffmpeg"]
    assert staged[0].read_bytes() == b"ffmpeg"


def test_stage_copies_shared_model_files_when_staging_full_runtime(tmp_path: Path) -> None:
    lock = release_assets.load_lock()
    locked = copy.deepcopy(lock)
    binary = tmp_path / "cache" / "bin" / "macos-arm64" / "ffmpeg"
    vocals = tmp_path / "addon-bin" / "models" / "spleeter-2stems-fp16" / "vocals.fp16.onnx"
    accompaniment = vocals.parent / "accompaniment.fp16.onnx"
    binary.parent.mkdir(parents=True)
    vocals.parent.mkdir(parents=True)
    binary.write_bytes(b"ffmpeg")
    vocals.write_bytes(b"vocals")
    accompaniment.write_bytes(b"accompaniment")
    locked["targets"]["macos-arm64"]["tools"]["ffmpeg"]["sha256"] = hashlib.sha256(b"ffmpeg").hexdigest()
    locked["shared_files"]["spleeter-vocals"]["sha256"] = hashlib.sha256(b"vocals").hexdigest()
    locked["shared_files"]["spleeter-accompaniment"]["sha256"] = hashlib.sha256(b"accompaniment").hexdigest()

    staged = release_assets.stage_assets(
        locked,
        cache_dir=tmp_path / "cache",
        addon_bin_dir=tmp_path / "addon-bin",
        destination=tmp_path / "stage",
        target_keys=["macos-arm64"],
        tool_names=["ffmpeg"],
        include_shared=True,
    )

    assert tmp_path / "stage" / "models" / "spleeter-2stems-fp16" / "vocals.fp16.onnx" in staged
    assert tmp_path / "stage" / "models" / "spleeter-2stems-fp16" / "accompaniment.fp16.onnx" in staged


def test_lock_checksums_writes_present_binary_hashes(tmp_path: Path) -> None:
    lock_path = tmp_path / "release_assets.lock.json"
    lock = release_assets.load_lock()
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    binary = tmp_path / "cache" / "bin" / "macos-arm64" / "ffmpeg"
    dpdfnet_binary = tmp_path / "addon-bin" / "macos-arm64" / "dpdfnet"
    runtime_file = tmp_path / "addon-bin" / "macos-arm64" / "libonnxruntime.1.24.4.dylib"
    vocals = tmp_path / "addon-bin" / "models" / "spleeter-2stems-fp16" / "vocals.fp16.onnx"
    binary.parent.mkdir(parents=True)
    dpdfnet_binary.parent.mkdir(parents=True, exist_ok=True)
    vocals.parent.mkdir(parents=True)
    binary.write_bytes(b"ffmpeg")
    dpdfnet_binary.write_bytes(b"dpdfnet")
    runtime_file.write_bytes(b"onnxruntime")
    vocals.write_bytes(b"vocals")

    release_assets.lock_checksums(
        lock_path=lock_path,
        cache_dir=tmp_path / "cache",
        addon_bin_dir=tmp_path / "addon-bin",
    )

    updated = json.loads(lock_path.read_text(encoding="utf-8"))
    assert updated["targets"]["macos-arm64"]["tools"]["ffmpeg"]["sha256"] == hashlib.sha256(
        b"ffmpeg"
    ).hexdigest()
    assert updated["targets"]["macos-arm64"]["tools"]["dpdfnet"]["sha256"] == hashlib.sha256(
        b"dpdfnet"
    ).hexdigest()
    sherpa_files = updated["targets"]["macos-arm64"]["tools"]["sherpa-spleeter"]["runtime_files"]
    assert sherpa_files[0]["sha256"] == hashlib.sha256(b"onnxruntime").hexdigest()
    assert updated["shared_files"]["spleeter-vocals"]["sha256"] == hashlib.sha256(b"vocals").hexdigest()


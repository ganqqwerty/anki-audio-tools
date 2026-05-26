"""Tests for release archive file selection."""

from __future__ import annotations

import copy
import hashlib
import json
import zipfile
from pathlib import Path

import pytest
from scripts import release, release_asset_common, release_assets, release_runtime

FAKE_COMMIT_HASH = "a" * 40
FAKE_RELEASE_INFO = {
    "schema_version": 1,
    "commit_hash": FAKE_COMMIT_HASH,
    "commit_message": "Package release metadata",
}


def test_release_excludes_retained_pause_pipeline_artifacts() -> None:
    artifact_manifest = (
        release.ADDON_DIR
        / "aqe_artifacts"
        / "clip__20260517_010203_123456_deadbeef"
        / "manifest.json"
    )

    assert release._should_include(artifact_manifest) is False


def test_release_keeps_committed_config_json() -> None:
    assert release._should_include(release.ADDON_DIR / "config.json") is True


def _write_archive(
    path: Path,
    names: list[str],
    executable_names: set[str] | None = None,
    *,
    release_info: bytes | None = None,
    runtime_manifest: bytes | None = None,
) -> None:
    executable_names = executable_names or set()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in names:
            info = zipfile.ZipInfo(name)
            info.external_attr = ((0o755 if name in executable_names else 0o644) & 0xFFFF) << 16
            if name in executable_names:
                content = b"binary"
            elif name == "bin/THIRD_PARTY_NOTICES.md":
                content = b"FFmpeg LAME DeepFilterNet RNNoise DPDFNet Sherpa Spleeter Silero"
            elif name == "release_info.json":
                content = release_info or (json.dumps(FAKE_RELEASE_INFO) + "\n").encode()
            elif name == "bin/runtime_manifest.json":
                content = runtime_manifest or _runtime_manifest_bytes()
            else:
                content = b""
            zf.writestr(info, content)


def _complete_manifest_names() -> list[str]:
    return release.release_manifest_files(release_assets.load_lock())


def _complete_embedded_manifest_names() -> list[str]:
    return release.release_manifest_files(release_assets.load_lock(), embed_runtime=True)


def _complete_executable_names() -> set[str]:
    return set(release.release_runtime_executables(release_assets.load_lock()))


def _external_ffmpeg_manifest_names() -> list[str]:
    return release.release_manifest_files(release_assets.load_lock(), include_ffmpeg=False, embed_runtime=True)


def _external_ffmpeg_executable_names() -> set[str]:
    return set(release.release_runtime_executables(release_assets.load_lock(), include_ffmpeg=False))


def _lock_with_binary_hashes(content: bytes = b"binary") -> dict:
    lock = copy.deepcopy(release_assets.load_lock())
    digest = hashlib.sha256(content).hexdigest()
    for target in release_assets.lock_targets(lock):
        for tool_name in release_assets.lock_tools(lock, target):
            lock["targets"][target]["tools"][tool_name]["sha256"] = digest
    empty_digest = hashlib.sha256(b"").hexdigest()
    for target in release_assets.lock_targets(lock):
        for tool_name in release_assets.lock_tools(lock, target):
            for file_entry in release_assets.tool_runtime_files(lock, target, tool_name):
                file_entry["sha256"] = empty_digest
    for file_name in release_assets.lock_shared_files(lock):
        lock["shared_files"][file_name]["sha256"] = empty_digest
    return lock


def _runtime_manifest_bytes(lock: dict | None = None) -> bytes:
    lock = lock or _lock_with_binary_hashes()
    manifest = {
        "schema_version": 1,
        "runtime_manifest_id": "test-runtime",
        "targets": {},
        "shared_files": {},
    }
    for target in release_assets.lock_targets(lock):
        target_entry = {
            "runtime_pack": {
                "name": f"aqe-runtime-test-{target}.zip",
                "url": f"https://example.com/aqe-runtime-test-{target}.zip",
                "sha256": "f" * 64,
                "size": 1,
            },
            "tools": {},
            "shared_files": {},
        }
        for tool_name in release_assets.lock_tools(lock, target):
            tool_entry = lock["targets"][target]["tools"][tool_name]
            target_entry["tools"][tool_name] = {
                "executable": tool_entry["executable"],
                "path": f"{target}/{tool_entry['executable']}",
                "sha256": tool_entry["sha256"],
                "size": len(b"binary"),
                "executable_bit": not target.startswith("windows-"),
                "diagnostic_args": tool_entry.get("diagnostic_args"),
                "runtime_files": [
                    {
                        "path": file_entry["path"],
                        "sha256": file_entry["sha256"],
                        "size": 0,
                    }
                    for file_entry in release_assets.tool_runtime_files(lock, target, tool_name)
                ],
            }
        for file_name in release_assets.lock_shared_files(lock):
            shared_entry = lock["shared_files"][file_name]
            target_entry["shared_files"][file_name] = {
                "path": shared_entry["path"],
                "sha256": shared_entry["sha256"],
                "size": 0,
            }
        manifest["targets"][target] = target_entry
    for file_name in release_assets.lock_shared_files(lock):
        shared_entry = lock["shared_files"][file_name]
        manifest["shared_files"][file_name] = {
            "path": shared_entry["path"],
            "sha256": shared_entry["sha256"],
            "size": 0,
        }
    return (json.dumps(manifest) + "\n").encode()


def test_release_validates_required_frontend_bundles(tmp_path, capsys) -> None:
    archive = tmp_path / "missing-batch-css.ankiaddon"
    names = [name for name in _complete_manifest_names() if name != "templates/batch/batch_bundle.css"]
    _write_archive(archive, names, _complete_executable_names())

    with pytest.raises(SystemExit):
        release._validate_archive(archive, allow_large_archive=False, lock=_lock_with_binary_hashes())

    output = capsys.readouterr().out
    assert "templates/batch/batch_bundle.css" in output


def test_release_validates_generated_contracts(tmp_path, capsys) -> None:
    archive = tmp_path / "missing-contracts.ankiaddon"
    names = [name for name in _complete_manifest_names() if name != "contracts_generated.py"]
    _write_archive(archive, names, _complete_executable_names())

    with pytest.raises(SystemExit):
        release._validate_archive(archive, allow_large_archive=False, lock=_lock_with_binary_hashes())

    assert "contracts_generated.py" in capsys.readouterr().out


def test_release_validates_platform_runtime_payloads(tmp_path, capsys) -> None:
    archive = tmp_path / "missing-windows-ffmpeg.ankiaddon"
    names = [name for name in _complete_embedded_manifest_names() if name != "bin/windows-x86_64/ffmpeg.exe"]
    _write_archive(archive, names, _complete_executable_names())

    with pytest.raises(SystemExit):
        release._validate_archive(archive, allow_large_archive=False, lock=_lock_with_binary_hashes(), embed_runtime=True)

    assert "bin/windows-x86_64/ffmpeg.exe" in capsys.readouterr().out


def test_release_archive_includes_all_locked_runtime_assets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lock = _lock_with_binary_hashes()

    def fake_stage_assets(
        lock_arg: dict,
        *,
        destination: Path,
        target_keys: list[str] | None = None,
        include_ffmpeg: bool = True,
    ) -> list[Path]:
        staged: list[Path] = []
        for target in target_keys or release_assets.lock_targets(lock_arg):
            for tool_name in release_asset_common.bundled_tool_names(
                release_assets.lock_tools(lock_arg, target),
                include_ffmpeg=include_ffmpeg,
            ):
                executable = lock_arg["targets"][target]["tools"][tool_name]["executable"]
                path = destination / target / executable
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"binary")
                if target.startswith("macos-"):
                    path.chmod(0o755)
                staged.append(path)
                for file_entry in release_assets.tool_runtime_files(lock_arg, target, tool_name):
                    support_path = destination / target / file_entry["path"]
                    support_path.write_bytes(b"")
                    staged.append(support_path)
        for file_name in release_assets.lock_shared_files(lock_arg):
            path = destination / lock_arg["shared_files"][file_name]["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"")
            staged.append(path)
        return staged

    monkeypatch.setattr(release, "_stage_source_tree", lambda _staging_dir: None)
    monkeypatch.setattr(release, "_latest_commit_info", lambda: FAKE_RELEASE_INFO)
    monkeypatch.setattr(release.release_assets, "stage_assets", fake_stage_assets)
    monkeypatch.setattr(release, "DIST_DIR", tmp_path / "dist")

    staging_dir = tmp_path / "staging"
    release._stage_release_tree(staging_dir, lock=lock, embed_runtime=True)
    archive = release._build_archive("0.0.0-test", staging_dir)

    with zipfile.ZipFile(archive, "r") as zf:
        names = set(zf.namelist())

    expected = {
        "release_info.json",
        "bin/runtime_manifest.json",
        *release.release_runtime_shared_files(lock),
        *release.release_runtime_executables(lock),
        *release.release_runtime_support_files(lock),
    }
    assert expected <= names


def test_release_archive_includes_latest_commit_info(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(release, "_stage_source_tree", lambda _staging_dir: None)
    monkeypatch.setattr(release, "_latest_commit_info", lambda: FAKE_RELEASE_INFO)
    monkeypatch.setattr(release.release_assets, "stage_assets", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(release, "DIST_DIR", tmp_path / "dist")

    staging_dir = tmp_path / "staging"
    release._stage_release_tree(
        staging_dir,
        lock=release_assets.load_lock(),
        target_keys=["macos-arm64"],
        include_ffmpeg=False,
    )
    archive = release._build_archive("0.0.0-test", staging_dir)

    with zipfile.ZipFile(archive, "r") as zf:
        release_info = json.loads(zf.read("release_info.json").decode())

    assert release_info == FAKE_RELEASE_INFO


def test_release_validation_requires_every_locked_runtime_asset(tmp_path, capsys) -> None:
    lock = _lock_with_binary_hashes()
    required_runtime_names = [
        *release.release_runtime_shared_files(lock),
        *release.release_runtime_executables(lock),
        *release.release_runtime_support_files(lock),
    ]

    for missing_name in required_runtime_names:
        archive = tmp_path / f"{missing_name.replace('/', '_')}.ankiaddon"
        names = [name for name in release.release_manifest_files(lock, embed_runtime=True) if name != missing_name]
        _write_archive(archive, names, _complete_executable_names())

        with pytest.raises(SystemExit):
            release._validate_archive(archive, allow_large_archive=False, lock=lock, embed_runtime=True)

        assert missing_name in capsys.readouterr().out


def test_release_validates_macos_executable_bits(tmp_path, capsys) -> None:
    archive = tmp_path / "bad-mode.ankiaddon"
    executable_names = _complete_executable_names() - {"bin/macos-arm64/ffmpeg"}
    _write_archive(archive, _complete_embedded_manifest_names(), executable_names)

    with pytest.raises(SystemExit):
        release._validate_archive(archive, allow_large_archive=False, lock=_lock_with_binary_hashes(), embed_runtime=True)

    assert "executable mode" in capsys.readouterr().out


def test_release_rejects_local_artifacts_and_macos_junk(tmp_path, capsys) -> None:
    archive = tmp_path / "junk.ankiaddon"
    names = [*_complete_manifest_names(), ".DS_Store"]
    _write_archive(archive, names, _complete_executable_names())

    with pytest.raises(SystemExit):
        release._validate_archive(archive, allow_large_archive=False, lock=_lock_with_binary_hashes())

    assert ".DS_Store" in capsys.readouterr().out


def test_release_validates_runtime_payload_checksums_even_before_release_ready(tmp_path, capsys) -> None:
    archive = tmp_path / "bad-checksum.ankiaddon"
    lock = _lock_with_binary_hashes(b"expected")
    _write_archive(archive, _complete_embedded_manifest_names(), _complete_executable_names())

    with pytest.raises(SystemExit):
        release._validate_archive(archive, allow_large_archive=False, lock=lock, embed_runtime=True)

    assert "checksum mismatch" in capsys.readouterr().out


def test_release_requires_runtime_payload_checksums(tmp_path, capsys) -> None:
    archive = tmp_path / "missing-checksum.ankiaddon"
    lock = _lock_with_binary_hashes()
    lock["targets"]["macos-arm64"]["tools"]["ffmpeg"].pop("sha256")
    _write_archive(archive, _complete_embedded_manifest_names(), _complete_executable_names())

    with pytest.raises(SystemExit):
        release._validate_archive(archive, allow_large_archive=False, lock=lock, embed_runtime=True)

    output = capsys.readouterr().out
    assert "bin/macos-arm64/ffmpeg" in output
    assert "missing sha256" in output


def test_release_validation_requires_valid_release_info(tmp_path: Path, capsys) -> None:
    archive = tmp_path / "bad-release-info.ankiaddon"
    invalid_release_info = json.dumps(
        {
            "schema_version": 1,
            "commit_hash": FAKE_COMMIT_HASH,
        }
    ).encode()
    _write_archive(
        archive,
        _complete_manifest_names(),
        _complete_executable_names(),
        release_info=invalid_release_info,
    )

    with pytest.raises(SystemExit):
        release._validate_archive(archive, allow_large_archive=False, lock=_lock_with_binary_hashes())

    assert "commit_message" in capsys.readouterr().out


def test_release_manifest_files_can_be_limited_to_single_runtime_target() -> None:
    names = release.release_manifest_files(
        release_assets.load_lock(),
        target_keys=["macos-arm64"],
        embed_runtime=True,
    )

    assert "bin/macos-arm64/ffmpeg" in names
    assert "bin/macos-arm64/silero-vad" in names
    assert "bin/macos-arm64/libonnxruntime.1.24.4.dylib" in names
    assert "bin/models/spleeter-2stems-fp16/vocals.fp16.onnx" in names
    assert "bin/models/silero-vad/silero_vad.onnx" in names
    assert "bin/windows-x86_64/ffmpeg.exe" not in names
    assert "bin/windows-x86_64/onnxruntime.dll" not in names


def test_release_manifest_files_default_to_thin_archive() -> None:
    names = release.release_manifest_files(
        release_assets.load_lock(),
        target_keys=["macos-arm64"],
    )

    assert "bin/runtime_manifest.json" in names
    assert "bin/macos-arm64/ffmpeg" not in names
    assert "bin/macos-arm64/libonnxruntime.1.24.4.dylib" not in names
    assert "bin/models/spleeter-2stems-fp16/vocals.fp16.onnx" not in names
    assert "bin/models/silero-vad/silero_vad.onnx" not in names


def test_release_manifest_files_can_exclude_ffmpeg_tools() -> None:
    names = release.release_manifest_files(
        release_assets.load_lock(),
        target_keys=["macos-arm64"],
        include_ffmpeg=False,
        embed_runtime=True,
    )

    assert "bin/macos-arm64/ffmpeg" not in names
    assert "bin/macos-arm64/ffprobe" not in names
    assert "bin/macos-arm64/deep-filter" in names
    assert "bin/macos-arm64/silero-vad" in names
    assert "bin/macos-arm64/libonnxruntime.1.24.4.dylib" in names
    assert "bin/models/spleeter-2stems-fp16/vocals.fp16.onnx" in names
    assert "bin/models/silero-vad/silero_vad.onnx" in names


def test_thin_release_validation_rejects_embedded_runtime_payload(tmp_path: Path, capsys) -> None:
    archive = tmp_path / "thin-with-runtime.ankiaddon"
    names = [*_complete_manifest_names(), "bin/macos-arm64/ffmpeg"]
    _write_archive(archive, names, {"bin/macos-arm64/ffmpeg"})

    with pytest.raises(SystemExit):
        release._validate_archive(archive, allow_large_archive=False, lock=_lock_with_binary_hashes())

    output = capsys.readouterr().out
    assert "thin archive embeds runtime payload" in output
    assert "bin/macos-arm64/ffmpeg" in output


def test_runtime_manifest_can_be_limited_to_single_runtime_target(tmp_path) -> None:
    lock = release_assets.load_lock()

    release._write_runtime_manifest(tmp_path, lock, target_keys=["windows-x86_64"])

    manifest = json.loads((tmp_path / "runtime_manifest.json").read_text(encoding="utf-8"))
    assert list(manifest["targets"]) == ["windows-x86_64"]
    assert manifest["targets"]["windows-x86_64"]["tools"]["sherpa-spleeter"]["runtime_files"]
    assert manifest["targets"]["windows-x86_64"]["tools"]["silero-vad"]["runtime_files"]
    assert manifest["shared_files"]["spleeter-vocals"]["path"] == "models/spleeter-2stems-fp16/vocals.fp16.onnx"
    assert manifest["shared_files"]["silero-vad-model"]["path"] == "models/silero-vad/silero_vad.onnx"


def test_runtime_manifest_can_exclude_ffmpeg_tools(tmp_path: Path) -> None:
    lock = release_assets.load_lock()

    release._write_runtime_manifest(tmp_path, lock, target_keys=["macos-arm64"], include_ffmpeg=False)

    manifest = json.loads((tmp_path / "runtime_manifest.json").read_text(encoding="utf-8"))
    assert "ffmpeg" not in manifest["targets"]["macos-arm64"]["tools"]
    assert "ffprobe" not in manifest["targets"]["macos-arm64"]["tools"]
    assert "deep-filter" in manifest["targets"]["macos-arm64"]["tools"]


def test_runtime_manifest_includes_locked_diagnostic_args(tmp_path) -> None:
    lock = release_assets.load_lock()

    release._write_runtime_manifest(tmp_path, lock, target_keys=["macos-arm64"])

    manifest = json.loads((tmp_path / "runtime_manifest.json").read_text(encoding="utf-8"))
    assert manifest["targets"]["macos-arm64"]["tools"]["ffmpeg"]["diagnostic_args"] == ["-version"]
    assert manifest["targets"]["macos-arm64"]["tools"]["silero-vad"]["diagnostic_args"] == ["--help"]


def test_runtime_pack_entries_deduplicate_shared_onnxruntime_support_files() -> None:
    lock = release_assets.load_lock()

    entries = release_runtime._runtime_pack_entries(
        lock,
        "macos-arm64",
        source_bin_dir=release.ADDON_DIR / "bin",
        include_ffmpeg=False,
    )
    paths = [entry["path"] for entry in entries]

    assert paths.count("macos-arm64/libonnxruntime.1.24.4.dylib") == 1


def test_release_validation_can_exclude_ffmpeg_runtime_payloads(tmp_path: Path) -> None:
    archive = tmp_path / "external-ffmpeg.ankiaddon"
    lock = _lock_with_binary_hashes()
    _write_archive(archive, _external_ffmpeg_manifest_names(), _external_ffmpeg_executable_names())

    release._validate_archive(archive, allow_large_archive=False, lock=lock, include_ffmpeg=False, embed_runtime=True)


def test_release_archive_name_marks_external_ffmpeg_variant(tmp_path: Path) -> None:
    monkeypatch_dist = tmp_path / "dist"
    original = release.DIST_DIR
    release.DIST_DIR = monkeypatch_dist
    try:
        archive = release._build_archive("1.2.3", tmp_path, target_label="macos-arm64", include_ffmpeg=False)
    finally:
        release.DIST_DIR = original

    assert archive.name == "anki-audio-quick-editor-1.2.3-macos-arm64-external-ffmpeg.ankiaddon"

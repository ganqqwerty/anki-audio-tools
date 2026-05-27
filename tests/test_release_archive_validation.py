"""Tests for release archive staging and validation."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest
from scripts import release, release_archive, release_asset_common, release_assets

from tests.release_archive_fixtures import (
    FAKE_COMMIT_HASH,
    FAKE_RELEASE_INFO,
    complete_embedded_manifest_names,
    complete_executable_names,
    complete_manifest_names,
    external_ffmpeg_executable_names,
    external_ffmpeg_manifest_names,
    lock_with_binary_hashes,
    write_archive,
)


def test_release_validates_required_frontend_bundles(tmp_path, capsys) -> None:
    archive = tmp_path / "missing-batch-css.ankiaddon"
    names = [name for name in complete_manifest_names() if name != "templates/batch/batch_bundle.css"]
    write_archive(archive, names, complete_executable_names())

    with pytest.raises(SystemExit):
        release_archive.validate_archive(archive, allow_large_archive=False, lock=lock_with_binary_hashes())

    assert "templates/batch/batch_bundle.css" in capsys.readouterr().out


def test_release_validates_generated_contracts(tmp_path, capsys) -> None:
    archive = tmp_path / "missing-contracts.ankiaddon"
    names = [name for name in complete_manifest_names() if name != "contracts_generated.py"]
    write_archive(archive, names, complete_executable_names())

    with pytest.raises(SystemExit):
        release_archive.validate_archive(archive, allow_large_archive=False, lock=lock_with_binary_hashes())

    assert "contracts_generated.py" in capsys.readouterr().out


def test_release_validates_platform_runtime_payloads(tmp_path, capsys) -> None:
    archive = tmp_path / "missing-windows-ffmpeg.ankiaddon"
    names = [name for name in complete_embedded_manifest_names() if name != "bin/windows-x86_64/ffmpeg.exe"]
    write_archive(archive, names, complete_executable_names())

    with pytest.raises(SystemExit):
        release_archive.validate_archive(
            archive,
            allow_large_archive=False,
            lock=lock_with_binary_hashes(),
            embed_runtime=True,
        )

    assert "bin/windows-x86_64/ffmpeg.exe" in capsys.readouterr().out


def test_release_archive_includes_all_locked_runtime_assets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    lock = lock_with_binary_hashes()

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

    monkeypatch.setattr(release_archive, "stage_source_tree", lambda _staging_dir: None)
    monkeypatch.setattr(release_archive, "latest_commit_info", lambda: FAKE_RELEASE_INFO)
    monkeypatch.setattr(release_archive.release_assets, "stage_assets", fake_stage_assets)
    monkeypatch.setattr(release_archive, "DIST_DIR", tmp_path / "dist")

    staging_dir = tmp_path / "staging"
    release_archive.stage_release_tree(staging_dir, lock=lock, embed_runtime=True)
    archive = release_archive.build_archive("0.0.0-test", staging_dir)

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


def test_release_archive_includes_latest_commit_info(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(release_archive, "stage_source_tree", lambda _staging_dir: None)
    monkeypatch.setattr(release_archive, "latest_commit_info", lambda: FAKE_RELEASE_INFO)
    monkeypatch.setattr(release_archive.release_assets, "stage_assets", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(release_archive, "DIST_DIR", tmp_path / "dist")

    staging_dir = tmp_path / "staging"
    release_archive.stage_release_tree(
        staging_dir,
        lock=release_assets.load_lock(),
        target_keys=["macos-arm64"],
        include_ffmpeg=False,
    )
    archive = release_archive.build_archive("0.0.0-test", staging_dir)

    with zipfile.ZipFile(archive, "r") as zf:
        release_info = json.loads(zf.read("release_info.json").decode())

    assert release_info == FAKE_RELEASE_INFO


def test_release_validation_requires_every_locked_runtime_asset(tmp_path, capsys) -> None:
    lock = lock_with_binary_hashes()
    required_runtime_names = [
        *release.release_runtime_shared_files(lock),
        *release.release_runtime_executables(lock),
        *release.release_runtime_support_files(lock),
    ]

    for missing_name in required_runtime_names:
        archive = tmp_path / f"{missing_name.replace('/', '_')}.ankiaddon"
        names = [name for name in release.release_manifest_files(lock, embed_runtime=True) if name != missing_name]
        write_archive(archive, names, complete_executable_names())

        with pytest.raises(SystemExit):
            release_archive.validate_archive(archive, allow_large_archive=False, lock=lock, embed_runtime=True)

        assert missing_name in capsys.readouterr().out


def test_release_validates_macos_executable_bits(tmp_path, capsys) -> None:
    archive = tmp_path / "bad-mode.ankiaddon"
    executable_names = complete_executable_names() - {"bin/macos-arm64/ffmpeg"}
    write_archive(archive, complete_embedded_manifest_names(), executable_names)

    with pytest.raises(SystemExit):
        release_archive.validate_archive(
            archive,
            allow_large_archive=False,
            lock=lock_with_binary_hashes(),
            embed_runtime=True,
        )

    assert "executable mode" in capsys.readouterr().out


def test_release_rejects_local_artifacts_and_macos_junk(tmp_path, capsys) -> None:
    archive = tmp_path / "junk.ankiaddon"
    names = [*complete_manifest_names(), ".DS_Store"]
    write_archive(archive, names, complete_executable_names())

    with pytest.raises(SystemExit):
        release_archive.validate_archive(archive, allow_large_archive=False, lock=lock_with_binary_hashes())

    assert ".DS_Store" in capsys.readouterr().out


def test_release_validates_runtime_payload_checksums_even_before_release_ready(tmp_path, capsys) -> None:
    archive = tmp_path / "bad-checksum.ankiaddon"
    lock = lock_with_binary_hashes(b"expected")
    write_archive(archive, complete_embedded_manifest_names(), complete_executable_names())

    with pytest.raises(SystemExit):
        release_archive.validate_archive(archive, allow_large_archive=False, lock=lock, embed_runtime=True)

    assert "checksum mismatch" in capsys.readouterr().out


def test_release_requires_runtime_payload_checksums(tmp_path, capsys) -> None:
    archive = tmp_path / "missing-checksum.ankiaddon"
    lock = lock_with_binary_hashes()
    lock["targets"]["macos-arm64"]["tools"]["ffmpeg"].pop("sha256")
    write_archive(archive, complete_embedded_manifest_names(), complete_executable_names())

    with pytest.raises(SystemExit):
        release_archive.validate_archive(archive, allow_large_archive=False, lock=lock, embed_runtime=True)

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
    write_archive(
        archive,
        complete_manifest_names(),
        complete_executable_names(),
        release_info=invalid_release_info,
    )

    with pytest.raises(SystemExit):
        release_archive.validate_archive(archive, allow_large_archive=False, lock=lock_with_binary_hashes())

    assert "commit_message" in capsys.readouterr().out


def test_thin_release_validation_rejects_embedded_runtime_payload(tmp_path: Path, capsys) -> None:
    archive = tmp_path / "thin-with-runtime.ankiaddon"
    names = [*complete_manifest_names(), "bin/macos-arm64/ffmpeg"]
    write_archive(archive, names, {"bin/macos-arm64/ffmpeg"})

    with pytest.raises(SystemExit):
        release_archive.validate_archive(archive, allow_large_archive=False, lock=lock_with_binary_hashes())

    output = capsys.readouterr().out
    assert "thin archive embeds runtime payload" in output
    assert "bin/macos-arm64/ffmpeg" in output


def test_release_validation_can_exclude_ffmpeg_runtime_payloads(tmp_path: Path) -> None:
    archive = tmp_path / "external-ffmpeg.ankiaddon"
    lock = lock_with_binary_hashes()
    write_archive(archive, external_ffmpeg_manifest_names(), external_ffmpeg_executable_names())

    release_archive.validate_archive(
        archive,
        allow_large_archive=False,
        lock=lock,
        include_ffmpeg=False,
        embed_runtime=True,
    )

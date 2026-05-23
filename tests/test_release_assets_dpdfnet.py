from __future__ import annotations

import copy
import hashlib
import stat
from pathlib import Path

import pytest
from scripts import release_assets


def test_stage_copies_macos_arm64_dpdfnet_binary(tmp_path: Path) -> None:
    lock = release_assets.load_lock()
    locked = copy.deepcopy(lock)
    binary = tmp_path / "cache" / "bin" / "macos-arm64" / "dpdfnet"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"dpdfnet")
    locked["targets"]["macos-arm64"]["tools"]["dpdfnet"]["sha256"] = hashlib.sha256(
        b"dpdfnet"
    ).hexdigest()

    staged = release_assets.stage_assets(
        locked,
        cache_dir=tmp_path / "cache",
        destination=tmp_path / "stage",
        target_keys=["macos-arm64"],
        tool_names=["dpdfnet"],
    )

    assert staged == [tmp_path / "stage" / "macos-arm64" / "dpdfnet"]
    assert staged[0].read_bytes() == b"dpdfnet"
    assert staged[0].stat().st_mode & stat.S_IXUSR


def test_stage_copies_windows_dpdfnet_binary(tmp_path: Path) -> None:
    lock = release_assets.load_lock()
    locked = copy.deepcopy(lock)
    binary = tmp_path / "cache" / "bin" / "windows-x86_64" / "dpdfnet.exe"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"dpdfnet.exe")
    locked["targets"]["windows-x86_64"]["tools"]["dpdfnet"]["sha256"] = hashlib.sha256(
        b"dpdfnet.exe"
    ).hexdigest()

    staged = release_assets.stage_assets(
        locked,
        cache_dir=tmp_path / "cache",
        destination=tmp_path / "stage",
        target_keys=["windows-x86_64"],
        tool_names=["dpdfnet"],
    )

    assert staged == [tmp_path / "stage" / "windows-x86_64" / "dpdfnet.exe"]
    assert staged[0].read_bytes() == b"dpdfnet.exe"


def test_stage_cli_accepts_dpdfnet_tool_filter(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_stage_assets(
        lock,
        *,
        destination: Path,
        target_keys: list[str] | None = None,
        tool_names: list[str] | None = None,
    ) -> list[Path]:
        calls.append(
            {
                "lock": lock,
                "destination": destination,
                "target_keys": target_keys,
                "tool_names": tool_names,
            }
        )
        return [destination / "macos-arm64" / "dpdfnet"]

    monkeypatch.setattr(release_assets, "load_lock", lambda: {"lock": True})
    monkeypatch.setattr(release_assets, "stage_assets", fake_stage_assets)

    assert (
        release_assets.main(
            [
                "stage",
                "--target",
                "macos-arm64",
                "--tool",
                "dpdfnet",
                "--destination",
                str(tmp_path),
            ]
        )
        == 0
    )
    assert calls == [
        {
            "lock": {"lock": True},
            "destination": tmp_path,
            "target_keys": ["macos-arm64"],
            "tool_names": ["dpdfnet"],
        }
    ]

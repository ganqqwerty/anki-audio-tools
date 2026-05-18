from __future__ import annotations

import json
import stat
import zipfile
from pathlib import Path

import pytest
from scripts import release_acceptance, release_assets


def _write_acceptance_archive(
    path: Path,
    *,
    target: str,
    tools: dict[str, tuple[str, bytes | None]],
) -> None:
    manifest = {
        "schema_version": 1,
        "targets": {
            target: {
                "tools": {
                    tool_name: {
                        "executable": executable,
                        "diagnostic_args": ["--version"],
                    }
                    for tool_name, (executable, _content) in tools.items()
                }
            }
        },
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("bin/runtime_manifest.json", json.dumps(manifest))
        for _tool_name, (executable, content) in tools.items():
            if content is None:
                continue
            info = zipfile.ZipInfo(f"bin/{target}/{executable}")
            info.create_system = 3
            info.external_attr = (stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR) << 16
            zf.writestr(info, content)


def _tool_matrix(script: bytes | None) -> dict[str, tuple[str, bytes | None]]:
    return {
        "ffmpeg": ("ffmpeg", script),
        "ffprobe": ("ffprobe", script),
        "deep-filter": ("deep-filter", script),
        "rnnoise-cli": ("rnnoise-cli", script),
    }


def test_acceptance_fails_when_runtime_tool_is_missing(tmp_path: Path, monkeypatch) -> None:
    target = "macos-arm64"
    archive = tmp_path / "missing-tool.ankiaddon"
    tools = _tool_matrix(b"#!/bin/sh\nexit 0\n")
    tools["ffmpeg"] = ("ffmpeg", None)
    _write_acceptance_archive(archive, target=target, tools=tools)
    monkeypatch.setattr(release_assets, "current_target_key", lambda: target)
    monkeypatch.setattr(release_acceptance, "ROOT", tmp_path)
    monkeypatch.setattr(release_acceptance, "_version", lambda: "0.1.0")

    with pytest.raises(release_acceptance.ReleaseAcceptanceError, match="ffmpeg.*missing"):
        release_acceptance.accept_archive(archive, "current")


def test_acceptance_fails_when_runtime_tool_diagnostic_fails(tmp_path: Path, monkeypatch) -> None:
    target = "macos-arm64"
    archive = tmp_path / "bad-diagnostic.ankiaddon"
    _write_acceptance_archive(
        archive,
        target=target,
        tools=_tool_matrix(b"#!/bin/sh\necho broken >&2\nexit 42\n"),
    )
    monkeypatch.setattr(release_assets, "current_target_key", lambda: target)
    monkeypatch.setattr(release_acceptance, "ROOT", tmp_path)
    monkeypatch.setattr(release_acceptance, "_version", lambda: "0.1.0")

    with pytest.raises(release_acceptance.ReleaseAcceptanceError, match="diagnostic failed"):
        release_acceptance.accept_archive(archive, "current")


def test_acceptance_writes_report_when_runtime_tools_pass(tmp_path: Path, monkeypatch) -> None:
    target = "macos-arm64"
    archive = tmp_path / "passing.ankiaddon"
    _write_acceptance_archive(
        archive,
        target=target,
        tools=_tool_matrix(b"#!/bin/sh\necho ok\nexit 0\n"),
    )
    monkeypatch.setattr(release_assets, "current_target_key", lambda: target)
    monkeypatch.setattr(release_acceptance, "ROOT", tmp_path)
    monkeypatch.setattr(release_acceptance, "_version", lambda: "0.1.0")

    report_path = release_acceptance.accept_archive(archive, "current")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["target"] == target
    assert report["status"] == "passed"
    assert set(report["tools"]) == {"ffmpeg", "ffprobe", "deep-filter", "rnnoise-cli"}


def test_version_reads_pyproject_without_runtime_tomllib(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '\n[project]\nname = "anki-audio-quick-editor"\nversion = "1.2.3"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(release_acceptance, "ROOT", tmp_path)

    assert release_acceptance._version() == "1.2.3"

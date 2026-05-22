from __future__ import annotations

from pathlib import Path

import pytest

from anki_audio_quick_editor.audio_processor import find_dpdfnet_bundle
from anki_audio_quick_editor.errors import MissingDpdfnetError


def test_find_dpdfnet_bundle_uses_bundled_executable_when_complete(
    tmp_path: Path,
    monkeypatch,
) -> None:
    dpdfnet_path = tmp_path / "bin" / "macos-arm64" / "dpdfnet"
    dpdfnet_path.parent.mkdir(parents=True)
    dpdfnet_path.write_text("")

    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_tools.expected_bundled_tool_path",
        lambda tool_name: dpdfnet_path if tool_name == "dpdfnet" else None,
    )

    assert find_dpdfnet_bundle() == dpdfnet_path


def test_find_dpdfnet_bundle_reports_unsupported_platform(monkeypatch) -> None:
    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_tools.expected_bundled_tool_path",
        lambda tool_name: None,
    )
    monkeypatch.setattr("anki_audio_quick_editor.audio_tools.platform_description", lambda: "Linux x86_64")

    with pytest.raises(MissingDpdfnetError, match="DPDFNet is not bundled for Linux x86_64"):
        find_dpdfnet_bundle()


def test_find_dpdfnet_bundle_raises_when_bundle_is_incomplete(
    tmp_path: Path,
    monkeypatch,
) -> None:
    expected_path = tmp_path / "bin" / "macos-arm64" / "dpdfnet"
    expected_path.parent.mkdir(parents=True)

    monkeypatch.setattr(
        "anki_audio_quick_editor.audio_tools.expected_bundled_tool_path",
        lambda tool_name: expected_path if tool_name == "dpdfnet" else None,
    )

    with pytest.raises(MissingDpdfnetError, match="bundled dpdfnet executable"):
        find_dpdfnet_bundle()

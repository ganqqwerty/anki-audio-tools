"""Tests for release archive file selection."""

from __future__ import annotations

import zipfile

import pytest
from scripts import release


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


def test_release_validates_required_frontend_bundles(tmp_path, capsys) -> None:
    archive = tmp_path / "missing-editor-css.ankiaddon"
    names = [
        name
        for name in release.REQUIRED_ARCHIVE_FILES
        if name != "templates/editor/editor_bundle.css"
    ]
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in names:
            zf.writestr(name, "")

    with pytest.raises(SystemExit):
        release._validate_archive(archive)

    output = capsys.readouterr().out
    assert "templates/editor/editor_bundle.css" in output

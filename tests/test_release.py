"""Tests for release archive file selection."""

from __future__ import annotations

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

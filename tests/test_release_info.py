"""Tests for packaged release provenance helpers."""

from __future__ import annotations

import json
from pathlib import Path

from anki_audio_quick_editor.release_info import empty_release_info, read_release_info


def test_read_release_info_returns_packaged_commit_metadata(tmp_path: Path) -> None:
    (tmp_path / "release_info.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "commit_hash": "a" * 40,
                "commit_message": "Package release metadata",
            }
        ),
        encoding="utf-8",
    )

    assert read_release_info(tmp_path) == {
        "commit_hash": "a" * 40,
        "commit_message": "Package release metadata",
    }


def test_read_release_info_returns_empty_shape_when_missing(tmp_path: Path) -> None:
    assert read_release_info(tmp_path) == empty_release_info()


def test_read_release_info_returns_empty_shape_for_invalid_json(tmp_path: Path) -> None:
    (tmp_path / "release_info.json").write_text("not-json", encoding="utf-8")

    assert read_release_info(tmp_path) == empty_release_info()

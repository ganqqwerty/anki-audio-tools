from __future__ import annotations

import json
from pathlib import Path

import pytest
from scripts import release


def _write_version_files(
    root: Path,
    *,
    pyproject_version: str,
    package_version: str,
    manifest_version: str,
) -> Path:
    addon_dir = root / "addon" / "anki_audio_quick_editor"
    addon_dir.mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        f'[project]\nname = "anki-audio-quick-editor"\nversion = "{pyproject_version}"\n',
        encoding="utf-8",
    )
    (addon_dir / "_version.py").write_text(
        f'"""Version metadata for Anki Audio Quick Editor."""\n\n__version__ = "{package_version}"\n',
        encoding="utf-8",
    )
    (addon_dir / "manifest.json").write_text(
        json.dumps(
            {
                "package": "anki_audio_quick_editor",
                "name": "Anki Audio Quick Editor",
                "human_version": manifest_version,
                "min_point_version": 250900,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return addon_dir


def test_release_version_guard_accepts_matching_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    addon_dir = _write_version_files(
        tmp_path,
        pyproject_version="1.2",
        package_version="1.2",
        manifest_version="1.2",
    )
    monkeypatch.setattr(release, "ROOT", tmp_path)
    monkeypatch.setattr(release, "ADDON_DIR", addon_dir)

    release._verify_versions("1.2")

    assert capsys.readouterr().out == ""


def test_release_version_guard_rejects_stale_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    addon_dir = _write_version_files(
        tmp_path,
        pyproject_version="1.2",
        package_version="1.2",
        manifest_version="1.1",
    )
    monkeypatch.setattr(release, "ROOT", tmp_path)
    monkeypatch.setattr(release, "ADDON_DIR", addon_dir)

    with pytest.raises(SystemExit):
        release._verify_versions("1.2")

    output = capsys.readouterr().out
    assert "version mismatch" in output
    assert "manifest='1.1'" in output

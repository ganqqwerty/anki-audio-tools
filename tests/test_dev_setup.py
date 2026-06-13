from __future__ import annotations

from pathlib import Path

from scripts.dev_tasks import setup


def test_setup_keeps_existing_frontend_deps_when_npm_missing(monkeypatch, tmp_path: Path, capsys) -> None:
    settings_ui = tmp_path / "settings_ui"
    (settings_ui / "node_modules").mkdir(parents=True)

    monkeypatch.setattr(setup, "SETTINGS_UI_DIR", settings_ui)
    monkeypatch.setattr(setup, "_find_anki_python", lambda: Path("/anki/python"))
    monkeypatch.setattr(setup, "_setup_addon_symlink", lambda: None)
    monkeypatch.setattr(setup, "find_npm_install_command", lambda: None)
    monkeypatch.setattr(setup, "_run", lambda *_args, **_kwargs: 0)

    assert setup.cmd_setup() == 0
    output = capsys.readouterr().out
    assert "keeping existing settings_ui/node_modules" in output


def test_setup_fails_when_npm_missing_and_frontend_deps_are_absent(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    settings_ui = tmp_path / "settings_ui"
    settings_ui.mkdir()

    monkeypatch.setattr(setup, "SETTINGS_UI_DIR", settings_ui)
    monkeypatch.setattr(setup, "_find_anki_python", lambda: Path("/anki/python"))
    monkeypatch.setattr(setup, "_setup_addon_symlink", lambda: None)
    monkeypatch.setattr(setup, "find_npm_install_command", lambda: None)
    monkeypatch.setattr(setup, "_run", lambda *_args, **_kwargs: 0)

    assert setup.cmd_setup() == 1
    error = capsys.readouterr().err
    assert "npm not found and settings_ui/node_modules is missing" in error

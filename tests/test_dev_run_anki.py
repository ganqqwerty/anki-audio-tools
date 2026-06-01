from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from scripts.dev_scripts import anki
from scripts.dev_tasks import python_env


def test_cmd_run_anki_builds_links_and_launches(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(anki, "cmd_build_ui", lambda: calls.append("build") or 0)
    monkeypatch.setattr(anki, "cmd_link_addon", lambda: calls.append("link") or 0)
    monkeypatch.setattr(anki, "cmd_launch_anki", lambda: calls.append("launch") or 0)

    assert anki.cmd_run_anki([]) == 0
    assert calls == ["build", "link", "launch"]


def test_cmd_run_anki_stops_when_build_fails(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(anki, "cmd_build_ui", lambda: calls.append("build") or 7)
    monkeypatch.setattr(anki, "cmd_link_addon", lambda: calls.append("link") or 0)
    monkeypatch.setattr(anki, "cmd_launch_anki", lambda: calls.append("launch") or 0)

    assert anki.cmd_run_anki([]) == 7
    assert calls == ["build"]


def test_cmd_run_anki_stops_when_link_fails(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(anki, "cmd_build_ui", lambda: calls.append("build") or 0)
    monkeypatch.setattr(anki, "cmd_link_addon", lambda: calls.append("link") or 8)
    monkeypatch.setattr(anki, "cmd_launch_anki", lambda: calls.append("launch") or 0)

    assert anki.cmd_run_anki([]) == 8
    assert calls == ["build", "link"]


def test_cmd_launch_anki_uses_launchservices_on_macos(monkeypatch, tmp_path) -> None:
    app = tmp_path / "Anki.app"
    app.mkdir()
    calls: list[tuple[list[str], bool]] = []

    def fake_run(command: list[str], *, check: bool) -> SimpleNamespace:
        calls.append((command, check))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(python_env.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(python_env, "MACOS_ANKI_APP_PATH", app)
    monkeypatch.setattr(python_env.subprocess, "run", fake_run)

    assert python_env.cmd_launch_anki() == 0
    assert calls == [(["open", "-a", str(app)], False)]


def test_cmd_launch_anki_starts_anki_python_on_non_macos(monkeypatch) -> None:
    calls: list[list[str]] = []

    class FakePopen:
        def __init__(self, command: list[str]) -> None:
            calls.append(command)

    monkeypatch.setattr(python_env.platform, "system", lambda: "Linux")
    monkeypatch.setattr(python_env, "_find_anki_python", lambda: Path("/opt/anki/python"))
    monkeypatch.setattr(python_env.subprocess, "Popen", FakePopen)

    assert python_env.cmd_launch_anki() == 0
    assert calls == [["/opt/anki/python", "-c", python_env.ANKI_PYTHON_LAUNCHER]]


def test_cmd_launch_anki_reports_launch_failure(monkeypatch, capsys) -> None:
    def fake_run(_command: list[str], *, check: bool) -> SimpleNamespace:
        assert check is False
        return SimpleNamespace(returncode=3)

    monkeypatch.setattr(python_env.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(python_env.subprocess, "run", fake_run)

    assert python_env.cmd_launch_anki() == 3
    assert "Anki launcher failed with exit code 3" in capsys.readouterr().err

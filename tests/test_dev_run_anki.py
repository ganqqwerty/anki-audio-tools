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


def test_candidate_paths_keep_macos_anki_program_files_location(monkeypatch) -> None:
    monkeypatch.setattr(python_env.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(python_env.Path, "home", lambda: Path("/Users/tester"))

    assert python_env._candidate_path_segments() == [
        (
            "/Users/tester",
            "Library",
            "Application Support",
            "AnkiProgramFiles",
            ".venv",
            "bin",
            "python3",
        )
    ]


def test_candidate_paths_prefer_windows_local_appdata(monkeypatch) -> None:
    monkeypatch.setattr(python_env.platform, "system", lambda: "Windows")
    monkeypatch.setenv("LOCALAPPDATA", r"C:\Users\tester\AppData\Local")
    monkeypatch.setenv("APPDATA", r"C:\Users\tester\AppData\Roaming")

    segments = python_env._candidate_path_segments()
    rendered_paths = [python_env._render_candidate_path(path_segments, system="Windows") for path_segments in segments]

    assert segments == [
        (r"C:\Users\tester\AppData\Local", "AnkiProgramFiles", ".venv", "Scripts", "python.exe"),
        (r"C:\Users\tester\AppData\Roaming", "AnkiProgramFiles", ".venv", "Scripts", "python.exe"),
    ]
    assert rendered_paths == [
        r"C:\Users\tester\AppData\Local\AnkiProgramFiles\.venv\Scripts\python.exe",
        r"C:\Users\tester\AppData\Roaming\AnkiProgramFiles\.venv\Scripts\python.exe",
    ]


def test_explicit_anki_python_accepts_runnable_path_command(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(
        command: list[str],
        *,
        capture_output: bool,
        timeout: int,
    ) -> SimpleNamespace:
        assert capture_output is True
        assert timeout == 15
        calls.append(command)
        return SimpleNamespace(returncode=0)

    monkeypatch.setenv("ANKI_PYTHON", "python")
    monkeypatch.setattr(python_env, "_load_dotenv", lambda: {})
    monkeypatch.setattr(python_env.shutil, "which", lambda command: f"/opt/hosted/{command}")
    monkeypatch.setattr(python_env.subprocess, "run", fake_run)

    assert python_env._find_anki_python() == Path("/opt/hosted/python")
    assert calls == [["/opt/hosted/python", "--version"]]


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
    assert calls == [[str(Path("/opt/anki/python")), "-c", python_env.ANKI_PYTHON_LAUNCHER]]


def test_cmd_launch_anki_reports_launch_failure(monkeypatch, capsys) -> None:
    def fake_run(_command: list[str], *, check: bool) -> SimpleNamespace:
        assert check is False
        return SimpleNamespace(returncode=3)

    monkeypatch.setattr(python_env.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(python_env.subprocess, "run", fake_run)

    assert python_env.cmd_launch_anki() == 3
    assert "Anki launcher failed with exit code 3" in capsys.readouterr().err

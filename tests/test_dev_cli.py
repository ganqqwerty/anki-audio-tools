from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest
import scripts.dev as dev


def test_parse_cli_args_accepts_verbose_before_command() -> None:
    command, command_args, verbose, idle_timeout_s = dev._parse_cli_args(
        ["--verbose", "check"],
        dev.COMMANDS,
    )

    assert command == "check"
    assert command_args == []
    assert verbose is True
    assert idle_timeout_s is None


def test_parse_cli_args_accepts_no_command() -> None:
    command, command_args, verbose, idle_timeout_s = dev._parse_cli_args([], dev.COMMANDS)

    assert command is None
    assert command_args == []
    assert verbose is False
    assert idle_timeout_s is None


def test_parse_cli_args_accepts_idle_timeout_before_command() -> None:
    command, command_args, verbose, idle_timeout_s = dev._parse_cli_args(
        ["--idle-timeout", "12.5", "check"],
        dev.COMMANDS,
    )

    assert command == "check"
    assert command_args == []
    assert verbose is False
    assert idle_timeout_s == 12.5


def test_parse_cli_args_enables_argcomplete_when_available(monkeypatch) -> None:
    calls: list[object] = []
    monkeypatch.setitem(
        sys.modules,
        "argcomplete",
        SimpleNamespace(autocomplete=lambda parser: calls.append(parser)),
    )

    command, command_args, verbose, idle_timeout_s = dev._parse_cli_args(["info"], dev.COMMANDS)

    assert command == "info"
    assert command_args == []
    assert verbose is False
    assert idle_timeout_s is None
    assert calls


def test_parse_cli_args_preserves_command_args() -> None:
    command, command_args, verbose, idle_timeout_s = dev._parse_cli_args(
        ["test-e2e", "e2e/test_editor.py"],
        dev.COMMANDS,
    )

    assert command == "test-e2e"
    assert command_args == ["e2e/test_editor.py"]
    assert verbose is False
    assert idle_timeout_s is None


def test_parse_cli_args_accepts_run_anki_command() -> None:
    command, command_args, verbose, idle_timeout_s = dev._parse_cli_args(
        ["run-anki"],
        dev.COMMANDS,
    )

    assert command == "run-anki"
    assert command_args == []
    assert verbose is False
    assert idle_timeout_s is None


def test_parse_cli_args_rejects_verbose_after_command() -> None:
    with pytest.raises(SystemExit) as excinfo:
        dev._parse_cli_args(["test-e2e", "e2e/test_editor.py", "--verbose"], dev.COMMANDS)

    assert excinfo.value.code == 2


def test_parse_cli_args_rejects_verbose_after_command_without_other_args() -> None:
    with pytest.raises(SystemExit) as excinfo:
        dev._parse_cli_args(["info", "--verbose"], dev.COMMANDS)

    assert excinfo.value.code == 2


def test_parse_cli_args_rejects_idle_timeout_after_command() -> None:
    with pytest.raises(SystemExit) as excinfo:
        dev._parse_cli_args(["info", "--idle-timeout", "12"], dev.COMMANDS)

    assert excinfo.value.code == 2


def test_parse_cli_args_rejects_negative_idle_timeout() -> None:
    with pytest.raises(SystemExit) as excinfo:
        dev._parse_cli_args(["--idle-timeout", "-1", "info"], dev.COMMANDS)

    assert excinfo.value.code == 2


def test_main_applies_idle_timeout(monkeypatch) -> None:
    calls: dict[str, object] = {}
    monkeypatch.setattr(dev, "COMMANDS", {"info": (lambda _args: 0, "Print info")})
    monkeypatch.setattr(dev, "parse_cli_args", lambda _args, _commands: ("info", [], False, 42.0))

    def fake_run_command(
        command: str | None,
        command_args: list[str],
        *,
        verbose: bool,
        idle_timeout_s: float | None,
        commands: object,
    ) -> int:
        calls["command"] = command
        calls["command_args"] = command_args
        calls["verbose"] = verbose
        calls["idle_timeout"] = idle_timeout_s
        calls["commands"] = commands
        return 0

    monkeypatch.setattr(
        dev,
        "run_command",
        fake_run_command,
    )

    with pytest.raises(SystemExit) as excinfo:
        dev.main()

    assert excinfo.value.code == 0
    assert calls == {
        "command": "info",
        "command_args": [],
        "verbose": False,
        "idle_timeout": 42.0,
        "commands": dev.COMMANDS,
    }

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
    monkeypatch.setattr(dev, "COMMANDS", {"info": (lambda: 0, "Print info")})
    monkeypatch.setattr(dev, "parse_cli_args", lambda _args, _commands: ("info", [], False, 42.0))
    monkeypatch.setattr(dev, "set_verbose", lambda verbose: calls.setdefault("verbose", verbose))
    monkeypatch.setattr(
        dev,
        "set_idle_timeout",
        lambda timeout_s: calls.setdefault("idle_timeout", timeout_s),
    )

    with pytest.raises(SystemExit) as excinfo:
        dev.main()

    assert excinfo.value.code == 0
    assert calls == {"verbose": False, "idle_timeout": 42.0}

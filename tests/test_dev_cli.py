from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest
import scripts.dev as dev


def test_parse_cli_args_accepts_verbose_before_command() -> None:
    command, command_args, verbose = dev._parse_cli_args(["--verbose", "check"], dev.COMMANDS)

    assert command == "check"
    assert command_args == []
    assert verbose is True


def test_parse_cli_args_accepts_no_command() -> None:
    command, command_args, verbose = dev._parse_cli_args([], dev.COMMANDS)

    assert command is None
    assert command_args == []
    assert verbose is False


def test_parse_cli_args_enables_argcomplete_when_available(monkeypatch) -> None:
    calls: list[object] = []
    monkeypatch.setitem(
        sys.modules,
        "argcomplete",
        SimpleNamespace(autocomplete=lambda parser: calls.append(parser)),
    )

    command, command_args, verbose = dev._parse_cli_args(["info"], dev.COMMANDS)

    assert command == "info"
    assert command_args == []
    assert verbose is False
    assert calls


def test_parse_cli_args_preserves_command_args() -> None:
    command, command_args, verbose = dev._parse_cli_args(["test-e2e", "e2e/test_editor.py"], dev.COMMANDS)

    assert command == "test-e2e"
    assert command_args == ["e2e/test_editor.py"]
    assert verbose is False


def test_parse_cli_args_rejects_verbose_after_command() -> None:
    with pytest.raises(SystemExit) as excinfo:
        dev._parse_cli_args(["test-e2e", "e2e/test_editor.py", "--verbose"], dev.COMMANDS)

    assert excinfo.value.code == 2


def test_parse_cli_args_rejects_verbose_after_command_without_other_args() -> None:
    with pytest.raises(SystemExit) as excinfo:
        dev._parse_cli_args(["info", "--verbose"], dev.COMMANDS)

    assert excinfo.value.code == 2

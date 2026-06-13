from __future__ import annotations

import sys

from scripts.dev_scripts import release as release_commands


def test_vendor_wheels_command_requires_subcommand(capsys) -> None:
    assert release_commands.cmd_vendor_wheels([]) == 1

    assert "vendor-wheels <verify|download>" in capsys.readouterr().err


def test_vendor_wheels_command_forwards_args(monkeypatch) -> None:
    calls: list[tuple[list[str], str]] = []

    def fake_run_process(command: list[str], *, label: str) -> int:
        calls.append((command, label))
        return 0

    monkeypatch.setattr(release_commands, "run_process", fake_run_process)

    assert release_commands.cmd_vendor_wheels(["verify"]) == 0
    assert calls == [
        ([sys.executable, "scripts/vendor_wheels.py", "verify"], "vendored wheels")
    ]

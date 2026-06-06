from __future__ import annotations

from scripts.dev_scripts import runner
from scripts.dev_tasks import process


def test_run_command_silences_test_commands(capsys) -> None:
    quiet_state: dict[str, bool] = {}

    def fake_test(_command_args: list[str]) -> int:
        quiet_state["test"] = process.is_quiet_test_output()
        return 0

    rc = runner.run_command(
        "test",
        [],
        verbose=False,
        idle_timeout_s=None,
        commands={"test": (fake_test, "Run tests")},
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert quiet_state == {"test": True}
    assert "[dev] selected command: test" not in captured.out


def test_run_command_keeps_non_test_commands_unchanged(capsys) -> None:
    quiet_state: dict[str, bool] = {}

    def fake_lint(_command_args: list[str]) -> int:
        quiet_state["lint"] = process.is_quiet_test_output()
        return 0

    rc = runner.run_command(
        "lint",
        [],
        verbose=False,
        idle_timeout_s=None,
        commands={"lint": (fake_lint, "Run lint")},
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert quiet_state == {"lint": False}
    assert "[dev] selected command: lint" in captured.out

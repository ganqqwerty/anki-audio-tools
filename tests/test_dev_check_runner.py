from __future__ import annotations

import threading

from scripts.dev_scripts import check as check_commands
from scripts.dev_scripts import check_runner
from scripts.dev_tasks import process


def test_check_includes_python_coverage_gate(monkeypatch) -> None:
    phases: list[tuple[str, list[str]]] = []

    monkeypatch.setattr(
        check_runner,
        "_run_check_steps_sequential",
        lambda steps: phases.append(("sequential", [name for name, _func in steps])) or [],
    )
    monkeypatch.setattr(
        check_runner,
        "_run_check_steps_parallel",
        lambda steps: phases.append(("parallel", [name for name, _func in steps])) or [],
    )

    assert check_commands.cmd_check([]) == 0
    assert phases == [
        (
            "sequential",
            ["config-schema", "contracts-generate", "contracts-check", "build-ui", "lint", "i18n"],
        ),
        (
            "parallel",
            [
                "architecture-report",
                "file-lines",
                "typecheck",
                "security",
                "deadcode",
                "deps",
                "complexity",
                "arch",
                "test-anki-api",
                "test",
            ],
        ),
        (
            "sequential",
            ["coverage", "qodana", "test-svelte"],
        ),
    ]


def test_check_parallel_executor_runs_multiple_steps_concurrently(monkeypatch) -> None:
    monkeypatch.setenv("DEV_CHECK_JOBS", "2")
    active = 0
    max_active = 0
    barrier = threading.Barrier(2, timeout=2)
    lock = threading.Lock()

    def make_step() -> int:
        nonlocal active, max_active
        with lock:
            active += 1
            max_active = max(max_active, active)
        barrier.wait()
        with lock:
            active -= 1
        return 0

    failed = check_runner._run_check_steps_parallel([("one", make_step), ("two", make_step)])

    assert failed == []
    assert max_active == 2


def test_check_parallel_executor_treats_exceptions_as_failures() -> None:
    def explode() -> int:
        raise RuntimeError("boom")

    failed = check_runner._run_check_steps_parallel([("explode", explode)])

    assert failed == ["explode"]


def test_check_sequential_suppresses_passing_test_step_banner(capsys) -> None:
    failed = check_runner._run_check_steps_sequential([("test", lambda: 0)])

    captured = capsys.readouterr()
    assert failed == []
    assert "check 1/1: test" not in captured.out


def test_check_sequential_keeps_non_test_step_banner(capsys) -> None:
    failed = check_runner._run_check_steps_sequential([("lint", lambda: 0)])

    captured = capsys.readouterr()
    assert failed == []
    assert "check 1/1: lint" in captured.out


def test_check_parallel_wraps_test_steps_in_quiet_context(monkeypatch) -> None:
    monkeypatch.setenv("DEV_CHECK_JOBS", "2")
    quiet_state: dict[str, bool] = {}

    def make_step(name: str):
        def step() -> int:
            quiet_state[name] = process.is_quiet_test_output()
            return 0

        return step

    failed = check_runner._run_check_steps_parallel(
        [("test", make_step("test")), ("lint", make_step("lint"))]
    )

    assert failed == []
    assert quiet_state == {"test": True, "lint": False}

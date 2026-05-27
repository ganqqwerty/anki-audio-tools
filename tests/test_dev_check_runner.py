from __future__ import annotations

import threading

import scripts.dev as dev


def test_check_includes_python_coverage_gate(monkeypatch) -> None:
    phases: list[tuple[str, list[str]]] = []

    monkeypatch.setattr(
        dev,
        "_run_check_steps_sequential",
        lambda steps: phases.append(("sequential", [name for name, _func in steps])) or [],
    )
    monkeypatch.setattr(
        dev,
        "_run_check_steps_parallel",
        lambda steps: phases.append(("parallel", [name for name, _func in steps])) or [],
    )

    assert dev.cmd_check() == 0
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
                "qodana",
                "arch",
                "test-anki-api",
                "test",
                "coverage",
            ],
        ),
        (
            "sequential",
            ["test-svelte"],
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

    failed = dev._run_check_steps_parallel([("one", make_step), ("two", make_step)])

    assert failed == []
    assert max_active == 2


def test_check_parallel_executor_treats_exceptions_as_failures() -> None:
    def explode() -> int:
        raise RuntimeError("boom")

    failed = dev._run_check_steps_parallel([("explode", explode)])

    assert failed == ["explode"]

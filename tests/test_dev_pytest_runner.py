from __future__ import annotations

from pathlib import Path

import scripts.dev as dev
from scripts.dev_tasks import coverage, process, pytest_runner


def test_pytest_args_are_quiet_by_default() -> None:
    process.set_verbose(False)

    args = pytest_runner._pytest_args("tests/")

    assert "-q" in args
    assert "--tb=short" in args
    assert "--show-capture=all" in args
    assert "-rfE" in args
    assert "-vv" not in args
    assert "-s" not in args
    assert "--setup-show" not in args


def test_pytest_args_keep_existing_detail_in_verbose_mode() -> None:
    process.set_verbose(True)

    try:
        args = pytest_runner._pytest_args("tests/")
    finally:
        process.set_verbose(False)

    assert "-vv" in args
    assert "-s" in args
    assert "--setup-show" in args


def test_pytest_args_can_override_cache_dir() -> None:
    cache_dir = Path("/tmp/aqe-pytest-cache")

    args = pytest_runner._pytest_args("tests/", cache_dir=cache_dir)

    assert "-o" in args
    assert f"cache_dir={cache_dir}" in args


def test_run_pytest_shows_output_on_collect_and_run_failures(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    monkeypatch.setattr(pytest_runner, "_find_anki_python", lambda: Path("/anki/python"))

    def fake_run(_cmd: list[str], **kwargs: object) -> int:
        calls.append(kwargs)
        return 0

    monkeypatch.setattr(pytest_runner, "_run", fake_run)

    assert pytest_runner._run_pytest("tests/", label="python tests") == 0
    assert [call["show_output_on_failure"] for call in calls] == [True, True]


def test_python_test_command_generates_contracts_before_pytest(monkeypatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr(dev, "cmd_contracts_generate", lambda: calls.append("contracts-generate") or 0)
    monkeypatch.setattr(
        dev,
        "_run_pytest",
        lambda target, *, label: calls.append(f"{target} {label}") or 0,
    )

    assert dev.cmd_test() == 0
    assert calls == ["contracts-generate", "tests/ python tests"]


def test_python_test_command_stops_when_contract_generation_fails(monkeypatch) -> None:
    monkeypatch.setattr(dev, "cmd_contracts_generate", lambda: 29)
    monkeypatch.setattr(
        dev,
        "_run_pytest",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("pytest should not run")),
    )

    assert dev.cmd_test() == 29


def test_coverage_pytest_shows_output_on_failure(monkeypatch) -> None:
    calls: list[tuple[list[str], dict[str, object]]] = []

    monkeypatch.setattr(coverage, "_find_anki_python", lambda: Path("/anki/python"))
    monkeypatch.setattr(
        coverage,
        "_run",
        lambda cmd, **kwargs: calls.append((cmd, kwargs)) or 0,
    )

    assert coverage.cmd_coverage() == 0
    assert calls[0][1]["show_output_on_failure"] is True

from __future__ import annotations

import threading
from pathlib import Path
from types import SimpleNamespace

import pytest
import scripts.dev as dev
from scripts.dev_tasks import coverage, frontend, process, pytest_runner, quality_tools


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


def test_build_ui_generates_contracts_before_frontend_build(monkeypatch, tmp_path: Path) -> None:
    settings_ui = tmp_path / "settings_ui"
    settings_ui.mkdir()
    calls: list[str] = []

    monkeypatch.setattr(frontend, "SETTINGS_UI_DIR", settings_ui)
    monkeypatch.setattr(frontend.shutil, "which", lambda name: "/usr/bin/npm" if name == "npm" else None)
    monkeypatch.setattr(frontend, "cmd_contracts_generate", lambda: calls.append("contracts-generate") or 0)
    monkeypatch.setattr(frontend, "_run", lambda cmd, **kwargs: calls.append(" ".join(cmd)) or 0)

    assert frontend.cmd_build_ui() == 0
    assert calls == ["contracts-generate", "npm run build"]


def test_build_ui_stops_when_contract_generation_fails(monkeypatch, tmp_path: Path) -> None:
    settings_ui = tmp_path / "settings_ui"
    settings_ui.mkdir()

    monkeypatch.setattr(frontend, "SETTINGS_UI_DIR", settings_ui)
    monkeypatch.setattr(frontend.shutil, "which", lambda name: "/usr/bin/npm" if name == "npm" else None)
    monkeypatch.setattr(frontend, "cmd_contracts_generate", lambda: 19)
    monkeypatch.setattr(
        frontend,
        "_run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("frontend build should not run")),
    )

    assert frontend.cmd_build_ui() == 19


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


def test_lint_runs_safe_autofix_before_check(monkeypatch) -> None:
    calls: list[str] = []
    anki_python = Path("/anki/python")

    monkeypatch.setattr(dev, "_find_anki_python", lambda: anki_python)
    monkeypatch.setattr(dev, "_run", lambda cmd, **kwargs: calls.append(" ".join(cmd)) or 0)

    assert dev.cmd_lint() == 0
    assert calls == [
        "/anki/python -m ruff check --fix",
        "/anki/python -m ruff check",
    ]


def test_lint_stops_when_safe_autofix_fails(monkeypatch) -> None:
    calls: list[str] = []
    anki_python = Path("/anki/python")

    monkeypatch.setattr(dev, "_find_anki_python", lambda: anki_python)
    monkeypatch.setattr(dev, "_run", lambda cmd, **kwargs: calls.append(" ".join(cmd)) or 42)

    assert dev.cmd_lint() == 42
    assert calls == ["/anki/python -m ruff check --fix"]


def test_test_svelte_builds_frontend_before_validation(monkeypatch, tmp_path: Path) -> None:
    settings_ui = tmp_path / "settings_ui"
    (settings_ui / "node_modules").mkdir(parents=True)
    calls: list[str] = []

    monkeypatch.setattr(frontend, "SETTINGS_UI_DIR", settings_ui)
    monkeypatch.setattr(frontend.shutil, "which", lambda name: "/usr/bin/npm" if name == "npm" else None)
    monkeypatch.setattr(frontend, "cmd_build_ui", lambda: calls.append("build") or 0)
    monkeypatch.setattr(
        frontend,
        "_run",
        lambda cmd, **kwargs: calls.append(" ".join(cmd)) or 0,
    )

    assert frontend.cmd_test_svelte() == 0
    assert calls == ["build", "npm run lint -- --fix", "npm run validate"]


def test_test_svelte_stops_when_lint_autofix_fails(monkeypatch, tmp_path: Path) -> None:
    settings_ui = tmp_path / "settings_ui"
    (settings_ui / "node_modules").mkdir(parents=True)
    calls: list[str] = []

    monkeypatch.setattr(frontend, "SETTINGS_UI_DIR", settings_ui)
    monkeypatch.setattr(frontend.shutil, "which", lambda name: "/usr/bin/npm" if name == "npm" else None)
    monkeypatch.setattr(frontend, "cmd_build_ui", lambda: calls.append("build") or 0)

    def fake_run(cmd: list[str], **_kwargs: object) -> int:
        calls.append(" ".join(cmd))
        return 31

    monkeypatch.setattr(frontend, "_run", fake_run)

    assert frontend.cmd_test_svelte() == 31
    assert calls == ["build", "npm run lint -- --fix"]


def test_test_svelte_stops_when_frontend_build_fails(monkeypatch, tmp_path: Path) -> None:
    settings_ui = tmp_path / "settings_ui"
    (settings_ui / "node_modules").mkdir(parents=True)

    monkeypatch.setattr(frontend, "SETTINGS_UI_DIR", settings_ui)
    monkeypatch.setattr(frontend.shutil, "which", lambda name: "/usr/bin/npm" if name == "npm" else None)
    monkeypatch.setattr(frontend, "cmd_build_ui", lambda: 17)
    monkeypatch.setattr(
        frontend,
        "_run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("validation should not run")),
    )

    assert frontend.cmd_test_svelte() == 17


def test_test_e2e_builds_frontend_before_pytest(monkeypatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr(dev, "_COMMAND_ARGS", [])
    monkeypatch.setattr(dev, "cmd_build_ui", lambda: calls.append("build") or 0)
    monkeypatch.setattr(
        dev,
        "_run_pytest",
        lambda target, *, label: calls.append(f"{target} {label}") or 0,
    )

    assert dev.cmd_test_e2e() == 0
    assert calls == ["build", "e2e/ python e2e tests"]


def test_test_e2e_forwards_explicit_pytest_targets(monkeypatch) -> None:
    calls: list[str] = []
    graph_default_target = (
        "e2e/test_editor_region_loop_graph_workflow.py::"
        "test_graph_default_repeat_can_be_turned_off_for_selected_region_playback"
    )
    multi_field_target = (
        "e2e/test_editor_region_loop_graph_workflow.py::"
        "test_two_audio_fields_keep_region_state_scoped_and_single_active_playback"
    )

    monkeypatch.setattr(dev, "_COMMAND_ARGS", [graph_default_target, multi_field_target])
    monkeypatch.setattr(dev, "cmd_build_ui", lambda: calls.append("build") or 0)
    monkeypatch.setattr(
        dev,
        "_run_pytest",
        lambda target, *, label: calls.append(f"{target} {label}") or 0,
    )

    assert dev.cmd_test_e2e() == 0
    assert calls == [
        "build",
        f"{graph_default_target} python e2e tests: {graph_default_target}",
        f"{multi_field_target} python e2e tests: {multi_field_target}",
    ]


def test_test_e2e_stops_when_frontend_build_fails(monkeypatch) -> None:
    monkeypatch.setattr(dev, "cmd_build_ui", lambda: 23)
    monkeypatch.setattr(
        dev,
        "_run_pytest",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("e2e should not run")),
    )

    assert dev.cmd_test_e2e() == 23


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


def test_qodana_runs_with_committed_config(monkeypatch) -> None:
    calls: list[tuple[list[str], dict[str, object]]] = []

    monkeypatch.setattr(quality_tools.shutil, "which", lambda name: "/usr/local/bin/qodana" if name == "qodana" else None)
    monkeypatch.setattr(
        quality_tools,
        "_run",
        lambda cmd, **kwargs: calls.append((cmd, kwargs)) or 0,
    )

    assert quality_tools.cmd_qodana() == 0
    assert calls == [
        (
            [
                "/usr/local/bin/qodana",
                "--disable-update-checks",
                "scan",
                "--config",
                "qodana.yaml",
                "--project-dir",
                str(quality_tools.ROOT),
                "--print-problems",
            ],
            {"label": "qodana code quality"},
        )
    ]


def test_qodana_reports_missing_cli(monkeypatch, capsys) -> None:
    monkeypatch.setattr(quality_tools.shutil, "which", lambda name: None)

    assert quality_tools.cmd_qodana() == 1

    captured = capsys.readouterr()
    assert "qodana not found" in captured.err


def test_check_includes_python_coverage_gate(monkeypatch) -> None:
    phases: list[tuple[str, list[str]]] = []

    monkeypatch.setattr(dev, "_run_check_steps_sequential", lambda steps: phases.append(("sequential", [name for name, _func in steps])) or [])
    monkeypatch.setattr(dev, "_run_check_steps_parallel", lambda steps: phases.append(("parallel", [name for name, _func in steps])) or [])

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


def test_cmd_i18n_reports_failures(monkeypatch, capsys) -> None:
    monkeypatch.setattr(dev, "locale_catalog_violations", lambda: ["de.json missing keys: beta"])

    assert dev.cmd_i18n() == 1

    captured = capsys.readouterr()
    assert "FAIL: locale catalogs differ from en.json:" in captured.out
    assert "de.json missing keys: beta" in captured.out


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

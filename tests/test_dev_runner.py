from __future__ import annotations

from pathlib import Path

import scripts.dev as dev


def test_build_ui_generates_contracts_before_frontend_build(monkeypatch, tmp_path: Path) -> None:
    settings_ui = tmp_path / "settings_ui"
    settings_ui.mkdir()
    calls: list[str] = []

    monkeypatch.setattr(dev, "SETTINGS_UI_DIR", settings_ui)
    monkeypatch.setattr(dev.shutil, "which", lambda name: "/usr/bin/npm" if name == "npm" else None)
    monkeypatch.setattr(dev, "cmd_contracts_generate", lambda: calls.append("contracts-generate") or 0)
    monkeypatch.setattr(dev, "_run", lambda cmd, **kwargs: calls.append(" ".join(cmd)) or 0)

    assert dev.cmd_build_ui() == 0
    assert calls == ["contracts-generate", "npm run build"]


def test_build_ui_stops_when_contract_generation_fails(monkeypatch, tmp_path: Path) -> None:
    settings_ui = tmp_path / "settings_ui"
    settings_ui.mkdir()

    monkeypatch.setattr(dev, "SETTINGS_UI_DIR", settings_ui)
    monkeypatch.setattr(dev.shutil, "which", lambda name: "/usr/bin/npm" if name == "npm" else None)
    monkeypatch.setattr(dev, "cmd_contracts_generate", lambda: 19)
    monkeypatch.setattr(
        dev,
        "_run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("frontend build should not run")),
    )

    assert dev.cmd_build_ui() == 19


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


def test_test_svelte_builds_frontend_before_validation(monkeypatch, tmp_path: Path) -> None:
    settings_ui = tmp_path / "settings_ui"
    (settings_ui / "node_modules").mkdir(parents=True)
    calls: list[str] = []

    monkeypatch.setattr(dev, "SETTINGS_UI_DIR", settings_ui)
    monkeypatch.setattr(dev.shutil, "which", lambda name: "/usr/bin/npm" if name == "npm" else None)
    monkeypatch.setattr(dev, "cmd_build_ui", lambda: calls.append("build") or 0)
    monkeypatch.setattr(
        dev,
        "_run",
        lambda cmd, **kwargs: calls.append(" ".join(cmd)) or 0,
    )

    assert dev.cmd_test_svelte() == 0
    assert calls == ["build", "npm run validate"]


def test_test_svelte_stops_when_frontend_build_fails(monkeypatch, tmp_path: Path) -> None:
    settings_ui = tmp_path / "settings_ui"
    (settings_ui / "node_modules").mkdir(parents=True)

    monkeypatch.setattr(dev, "SETTINGS_UI_DIR", settings_ui)
    monkeypatch.setattr(dev.shutil, "which", lambda name: "/usr/bin/npm" if name == "npm" else None)
    monkeypatch.setattr(dev, "cmd_build_ui", lambda: 17)
    monkeypatch.setattr(
        dev,
        "_run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("validation should not run")),
    )

    assert dev.cmd_test_svelte() == 17


def test_test_e2e_builds_frontend_before_pytest(monkeypatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr(dev, "cmd_build_ui", lambda: calls.append("build") or 0)
    monkeypatch.setattr(
        dev,
        "_run_pytest",
        lambda target, *, label: calls.append(f"{target} {label}") or 0,
    )

    assert dev.cmd_test_e2e() == 0
    assert calls == ["build", "e2e/ python e2e tests"]


def test_test_e2e_stops_when_frontend_build_fails(monkeypatch) -> None:
    monkeypatch.setattr(dev, "cmd_build_ui", lambda: 23)
    monkeypatch.setattr(
        dev,
        "_run_pytest",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("e2e should not run")),
    )

    assert dev.cmd_test_e2e() == 23


def test_qodana_runs_with_committed_config(monkeypatch) -> None:
    calls: list[tuple[list[str], dict[str, object]]] = []

    monkeypatch.setattr(dev.shutil, "which", lambda name: "/usr/local/bin/qodana" if name == "qodana" else None)
    monkeypatch.setattr(
        dev,
        "_run",
        lambda cmd, **kwargs: calls.append((cmd, kwargs)) or 0,
    )

    assert dev.cmd_qodana() == 0
    assert calls == [
        (
            [
                "/usr/local/bin/qodana",
                "--disable-update-checks",
                "scan",
                "--config",
                "qodana.yaml",
                "--project-dir",
                str(dev.ROOT),
                "--print-problems",
            ],
            {"label": "qodana code quality"},
        )
    ]


def test_qodana_reports_missing_cli(monkeypatch, capsys) -> None:
    monkeypatch.setattr(dev.shutil, "which", lambda name: None)

    assert dev.cmd_qodana() == 1

    captured = capsys.readouterr()
    assert "qodana not found" in captured.err


def test_check_includes_python_coverage_gate(monkeypatch) -> None:
    calls: list[str] = []

    command_results = {
        "cmd_config_schema": 0,
        "cmd_contracts_generate": 0,
        "cmd_contracts_check": 0,
        "cmd_architecture_report": 0,
        "cmd_lint": 0,
        "cmd_file_lines": 0,
        "cmd_typecheck": 0,
        "cmd_security": 0,
        "cmd_deadcode": 0,
        "cmd_deps": 0,
        "cmd_complexity": 0,
        "cmd_qodana": 0,
        "cmd_arch": 0,
        "cmd_test_anki_api": 0,
        "cmd_test": 0,
        "cmd_coverage": 0,
        "cmd_test_svelte": 0,
    }

    for name, result in command_results.items():
        monkeypatch.setattr(dev, name, lambda name=name, result=result: calls.append(name) or result)

    assert dev.cmd_check() == 0
    assert "cmd_coverage" in calls
    assert calls.index("cmd_coverage") > calls.index("cmd_test")
    assert calls.index("cmd_coverage") < calls.index("cmd_test_svelte")
    assert calls.index("cmd_qodana") > calls.index("cmd_complexity")
    assert calls.index("cmd_qodana") < calls.index("cmd_arch")

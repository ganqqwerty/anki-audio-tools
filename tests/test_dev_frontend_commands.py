from __future__ import annotations

from pathlib import Path

import scripts.dev as dev
from scripts.dev_tasks import frontend


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

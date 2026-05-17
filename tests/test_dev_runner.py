from __future__ import annotations

from pathlib import Path

import scripts.dev as dev


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

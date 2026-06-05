from __future__ import annotations

import json
import sys
from pathlib import Path

from scripts import dev_runtime
from scripts.dev_scripts import registry
from scripts.dev_scripts import runtime as runtime_commands


def test_stage_runtime_manifest_writes_release_compatible_all_target_manifest(tmp_path: Path) -> None:
    addon_dir = tmp_path / "addon"

    manifest = dev_runtime.stage_runtime_manifest(addon_dir)

    metadata = dev_runtime.release_runtime_metadata.load_runtime_release_lock()
    manifest_path = addon_dir / "bin" / "runtime_manifest.json"
    stored_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert stored_manifest == manifest
    assert set(manifest["targets"]) == set(metadata["targets"])
    assert manifest["runtime_manifest_id"] == metadata["runtime_manifest_id"]
    for target_entry in manifest["targets"].values():
        assert "runtime_pack" in target_entry


def test_headless_runtime_loader_does_not_execute_addon_bootstrap(tmp_path: Path) -> None:
    addon_dir = tmp_path / "addon"
    addon_dir.mkdir()
    (addon_dir / "__init__.py").write_text("raise RuntimeError('bootstrap executed')\n", encoding="utf-8")
    (addon_dir / "runtime_dependency.py").write_text("VALUE = 42\n", encoding="utf-8")
    (addon_dir / "runtime_manager.py").write_text(
        "from .runtime_dependency import VALUE\n",
        encoding="utf-8",
    )

    module = dev_runtime.load_runtime_manager(
        addon_dir=addon_dir,
        package_name="_aqe_runtime_loader_test",
    )

    assert module.VALUE == 42


def test_install_runtime_calls_shared_core_with_force_verify(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    calls: list[tuple[Path, bool, bool]] = []
    final_status = {
        "phase": "ready",
        "platform": "windows-x86_64",
        "runtime_manifest_id": "runtime-test",
        "runtime_root": str(tmp_path / "runtime"),
        "message": "Runtime is ready.",
    }

    class FakeRuntimeManager:
        @staticmethod
        def ensure_runtime(addon_dir, *, progress, force_verify):
            calls.append((addon_dir, force_verify, progress is not None))
            progress({"progress": 25, "step": "Download zip", "detail": "Downloaded bytes"})
            return final_status

    monkeypatch.setattr(dev_runtime, "stage_runtime_manifest", lambda _addon_dir: {})
    monkeypatch.setattr(dev_runtime, "load_runtime_manager", lambda *, addon_dir: FakeRuntimeManager)

    assert dev_runtime.install_runtime(tmp_path) == 0

    assert calls == [(tmp_path, True, True)]
    output = capsys.readouterr().out
    assert "Download zip: Downloaded bytes" in output
    assert "phase=ready" in output


def test_install_runtime_returns_failure_for_non_ready_status(monkeypatch, tmp_path: Path) -> None:
    class FakeRuntimeManager:
        @staticmethod
        def ensure_runtime(addon_dir, *, progress, force_verify):
            del addon_dir, progress, force_verify
            return {
                "phase": "missing",
                "platform": "windows-x86_64",
                "runtime_manifest_id": "runtime-test",
                "runtime_root": "",
                "message": "Runtime assets are not installed.",
            }

    monkeypatch.setattr(dev_runtime, "stage_runtime_manifest", lambda _addon_dir: {})
    monkeypatch.setattr(dev_runtime, "load_runtime_manager", lambda *, addon_dir: FakeRuntimeManager)

    assert dev_runtime.install_runtime(tmp_path) == 1


def test_require_ready_fails_with_install_hint_and_does_not_install(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    class FakeRuntimeManager:
        @staticmethod
        def runtime_status(addon_dir):
            del addon_dir
            return {
                "phase": "missing",
                "platform": "windows-x86_64",
                "runtime_manifest_id": "runtime-test",
                "runtime_root": "",
                "message": "Runtime assets are not installed.",
            }

        @staticmethod
        def ensure_runtime(*_args, **_kwargs):
            raise AssertionError("require-ready must not install runtime assets")

    monkeypatch.setattr(dev_runtime, "stage_runtime_manifest", lambda _addon_dir: {})
    monkeypatch.setattr(dev_runtime, "load_runtime_manager", lambda *, addon_dir: FakeRuntimeManager)

    assert dev_runtime.require_ready(tmp_path) == 1

    assert "runtime-install" in capsys.readouterr().err


def test_runtime_install_command_forwards_to_anki_python(monkeypatch) -> None:
    calls: list[tuple[list[str], str, bool]] = []

    def fake_run_process(command: list[str], *, label: str, show_output_on_failure: bool = False) -> int:
        calls.append((command, label, show_output_on_failure))
        return 0

    monkeypatch.setattr(runtime_commands, "find_anki_python", lambda: Path("AnkiPython"))
    monkeypatch.setattr(runtime_commands, "run_process", fake_run_process)

    assert runtime_commands.cmd_runtime_install([]) == 0
    assert calls == [
        (
            ["AnkiPython", "scripts/dev_runtime.py", "install"],
            "managed runtime install",
            True,
        )
    ]


def test_runtime_preflight_checks_runtime_before_wheels(monkeypatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        runtime_commands,
        "_run_runtime_helper",
        lambda action, *, label: calls.append(f"{action} {label}") or 0,
    )
    monkeypatch.setattr(
        runtime_commands,
        "run_process",
        lambda command, *, label, show_output_on_failure=False: (
            calls.append(f"{label} {' '.join(command)} {show_output_on_failure}") or 0
        ),
    )

    assert runtime_commands.cmd_runtime_preflight() == 0
    assert calls == [
        "require-ready managed runtime readiness",
        f"vendored runtime wheels {sys.executable} scripts/vendor_wheels.py verify True",
    ]


def test_runtime_preflight_stops_before_wheels_when_runtime_missing(monkeypatch) -> None:
    monkeypatch.setattr(runtime_commands, "_run_runtime_helper", lambda _action, *, label: 12)
    monkeypatch.setattr(
        runtime_commands,
        "run_process",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("wheel verify should not run")),
    )

    assert runtime_commands.cmd_runtime_preflight() == 12


def test_runtime_install_is_registered() -> None:
    assert "runtime-install" in registry.COMMANDS

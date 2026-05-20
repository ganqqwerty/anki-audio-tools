#!/usr/bin/env python3
"""Smoke-test a built .ankiaddon archive from an extracted install tree."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import types
import zipfile
from pathlib import Path
from unittest.mock import MagicMock


def _install_anki_stubs() -> None:
    aqt = types.ModuleType("aqt")
    qt = types.ModuleType("aqt.qt")
    gui_hooks = types.SimpleNamespace(
        main_window_did_init=[],
        editor_did_init=[],
        editor_will_load_note=[],
        browser_menus_did_init=[],
        browser_will_show_context_menu=[],
    )
    addon_manager = types.SimpleNamespace(
        addonFromModule=lambda _module: "anki_audio_quick_editor",
        getConfig=lambda _addon_id: {},
        addonConfigDefaults=lambda _addon_id: {},
        writeConfig=lambda _addon_id, _config: None,
        addonsFolder=lambda _addon_id: tempfile.gettempdir(),
        setConfigAction=lambda _module, _callback: None,
    )
    menu = types.SimpleNamespace(addMenu=lambda _name: types.SimpleNamespace(addAction=lambda _label: MagicMock()))
    aqt.mw = types.SimpleNamespace(addonManager=addon_manager, form=types.SimpleNamespace(menuTools=menu))
    aqt.gui_hooks = gui_hooks
    qt.qconnect = lambda *_args, **_kwargs: None
    sys.modules.update({"aqt": aqt, "aqt.qt": qt})


def _extract_archive(archive: Path, root: Path) -> Path:
    package_dir = root / "anki_audio_quick_editor"
    package_dir.mkdir(parents=True)
    with zipfile.ZipFile(archive, "r") as zf:
        for info in zf.infolist():
            extracted = Path(zf.extract(info, package_dir))
            mode = (info.external_attr >> 16) & 0o777
            if mode:
                extracted.chmod(mode)
    return package_dir


def _require_nonempty(package_dir: Path, relative: str) -> None:
    path = package_dir / relative
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"missing or empty archive file: {relative}")


def _run_tool(path: Path, args: list[str]) -> None:
    result = subprocess.run([str(path), *args], capture_output=True, text=True, timeout=20, check=False)  # nosec B603
    if result.returncode != 0:
        output = (result.stdout or result.stderr).strip()
        raise RuntimeError(f"{path.name} diagnostic failed: {output}")


def smoke_archive(archive: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="anki-audio-smoke-") as tmp:
        root = Path(tmp)
        package_dir = _extract_archive(archive, root)
        empty_path = root / "empty-path"
        empty_path.mkdir()
        os.environ["PATH"] = str(empty_path)
        sys.path.insert(0, str(root))
        _install_anki_stubs()

        _require_nonempty(package_dir, "contracts_generated.py")
        _require_nonempty(package_dir, "templates/settings/settings_bundle.js")
        _require_nonempty(package_dir, "templates/editor/editor_bundle.js")
        _require_nonempty(package_dir, "templates/batch/batch_bundle.js")
        _require_nonempty(package_dir, "templates/batch/batch_bundle.css")
        __import__("anki_audio_quick_editor.contracts_generated")
        audio_tools = __import__("anki_audio_quick_editor.audio_tools", fromlist=["audio_tools"])

        platform_key = audio_tools.current_platform_key()
        if platform_key is None:
            raise RuntimeError("current platform is not in the release target matrix")
        manifest = json.loads((package_dir / "bin" / "runtime_manifest.json").read_text(encoding="utf-8"))
        tools = manifest["targets"][platform_key]["tools"]
        ffmpeg = audio_tools.find_ffmpeg("")
        ffprobe = audio_tools.find_ffprobe(ffmpeg)
        deep_filter = audio_tools.find_deep_filter("")
        rnnoise = audio_tools.find_rnnoise_bundle()
        for tool_name, path in {
            "ffmpeg": ffmpeg,
            "ffprobe": ffprobe,
            "deep-filter": deep_filter,
            "rnnoise-cli": rnnoise,
        }.items():
            if str(package_dir) not in str(path):
                raise RuntimeError(f"{tool_name} did not resolve inside extracted archive: {path}")
        _run_tool(ffmpeg, tools["ffmpeg"].get("diagnostic_args", ["-version"]))
        _run_tool(ffprobe, tools["ffprobe"].get("diagnostic_args", ["-version"]))
        _run_tool(deep_filter, tools["deep-filter"].get("diagnostic_args", ["--version"]))
        _run_tool(rnnoise, tools["rnnoise-cli"].get("diagnostic_args", ["--version"]))


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test an extracted .ankiaddon archive")
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    smoke_archive(args.archive)
    print(f"release smoke passed: {args.archive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

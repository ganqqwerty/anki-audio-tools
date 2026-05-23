from __future__ import annotations

import json
import stat
import sys
import types
import zipfile
from pathlib import Path

from scripts import release_smoke


def test_release_smoke_extract_preserves_executable_bits(tmp_path: Path) -> None:
    archive = tmp_path / "addon.ankiaddon"
    with zipfile.ZipFile(archive, "w") as zf:
        info = zipfile.ZipInfo("bin/macos-arm64/ffmpeg")
        info.external_attr = 0o755 << 16
        zf.writestr(info, b"binary")

    package_dir = release_smoke._extract_archive(archive, tmp_path / "extract")

    extracted = package_dir / "bin" / "macos-arm64" / "ffmpeg"
    assert extracted.stat().st_mode & stat.S_IXUSR


def test_release_smoke_skips_ffmpeg_when_manifest_omits_it(tmp_path: Path, monkeypatch) -> None:
    archive = tmp_path / "external-ffmpeg.ankiaddon"
    manifest = {
        "schema_version": 1,
        "targets": {
            "macos-arm64": {
                "tools": {
                    "deep-filter": {"executable": "deep-filter", "diagnostic_args": ["--version"]},
                    "rnnoise-cli": {"executable": "rnnoise-cli", "diagnostic_args": ["--version"]},
                }
            }
        },
    }
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("bin/runtime_manifest.json", json.dumps(manifest))
        for name in ("contracts_generated.py", "templates/settings/settings_bundle.js", "templates/editor/editor_bundle.js", "templates/batch/batch_bundle.js", "templates/batch/batch_bundle.css"):
            zf.writestr(name, b"x")
        for name in ("bin/macos-arm64/deep-filter", "bin/macos-arm64/rnnoise-cli"):
            info = zipfile.ZipInfo(name)
            info.external_attr = 0o755 << 16
            zf.writestr(info, b"binary")

    calls: list[tuple[str, tuple[str, ...]]] = []

    def fake_run_tool(path: Path, args: list[str]) -> None:
        calls.append((path.name, tuple(args)))

    monkeypatch.setattr(release_smoke, "_run_tool", fake_run_tool)
    monkeypatch.setattr(release_smoke, "_install_anki_stubs", lambda: None)
    original_extract = release_smoke._extract_archive
    audio_tools_stub = types.ModuleType("anki_audio_quick_editor.audio_tools")
    audio_tools_stub.current_platform_key = lambda: "macos-arm64"

    def fake_extract(archive_path: Path, root: Path) -> Path:
        package_dir = original_extract(archive_path, root)
        audio_tools_stub.find_deep_filter = lambda _configured_path: package_dir / "bin" / "macos-arm64" / "deep-filter"
        audio_tools_stub.find_rnnoise_bundle = lambda: package_dir / "bin" / "macos-arm64" / "rnnoise-cli"
        return package_dir

    monkeypatch.setattr(release_smoke, "_extract_archive", fake_extract)
    monkeypatch.setitem(sys.modules, "anki_audio_quick_editor.audio_tools", audio_tools_stub)

    release_smoke.smoke_archive(archive)

    assert calls == [
        ("deep-filter", ("--version",)),
        ("rnnoise-cli", ("--version",)),
    ]

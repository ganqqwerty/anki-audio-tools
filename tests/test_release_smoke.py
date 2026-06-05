from __future__ import annotations

import json
import os
import stat
import zipfile
from pathlib import Path

import pytest
from scripts import release_smoke


def test_release_smoke_extract_preserves_executable_bits(tmp_path: Path) -> None:
    archive = tmp_path / "addon.ankiaddon"
    with zipfile.ZipFile(archive, "w") as zf:
        info = zipfile.ZipInfo("bin/macos-arm64/ffmpeg")
        info.external_attr = 0o755 << 16
        zf.writestr(info, b"binary")

    package_dir = release_smoke._extract_archive(archive, tmp_path / "extract")

    extracted = package_dir / "bin" / "macos-arm64" / "ffmpeg"
    if os.name == "posix":
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
        zf.writestr("__init__.py", b"# test package\n")
        zf.writestr("contracts_generated.py", b"VALUE = 1\n")
        zf.writestr(
            "audio_tools.py",
            "\n".join(
                [
                    "from pathlib import Path",
                    "def current_platform_key():",
                    "    return 'macos-arm64'",
                    "def find_deep_filter(_configured_path):",
                    "    return Path(__file__).parent / 'bin' / 'macos-arm64' / 'deep-filter'",
                    "def find_rnnoise_bundle():",
                    "    return Path(__file__).parent / 'bin' / 'macos-arm64' / 'rnnoise-cli'",
                    "",
                ]
            ).encode(),
        )
        for name in ("templates/settings/settings_bundle.js", "templates/editor/editor_bundle.js", "templates/batch/batch_bundle.js", "templates/batch/batch_bundle.css"):
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
    release_smoke.smoke_archive(archive)

    assert calls == [
        ("deep-filter", ("--version",)),
        ("rnnoise-cli", ("--version",)),
    ]


def test_release_smoke_accepts_thin_runtime_manifest(tmp_path: Path, monkeypatch) -> None:
    archive = tmp_path / "thin.ankiaddon"
    manifest = {
        "schema_version": 1,
        "targets": {
            "macos-arm64": {
                "runtime_pack": {
                    "name": "aqe-runtime-1.0-macos-arm64.zip",
                    "url": "https://example.invalid/runtime-v1.0/aqe-runtime-1.0-macos-arm64.zip",
                    "sha256": "a" * 64,
                    "size": 1,
                },
                "tools": {},
            }
        },
    }
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("bin/runtime_manifest.json", json.dumps(manifest))
        zf.writestr("__init__.py", b"# test package\n")
        zf.writestr("contracts_generated.py", b"VALUE = 1\n")
        zf.writestr("audio_tools.py", b"def current_platform_key():\n    return 'macos-arm64'\n")
        for name in (
            "templates/settings/settings_bundle.js",
            "templates/editor/editor_bundle.js",
            "templates/batch/batch_bundle.js",
            "templates/batch/batch_bundle.css",
        ):
            zf.writestr(name, b"x")

    monkeypatch.setattr(release_smoke, "_run_tool", lambda _path, _args: pytest.fail("unexpected tool run"))
    monkeypatch.setattr(release_smoke, "_install_anki_stubs", lambda: None)

    release_smoke.smoke_archive(archive)

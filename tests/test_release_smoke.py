from __future__ import annotations

import stat
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

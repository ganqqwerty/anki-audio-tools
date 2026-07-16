from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

from anki_audio_quick_editor import runtime_manager


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_manifest(
    addon_dir: Path,
    *,
    archive: Path,
    archive_sha: str,
    file_payloads: dict[str, bytes],
    manifest_id: str = "runtime-test",
    archive_size: int | None = None,
) -> None:
    (addon_dir / "bin").mkdir(parents=True, exist_ok=True)
    files = {
        rel: {
            "path": rel,
            "sha256": _sha(payload),
            "size": len(payload),
            "executable_bit": rel.endswith("ffmpeg") or rel.endswith("rnnoise-cli"),
        }
        for rel, payload in file_payloads.items()
    }
    shared_files = {
        "spleeter-vocals": files["models/spleeter-2stems-fp16/vocals.fp16.onnx"],
    }
    if "models/silero-vad/silero_vad.onnx" in files:
        shared_files["silero-vad-model"] = files["models/silero-vad/silero_vad.onnx"]
    manifest = {
        "schema_version": 2,
        "runtime_manifest_id": manifest_id,
        "targets": {
            "macos-arm64": {
                "runtime_pack": {
                    "name": archive.name,
                    "url": archive.as_uri(),
                    "sha256": archive_sha,
                    "size": archive.stat().st_size if archive_size is None else archive_size,
                },
                "tools": {
                    "ffmpeg": {
                        "path": "macos-arm64/ffmpeg",
                        "executable": "ffmpeg",
                        **files["macos-arm64/ffmpeg"],
                    },
                    "rnnoise-cli": {
                        "path": "macos-arm64/rnnoise-cli",
                        "executable": "rnnoise-cli",
                        **files["macos-arm64/rnnoise-cli"],
                    },
                },
                "shared_files": shared_files,
            }
        },
    }
    (addon_dir / "bin" / "runtime_manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )


def _write_runtime_pack(path: Path, payloads: dict[str, bytes]) -> str:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, payload in payloads.items():
            zf.writestr(name, payload)
    return runtime_manager.sha256_file(path)

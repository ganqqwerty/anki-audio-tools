"""Pause pipeline artifact and manifest helpers."""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

from .audio_pipeline import PAUSE_PIPELINE_MANIFEST_VERSION, make_pause_pipeline_run_id
from .audio_state import AudioEditState, AudioProcessingConfig
from .audio_tools import PACKAGE_DIR


def _create_pause_pipeline_run_dir(source_path: Path, artifact_root: Path | None) -> Path:
    root = artifact_root or (PACKAGE_DIR / "aqe_artifacts")
    run_dir = Path(root).expanduser() / make_pause_pipeline_run_id(source_path.name)
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def _build_pause_pipeline_manifest(
    run_dir: Path,
    source_path: Path,
    state: AudioEditState,
    config: AudioProcessingConfig,
    source_duration_ms: int,
    *,
    stages: list[dict[str, object]],
    artifacts: list[dict[str, object]],
    warnings: list[str],
    errors: list[str],
) -> dict[str, object]:
    return {
        "schema_version": PAUSE_PIPELINE_MANIFEST_VERSION,
        "run_id": run_dir.name,
        "created_at": datetime.now().isoformat(),
        "operation": "deep_filter_pause_speedup",
        "artifact_dir": str(run_dir),
        "source": _source_file_record(source_path, source_duration_ms),
        "state": {
            "source_file": state.source_file,
            "left_trim_ms": state.left_trim_ms,
            "right_trim_ms": state.right_trim_ms,
            "speed": state.speed,
            "volume_db": state.volume_db,
            "remove_internal_pauses_enabled": state.remove_internal_pauses_enabled,
        },
        "config": _pause_pipeline_config_snapshot(config),
        "stages": stages,
        "artifacts": artifacts,
        "silence_intervals": [],
        "timeline": [],
        "warnings": warnings,
        "errors": errors,
        "working_duration_ms": None,
        "final_output": None,
    }


def _source_file_record(source_path: Path, duration_ms: int) -> dict[str, object]:
    stat = source_path.stat()
    return {
        "filename": source_path.name,
        "path": str(source_path),
        "duration_ms": duration_ms,
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": _sha256_file(source_path),
    }


def _pause_pipeline_config_snapshot(config: AudioProcessingConfig) -> dict[str, object]:
    return {
        "ffmpeg_path": config.ffmpeg_path,
        "deep_filter_path": config.deep_filter_path,
        "deep_filter_post_filter": config.deep_filter_post_filter,
        "internal_pause_silence_threshold_db": config.internal_pause_silence_threshold_db,
        "internal_pause_threshold_ms": config.internal_pause_threshold_ms,
        "internal_pause_target_gap_ms": config.internal_pause_target_gap_ms,
        "speed": {
            "min": config.min_speed,
            "max": config.max_speed,
        },
        "output_format": config.output_format,
    }


def _artifact_record(artifact_id: str, path: Path, kind: str) -> dict[str, object]:
    exists = path.exists()
    record: dict[str, object] = {
        "id": artifact_id,
        "path": str(path),
        "kind": kind,
        "exists": exists,
    }
    if path.is_file():
        stat = path.stat()
        record["size_bytes"] = stat.st_size
        record["sha256"] = _sha256_file(path)
    return record


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


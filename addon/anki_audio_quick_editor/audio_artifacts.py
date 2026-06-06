"""Pause pipeline artifact and manifest helpers."""

from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from pathlib import Path, PureWindowsPath

from .audio_pipeline import (
    PAUSE_PIPELINE_MANIFEST_VERSION,
    PAUSE_PIPELINE_RUN_ID_COMPONENT_MAX_LENGTH,
    make_pause_pipeline_run_id,
)
from .audio_state import AudioEditState, AudioProcessingConfig
from .audio_tools import PACKAGE_DIR
from .errors import AudioProcessingError

_WINDOWS_LEGACY_MAX_PATH_LENGTH = 259
_LONGEST_PAUSE_PIPELINE_ARTIFACT_NAME = "04_detected_pause_intervals.json"
_MIN_PAUSE_PIPELINE_RUN_ID_LENGTH = len(
    make_pause_pipeline_run_id(
        "a",
        now=datetime(2000, 1, 1, 0, 0, 0, 0, tzinfo=UTC),
        token="00000000",
    )
)


def _max_pause_pipeline_run_id_length(
    artifact_root: Path,
    *,
    is_windows: bool | None = None,
) -> int:
    if is_windows is None:
        is_windows = os.name == "nt"
    if not is_windows:
        return PAUSE_PIPELINE_RUN_ID_COMPONENT_MAX_LENGTH

    root_text = str(PureWindowsPath(str(artifact_root)))
    run_id_budget = (
        _WINDOWS_LEGACY_MAX_PATH_LENGTH
        - len(root_text)
        - 2
        - len(_LONGEST_PAUSE_PIPELINE_ARTIFACT_NAME)
    )
    if run_id_budget < _MIN_PAUSE_PIPELINE_RUN_ID_LENGTH:
        raise AudioProcessingError(
            "Pause-removal support artifact path is too long for Windows. "
            "Shorten the source audio filename or use a shorter Anki/add-on path."
        )
    return min(PAUSE_PIPELINE_RUN_ID_COMPONENT_MAX_LENGTH, run_id_budget)


def _create_pause_pipeline_run_dir(source_path: Path, artifact_root: Path | None) -> Path:
    root = artifact_root or (PACKAGE_DIR / "aqe_artifacts")
    root = Path(root).expanduser()
    run_dir = root / make_pause_pipeline_run_id(
        source_path.name,
        max_length=_max_pause_pipeline_run_id_length(root),
    )
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
        "created_at": datetime.now(UTC).isoformat(),
        "operation": "pause_removal",
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
        "deep_filter_post_filter": config.deep_filter_post_filter,
        "pause_detection_algorithm": config.pause_detection_algorithm,
        "pause_aggressiveness": config.pause_aggressiveness,
        "pause_silencedetect_threshold_db": config.pause_silencedetect_threshold_db,
        "pause_silencedetect_min_silence_seconds": (
            config.pause_silencedetect_min_silence_seconds
        ),
        "pause_silencedetect_min_speech_seconds": (
            config.pause_silencedetect_min_speech_seconds
        ),
        "pause_silencedetect_preprocess_denoise": (
            config.pause_silencedetect_preprocess_denoise
        ),
        "pause_silero_threshold": config.pause_silero_threshold,
        "pause_silero_min_silence_seconds": config.pause_silero_min_silence_seconds,
        "pause_silero_min_speech_seconds": config.pause_silero_min_speech_seconds,
        "pause_silero_preprocess_denoise": config.pause_silero_preprocess_denoise,
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

"""Managed runtime asset installation and lookup facade."""

from __future__ import annotations

from .runtime_install import (
    DOWNLOAD_TIMEOUT_SECONDS,
    USER_AGENT,
    ensure_runtime,
    ensure_runtime_async,
    runtime_status,
)
from .runtime_lookup import (
    expected_managed_model_path,
    expected_managed_silero_vad_model_path,
    expected_managed_spleeter_model_path,
    expected_managed_tool_path,
    is_runtime_ready,
    managed_model_path,
    managed_silero_vad_model_path,
    managed_spleeter_model_path,
    managed_tool_path,
)
from .runtime_manifest import sha256_file
from .runtime_paths import (
    DOWNLOADS_DIRNAME,
    RUNTIME_DIRNAME,
    RUNTIME_STATE_FILENAME,
    USER_FILES_DIRNAME,
    managed_runtime_root,
    runtime_base_dir,
    runtime_manifest_path,
    runtime_state_path,
    user_files_dir,
)
from .runtime_platform import _TOOL_EXECUTABLES, current_platform_key, platform
from .runtime_state import (
    RUNTIME_PHASE_DOWNLOADING,
    RUNTIME_PHASE_ERROR,
    RUNTIME_PHASE_MISSING,
    RUNTIME_PHASE_READY,
    RUNTIME_PHASE_UNSUPPORTED,
    RUNTIME_SOURCE_MANAGED,
    read_state,
)

__all__ = [
    "DOWNLOADS_DIRNAME",
    "DOWNLOAD_TIMEOUT_SECONDS",
    "RUNTIME_DIRNAME",
    "RUNTIME_PHASE_DOWNLOADING",
    "RUNTIME_PHASE_ERROR",
    "RUNTIME_PHASE_MISSING",
    "RUNTIME_PHASE_READY",
    "RUNTIME_PHASE_UNSUPPORTED",
    "RUNTIME_SOURCE_MANAGED",
    "RUNTIME_STATE_FILENAME",
    "USER_AGENT",
    "USER_FILES_DIRNAME",
    "_TOOL_EXECUTABLES",
    "current_platform_key",
    "ensure_runtime",
    "ensure_runtime_async",
    "expected_managed_model_path",
    "expected_managed_silero_vad_model_path",
    "expected_managed_spleeter_model_path",
    "expected_managed_tool_path",
    "is_runtime_ready",
    "managed_model_path",
    "managed_runtime_root",
    "managed_silero_vad_model_path",
    "managed_spleeter_model_path",
    "managed_tool_path",
    "platform",
    "read_state",
    "runtime_base_dir",
    "runtime_manifest_path",
    "runtime_state_path",
    "runtime_status",
    "sha256_file",
    "user_files_dir",
]

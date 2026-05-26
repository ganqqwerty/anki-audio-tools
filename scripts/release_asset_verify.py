"""Verification helpers for release assets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.release_asset_common import (
    SHARED_FILE_NAMES,
    VerificationResult,
    _shared_file_entry,
    _tool_entry,
    _validate_target,
    sha256_file,
    tracked_runtime_file_path,
    tracked_shared_asset_path,
)
from scripts.release_sherpa_assets import append_sherpa_spleeter_smoke_report
from scripts.release_silero_assets import append_silero_vad_smoke_report


def verify_assets(
    lock: dict[str, Any],
    *,
    cache_dir: Path,
    addon_bin_dir: Path,
    target_keys: list[str],
    run_diagnostics: bool,
    lock_tools,
    tool_runtime_files,
    source_tool_binary_path,
    current_target_key,
    append_diagnostic_report,
) -> VerificationResult:
    errors: list[str] = []
    reports: list[str] = []
    for target in target_keys:
        _validate_target(target)
        for tool_name in lock_tools(lock, target):
            _verify_tool_asset(
                lock,
                cache_dir,
                addon_bin_dir,
                reports,
                errors,
                target,
                tool_name,
                run_diagnostics=run_diagnostics,
                source_tool_binary_path=source_tool_binary_path,
                current_target_key=current_target_key,
                append_diagnostic_report=append_diagnostic_report,
            )
            _verify_tool_runtime_files(lock, addon_bin_dir, reports, errors, target, tool_name, tool_runtime_files)
    for file_name in SHARED_FILE_NAMES:
        _verify_shared_asset(lock, addon_bin_dir, reports, errors, file_name)
    if run_diagnostics:
        append_sherpa_spleeter_smoke_report(
            lock,
            cache_dir=cache_dir,
            addon_bin_dir=addon_bin_dir,
            target_keys=target_keys,
            current_target=current_target_key(),
            reports=reports,
            errors=errors,
        )
        append_silero_vad_smoke_report(
            lock,
            addon_bin_dir=addon_bin_dir,
            target_keys=target_keys,
            current_target=current_target_key(),
            reports=reports,
            errors=errors,
        )
    return VerificationResult(errors=errors, reports=reports)


def _verify_tool_asset(
    lock: dict[str, Any],
    cache_dir: Path,
    addon_bin_dir: Path,
    reports: list[str],
    errors: list[str],
    target: str,
    tool_name: str,
    *,
    run_diagnostics: bool,
    source_tool_binary_path,
    current_target_key,
    append_diagnostic_report,
) -> None:
    entry = _tool_entry(lock, target, tool_name)
    path = source_tool_binary_path(cache_dir, addon_bin_dir, target, tool_name, entry)
    actual_sha = _verified_asset_sha(path, entry.get("sha256"), errors, f"{target}/{tool_name}", "binary")
    if actual_sha is None:
        return
    reports.append(f"{target}/{tool_name}: {path} sha256={actual_sha}")
    if run_diagnostics and target == current_target_key():
        append_diagnostic_report(path, entry, reports, errors, target, tool_name)


def _verify_shared_asset(
    lock: dict[str, Any],
    addon_bin_dir: Path,
    reports: list[str],
    errors: list[str],
    file_name: str,
) -> None:
    entry = _shared_file_entry(lock, file_name)
    path = tracked_shared_asset_path(addon_bin_dir, entry)
    actual_sha = _verified_asset_sha(path, entry.get("sha256"), errors, f"shared/{file_name}", "file")
    if actual_sha is not None:
        reports.append(f"shared/{file_name}: {path} sha256={actual_sha}")


def _verify_tool_runtime_files(
    lock: dict[str, Any],
    addon_bin_dir: Path,
    reports: list[str],
    errors: list[str],
    target: str,
    tool_name: str,
    tool_runtime_files,
) -> None:
    for file_entry in tool_runtime_files(lock, target, tool_name):
        label = f"{target}/{tool_name}/{file_entry['path']}"
        path = tracked_runtime_file_path(addon_bin_dir, target, file_entry)
        actual_sha = _verified_asset_sha(path, file_entry.get("sha256"), errors, label, "file")
        if actual_sha is not None:
            reports.append(f"{label}: {path} sha256={actual_sha}")


def _verified_asset_sha(
    path: Path,
    expected_sha: object,
    errors: list[str],
    label: str,
    asset_kind: str,
) -> str | None:
    if not path.is_file():
        errors.append(f"{label}: missing {asset_kind} at {path}")
        return None
    if not expected_sha:
        errors.append(f"{label}: missing sha256 in release_assets.lock.json")
        return None
    actual_sha = sha256_file(path)
    if actual_sha != expected_sha:
        errors.append(f"{label}: checksum mismatch (expected {expected_sha}, got {actual_sha})")
        return None
    return actual_sha

"""Settings async operation implementations."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..contracts_generated import (
    Config,
    HealthReport,
    RuntimeStatus,
    ShowLogFileResult,
    SupportReportResult,
)
from ..diagnostics_runtime import record_breadcrumb, support_report_context
from ..errors import SettingsCommandError

CONTRACT_DECODE_ERRORS = (AssertionError, TypeError, ValueError)


def dispatch_settings_async_op(
    op: str,
    payload: dict[str, Any],
    progress_fn: Callable[[int, str], None],
) -> Any:
    """Run one settings async operation."""
    if op == "health_check":
        return _op_health_check(payload, progress_fn)
    if op == "support_report":
        return _op_support_report(payload, progress_fn)
    if op == "show_log_file":
        return _op_show_log_file(progress_fn)
    if op == "runtime_status":
        return _op_runtime_status()
    if op == "runtime_install":
        return _op_runtime_install(progress_fn)
    raise SettingsCommandError(f"Unknown async operation: {op}")


def _op_health_check(
    payload: dict[str, Any],
    progress_fn: Callable[[int, str], None],
) -> Any:
    from aqt import mw

    from ..db_helpers import build_health_report
    from ..diagnostics import (
        build_deep_filter_health,
        build_dpdfnet_health,
        build_rnnoise_health,
        build_silero_vad_health,
        build_spleeter_health,
    )
    from ..i18n import t

    progress_fn(20, t("settings.health.inspecting_collection"))
    report = build_health_report(mw.col)
    progress_fn(55, t("settings.health.checking_deep_filter"))
    config = _config_payload(payload)
    report["deep_filter"] = build_deep_filter_health(config)
    progress_fn(75, t("settings.health.checking_rnnoise"))
    report["rnnoise"] = build_rnnoise_health()
    progress_fn(85, t("settings.health.checking_dpdfnet"))
    report["dpdfnet"] = build_dpdfnet_health()
    progress_fn(95, t("settings.health.checking_spleeter"))
    report["spleeter"] = build_spleeter_health()
    report["silero_vad"] = build_silero_vad_health()
    report["runtime"] = _runtime_status_for_settings()
    progress_fn(100, t("settings.async.done"))
    return HealthReport.from_dict(report).to_dict()


def _op_support_report(payload: dict[str, Any], progress_fn: Callable[[int, str], None]) -> Any:
    from aqt import mw

    from .._version import __version__
    from ..diagnostics import (
        build_deep_filter_health,
        build_dpdfnet_health,
        build_rnnoise_health,
        build_silero_vad_health,
        build_spleeter_health,
    )
    from ..i18n import t
    from ..release_info import read_release_info
    from ..support import (
        addon_log_path,
        build_support_report_text,
        latest_denoise_support_incident,
        latest_pause_pipeline_support_incident,
        latest_spleeter_support_incident,
        read_log_tail,
    )

    record_breadcrumb("settings.support_report.collect", source="settings", operation="settings.support_report")
    progress_fn(20, t("settings.support.collecting_environment"))
    config = _config_payload(payload)
    addon_id = mw.addonManager.addonFromModule(__name__)
    addon_dir = mw.addonManager.addonsFolder(addon_id)
    log_path = addon_log_path(addon_dir)
    progress_fn(50, t("settings.support.checking_external_tools"))
    deep_filter_health = build_deep_filter_health(config)
    rnnoise_health = build_rnnoise_health()
    dpdfnet_health = build_dpdfnet_health()
    spleeter_health = build_spleeter_health()
    silero_vad_health = build_silero_vad_health()
    progress_fn(75, t("settings.support.reading_recent_logs"))
    diagnostics_context = support_report_context()
    diagnostics_context["runtime"] = _runtime_status_for_settings()
    report_text = build_support_report_text(
        version=__version__,
        addon_dir=addon_dir,
        log_file_path=str(log_path),
        deep_filter_health=deep_filter_health,
        rnnoise_health=rnnoise_health,
        dpdfnet_health=dpdfnet_health,
        silero_vad_health=silero_vad_health,
        denoise_incident=latest_denoise_support_incident(),
        pause_pipeline_incident=latest_pause_pipeline_support_incident(),
        log_tail=read_log_tail(log_path),
        spleeter_health=spleeter_health,
        spleeter_incident=latest_spleeter_support_incident(),
        diagnostics_context=diagnostics_context,
        release_info=read_release_info(addon_dir),
    )
    progress_fn(100, t("settings.async.done"))
    return SupportReportResult(report_text).to_dict()


def _op_show_log_file(
    progress_fn: Callable[[int, str], None],
) -> Any:
    from aqt import mw

    from ..file_reveal import reveal_file
    from ..i18n import t
    from ..support import addon_log_path

    progress_fn(25, t("settings.log.locating"))
    addon_id = mw.addonManager.addonFromModule(__name__)
    addon_dir = mw.addonManager.addonsFolder(addon_id)
    log_path = addon_log_path(addon_dir)
    progress_fn(75, t("settings.log.opening"))
    reveal_file(log_path, missing_message=t("settings.log.missing"))
    progress_fn(100, t("settings.async.done"))
    return ShowLogFileResult(str(log_path)).to_dict()


def _op_runtime_status() -> Any:
    return RuntimeStatus.from_dict(_runtime_status_for_settings()).to_dict()


def _op_runtime_install(progress_fn: Callable[[int, str], None]) -> Any:
    from .. import runtime_manager
    from ..i18n import t

    def _progress(progress_status: dict[str, Any]) -> None:
        progress_fn(int(progress_status.get("progress", 0) or 0), str(progress_status.get("message", "")))

    progress_fn(1, t("settings.runtime.installing"))
    status = runtime_manager.ensure_runtime(_addon_dir_for_settings(), progress=_progress)
    progress_fn(100, status.get("message") or status.get("error") or t("settings.async.done"))
    return RuntimeStatus.from_dict(status).to_dict()


def _config_payload(payload: dict[str, Any]) -> dict[str, Any]:
    raw_config = payload.get("config")
    if not isinstance(raw_config, dict):
        return {}
    try:
        return Config.from_dict(raw_config).to_dict()
    except CONTRACT_DECODE_ERRORS:
        return {}


def _runtime_status_for_settings() -> dict[str, Any]:
    from ..runtime_manager import runtime_status

    return runtime_status(_addon_dir_for_settings())


def _addon_dir_for_settings() -> Path:
    from aqt import mw

    addon_id = mw.addonManager.addonFromModule(__name__)
    return Path(mw.addonManager.addonsFolder(addon_id))

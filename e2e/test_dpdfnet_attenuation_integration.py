"""E2E tests for DPDFNet aggressiveness settings integration."""

from __future__ import annotations

import json

from PyQt6.QtWidgets import QApplication

from e2e.conftest import import_runtime_addon_module
from e2e.editor_note_helpers import (
    ADDON_NUMERIC_ID,
    _configure_ffmpeg,
)
from e2e.helpers import (
    click_selector,
    run_js,
    wait_for_condition,
    wait_for_js_condition,
    wait_for_selector,
)
from e2e.settings_dialog_helpers import open_settings_dialog


def _split_slug(command: str) -> str:
    if command in {"aqe:volume-up", "aqe:volume-down"}:
        return "volume"
    if command in {"aqe:faster", "aqe:slower"}:
        return "speed"
    return command.removeprefix("aqe:")


def _split_menu_selector(command: str, ord_: int = 0) -> str:
    slug = _split_slug(command)
    return f'[data-testid="aqe-split-{ord_}-{slug}-menu"]'


def test_settings_dialog_saves_dpdfnet_aggressiveness(anki_mw) -> None:
    config = anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID) or {}
    config["dpdfnet_attn_limit_db"] = 12.0
    anki_mw.addonManager.writeConfig(ADDON_NUMERIC_ID, config)

    dialog = open_settings_dialog(anki_mw)
    selector = '[data-testid="dpdfnet-attn-limit-db-18"]'
    wait_for_selector(dialog, selector, timeout=5.0)
    click_selector(dialog, selector, timeout=5.0)
    wait_for_js_condition(
        dialog,
        f"document.querySelector({json.dumps(selector)})?.getAttribute('aria-checked')",
        lambda value: value == "true",
        timeout=5.0,
    )

    click_selector(dialog, '[data-testid="settings-save"]', timeout=5.0)
    wait_for_condition(
        lambda: not dialog.isVisible(),
        timeout=5.0,
        message="Timed out waiting for settings dialog to close after save",
    )
    saved_config = anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID) or {}
    assert saved_config["dpdfnet_attn_limit_db"] == 18


def test_batch_dialog_emits_saved_dpdfnet_aggressiveness(anki_mw, ffmpeg_config) -> None:
    audio_processing_config = import_runtime_addon_module(".audio_state").AudioProcessingConfig
    field_group = import_runtime_addon_module(".batch_operations").FieldGroup
    batch_operations_dialog = import_runtime_addon_module(".browser_dialog").BatchOperationsDialog

    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        dpdfnet_attn_limit_db=18.0,
        speed_step=1.5,
        volume_step_db=6.0,
        pause_aggressiveness="aggressive",
    )
    config = audio_processing_config.from_config(
        anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID) or {}
    )
    started_requests = []
    dialog = batch_operations_dialog(
        anki_mw,
        [1, 2],
        (field_group("Basic", ("Front", "Back")),),
        config,
        lambda _browser, _dialog, _note_ids, captured_request: started_requests.append(captured_request),
    )
    dialog._dialog.show()
    QApplication.processEvents()
    try:
        wait_for_js_condition(
            dialog._webview,
            """
            (() => {
              const operation = document.querySelector('select')?.value;
              const labels = Array.from(document.querySelectorAll('label')).map((label) => label.textContent || "");
              return { operation, labels };
            })()
            """,
            lambda value: value is not None and value["operation"] == "graph",
            timeout=5.0,
        )
        run_js(
            dialog._webview,
            """
            const operation = document.querySelector('[data-testid="batch-operation"]');
            operation.value = 'denoise';
            operation.dispatchEvent(new Event('change', { bubbles: true }));
            """,
        )
        wait_for_selector(dialog._webview, '[data-testid="batch-denoise-algorithm-dpdfnet"]')
        click_selector(dialog._webview, '[data-testid="batch-denoise-algorithm-dpdfnet"]')
        wait_for_selector(dialog._webview, '[data-testid="batch-dpdfnet-attn-limit-db-18"]')
        click_selector(dialog._webview, '[data-testid="batch-dpdfnet-attn-limit-db-18"]')
        click_selector(dialog._webview, '[data-testid="batch-start"]')
        wait_for_condition(
            lambda: len(started_requests) == 1,
            timeout=5.0,
            message="Batch dialog did not emit a start request",
        )

        request = started_requests[0]
        assert request.operation == "denoise"
        assert request.parameters.denoise_algorithm == "dpdfnet"
        assert request.parameters.dpdfnet_attn_limit_db == 18.0
    finally:
        dialog._dialog.close()

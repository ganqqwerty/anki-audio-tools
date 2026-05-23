"""E2E tests for DPDFNet aggressiveness settings integration."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from PyQt6.QtWidgets import QApplication

from e2e.editor_note_helpers import (
    ADDON_NUMERIC_ID,
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
    _sound_filename,
    _wait_for_status_flow,
)
from e2e.helpers import (
    click_selector,
    generate_tone,
    wait_for_condition,
    wait_for_js_condition,
    wait_for_selector,
)
from e2e.test_settings_dialog import _open_settings_dialog


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

    dialog = _open_settings_dialog(anki_mw)
    selector = '[data-testid="dpdfnet-attn-limit-db-18"]'
    wait_for_selector(dialog, selector, timeout=5.0)
    click_selector(dialog, selector, timeout=5.0)
    wait_for_js_condition(
        dialog,
        f"document.querySelector({json.dumps(selector)})?.getAttribute('aria-checked')",
        lambda value: value == "true",
        timeout=5.0,
    )

    with patch.object(
        anki_mw.addonManager,
        "writeConfig",
        wraps=anki_mw.addonManager.writeConfig,
    ) as mock_write:
        click_selector(dialog, '[data-testid="settings-save"]', timeout=5.0)
        wait_for_condition(lambda: mock_write.called, timeout=5.0)

    saved_config = mock_write.call_args.args[1]
    assert saved_config["dpdfnet_attn_limit_db"] == 18


def test_editor_dpdfnet_uses_selected_aggressiveness(
    anki_mw,
    ffmpeg_config,
    monkeypatch,
) -> None:
    from anki_audio_quick_editor.audio_state import AudioProcessingConfig

    captured: list[float] = []
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_dpdfnet_attn_limit_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, dpdfnet_attn_limit_db=18.0)

    def fake_render_dpdfnet_audio(
        _source_path: Path,
        config: AudioProcessingConfig,
        output_path: Path,
        **_kwargs,
    ) -> None:
        captured.append(config.dpdfnet_attn_limit_db)
        output_path.write_bytes(b"denoised")

    monkeypatch.setattr(
        "anki_audio_quick_editor.editor_dependencies.render_dpdfnet_audio",
        fake_render_dpdfnet_audio,
    )

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:denoise-standard"), timeout=10.0)
        click_selector(editor.web, _split_menu_selector("aqe:denoise-standard"), timeout=5.0)
        wait_for_js_condition(
            editor.web,
            """
            document.querySelector('[data-testid="aqe-split-0-denoise-standard-preset-dpdfnet"]')
              ?.getAttribute('data-aqe-tooltip-content')
            """,
            lambda value: value == "Denoise speech with DPDFNet, Aggressiveness: Aggressive",
            timeout=5.0,
        )
        click_selector(
            editor.web,
            '[data-testid="aqe-split-0-denoise-standard-preset-dpdfnet"]',
            timeout=5.0,
        )
        wait_for_js_condition(
            editor.web,
            """
            document.querySelector('[data-testid="aqe-button-0-denoise-standard"]')
              ?.getAttribute('data-aqe-tooltip-content')
            """,
            lambda value: value == "Remove noise and music using DPDFNet",
            timeout=5.0,
        )
        click_selector(editor.web, _button_selector("aqe:denoise-standard"), timeout=5.0)
        wait_for_condition(
            lambda: captured == [18.0] and _sound_filename(note.fields[0]) != source.name,
            timeout=10.0,
            message="Editor did not pass selected DPDFNet aggressiveness to renderer",
        )
        _wait_for_status_flow(
            editor,
            lambda status: status["text"] == "Cleaned audio with DPDFNet at Aggressive aggressiveness.",
            timeout=10.0,
        )
    finally:
        editor.set_note(None)
        parent.close()


def test_batch_dialog_loads_with_saved_dpdfnet_aggressiveness(anki_mw, ffmpeg_config) -> None:
    from anki_audio_quick_editor.audio_state import AudioProcessingConfig
    from anki_audio_quick_editor.batch_operations import FieldGroup
    from anki_audio_quick_editor.browser_dialog import BatchOperationsDialog

    _configure_ffmpeg(
        anki_mw,
        ffmpeg_config,
        dpdfnet_attn_limit_db=18.0,
        speed_step=0.1,
        volume_step_db=6.0,
        pause_aggressiveness="aggressive",
    )
    config = AudioProcessingConfig.from_config(
        anki_mw.addonManager.getConfig(ADDON_NUMERIC_ID) or {}
    )
    started_requests = []
    dialog = BatchOperationsDialog(
        anki_mw,
        [1, 2],
        (FieldGroup("Basic", ("Front", "Back")),),
        config,
        lambda _browser, _dialog, _note_ids, request: started_requests.append(request),
    )
    dialog._dialog.show()
    QApplication.processEvents()
    try:
        state = wait_for_js_condition(
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
        assert "Operation" in " ".join(state["labels"])
        assert config.dpdfnet_attn_limit_db == 18.0
        assert started_requests == []
    finally:
        dialog._dialog.close()

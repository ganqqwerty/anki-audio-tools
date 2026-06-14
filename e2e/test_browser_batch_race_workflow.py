from __future__ import annotations

from e2e.browser_workflow_helpers import (
    add_basic_audio_note,
    click_batch_start,
    open_batch_dialog,
    select_batch_operation,
    trigger_cards_menu_action,
    wait_for_batch_dialog_ready,
)
from e2e.conftest import import_runtime_addon_module
from e2e.helpers import run_js, wait_for_js_condition


def test_batch_dialog_running_controls_explain_disabled_tooltip(anki_mw, monkeypatch) -> None:
    note = add_basic_audio_note(
        anki_mw,
        ("aqe_browser_batch_one.mp3",),
    )

    def fake_run_batch(_browser, _run_dialog, _note_ids, _request):
        return None

    browser_dialog = import_runtime_addon_module(".browser_dialog")
    browser, opened_context, action_label = open_batch_dialog(
        anki_mw,
        note,
        browser_dialog.BatchOperationsDialog,
    )
    monkeypatch.setattr(browser_dialog.BatchOperationsDialog, "exec", lambda self: 0)
    monkeypatch.setattr(browser_dialog, "run_batch_in_background", fake_run_batch, raising=False)

    with opened_context as opened:
        trigger_cards_menu_action(browser, action_label)
        assert len(opened) == 1
        dialog = opened[0]
        dialog._run_batch_in_background = fake_run_batch
        wait_for_batch_dialog_ready(dialog)
        select_batch_operation(dialog, "remove_pauses")
        click_batch_start(dialog)
        wait_for_js_condition(
            dialog._webview,
            """
            (() => {
              const operation = document.querySelector('[data-testid="batch-operation"]');
              return operation ? operation.value : null;
            })();
            """,
            lambda value: value == "remove_pauses",
            timeout=5.0,
        )

        tooltip_state = wait_for_js_condition(
            dialog._webview,
            """
            (() => {
              const button = document.querySelector('[data-testid="batch-pause-aggressiveness-aggressive"]');
              const wrapper = button?.closest('.field-tooltip-target');
              return button && wrapper ? {
                disabled: button.disabled,
                buttonTooltip: button.getAttribute('data-aqe-tooltip-content') || '',
                wrapperTooltip: wrapper.getAttribute('data-aqe-tooltip-content') || '',
              } : null;
            })();
            """,
            lambda value: (
                value
                and value["disabled"] is True
                and "150 ms" in value["buttonTooltip"]
                and "Disabled while the batch is running." in value["buttonTooltip"]
                and "Disabled while the batch is running." in value["wrapperTooltip"]
            ),
            timeout=5.0,
        )

        assert "Aggressive" in tooltip_state["buttonTooltip"]

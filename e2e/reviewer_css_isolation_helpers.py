"""Reviewer CSS-isolation assertions for inline audio controls."""

from __future__ import annotations

from e2e.editor_note_helpers import _button_selector
from e2e.editor_region_loop_helpers import _shift_drag_region
from e2e.helpers import wait_for_js_condition


def assert_reviewer_audio_controls_css_isolated(reviewer, field_ord: int) -> None:
    """Assert hostile card CSS cannot alter AQE reviewer control spacing."""
    style = wait_for_js_condition(
        reviewer.web,
        f"""
        (() => {{
          const controls = document.querySelector('.aqe-controls[data-aqe-field-ord="{field_ord}"]');
          const button = document.querySelector({(_button_selector('aqe:play', field_ord))!r});
          const removePausesButton = document.querySelector({(_button_selector('aqe:remove-pauses', field_ord))!r});
          const splitMenu = document.querySelector('[data-testid="aqe-split-{field_ord}-play-menu"]');
          const help = document.querySelector('[data-testid="aqe-help-{field_ord}"]');
          const icon = button?.querySelector('svg, .aqe-button-icon');
          const removePausesLabel = removePausesButton?.querySelector('.aqe-button-label');
          if (!controls || !button || !removePausesButton || !splitMenu || !help || !removePausesLabel) return null;
          help.open = true;
          const helpCommand = help.querySelector('.aqe-help-command');
          if (!helpCommand) return null;
          const controlsStyle = getComputedStyle(controls);
          const buttonStyle = getComputedStyle(button);
          const helpCommandStyle = getComputedStyle(helpCommand);
          const removePausesButtonStyle = getComputedStyle(removePausesButton);
          const removePausesLabelStyle = getComputedStyle(removePausesLabel);
          const splitMenuStyle = getComputedStyle(splitMenu);
          const iconStyle = icon ? getComputedStyle(icon) : null;
          const helpRect = help.getBoundingClientRect();
          const helpCommandRect = helpCommand.getBoundingClientRect();
          const buttonRect = button.getBoundingClientRect();
          const host = controls.closest('.aqe-mount-host');
          const hostClone = host ? host.cloneNode(true) : null;
          let naturalControlsWidth = controls.getBoundingClientRect().width;
          if (hostClone instanceof HTMLElement) {{
            hostClone.style.left = '-10000px';
            hostClone.style.maxWidth = 'none';
            hostClone.style.position = 'absolute';
            hostClone.style.visibility = 'hidden';
            hostClone.style.width = 'auto';
            document.body.appendChild(hostClone);
            naturalControlsWidth = hostClone.querySelector('.aqe-controls').getBoundingClientRect().width;
            hostClone.remove();
          }}
          const toolbarItems = Array.from(controls.children)
            .filter((node) => !node.matches('.aqe-help, .aqe-visualizer, .aqe-status-row'));
          const maxRowGap = toolbarItems.reduce((maxGap, node, index) => {{
            const next = toolbarItems[index + 1];
            if (!next) return maxGap;
            const rect = node.getBoundingClientRect();
            const nextRect = next.getBoundingClientRect();
            if (Math.abs(nextRect.top - rect.top) > 4) return maxGap;
            return Math.max(maxGap, nextRect.left - rect.right);
          }}, 0);
          return {{
            controlsBorderColor: controlsStyle.borderTopColor,
            controlsJustifyContent: controlsStyle.justifyContent,
            controlsWidth: controls.getBoundingClientRect().width,
            maxRowGap,
            naturalControlsWidth,
            borderTopWidth: buttonStyle.borderTopWidth,
            marginLeft: buttonStyle.marginLeft,
            paddingLeft: buttonStyle.paddingLeft,
            removePausesFontFamily: removePausesButtonStyle.fontFamily,
            removePausesFontSize: removePausesButtonStyle.fontSize,
            removePausesLabelFontSize: removePausesLabelStyle.fontSize,
            removePausesLabelPaddingLeft: removePausesLabelStyle.paddingLeft,
            splitMenuPaddingLeft: splitMenuStyle.paddingLeft,
            splitMenuWidth: splitMenu.getBoundingClientRect().width,
            textTransform: buttonStyle.textTransform,
            viewportWidth: document.documentElement.clientWidth,
            iconTransform: iconStyle ? iconStyle.transform : null,
            helpCommandFontSize: helpCommandStyle.fontSize,
            helpCommandPaddingLeft: helpCommandStyle.paddingLeft,
            helpCommandPaddingTop: helpCommandStyle.paddingTop,
            helpCommandHeight: helpCommandRect.height,
            helpLeftDelta: helpRect.left - controls.getBoundingClientRect().left,
            helpTopDelta: helpRect.top - buttonRect.bottom,
          }};
        }})()
        """,
        lambda value: isinstance(value, dict),
        timeout=5.0,
    )

    assert style["borderTopWidth"] == "1px"
    assert style["controlsBorderColor"] not in {"rgba(0, 0, 0, 0)", "transparent"}
    assert style["controlsJustifyContent"] == "flex-start"
    assert style["controlsWidth"] <= style["naturalControlsWidth"] + 4
    assert style["maxRowGap"] <= 8
    assert style["marginLeft"] == "0px"
    assert style["paddingLeft"] != "24px"
    assert "Georgia" not in style["removePausesFontFamily"]
    assert style["removePausesFontSize"] == "12px"
    assert style["removePausesLabelFontSize"] == "12px"
    assert style["removePausesLabelPaddingLeft"] == "0px"
    assert style["splitMenuPaddingLeft"] == "0px"
    assert style["splitMenuWidth"] <= 18
    assert style["textTransform"] != "uppercase"
    assert style["helpCommandFontSize"] == "12px"
    assert style["helpCommandPaddingLeft"] == "6px"
    assert style["helpCommandPaddingTop"] == "2px"
    assert style["helpCommandHeight"] <= 30
    assert abs(style["helpLeftDelta"]) <= 8
    assert style["helpTopDelta"] >= -2
    if style["iconTransform"] is not None:
        assert style["iconTransform"] in {"none", "matrix(1, 0, 0, 1, 0, 0)"}


def assert_reviewer_remove_pauses_popover_css_isolated(reviewer, field_ord: int) -> None:
    """Assert the Shorten Pauses popover keeps AQE-owned padding and font."""
    popover_style = wait_for_js_condition(
        reviewer.web,
        f"""
        (() => {{
          const menu = document.querySelector('[data-testid="aqe-split-{field_ord}-remove-pauses-menu"]');
          if (!menu) return null;
          if (menu.getAttribute("aria-expanded") !== "true") menu.click();
          const popover = document.querySelector('[data-testid="aqe-split-{field_ord}-remove-pauses-popover"]');
          const title = popover?.querySelector('.aqe-split-popover-title');
          const preset = popover?.querySelector('.aqe-split-preset');
          if (!popover || !title || !preset) return null;
          const popoverStyle = getComputedStyle(popover);
          const titleStyle = getComputedStyle(title);
          const presetStyle = getComputedStyle(preset);
          return {{
            paddingLeft: popoverStyle.paddingLeft,
            titleFontFamily: titleStyle.fontFamily,
            titleFontSize: titleStyle.fontSize,
            presetPaddingLeft: presetStyle.paddingLeft,
          }};
        }})()
        """,
        lambda value: isinstance(value, dict),
        timeout=5.0,
    )
    assert popover_style["paddingLeft"] == "10px"
    assert "Georgia" not in popover_style["titleFontFamily"]
    assert popover_style["titleFontSize"] == "12px"
    assert popover_style["presetPaddingLeft"] == "6px"


def assert_reviewer_segment_panel_css_isolated(reviewer, field_ord: int) -> None:
    """Assert the floating segment panel keeps its own padding and sizing."""
    _shift_drag_region(reviewer, 0.25, 0.75, ord_=field_ord)
    segment_style = wait_for_js_condition(
        reviewer.web,
        f"""
        (() => {{
          const entry = document.querySelector('[data-testid="aqe-selection-toolbar-practice-segments-{field_ord}"]');
          if (!entry) return null;
          const panelSelector = '[data-testid="aqe-segment-{field_ord}-panel"]';
          if (!document.querySelector(panelSelector)) entry.click();
          const panel = document.querySelector(panelSelector);
          const controls = panel?.querySelector('.aqe-segment-practice-controls');
          const edit = panel?.querySelector('[data-testid="aqe-segment-{field_ord}-edit"]');
          const clear = panel?.querySelector('[data-testid="aqe-segment-{field_ord}-clear"]');
          if (!panel || !controls || !edit || !clear) return null;
          const panelStyle = getComputedStyle(panel);
          const controlsStyle = getComputedStyle(controls);
          const editStyle = getComputedStyle(edit);
          const clearStyle = getComputedStyle(clear);
          return {{
            panelPaddingLeft: panelStyle.paddingLeft,
            panelFontSize: panelStyle.fontSize,
            controlsGap: controlsStyle.gap,
            editFontSize: editStyle.fontSize,
            editPaddingLeft: editStyle.paddingLeft,
            clearPaddingLeft: clearStyle.paddingLeft,
          }};
        }})()
        """,
        lambda value: isinstance(value, dict),
        timeout=5.0,
    )
    assert segment_style["panelPaddingLeft"] == "8px"
    assert segment_style["panelFontSize"] == "12px"
    assert segment_style["controlsGap"] == "6px"
    assert segment_style["editFontSize"] == "11px"
    assert segment_style["editPaddingLeft"] == "8px"
    assert segment_style["clearPaddingLeft"] == "0px"

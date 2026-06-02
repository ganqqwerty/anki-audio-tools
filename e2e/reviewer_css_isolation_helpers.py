"""Reviewer CSS-isolation assertions for inline audio controls."""

from __future__ import annotations

from e2e.editor_note_helpers import _button_selector
from e2e.editor_region_loop_helpers import _shift_drag_region
from e2e.helpers import wait_for_js_condition


def assert_reviewer_audio_controls_full_width(reviewer, field_ord: int) -> None:
    """Assert reviewer controls fill their available row before the graph opens."""
    layout = wait_for_js_condition(
        reviewer.web,
        f"""
        (() => {{
          const controls = document.querySelector('.aqe-controls[data-aqe-field-ord="{field_ord}"]');
          const host = controls?.closest('.aqe-mount-host');
          if (!controls || !(host instanceof HTMLElement) || !host.parentElement) return null;
          const hostRect = host.getBoundingClientRect();
          const parentRect = host.parentElement.getBoundingClientRect();
          const parentStyle = getComputedStyle(host.parentElement);
          const controlsRect = controls.getBoundingClientRect();
          const hostStyle = getComputedStyle(host);
          const controlsStyle = getComputedStyle(controls);
          const parentContentWidth = parentRect.width
            - parseFloat(parentStyle.paddingLeft || '0')
            - parseFloat(parentStyle.paddingRight || '0');
          return {{
            controlsBoxSizing: controlsStyle.boxSizing,
            controlsLeftDelta: Math.abs(controlsRect.left - hostRect.left),
            controlsRightDelta: Math.abs(controlsRect.right - hostRect.right),
            controlsWidth: controlsRect.width,
            hostBoxSizing: hostStyle.boxSizing,
            hostDisplay: hostStyle.display,
            hostPaddingLeft: hostStyle.paddingLeft,
            hostWidth: hostRect.width,
            parentContentWidth,
          }};
        }})()
        """,
        lambda value: isinstance(value, dict),
        timeout=5.0,
    )

    assert layout["hostDisplay"] == "block"
    assert layout["hostBoxSizing"] == "border-box"
    assert layout["hostPaddingLeft"] == "0px"
    assert layout["controlsBoxSizing"] == "border-box"
    assert layout["hostWidth"] >= layout["parentContentWidth"] - 8
    assert abs(layout["controlsWidth"] - layout["hostWidth"]) <= 2
    assert layout["controlsLeftDelta"] <= 1
    assert layout["controlsRightDelta"] <= 1


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
          if (!(host instanceof HTMLElement)) return null;
          const hostStyle = getComputedStyle(host);
          const controlsRect = controls.getBoundingClientRect();
          const hostRect = host.getBoundingClientRect();
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
            controlsRightDelta: Math.abs(controlsRect.right - hostRect.right),
            controlsWidth: controlsRect.width,
            maxRowGap,
            hostDisplay: hostStyle.display,
            hostPaddingLeft: hostStyle.paddingLeft,
            hostWidth: hostRect.width,
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
    assert style["hostDisplay"] == "block"
    assert style["hostPaddingLeft"] == "0px"
    assert abs(style["controlsWidth"] - style["hostWidth"]) <= 2
    assert style["controlsRightDelta"] <= 1
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


def assert_reviewer_tooltip_css_isolated(reviewer) -> None:
    """Assert AQE tooltip roots keep compact padding under hostile card CSS."""
    tooltip_style = wait_for_js_condition(
        reviewer.web,
        """
        (() => {
          const card = document.querySelector('.card') || document.body;
          const probe = document.createElement('div');
          probe.className = 'aqe-ui-root aqe-rich-tooltip';
          probe.textContent = 'Tooltip probe';
          card.appendChild(probe);
          const style = getComputedStyle(probe);
          const result = {
            fontSize: style.fontSize,
            marginLeft: style.marginLeft,
            paddingLeft: style.paddingLeft,
            paddingTop: style.paddingTop,
            textTransform: style.textTransform,
          };
          probe.remove();
          return result;
        })()
        """,
        lambda value: isinstance(value, dict),
        timeout=5.0,
    )
    assert tooltip_style["fontSize"] == "11px"
    assert tooltip_style["marginLeft"] == "0px"
    assert tooltip_style["paddingLeft"] == "8px"
    assert tooltip_style["paddingTop"] == "6px"
    assert tooltip_style["textTransform"] != "uppercase"


def assert_reviewer_back_chaining_panel_css_isolated(reviewer, field_ord: int) -> None:
    """Assert the back-chaining panel keeps its own padding and sizing."""
    _shift_drag_region(reviewer, 0.25, 0.75, ord_=field_ord)
    back_chaining_style = wait_for_js_condition(
        reviewer.web,
        f"""
        (() => {{
          const entry = document.querySelector('[data-testid="aqe-selection-toolbar-back-chaining-{field_ord}"]');
          if (!entry) return null;
          const panelSelector = '[data-testid="aqe-back-chaining-{field_ord}-panel"]';
          if (!document.querySelector(panelSelector)) entry.click();
          const panel = document.querySelector(panelSelector);
          const controls = panel?.querySelector('.aqe-back-chaining-controls');
          const edit = panel?.querySelector('[data-testid="aqe-back-chaining-{field_ord}-edit"]');
          const clear = panel?.querySelector('[data-testid="aqe-back-chaining-{field_ord}-clear"]');
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
    assert back_chaining_style["panelPaddingLeft"] == "6px"
    assert back_chaining_style["panelFontSize"] == "12px"
    assert back_chaining_style["controlsGap"] == "6px"
    assert back_chaining_style["editFontSize"] == "11px"
    assert back_chaining_style["editPaddingLeft"] == "8px"
    assert back_chaining_style["clearPaddingLeft"] == "0px"

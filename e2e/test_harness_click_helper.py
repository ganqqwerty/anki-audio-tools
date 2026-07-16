"""Real-WebEngine canaries for the synthetic click contract."""

from __future__ import annotations

import pytest

from e2e.helpers import click_selector, run_js, wait_for_js_condition
from e2e.settings_dialog_helpers import open_settings_dialog

pytestmark = pytest.mark.shared_desktop


def _install_click_fixture(web, variant: str) -> None:
    run_js(
        web,
        f"""
        (() => {{
          document.querySelector('#aqe-click-fixture')?.remove();
          const root = document.createElement('div');
          root.id = 'aqe-click-fixture';
          root.innerHTML = `
            <div style="height: 1800px"></div>
            <button id="aqe-click-target">Target</button>
            <div id="aqe-click-cover"></div>`;
          document.body.appendChild(root);
          const target = root.querySelector('#aqe-click-target');
          const cover = root.querySelector('#aqe-click-cover');
          target.addEventListener('click', () => {{ window.__aqeHarnessClicked = true; }});
          window.__aqeHarnessClicked = false;
          if ({variant!r} === 'hidden') target.style.display = 'none';
          if ({variant!r} === 'disabled') target.disabled = true;
          if ({variant!r} === 'pointer-none') target.style.pointerEvents = 'none';
          if ({variant!r} === 'covered') {{
            target.scrollIntoView({{ block: 'center' }});
            const rect = target.getBoundingClientRect();
            Object.assign(cover.style, {{
              position: 'fixed', left: `${{rect.left}}px`, top: `${{rect.top}}px`,
              width: `${{rect.width}}px`, height: `${{rect.height}}px`, zIndex: '999999'
            }});
          }}
          return true;
        }})()
        """,
    )


@pytest.mark.parametrize("variant", ["hidden", "disabled", "pointer-none", "covered"])
def test_click_helper_rejects_non_user_clickable_targets(anki_mw, variant: str) -> None:
    dialog = open_settings_dialog(anki_mw)
    try:
        _install_click_fixture(dialog, variant)
        with pytest.raises(TimeoutError, match="Timed out clicking selector"):
            click_selector(dialog, "#aqe-click-target", timeout=0.3)
    finally:
        dialog.close()


def test_click_helper_scrolls_offscreen_target_then_checks_real_hit_target(anki_mw) -> None:
    dialog = open_settings_dialog(anki_mw)
    try:
        _install_click_fixture(dialog, "offscreen")
        click_selector(dialog, "#aqe-click-target", timeout=2.0)
        wait_for_js_condition(
            dialog,
            "window.__aqeHarnessClicked === true",
            lambda value: value is True,
        )
    finally:
        dialog.close()

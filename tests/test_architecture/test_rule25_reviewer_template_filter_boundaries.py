"""Rule 25: Reviewer template-filter plumbing stays in reviewer-owned layers."""

from __future__ import annotations

from pathlib import Path

from .conftest import ADDON_DIR

PROJECT_ROOT = ADDON_DIR.parent.parent
SETTINGS_UI_DIR = PROJECT_ROOT / "settings_ui" / "src" / "editor-inline"
EDITOR_INTEGRATION = ADDON_DIR / "editor_integration.py"
EDITOR_WEBVIEW_INJECTION = ADDON_DIR / "editor_webview_injection.py"
REVIEWER_AUDIO_TARGETS = ADDON_DIR / "reviewer_audio_targets.py"
REVIEWER_INTEGRATION = ADDON_DIR / "reviewer_integration.py"
REVIEWER_TEMPLATE_FILTER = ADDON_DIR / "reviewer_template_filter.py"
REVIEWER_TEMPLATE_FILTER_INTEGRATION = ADDON_DIR / "reviewer_template_filter_integration.py"
REVIEWER_PANEL_TRIGGER = SETTINGS_UI_DIR / "reviewer-panel-trigger.ts"
DOM_SELECTORS = SETTINGS_UI_DIR / "dom-selectors.ts"
RUNTIME = SETTINGS_UI_DIR / "runtime.ts"


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _imports_module(source: str, module: str) -> bool:
    return (
        f"from .{module} import" in source
        or f"from anki_audio_quick_editor.{module} import" in source
        or f"import anki_audio_quick_editor.{module}" in source
    )


def test_aqe_audio_panel_template_filter_is_registered_only_by_tag_integration() -> None:
    offenders = [
        path.relative_to(ADDON_DIR).as_posix()
        for path in ADDON_DIR.rglob("*.py")
        if path != REVIEWER_TEMPLATE_FILTER_INTEGRATION and "field_filter" in _source(path)
    ]

    tag_integration_source = _source(REVIEWER_TEMPLATE_FILTER_INTEGRATION)
    target_source = _source(REVIEWER_AUDIO_TARGETS)
    filter_source = _source(REVIEWER_TEMPLATE_FILTER)

    assert offenders == []
    assert "anki_hooks.field_filter.append(_aqe_audio_panel_filter)" in tag_integration_source
    assert "gui_hooks.card_layout_will_show.append(_on_card_layout_will_show)" in tag_integration_source
    assert "from .reviewer_template_filter import audio_panel_filter_html" in tag_integration_source
    assert 'AQE_AUDIO_PANEL_FILTER = "aqe-audio-panel"' in target_source
    assert "_reviewer_editor_enabled" not in filter_source
    assert "enable_reviewer_editor" not in tag_integration_source


def test_edit_view_and_tag_entrypoints_do_not_import_each_other() -> None:
    entrypoints = {
        "edit mode": (
            EDITOR_INTEGRATION,
            (
                "reviewer_integration",
                "reviewer_template_filter",
                "reviewer_template_filter_integration",
            ),
        ),
        "view mode": (
            REVIEWER_INTEGRATION,
            (
                "editor_integration",
                "reviewer_template_filter",
                "reviewer_template_filter_integration",
            ),
        ),
        "tag mode": (
            REVIEWER_TEMPLATE_FILTER_INTEGRATION,
            (
                "editor_integration",
                "reviewer_integration",
            ),
        ),
    }
    offenders = [
        f"{owner}: imports {forbidden_module}"
        for owner, (path, forbidden_modules) in entrypoints.items()
        for forbidden_module in forbidden_modules
        if _imports_module(_source(path), forbidden_module)
    ]

    assert offenders == []
    assert _imports_module(_source(EDITOR_INTEGRATION), "editor_note_load_hooks")
    assert _imports_module(_source(REVIEWER_INTEGRATION), "editor_webview_injection")
    assert "from .reviewer_audio_targets import" in _source(REVIEWER_INTEGRATION)
    assert "from .reviewer_audio_targets import" in _source(REVIEWER_TEMPLATE_FILTER)


def test_reviewer_template_filter_helper_is_import_safe() -> None:
    filter_source = _source(REVIEWER_TEMPLATE_FILTER)
    target_source = _source(REVIEWER_AUDIO_TARGETS)

    for source in (filter_source, target_source):
        assert "from aqt" not in source
        assert "import anki" not in source
        assert "mw." not in source


def test_reviewer_panel_trigger_uses_runtime_and_selector_boundaries() -> None:
    trigger_source = _source(REVIEWER_PANEL_TRIGGER)
    selector_source = _source(DOM_SELECTORS)
    runtime_source = _source(RUNTIME)

    assert "document.querySelector" not in trigger_source
    assert "from \"./dom-selectors.js\"" in trigger_source
    assert "from \"./runtime.js\"" not in trigger_source
    assert "installReviewerPanelTriggers" in runtime_source
    assert "reviewTargetIsOpen" in runtime_source
    assert "allReviewerPanelTriggers" in selector_source
    assert "reviewerPanelTargetForTrigger" in selector_source

"""Tests for shared WebView shell rendering."""

from __future__ import annotations

from anki_audio_quick_editor.webview_shell import render_webview_content


def test_render_webview_content_embeds_state_bundle_and_error_reporter(tmp_path) -> None:
    bundle_js = tmp_path / "bundle.js"
    bundle_css = tmp_path / "bundle.css"
    bundle_js.write_text("window.__loaded = true;", encoding="utf-8")
    bundle_css.write_text(".app { color: red; }", encoding="utf-8")

    body, head = render_webview_content(
        initial_state_name="__STATE__",
        initial_state={"danger": "</script>"},
        bundle_js=bundle_js,
        bundle_css=bundle_css,
        scope="settings",
    )

    assert "<style>.app { color: red; }</style>" in head
    assert 'window.__STATE__ = {"danger": "<\\/script>"};' in body
    assert "window.__aqeSendBridge" in body
    assert "frontend.log" in body
    assert "bridge:" in body
    assert "window.__loaded = true;" in body


def test_render_webview_content_shows_missing_js_bundle_placeholder(tmp_path) -> None:
    body, _head = render_webview_content(
        initial_state_name="__STATE__",
        initial_state={},
        bundle_js=tmp_path / "missing.js",
        bundle_css=tmp_path / "missing.css",
        scope="batch",
    )

    assert "batch WebView JavaScript bundle is missing: missing.js" in body

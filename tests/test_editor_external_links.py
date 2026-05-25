"""Editor bridge external-link tests."""

from __future__ import annotations

from unittest.mock import MagicMock

from anki_audio_quick_editor.editor_integration import _handle_bridge_command


def test_bridge_opens_allowed_external_url() -> None:
    from aqt.qt import QDesktopServices, QUrl

    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.web = MagicMock()
    url = "https://ganqqwerty.github.io/anki-audio-tools/#video-pitch-hum"
    QDesktopServices.openUrl.return_value = True

    _handle_bridge_command(editor, f'{{"command":"aqe:open-url","url":"{url}"}}')

    QUrl.assert_called_once_with(url)
    QDesktopServices.openUrl.assert_called_once_with(QUrl.return_value)


def test_bridge_rejects_unlisted_external_url() -> None:
    from aqt.qt import QDesktopServices

    class Editor:
        pass

    editor = Editor()
    editor.currentField = 0
    editor.web = MagicMock()

    _handle_bridge_command(editor, '{"command":"aqe:open-url","url":"https://example.com"}')

    QDesktopServices.openUrl.assert_not_called()
    assert any("Could not open that link." in call.args[0] for call in editor.web.eval.call_args_list)

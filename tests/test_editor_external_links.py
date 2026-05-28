"""Editor bridge external-link tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from anki_audio_quick_editor.editor_integration import _handle_bridge_command


class Editor:
    pass


def _editor() -> Editor:
    editor = Editor()
    editor.currentField = 0
    editor.web = MagicMock()
    return editor


@pytest.mark.parametrize(
    "url",
    [
        "https://ganqqwerty.github.io/anki-audio-tools/",
        "https://ganqqwerty.github.io/anki-audio-tools/go/video-play/",
        "https://ganqqwerty.github.io/anki-audio-tools/#video-pitch-hum",
    ],
)
def test_bridge_opens_first_party_github_pages_url(url: str) -> None:
    from aqt.qt import QDesktopServices, QUrl

    editor = _editor()
    QDesktopServices.openUrl.return_value = True

    _handle_bridge_command(editor, f'{{"command":"aqe:open-url","url":"{url}"}}')

    QUrl.assert_called_once_with(url)
    QDesktopServices.openUrl.assert_called_once_with(QUrl.return_value)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.invalid/anki-audio-tools/go/video-play/",
        "http://ganqqwerty.github.io/anki-audio-tools/go/video-play/",
        "https://ganqqwerty.github.io.evil.invalid/anki-audio-tools/go/video-play/",
        "https://ganqqwerty.github.io/not-the-addon/go/video-play/",
        "https://user:pass@ganqqwerty.github.io/anki-audio-tools/go/video-play/",
    ],
)
def test_bridge_rejects_non_first_party_external_url(url: str) -> None:
    from aqt.qt import QDesktopServices

    editor = _editor()

    _handle_bridge_command(editor, f'{{"command":"aqe:open-url","url":"{url}"}}')

    QDesktopServices.openUrl.assert_not_called()
    assert any("Could not open that link." in call.args[0] for call in editor.web.eval.call_args_list)

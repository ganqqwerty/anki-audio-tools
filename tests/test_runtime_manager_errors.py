from __future__ import annotations

import urllib.error

from anki_audio_quick_editor.runtime_install import _friendly_download_error


def test_friendly_download_error_mentions_firewall_for_timeouts() -> None:
    message = _friendly_download_error(urllib.error.URLError(TimeoutError("timed out")))

    assert message.startswith("AQE-RUNTIME-003:")
    assert "Runtime download timed out" in message
    assert "/errors/AQE-RUNTIME-003/" in message
    assert "firewall, proxy, VPN, antivirus" in message


def test_friendly_download_error_mentions_permissions_for_write_errors() -> None:
    message = _friendly_download_error(PermissionError(13, "Permission denied"))

    assert message.startswith("AQE-RUNTIME-003:")
    assert "could not write files" in message
    assert "security software" in message


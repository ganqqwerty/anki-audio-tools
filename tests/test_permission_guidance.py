"""Tests for macOS executable permission recovery guidance."""

from __future__ import annotations

from anki_audio_quick_editor.permission_guidance import (
    chmod_bin_command,
    message_with_macos_permission_guidance,
)


def test_permission_guidance_adds_full_chmod_command_on_macos(monkeypatch) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.permission_guidance.platform.system", lambda: "Darwin")

    message = message_with_macos_permission_guidance(
        "[Errno 13] Permission denied: '/addon/bin/macos-arm64/ffmpeg'",
        PermissionError(13, "Permission denied", "/addon/bin/macos-arm64/ffmpeg"),
    )

    assert "close Anki, open Terminal" in message
    assert chmod_bin_command() in message


def test_permission_guidance_leaves_other_errors_unchanged(monkeypatch) -> None:
    monkeypatch.setattr("anki_audio_quick_editor.permission_guidance.platform.system", lambda: "Darwin")

    message = "No space left on device"

    assert message_with_macos_permission_guidance(message, OSError(28, message)) == message

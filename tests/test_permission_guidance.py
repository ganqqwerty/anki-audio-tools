"""Tests for executable permission recovery guidance."""

from __future__ import annotations

from anki_audio_quick_editor.permission_guidance import (
    bin_folder_path,
    chmod_bin_command,
    external_tool_error_message,
    message_with_permission_guidance,
)


def test_permission_guidance_adds_full_chmod_command_on_macos(monkeypatch) -> None:
    monkeypatch.setattr(
        "anki_audio_quick_editor.permission_guidance.platform.system",
        lambda: "Darwin",
    )

    message = message_with_permission_guidance(
        "[Errno 13] Permission denied: '/addon/bin/macos-arm64/ffmpeg'",
        PermissionError(13, "Permission denied", "/addon/bin/macos-arm64/ffmpeg"),
    )

    assert "close Anki, open Terminal" in message
    assert chmod_bin_command() in message


def test_permission_guidance_adds_windows_security_recovery_on_windows(monkeypatch) -> None:
    monkeypatch.setattr(
        "anki_audio_quick_editor.permission_guidance.platform.system",
        lambda: "Windows",
    )

    message = message_with_permission_guidance(
        "[WinError 5] Access is denied: 'C:\\Anki\\addons21\\1000000002\\bin\\windows-x86_64\\ffmpeg.exe'",
        PermissionError(
            13,
            "Permission denied",
            "C:\\Anki\\addons21\\1000000002\\bin\\windows-x86_64\\ffmpeg.exe",
        ),
    )

    assert "Windows Security" in message
    assert "Protection history" in message
    assert "antivirus" in message
    assert str(bin_folder_path()) in message


def test_permission_guidance_leaves_other_errors_unchanged(monkeypatch) -> None:
    monkeypatch.setattr(
        "anki_audio_quick_editor.permission_guidance.platform.system",
        lambda: "Darwin",
    )

    message = "No space left on device"

    assert message_with_permission_guidance(message, OSError(28, message)) == message


def test_permission_guidance_leaves_non_permission_windows_errors_unchanged(monkeypatch) -> None:
    monkeypatch.setattr(
        "anki_audio_quick_editor.permission_guidance.platform.system",
        lambda: "Windows",
    )

    message = "No space left on device"

    assert message_with_permission_guidance(message, OSError(28, message)) == message


def test_external_tool_guidance_describes_corrupt_executable_or_model() -> None:
    message = external_tool_error_message(
        "Failed to load model: invalid ONNX protobuf",
        tool_name="silero-vad",
    )

    assert (
        "silero-vad reported a corrupted or incompatible executable/model file"
        in message
    )
    assert "Settings > Diagnostics" in message


def test_external_tool_guidance_describes_unsupported_ffmpeg_build() -> None:
    message = external_tool_error_message(
        "Unknown encoder 'libmp3lame'",
        tool_name="ffmpeg",
    )

    assert "does not include the codec, encoder, decoder" in message
    assert "full ffmpeg build" in message


def test_external_tool_guidance_describes_permission_blocks() -> None:
    message = external_tool_error_message(
        "Permission denied while opening output file",
        tool_name="ffmpeg",
    )

    assert "could not read, write, or execute" in message
    assert "Windows Security" in message

from __future__ import annotations

from anki_audio_quick_editor.error_codes import (
    AQE_BATCH_INVALID_REQUEST,
    AQE_RUNTIME_FFMPEG_MISSING,
    UserFacingError,
    coded_error,
    format_coded_message,
    public_help_url,
)


def test_coded_error_payload_contains_code_message_and_details() -> None:
    payload = coded_error(
        AQE_RUNTIME_FFMPEG_MISSING,
        "Audio Quick Editor requires ffmpeg.",
        details="configured path did not exist",
    )

    assert payload == {
        "code": "AQE-RUNTIME-001",
        "message": "Audio Quick Editor requires ffmpeg.",
        "details": "configured path did not exist",
    }


def test_public_help_url_is_deterministic() -> None:
    assert public_help_url(AQE_BATCH_INVALID_REQUEST) == (
        "https://ganqqwerty.github.io/anki-audio-tools/errors/AQE-BATCH-001/"
    )


def test_user_facing_error_omits_empty_details() -> None:
    payload = UserFacingError("AQE-MEDIA-001", "No audio.").to_dict()

    assert payload == {"code": "AQE-MEDIA-001", "message": "No audio."}


def test_format_coded_message_adds_code_and_help_url() -> None:
    assert format_coded_message(AQE_RUNTIME_FFMPEG_MISSING, "ffmpeg missing") == (
        "AQE-RUNTIME-001: ffmpeg missing Help: "
        "https://ganqqwerty.github.io/anki-audio-tools/errors/AQE-RUNTIME-001/"
    )


def test_format_coded_message_does_not_duplicate_existing_code() -> None:
    message = "AQE-RUNTIME-001: ffmpeg missing Help: https://example.invalid"

    assert format_coded_message(AQE_RUNTIME_FFMPEG_MISSING, message) == message

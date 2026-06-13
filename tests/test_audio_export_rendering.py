from __future__ import annotations

from pathlib import Path

from anki_audio_quick_editor.audio_export_rendering import (
    build_concat_list_text,
    build_final_mp3_command,
    build_normalize_wav_command,
    build_silence_wav_command,
)


def test_build_normalize_wav_command_uses_stable_pcm_output() -> None:
    command = build_normalize_wav_command(
        ffmpeg_path=Path("/bin/ffmpeg"),
        source_path=Path("/media/source.mp3"),
        output_path=Path("/tmp/0001.wav"),
    )

    assert command == (
        "/bin/ffmpeg",
        "-y",
        "-i",
        "/media/source.mp3",
        "-vn",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-c:a",
        "pcm_s16le",
        "/tmp/0001.wav",
    )


def test_build_silence_wav_command_uses_anullsrc_duration() -> None:
    command = build_silence_wav_command(
        ffmpeg_path=Path("/bin/ffmpeg"),
        duration_seconds=1.25,
        output_path=Path("/tmp/silence.wav"),
    )

    assert command == (
        "/bin/ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=44100:cl=stereo",
        "-t",
        "1.250",
        "-c:a",
        "pcm_s16le",
        "/tmp/silence.wav",
    )


def test_build_concat_list_text_escapes_single_quotes() -> None:
    text = build_concat_list_text([Path("/tmp/a.wav"), Path("/tmp/has'quote.wav")])

    assert text == "file '/tmp/a.wav'\nfile '/tmp/has'\\''quote.wav'\n"


def test_build_final_mp3_command_uses_concat_demuxer_and_mp3_codec() -> None:
    command = build_final_mp3_command(
        ffmpeg_path=Path("/bin/ffmpeg"),
        concat_list_path=Path("/tmp/list.txt"),
        output_path=Path("/tmp/out.mp3"),
    )

    assert command[:7] == (
        "/bin/ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
    )
    assert command[7] == "/tmp/list.txt"
    assert command[-1] == "/tmp/out.mp3"
    assert "-vn" in command

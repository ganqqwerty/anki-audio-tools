"""Audio fixture generation helpers for editor E2E tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

from e2e.conftest import import_runtime_addon_module


def _render_direct_deep_filter_reference(
    ffmpeg_config,
    source: Path,
    output_path: Path,
    *,
    post_filter: bool,
) -> None:
    find_deep_filter = import_runtime_addon_module(".audio_processor").find_deep_filter
    deep_filter = find_deep_filter("")
    work_dir = output_path.parent / "direct_deep_filter_work"
    input_wav = work_dir / "input_48k_mono.wav"
    output_dir = work_dir / "deep_filter_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            ffmpeg_config.ffmpeg_path,
            "-y",
            "-i",
            str(source),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "48000",
            "-codec:a",
            "pcm_s16le",
            str(input_wav),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    deep_filter_command = [str(deep_filter), "-D"]
    if post_filter:
        deep_filter_command.append("--pf")
    deep_filter_command.extend(["-o", str(output_dir), str(input_wav)])
    subprocess.run(
        deep_filter_command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    wav_outputs = sorted(output_dir.glob("*.wav"))
    assert len(wav_outputs) == 1
    codec_args = ("-codec:a", "pcm_s16le", "-ar", "48000", "-ac", "1")
    if output_path.suffix.lower() == ".mp3":
        codec_args = ("-codec:a", "libmp3lame", "-q:a", "4")
    subprocess.run(
        [
            ffmpeg_config.ffmpeg_path,
            "-y",
            "-i",
            str(wav_outputs[0]),
            "-vn",
            *codec_args,
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
def _generate_tone_silence_tone(ffmpeg_config, path: Path) -> None:
    subprocess.run(
        [
            ffmpeg_config.ffmpeg_path,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=220:duration=0.4",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=44100:cl=mono:d=0.45",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=330:duration=0.4",
            "-filter_complex",
            "[0:a][1:a][2:a]concat=n=3:v=0:a=1[out]",
            "-map",
            "[out]",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _generate_high_bitrate_mp3(ffmpeg_config, path: Path, *, duration_s: float = 2.0) -> None:
    subprocess.run(
        [
            ffmpeg_config.ffmpeg_path,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=440:duration={duration_s}",
            "-vn",
            "-ac",
            "2",
            "-ar",
            "48000",
            "-codec:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

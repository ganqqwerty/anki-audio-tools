"""Audio fixture generation helpers for editor E2E tests."""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path

from e2e.conftest import import_runtime_addon_module


def _fake_deep_filter_executable(
    tmp_path: Path,
    *,
    fail: bool = False,
    cleaned_source: Path | None = None,
) -> tuple[Path, Path]:
    log_path = tmp_path / "deep-filter-argv.json"
    script_path = tmp_path / "fake_deep_filter.py"
    cleaned_source_value = str(cleaned_source) if cleaned_source is not None else ""
    script_path.write_text(
        "\n".join(
            [
                "from __future__ import annotations",
                "",
                "import json",
                "import shutil",
                "import sys",
                "from pathlib import Path",
                "",
                f"LOG_PATH = Path({str(log_path)!r})",
                f"FAIL = {fail!r}",
                f"CLEANED_SOURCE = {cleaned_source_value!r}",
                "",
                "args = sys.argv[1:]",
                "LOG_PATH.write_text(json.dumps(args), encoding='utf-8')",
                "if FAIL:",
                "    sys.stderr.write('fake deep-filter failed')",
                "    raise SystemExit(12)",
                "if '--version' in args:",
                "    print('fake deep-filter 0.0')",
                "    raise SystemExit(0)",
                "try:",
                "    output_dir = Path(args[args.index('-o') + 1])",
                "except (ValueError, IndexError):",
                "    sys.stderr.write('missing output directory')",
                "    raise SystemExit(2)",
                "input_wav = Path(args[-1])",
                "output_dir.mkdir(parents=True, exist_ok=True)",
                "source_wav = Path(CLEANED_SOURCE) if CLEANED_SOURCE else input_wav",
                "shutil.copyfile(source_wav, output_dir / 'clean.wav')",
            ]
        ),
        encoding="utf-8",
    )
    if os.name == "nt":
        executable = tmp_path / "deep-filter.cmd"
        executable.write_text(
            f'@echo off\n"{sys.executable}" "{script_path}" %*\n',
            encoding="utf-8",
        )
    else:
        executable = tmp_path / "deep-filter"
        executable.write_text(
            "#!/bin/sh\n"
            f"exec {shlex.quote(sys.executable)} {shlex.quote(str(script_path))} \"$@\"\n",
            encoding="utf-8",
        )
        executable.chmod(0o755)
    return executable, log_path


def _render_direct_deep_filter_reference(
    ffmpeg_config,
    source: Path,
    output_path: Path,
    *,
    post_filter: bool,
) -> None:
    from e2e.editor_note_helpers import _restore_bundled_deep_filter_for_e2e

    _restore_bundled_deep_filter_for_e2e()
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
    )

    wav_outputs = sorted(output_dir.glob("*.wav"))
    assert len(wav_outputs) == 1
    subprocess.run(
        [
            ffmpeg_config.ffmpeg_path,
            "-y",
            "-i",
            str(wav_outputs[0]),
            "-vn",
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "4",
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
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
    )


def _generate_noisy_pause_and_clean_analysis(
    ffmpeg_config,
    noisy_path: Path,
    cleaned_analysis_path: Path,
) -> None:
    for path, middle_filter, sample_rate in (
        (
            noisy_path,
            "anoisesrc=c=white:r=44100:d=0.8:a=0.06",
            "44100",
        ),
        (
            cleaned_analysis_path,
            "anullsrc=r=48000:cl=mono:d=0.8",
            "48000",
        ),
    ):
        subprocess.run(
            [
                ffmpeg_config.ffmpeg_path,
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency=440:sample_rate={sample_rate}:duration=0.35",
                "-f",
                "lavfi",
                "-i",
                middle_filter,
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency=660:sample_rate={sample_rate}:duration=0.35",
                "-filter_complex",
                "[0:a][1:a][2:a]concat=n=3:v=0:a=1[out]",
                "-map",
                "[out]",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

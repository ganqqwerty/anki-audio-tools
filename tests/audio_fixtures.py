from __future__ import annotations

import math
import random
import shutil
import subprocess
import sys
import wave
from array import array
from pathlib import Path

from anki_audio_quick_editor.audio_processor import find_deep_filter
from anki_audio_quick_editor.errors import MissingDeepFilterError

FFMPEG_SKIP_REASON = "ffmpeg and ffprobe are required for audio rendering smoke tests"


def _deep_filter_available() -> bool:
    try:
        find_deep_filter()
    except MissingDeepFilterError:
        return False
    return True


def _fake_deep_filter_executable(tmp_path: Path, *, fail: bool = False) -> Path:
    script_path = tmp_path / "fake_deep_filter.py"
    script_path.write_text(
        "\n".join(
            [
                "from __future__ import annotations",
                "import shutil",
                "import sys",
                "from pathlib import Path",
                f"FAIL = {fail!r}",
                "args = sys.argv[1:]",
                "if FAIL:",
                "    sys.stderr.write('fake deep-filter failed')",
                "    raise SystemExit(12)",
                "output_dir = Path(args[args.index('-o') + 1])",
                "input_wav = Path(args[-1])",
                "output_dir.mkdir(parents=True, exist_ok=True)",
                "shutil.copyfile(input_wav, output_dir / 'clean.wav')",
            ]
        ),
        encoding="utf-8",
    )
    executable = tmp_path / "deep-filter"
    executable.write_text(
        "#!/bin/sh\n"
        f"exec {sys.executable!r} {str(script_path)!r} \"$@\"\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    return executable


FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
DEEP_FILTER_AVAILABLE = _deep_filter_available()

def _generate_short_pause_clip(path: Path) -> None:
    _run_ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=220:duration=0.25",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=44100:cl=mono:d=0.25",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=300:duration=0.25",
        "-filter_complex",
        "[0:a][1:a][2:a]concat=n=3:v=0:a=1[out]",
        "-map",
        "[out]",
        str(path),
    )


def _generate_long_pause_clip(path: Path) -> None:
    _run_ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=220:duration=0.25",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=44100:cl=mono:d=0.75",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=300:duration=0.25",
        "-filter_complex",
        "[0:a][1:a][2:a]concat=n=3:v=0:a=1[out]",
        "-map",
        "[out]",
        str(path),
    )


def _generate_quiet_micro_word_clip(path: Path) -> None:
    _run_ffmpeg(
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=220:duration=0.20",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=44100:cl=mono:d=0.31",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=260:duration=0.07,volume=0.08",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=44100:cl=mono:d=0.31",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=300:duration=0.20",
        "-filter_complex",
        "[0:a][1:a][2:a][3:a][4:a]concat=n=5:v=0:a=1[out]",
        "-map",
        "[out]",
        str(path),
    )


def _generate_noisy_speech_like_clip(path: Path) -> None:
    sample_rate = 48_000
    duration_s = 1.6
    noise_only_s = 0.4
    rng = random.Random(42)
    samples: list[int] = []
    for index in range(round(sample_rate * duration_s)):
        time_s = index / sample_rate
        noise = rng.uniform(-0.08, 0.08)
        signal = 0.0
        if noise_only_s <= time_s < duration_s - noise_only_s:
            speech_time = time_s - noise_only_s
            envelope = 0.55 + 0.45 * math.sin(2 * math.pi * 4.5 * speech_time) ** 2
            signal = envelope * (
                0.16 * math.sin(2 * math.pi * 180 * speech_time)
                + 0.08 * math.sin(2 * math.pi * 360 * speech_time)
                + 0.04 * math.sin(2 * math.pi * 540 * speech_time)
            )
        value = max(-0.95, min(0.95, signal + noise))
        samples.append(round(value * 32767))

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(array("h", samples).tobytes())


def _decode_mono_pcm16(path: Path, sample_rate: int = 48_000) -> list[int]:
    result = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-ac",
            "1",
            "-ar",
            str(sample_rate),
            "-f",
            "s16le",
            "pipe:1",
        ],
        check=True,
        capture_output=True,
    )
    samples = array("h")
    samples.frombytes(result.stdout)
    return list(samples)


def _window_rms(
    samples: list[int],
    *,
    start_s: float,
    end_s: float,
    sample_rate: int = 48_000,
) -> float:
    start = round(start_s * sample_rate)
    end = round(end_s * sample_rate)
    window = samples[start:end]
    assert window
    return math.sqrt(sum((sample / 32768) ** 2 for sample in window) / len(window))


def _db_drop(before: float, after: float) -> float:
    floor = 1e-9
    return 20 * math.log10(max(before, floor) / max(after, floor))


def _run_ffmpeg(*args: str) -> None:
    subprocess.run(
        ["ffmpeg", "-y", *args],
        check=True,
        capture_output=True,
        text=True,
    )

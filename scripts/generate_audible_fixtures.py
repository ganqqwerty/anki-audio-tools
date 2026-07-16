"""Generate deterministic addressable-audio fixtures for acoustic E2E tests."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import wave
from pathlib import Path

from addressable_audio_fixture import ADDRESSABLE_SAMPLE_RATE, addressable_samples

ROOT = Path(__file__).resolve().parents[1]
AUDIO_ROOT = ROOT / "e2e" / "fixtures" / "audio"
WAV_NAME = "addressable-timecode.wav"
CODECS = {
    "addressable-timecode.mp3": "libmp3lame",
    "addressable-timecode.ogg": "libvorbis",
    "addressable-timecode.m4a": "aac",
}


def main() -> None:
    """Write the canonical WAV fixture and its machine-readable manifest."""
    pcm, metadata = addressable_samples()
    AUDIO_ROOT.mkdir(parents=True, exist_ok=True)
    wav_path = AUDIO_ROOT / WAV_NAME
    with wave.open(str(wav_path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(ADDRESSABLE_SAMPLE_RATE)
        output.writeframes(pcm)

    checksum = hashlib.sha256(wav_path.read_bytes()).hexdigest()
    checksums = {WAV_NAME: checksum}
    ffmpeg = _managed_ffmpeg()
    for name, codec in CODECS.items():
        target = AUDIO_ROOT / name
        subprocess.run(
            [
                str(ffmpeg), "-v", "error", "-y", "-i", str(wav_path),
                "-map_metadata", "-1", "-fflags", "+bitexact",
                "-flags:a", "+bitexact", "-codec:a", codec, str(target),
            ],
            check=True,
        )
        checksums[name] = hashlib.sha256(target.read_bytes()).hexdigest()
    metadata["checksums"] = checksums
    metadata["codecs"] = {WAV_NAME: "pcm_s16le", **CODECS}
    manifest = {
        "addressableTimecode": metadata,
        "files": checksums,
        "generator": "scripts/generate_audible_fixtures.py",
    }
    (AUDIO_ROOT / "addressable-timecode.manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _managed_ffmpeg() -> Path:
    override = os.environ.get("AQE_E2E_FFMPEG")
    if override:
        path = Path(override).expanduser()
        if path.is_file():
            return path
        raise FileNotFoundError(f"AQE_E2E_FFMPEG does not exist: {path}")
    runtime_root = ROOT / "addon" / "anki_audio_quick_editor" / "user_files" / "runtime"
    candidates = sorted(runtime_root.glob("*/macos-arm64/ffmpeg"))
    if len(candidates) != 1:
        raise FileNotFoundError(
            f"expected one managed ffmpeg under {runtime_root}, found {candidates!r}"
        )
    return candidates[0]


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Validate managed FFmpeg binaries for source-quality audio output."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PROFILE_NAME = "aqe-source-audio-v1"
REQUIRED_AUDIO_OUTPUT_CAPABILITY_PROFILE = {
    "encoders": {
        "libmp3lame",
        "aac",
        "flac",
        "libvorbis",
        "libopus",
        "pcm_s16le",
        "pcm_s24le",
    },
    "muxers": {
        "mp3",
        "mp4",
        "adts",
        "wav",
        "flac",
        "ogg",
        "opus",
        "webm",
    },
}

_MISSING_ENCODER_MESSAGES = {
    "libopus": ".opus and .webm preservation requires FFmpeg encoder libopus",
    "libvorbis": ".ogg and .oga preservation requires FFmpeg encoder libvorbis",
    "pcm_s24le": "24-bit WAV preservation requires FFmpeg encoder pcm_s24le",
}
_MISSING_MUXER_MESSAGES = {
    "adts": "raw .aac preservation requires FFmpeg muxer adts",
}


@dataclass(frozen=True)
class FfmpegCapabilities:
    encoders: set[str]
    muxers: set[str]


@dataclass(frozen=True)
class CapabilityReport:
    missing_encoders: set[str]
    missing_muxers: set[str]
    messages: list[str]

    @property
    def ok(self) -> bool:
        return not self.missing_encoders and not self.missing_muxers


def parse_ffmpeg_table(output: str) -> set[str]:
    """Extract capability names from an FFmpeg table-style command output."""
    names: set[str] = set()
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped or stripped.endswith(":") or stripped.startswith("--"):
            continue
        parts = stripped.split()
        if len(parts) < 2:
            continue
        if _looks_like_ffmpeg_flags(parts[0]):
            names.add(parts[1])
    return names


def collect_ffmpeg_capabilities(ffmpeg_path: Path) -> FfmpegCapabilities:
    """Run FFmpeg capability commands and return available encoders and muxers."""
    encoders = _run_ffmpeg_capability_command(ffmpeg_path, "-encoders")
    muxers = _run_ffmpeg_capability_command(ffmpeg_path, "-muxers")
    return FfmpegCapabilities(encoders=parse_ffmpeg_table(encoders), muxers=parse_ffmpeg_table(muxers))


def validate_required_audio_output_capabilities(capabilities: FfmpegCapabilities) -> CapabilityReport:
    """Return a report for missing source-quality final-output capabilities."""
    missing_encoders = REQUIRED_AUDIO_OUTPUT_CAPABILITY_PROFILE["encoders"] - capabilities.encoders
    missing_muxers = REQUIRED_AUDIO_OUTPUT_CAPABILITY_PROFILE["muxers"] - capabilities.muxers
    messages = [
        _MISSING_ENCODER_MESSAGES.get(encoder, f"missing required FFmpeg encoder {encoder}")
        for encoder in sorted(missing_encoders)
    ]
    messages.extend(
        _MISSING_MUXER_MESSAGES.get(muxer, f"missing required FFmpeg muxer {muxer}")
        for muxer in sorted(missing_muxers)
    )
    return CapabilityReport(missing_encoders=missing_encoders, missing_muxers=missing_muxers, messages=messages)


def verify_ffmpeg_binary(ffmpeg_path: Path) -> None:
    """Raise if ``ffmpeg_path`` does not satisfy the managed runtime profile."""
    report = validate_required_audio_output_capabilities(collect_ffmpeg_capabilities(ffmpeg_path))
    if not report.ok:
        details = "\n".join(f"- {message}" for message in report.messages)
        raise RuntimeError(f"{ffmpeg_path} does not satisfy {PROFILE_NAME}:\n{details}")


def _run_ffmpeg_capability_command(ffmpeg_path: Path, flag: str) -> str:
    result = subprocess.run(
        [str(ffmpeg_path), "-hide_banner", flag],
        capture_output=True,
        text=True,
        check=False,
    )  # nosec B603
    if result.returncode != 0:
        stderr = result.stderr.strip()
        message = stderr or f"ffmpeg {flag} failed with exit code {result.returncode}"
        raise RuntimeError(message)
    return result.stdout


def _looks_like_ffmpeg_flags(value: str) -> bool:
    return bool(value) and all(ch.isalpha() or ch == "." for ch in value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffmpeg", type=Path, required=True, help="path to the FFmpeg binary to verify")
    args = parser.parse_args(argv)
    try:
        verify_ffmpeg_binary(args.ffmpeg)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"{args.ffmpeg} satisfies {PROFILE_NAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Third-Party Runtime Notices

Audio Quick Editor release archives include native command-line tools below
`bin/<target>/`. The exact executable checksums and source URLs are locked in
`release_assets.lock.json` and copied into `bin/runtime_manifest.json` during
release packaging.

## FFmpeg and FFprobe

- Version: FFmpeg 8.1.1
- Source and binary directory: https://ffmpeg.org/download.html
- macOS provider: https://ffmpeg.martin-riedl.de/
- Windows provider: https://www.gyan.dev/ffmpeg/builds/
- License posture: third-party static builds are redistributed under GPLv3
  terms for this release.
- Distribution note: release builds include `ffmpeg` and `ffprobe` only, not
  `ffplay`, headers, static libraries, or provider documentation bundles.

## LAME

- Purpose: MP3 encoding through FFmpeg's `libmp3lame` encoder.
- Source: https://lame.sourceforge.io/
- Distribution note: LAME is included through the bundled third-party FFmpeg
  builds; the exact FFmpeg provider archives and executable checksums are
  locked in `release_assets.lock.json`.

## DeepFilterNet

- Version: 0.5.6
- Source: https://github.com/Rikorose/DeepFilterNet/releases/tag/v0.5.6
- Licenses: MIT and Apache-2.0 as published by upstream.
- Distribution note: release packaging normalizes upstream executable names to
  `deep-filter` on macOS and `deep-filter.exe` on Windows.

## RNNoise

- Version: 0.2
- Source: https://github.com/xiph/rnnoise/releases/tag/v0.2
- License: BSD-style upstream license.
- Distribution note: `rnnoise-cli` is built from upstream RNNoise source and
  the local wrapper source at `scripts/rnnoise_cli/rnnoise_cli.c`.

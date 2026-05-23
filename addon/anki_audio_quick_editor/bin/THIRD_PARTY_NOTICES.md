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

## DPDFNet

- Version: DPDFNet Lite CLI 0.1.0 with the `dpdfnet4.tflite` model.
- Source: https://github.com/ceva-ip/DPDFNet
- License: Apache-2.0.
- Distribution note: `dpdfnet` is built as a standalone TFLite command-line
  tool from the vendored Lite source in `scripts/dpdfnet_cli/lite_src/`.

## Sherpa ONNX Spleeter

- Version: Sherpa ONNX 1.13.2 runtime plus `sherpa-onnx-spleeter-2stems-fp16`
  model files.
- Runtime source: https://github.com/k2-fsa/sherpa-onnx/releases/tag/v1.13.2
- Model source: https://github.com/k2-fsa/sherpa-onnx/releases/tag/source-separation-models
- License posture: Sherpa ONNX runtime assets are published under Apache-2.0
  terms; the Spleeter model files follow the upstream model release terms
  tracked in `release_assets.lock.json`.
- Distribution note: release packaging extracts the upstream
  `sherpa-onnx-offline-source-separation` executable as `sherpa-spleeter`,
  stages the required ONNX Runtime libraries beside it, and shares
  `vocals.fp16.onnx` and `accompaniment.fp16.onnx` once under
  `bin/models/spleeter-2stems-fp16/`.

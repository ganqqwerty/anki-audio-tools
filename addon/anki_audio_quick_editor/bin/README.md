# Bundled Runtime Payloads

Release archives stage native executables and support files into this generated
layout:

```text
bin/
  README.md
  THIRD_PARTY_NOTICES.md
  runtime_manifest.json
  macos-arm64/
    ffmpeg
    ffprobe
    deep-filter
    rnnoise-cli
    dpdfnet
    sherpa-spleeter
    silero-vad
    libonnxruntime.1.24.4.dylib
  macos-x86_64/
    ffmpeg
    ffprobe
    deep-filter
    rnnoise-cli
    dpdfnet
    sherpa-spleeter
    silero-vad
    libonnxruntime.1.24.4.dylib
  windows-x86_64/
    ffmpeg.exe
    ffprobe.exe
    deep-filter.exe
    rnnoise-cli.exe
    dpdfnet.exe
    sherpa-spleeter.exe
    silero-vad.exe
    onnxruntime.dll
    onnxruntime_providers_shared.dll
  models/
    spleeter-2stems-fp16/
      vocals.fp16.onnx
      accompaniment.fp16.onnx
    silero-vad/
      silero_vad.onnx
```

The source of truth is split by asset class and enforced by
`release_assets.lock.json`. This checked-in `bin/` tree is the canonical home
for all non-FFmpeg runtime payloads:

- target-specific `deep-filter`, `rnnoise-cli`, `dpdfnet`, `sherpa-spleeter`, `silero-vad`,
  and Sherpa runtime libraries live under `bin/<target>/`
- shared Spleeter fp16 and Silero VAD model files live under `bin/models/`
- `runtime_manifest.json` is generated during packaging and is not committed

`ffmpeg` and `ffprobe` remain external. Packaging and `release-assets verify`
read them from `.release-assets/bin/<target>/`, verify their SHA-256 checksums,
and assemble a target-specific release staging tree with the tracked non-FFmpeg
payloads from this directory. FFmpeg/FFprobe use locked third-party release
archives, RNNoise is locally built from source, DPDFNet is bundled from the
vendored standalone TFLite CLI source in `scripts/dpdfnet_cli/lite_src/`, and
Sherpa Spleeter/Silero VAD are extracted from locked Sherpa ONNX native
archives by renaming upstream executables to `sherpa-spleeter` and
`silero-vad`.

Runtime discovery uses user-configured overrides first where supported, then
the managed downloaded runtime, then this source-tree bundle as a development
fallback. `PATH` is only a compatibility fallback for `ffmpeg`, `ffprobe`, and
`deep-filter`.

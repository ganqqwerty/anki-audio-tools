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
    libonnxruntime.1.24.4.dylib
  macos-x86_64/
    ffmpeg
    ffprobe
    deep-filter
    rnnoise-cli
    sherpa-spleeter
    libonnxruntime.1.24.4.dylib
  windows-x86_64/
    ffmpeg.exe
    ffprobe.exe
    deep-filter.exe
    rnnoise-cli.exe
    sherpa-spleeter.exe
    onnxruntime.dll
    onnxruntime_providers_shared.dll
  models/
    spleeter-2stems-fp16/
      vocals.fp16.onnx
      accompaniment.fp16.onnx
```

The source of truth is `release_assets.lock.json`. Runtime binaries are fetched
or built into `.release-assets/bin/<target>/`, verified by SHA-256, then copied
into a temporary release staging tree. FFmpeg/FFprobe use locked third-party
release archives, RNNoise is locally built from source, DPDFNet is bundled from
the local standalone TFLite CLI build for supported targets, and Sherpa Spleeter
is extracted from locked Sherpa ONNX native archives by renaming
`sherpa-onnx-offline-source-separation` to `sherpa-spleeter`. The shared
Spleeter fp16 model files are downloaded once into `.release-assets/shared/`.
The checked-in `bin/` directory contains only documentation and notices;
generated release payloads are not committed here.

Runtime discovery uses user-configured overrides first, bundled executables
second, and `PATH` as a compatibility fallback where supported.

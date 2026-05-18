# Bundled Runtime Payloads

Release archives stage native executables into this generated layout:

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
  macos-x86_64/
    ffmpeg
    ffprobe
    deep-filter
    rnnoise-cli
  windows-x86_64/
    ffmpeg.exe
    ffprobe.exe
    deep-filter.exe
    rnnoise-cli.exe
```

The source of truth is `release_assets.lock.json`. Runtime binaries are fetched
or built into `.release-assets/bin/<target>/`, verified by SHA-256, then copied
into a temporary release staging tree. FFmpeg/FFprobe use locked third-party
release archives, while RNNoise is locally built from source. The checked-in
`bin/` directory contains only documentation and notices; generated release
payloads are not committed here.

Runtime discovery uses user-configured overrides first, bundled executables
second, and `PATH` as a compatibility fallback where supported.

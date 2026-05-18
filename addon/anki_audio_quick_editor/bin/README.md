# Bundled External Audio Runtimes

This directory contains pinned external executables used by Audio Quick Editor.

## deep-filter 0.5.6 for macOS arm64

- File: `deep-filter-0.5.6-aarch64-apple-darwin`
- Source: <https://github.com/Rikorose/DeepFilterNet/releases/tag/v0.5.6>
- Download URL: <https://github.com/Rikorose/DeepFilterNet/releases/download/v0.5.6/deep-filter-0.5.6-aarch64-apple-darwin>
- SHA-256: `4601e7f4e4c03e59a4c5b5000216ef3add3e808799cfccd95e14e83ea4611081`
- Upstream licenses: Apache-2.0 and MIT, as published in the DeepFilterNet repository.

The add-on still supports an explicit `deep_filter_path` override. If no override
is configured, the runtime uses a bundled binary for the current platform when
available, then falls back to `deep-filter` on `PATH`.

## RNNoise CLI bundle for macOS arm64

- Directory: `rnnoise-cli-macos-arm64/`
- Upstream repo: <https://github.com/xiph/rnnoise>
- Upstream release: <https://github.com/xiph/rnnoise/releases/tag/v0.2>
- Upstream source archive: <https://github.com/xiph/rnnoise/releases/download/v0.2/rnnoise-0.2.tar.gz>
- Upstream license: BSD-3-Clause; bundled copy at `rnnoise-cli-macos-arm64/LICENSE-RNNoise.txt`
- Runtime binary: `rnnoise-cli-macos-arm64/bin/rnnoise-cli`
- Runtime source: `scripts/rnnoise_cli/rnnoise_cli.c`

Checksums:

- `bin/rnnoise-cli` SHA-256:
  `fa9faa2cd0f98fcf7b76a86f729047425d363fd8c3ac830dfecebe0b8a56be97`
- `LICENSE-RNNoise.txt` SHA-256:
  `45d37ca1cdb278c088e1aa85e0e65ca3a534ed86a28dcc96ca16810248a61d35`
- `scripts/rnnoise_cli/rnnoise_cli.c` SHA-256:
  `339666b7114e41d13f2a625e4923e633af2f8eb64676cfb5655981bebccb6dad`

Build/package provenance:

1. Downloaded `rnnoise-0.2.tar.gz` from the upstream release.
2. Built the upstream static RNNoise library for macOS arm64 with:
   `./configure --disable-shared --enable-static CFLAGS='-O3 -arch arm64 -mmacosx-version-min=11.0' LDFLAGS='-arch arm64 -mmacosx-version-min=11.0'`.
3. Added a minimal local `src/os_support.h` compatibility header for the upstream
   source archive build, defining `OPUS_CLEAR` with `memset`.
4. Built `scripts/rnnoise_cli/rnnoise_cli.c` against the static RNNoise library
   with `clang -O3 -arch arm64 -mmacosx-version-min=11.0`.
5. Verified `rnnoise-cli --version`, confirmed the binary links only to
   `/usr/lib/libSystem.B.dylib`, and smoke-tested raw PCM denoise plus ffmpeg
   MP3 encoding.

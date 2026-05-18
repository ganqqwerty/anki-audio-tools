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

## MP-SENet CPU bundle for macOS arm64

- Directory: `mp-senet-cli-macos-arm64/`
- Upstream repo: <https://github.com/yxlu-0102/MP-SENet>
- Upstream license: MIT; bundled copy at `mp-senet-cli-macos-arm64/LICENSE-MP-SENet.txt`
- Bundled entrypoint: `mp-senet-cli-macos-arm64/bin/mp-senet-cli`
- Runtime binary: `mp-senet-cli-macos-arm64/bin/mp-senet-cli-real`
- Runtime source: `scripts/mp_senet_cli/mp_senet_cli.cpp`
- Model source: upstream `best_ckpt/g_best_vb` VoiceBank+DEMAND checkpoint
- Model format: TorchScript export, `mp-senet-cli-macos-arm64/models/mp_senet_vb.torchscript.pt`

Checksums:

- `bin/mp-senet-cli-real` SHA-256:
  `fd68048138c8027dc06a5c048d1c4a49538f125029880011068dc838b65b6a8f`
- `models/mp_senet_vb.torchscript.pt` SHA-256:
  `0060b034933cf80b1480df8fc56d20eb7a2fac47f3335165a40c19eb6dd5df82`
- `models/config.json` SHA-256:
  `339cb60721e4ab0ee3ed4825ca9dfc981c7554c7b5e87f043e454e5a17b58f92`
- Upstream checkpoint `best_ckpt/g_best_vb` SHA-256:
  `aedfb1aa549159f71b39613d94db831dfa983b3a68b0deea02e84e0ad563f4f9`

Build/package provenance:

1. Cloned `https://github.com/yxlu-0102/MP-SENet` at `main` and used the bundled
   `best_ckpt/g_best_vb` checkpoint plus `best_ckpt/config.json`.
2. Exported the VoiceBank+DEMAND checkpoint to TorchScript CPU format with
   PyTorch 2.7.1.
3. Built `scripts/mp_senet_cli/mp_senet_cli.cpp` against the existing
   LibTorch 2.10.0 macOS arm64 headers/libs.
4. Copied the binary, TorchScript model, LibTorch dylibs, upstream config, and
   upstream MIT license into `mp-senet-cli-macos-arm64/`.
5. Added a `bin/mp-senet-cli` shell wrapper that sets `DYLD_LIBRARY_PATH` to the
   bundle-local `lib/` LibTorch dylibs before executing `bin/mp-senet-cli-real`.

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

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

## Sidon CPU bundle for macOS arm64

- Directory: `sidon-cli-macos-arm64/`
- Source repo used to build it: `/Users/iuriikatkov/Documents/sidon-exec`
- Bundled entrypoint: `sidon-cli-macos-arm64/bin/sidon-cli`
- Runtime binary: `sidon-cli-macos-arm64/bin/sidon-cli-real`
- Model revision: `94ec832fcf5f55ef0610c4261d38c39802eeb774`
- `feature_extractor_cpu.pt` SHA-256:
  `fd9abc906a9048b3c047bd3d246a25f6485d09c2d6bb85e098f527f844efc019`
- `decoder_cpu.pt` SHA-256:
  `34dcc80fab75bd1336369ba5b2063f6da475887aa824db94b495c4059c5fdea4`

Build/package provenance:

1. Downloaded official LibTorch CPU macOS arm64 archive:
   `https://download.pytorch.org/libtorch/cpu/libtorch-macos-arm64-2.10.0.zip`
2. Fetched Sidon models with `/Users/iuriikatkov/Documents/sidon-exec/scripts/fetch_models.sh`
3. Packaged Sidon from `/Users/iuriikatkov/Documents/sidon-exec` with
   `LIBTORCH_DIR=/private/tmp/sidon-build/libtorch ARCH=arm64 ./scripts/package_macos.sh`
4. Copied the packaged bundle into this directory
5. Replaced the packaged `bin/sidon-cli` with a shell wrapper that sets
   `DYLD_LIBRARY_PATH` to the bundled `lib/` directory before executing
   `bin/sidon-cli-real`

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
   PyTorch 2.7.1 from `/Users/iuriikatkov/Documents/sidon-exec/.venv`.
3. Built `scripts/mp_senet_cli/mp_senet_cli.cpp` against the existing
   `/private/tmp/sidon-build/libtorch` 2.10.0 macOS arm64 headers/libs.
4. Copied the binary, TorchScript model, upstream config, and upstream MIT
   license into `mp-senet-cli-macos-arm64/`.
5. Added a `bin/mp-senet-cli` shell wrapper that sets `DYLD_LIBRARY_PATH` to the
   already bundled `sidon-cli-macos-arm64/lib/` LibTorch dylibs before executing
   `bin/mp-senet-cli-real`.

# Bundled DeepFilterNet Binary

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

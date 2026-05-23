# Development Setup & Dependencies

## The Two-Python Setup

This repo uses two Python environments:

| Environment | Purpose |
|-------------|---------|
| System `python3` | Runs `scripts/dev.py` |
| Anki bundled Python | Runs pytest, ruff, mypy, import-linter, and other tooling |

Always go through `python3 scripts/dev.py ...`. The task runner discovers Anki's Python automatically and can be overridden with `ANKI_PYTHON` in `.env`.

## First-Time Setup

```bash
python3 scripts/dev.py setup
```

This:

- installs Python dev dependencies into Anki's Python
- creates the add-on symlink in `addons21/1000000002`
- runs `npm ci` in `settings_ui/` when `package-lock.json` is present, otherwise `npm install`

## E2E Add-on Config Isolation

The local development install is a symlink from Anki's `addons21/1000000002` to `addon/anki_audio_quick_editor/`. Anki stores per-add-on user config in `meta.json` inside the add-on folder, and `meta.json` is intentionally git-ignored.

The real Anki development add-on follows the symlink in the main checkout. If you are working from a feature worktree such as `.worktrees/<name>`, launching real Anki will not show that worktree's code unless you first merge the worktree back into the main checkout or temporarily repoint `~/Library/Application Support/Anki2/addons21/1000000002` at the worktree's `addon/anki_audio_quick_editor/`. Repoint it back before switching tasks so manual testing does not accidentally exercise an old worktree.

E2E tests must copy the add-on into their temporary `ANKI_BASE` instead of symlinking back to the repo. Otherwise, test-only config writes can leak into the real development add-on. The most visible symptom is manual Anki clicks behaving differently from defaults because test settings were written into `addon/anki_audio_quick_editor/meta.json`.

If that happens, remove `addon/anki_audio_quick_editor/meta.json` or use the settings dialog to reset defaults. The E2E fixture should keep excluding `meta.json`, logs, caches, and artifact directories from the copied add-on tree.

## Runtime Dependencies

Anki add-ons cannot rely on `pip install` at user runtime. Audio Quick Editor uses the Python/Qt runtime bundled with Anki and ships a locked native runtime payload for supported release platforms. The self-sufficient release matrix is macOS arm64, macOS x86_64, and Windows x86_64.

Release archives bundle `ffmpeg`, `ffprobe`, DeepFilterNet's `deep-filter`, `rnnoise-cli`, Sherpa's `sherpa-spleeter`, and DPDFNet Lite below `bin/<target>/`, plus shared Spleeter model files below `bin/models/spleeter-2stems-fp16/`. Runtime discovery checks the configured ffmpeg path where supported, bundled tools second, and `PATH` as a compatibility fallback. The settings diagnostics report whether each tool came from config, the bundled payload, or `PATH`.

`release_assets.lock.json` remains the source of truth for the runtime matrix, source URLs, diagnostic arguments, and SHA-256 values, but the files now come from two places. Commit all non-FFmpeg runtime payloads directly under `addon/anki_audio_quick_editor/bin/<target>/` and `addon/anki_audio_quick_editor/bin/models/`. Keep only `ffmpeg` and `ffprobe` external in `.release-assets/bin/<target>/`. Source-tree development uses the same canonical layout as releases, so runtime lookups keep reading from the add-on `bin/` tree.

Release asset workflow:

```bash
python3 scripts/dev.py release-assets fetch-deepfilter --target all
python3 scripts/dev.py release-assets fetch-ffmpeg --target all
python3 scripts/dev.py release-assets fetch-sherpa-spleeter --target all
python3 scripts/dev.py release-assets fetch-spleeter-models
python3 scripts/dev.py release-assets build-rnnoise --target macos-arm64
python3 scripts/dev.py release-assets build-rnnoise --target macos-x86_64
python3 scripts/dev.py release-assets build-rnnoise --target windows-x86_64
scripts/dpdfnet_cli/build_macos.sh macos-arm64
scripts/dpdfnet_cli/build_macos.sh macos-x86_64
pwsh -File scripts/dpdfnet_cli/build_windows.ps1 -Target windows-x86_64
python3 scripts/dev.py release-assets verify --target all
python3 scripts/dev.py release-assets verify --target current --diagnostics
python3 scripts/dev.py release-assets lock-checksums
```

DPDFNet Lite artifacts are prepared through the manual GitHub Actions workflows
`Build macOS DPDFNet` and `Build Windows DPDFNet`, or locally on a matching
native host. The scripts build the vendored TFLite CLI source in
`scripts/dpdfnet_cli/lite_src/`, bundle the locked `dpdfnet4.tflite` model,
smoke-test `enhance`, and upload platform artifacts. After downloading an
artifact, copy it into `addon/anki_audio_quick_editor/bin/<target>/dpdfnet` or
`addon/anki_audio_quick_editor/bin/windows-x86_64/dpdfnet.exe`, refresh the
lock with `python3 scripts/dev.py release-assets lock-checksums`, and keep
`dpdfnet` embedded-only in that target's release/runtime matrix.

On a Windows host, the equivalent local build command is:

```powershell
.\scripts\dpdfnet_cli\build_windows.ps1 -Target windows-x86_64
```

FFmpeg and FFprobe are fetched from locked third-party static release archives into `.release-assets/bin/<target>/`: Martin Riedl's macOS builds and Gyan Doshi's Windows essentials build. The lock records both the provider archive SHA-256 and the extracted executable SHA-256. RNNoise is still built locally from source; Windows RNNoise can be cross-built from macOS when `x86_64-w64-mingw32-gcc` is available. The default maintainer workflow for non-FFmpeg assets is regenerate externally, copy the verified artifact into `addon/anki_audio_quick_editor/bin/`, refresh checksums, and commit. A release is not approved until native acceptance has run on each supported platform.

`python3 scripts/dev.py release-assets verify` is intentionally file-focused:
it fails on missing or checksum-mismatched runtime payloads, but does not run
host-specific runtime probes unless you add `--diagnostics`. Use
`release-smoke`, native acceptance, or explicit `--diagnostics` runs when you
need executable behavior checks on the current host.

Sherpa Spleeter is fetched from locked `sherpa-onnx` native archives. Packaging renames the upstream `sherpa-onnx-offline-source-separation` executable to `sherpa-spleeter`, stages the target-specific ONNX Runtime libraries beside it, and reads the committed shared Spleeter 2-stems fp16 model files from `addon/anki_audio_quick_editor/bin/models/`.

Package one platform at a time for normal distribution:

```bash
python3 scripts/release.py --target macos-arm64
python3 scripts/release.py --target macos-x86_64
python3 scripts/release.py --target windows-x86_64
```

If you need a smaller variant that keeps FFmpeg external, build:

```bash
python3 scripts/release.py --target macos-arm64 --no-bundle-ffmpeg
python3 scripts/release.py --target macos-x86_64 --no-bundle-ffmpeg
python3 scripts/release.py --target windows-x86_64 --no-bundle-ffmpeg
```

Those archives use an `-external-ffmpeg.ankiaddon` suffix, omit bundled
`ffmpeg`/`ffprobe`, and expect users to provide them via settings or `PATH`.

The universal `--target all` archive still works for direct distribution when
called with `--allow-large-archive "<reason>"`, but third-party static FFmpeg
pushes it above the normal compressed-size gate.

Pause-shortening runs retain provenance under `<addon_dir>/aqe_artifacts/<run_id>/`, including intermediate WAV files, raw silence metadata, timeline JSON, filter script, final output copy, and `manifest.json`. The directory is intentionally unbounded for now, so clean it manually during local testing if it grows large.

RNNoise denoising uses ffmpeg to convert arbitrary source audio to raw 48 kHz mono signed 16-bit PCM, runs RNNoise over that raw stream, then uses ffmpeg to encode the result as MP3.

Prosody visualization can use `praat-parselmouth` when it is already available in Anki's Python, but the shipped add-on does not require it. The required cross-platform path is the built-in ffmpeg/PCM fallback. A dry-run compatibility check on this machine resolved `praat-parselmouth 0.4.7` and `numpy 2.4.4` for Anki Python 3.13, but those packages were not installed or vendored.

Local ffmpeg setup remains useful for development and e2e baselines:

- Installed with Homebrew: `ffmpeg 8.1.1`
- Binaries: `/opt/homebrew/bin/ffmpeg` and `/opt/homebrew/bin/ffprobe`

When adding another external executable dependency, keep normal e2e coverage on the real binary where it is available, and use fake or mock executables only for exceptional cases that are hard to force with the real tool: missing binary, permission errors, bad arguments, malformed output, nonzero exits, or timeout-style behavior. Document the expected binary name, discovery order, supported override config, and the exact fake-binary scenarios covered by tests.

## Dev Dependencies

Python dev dependencies live in two places and must stay in sync:

1. `scripts/dev.py` -> `DEV_DEPS`
2. `pyproject.toml` -> `[dependency-groups].dev`

Qodana is an external CLI dependency, not a Python package. It is configured by
`qodana.yaml`, runs in native mode with `qodana-python-community`, and is part of
`python3 scripts/dev.py check` through `python3 scripts/dev.py qodana`.

## Frontend Dependencies

The settings dialog, inline editor UI, and Browser batch UI use Svelte 5 and Vite from `settings_ui/package.json`. Rebuild ignored generated bundles after editing `.svelte` or `.ts` files:

```bash
python3 scripts/dev.py build
```

`python3 scripts/dev.py test-svelte` and `python3 scripts/dev.py test-e2e` also run the frontend bundle build before their tests. Keep that dependency in `scripts/dev.py` so test callers do not need to remember it.

Do not treat `settings_ui/src/` as the runtime artifact. During Anki and e2e runs, the add-on reads `addon/anki_audio_quick_editor/templates/settings/settings_bundle.{js,css}`, `addon/anki_audio_quick_editor/templates/editor/editor_bundle.{js,css}`, and `addon/anki_audio_quick_editor/templates/batch/batch_bundle.{js,css}`. Build output changes after `check`, `test-svelte`, or `test-e2e` are expected when source changed, but those generated files are ignored by git.

Settings and Browser batch WebView commands use the shared `bridge:{ command, payload }` JSON envelope. Add new settings or batch bridge commands through `settings_ui/src/lib/bridge.ts` or `settings_ui/src/batch/bridge.ts`, decode them with `webview_bridge.py`, and keep payload shapes contract-backed when they cross the Python/TypeScript boundary.

`quicktype` is pinned as a settings UI dev dependency and installed from `settings_ui/package-lock.json`. It is used only for development-time JSON contract generation and is not bundled into the Anki add-on runtime.

Frontend quality checks run through:

```bash
python3 scripts/dev.py test-svelte
```

That command requires `settings_ui/node_modules`, rebuilds the ignored generated bundles, then runs `npm run validate`, which chains `svelte-check`, ESLint, `tsc --noEmit`, and Vitest coverage thresholds.

Generate and verify communication contracts with:

```bash
python3 scripts/dev.py contracts-generate
python3 scripts/dev.py contracts-check
```

`python3 scripts/dev.py check` generates contracts before checking them, and the frontend bundle build also generates contracts first. Generated contract files are ignored by git.

## Type And Exception Policy

- Python runtime modules are checked with `disallow_untyped_defs` and `disallow_incomplete_defs`; annotate new function parameters and returns instead of relying on unchecked signatures.
- Python `Any` should stay at dynamic Anki/Qt seams, generated contract helpers, or intentionally JSON-like payload edges. Prefer concrete dataclasses, protocols, or generated contract DTOs for owned data.
- Svelte and TypeScript source must not use explicit `any`. Use `unknown` at external/bridge boundaries, then narrow before use.
- Broad `except Exception` handlers are allowed only at documented boundaries: Anki/Qt callbacks, background worker edges, per-note batch isolation, diagnostics/external-tool probes, and best-effort reveal/refresh paths. Additions require the allowlist in `tests/test_architecture/test_rule21_broad_exception_allowlist.py` with a reason.

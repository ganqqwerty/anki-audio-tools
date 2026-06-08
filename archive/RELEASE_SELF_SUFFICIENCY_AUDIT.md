# Release Self-Sufficiency Audit

Date: 2026-05-18

This audit looks at whether `scripts/release.py` produces a `.ankiaddon` that is self-sufficient on any platform. In this document, "self-sufficient" means a user can install the archive into a supported Anki desktop runtime and use every advertised feature without installing extra command-line tools, Python packages, Node packages, or generated build artifacts.

## Current Release Flow

`python3 scripts/release.py`:

1. Reads the version from `pyproject.toml` unless `--version` is supplied.
2. Verifies the requested version matches `pyproject.toml` and `addon/anki_audio_quick_editor/_version.py`.
3. Unless `--skip-checks` is supplied, discovers Anki's Python, runs `python3 scripts/dev.py check`, optionally runs e2e and Sonar with `--full`, and verifies settings/editor webview bundles are fresher than their Svelte/TypeScript sources.
4. Zips files from `addon/anki_audio_quick_editor/` when `_should_include()` allows them.
5. Verifies a small fixed list of required archive files and rejects `__pycache__`, `.pyc`, `.so`, and `.pyd` entries.

The archive built during this audit with `python3 scripts/release.py --skip-checks` contained 65 files and compressed to about 15 MB. It included Python runtime modules, `config.json`, `config.schema.json`, generated `contracts_generated.py`, generated settings/editor webview bundles, and the currently committed `bin/` contents.

## Current Packaged Runtime Surface

The archive includes:

- Add-on Python modules under `addon/anki_audio_quick_editor/`.
- Default config and config schema.
- Generated Python communication contracts when `contracts_generated.py` exists locally.
- Generated settings and editor webview bundles when they exist locally.
- Native audio helper binaries currently present in `addon/anki_audio_quick_editor/bin/`.

The current `bin/` payload is:

- `deep-filter-0.5.6-aarch64-apple-darwin`, a macOS arm64 DeepFilterNet executable.
- `rnnoise-cli-macos-arm64/bin/rnnoise-cli`, a macOS arm64 RNNoise CLI executable.
- RNNoise license/provenance notes and a `bin/README.md`.

The archive preserves executable bits for both packaged macOS arm64 binaries.

## Self-Sufficiency Gaps

### 1. `ffmpeg` and `ffprobe` are not bundled

This is the largest gap. Core features call `find_ffmpeg()` and `find_ffprobe()` through `audio_tools.py`, and those functions only use a configured path or `PATH`.

Affected runtime behavior:

- Basic trim, speed, volume, playback segment, and region-delete rendering.
- MP3 encoding for DeepFilterNet and RNNoise paths.
- Pause-shortening silence detection and final rendering.
- Fallback prosody visualization through `prosody_fallback.py`.
- Duration probing through `probe_duration_ms()`.

The add-on therefore cannot be self-sufficient on a clean machine unless Anki or the OS already provides compatible `ffmpeg` and `ffprobe` commands. The README and DEVELOPMENT docs currently describe this as a requirement, not as a bundled runtime.

Missing work:

- Add platform-specific bundled `ffmpeg` and `ffprobe` binaries, or choose an embedded library/runtime strategy that avoids shelling out.
- Add platform dispatch in `audio_tools.py` for bundled ffmpeg/ffprobe before falling back to config and `PATH`.
- Verify codec support, especially `libmp3lame`, because the current commands encode MP3 with `-codec:a libmp3lame`.
- Add archive validation that every supported platform has both binaries.
- Add e2e/runtime smoke tests that can run with `PATH` stripped so bundled binaries are actually exercised.

### 2. Native denoise binaries only cover macOS arm64

DeepFilterNet and RNNoise are both packaged only for `("Darwin", "arm64")`.

Current dispatch:

- `_BUNDLED_DEEP_FILTER_BY_PLATFORM` maps only macOS arm64.
- `_BUNDLED_RNNOISE_DIR_BY_PLATFORM` maps only macOS arm64.
- Other platforms must use `deep_filter_path`, `deep-filter` on `PATH`, or receive the RNNoise unsupported-runtime diagnostic.

Affected runtime behavior:

- `Denoise > Standard` and pause shortening are not self-sufficient outside macOS arm64.
- `Denoise > RNNoise` is not self-sufficient outside macOS arm64 and has no external override path.

Missing work:

- Decide the supported platform matrix explicitly: at minimum macOS arm64, macOS x86_64, Windows x86_64, and Linux x86_64 if "any platform" means normal Anki desktop platforms.
- Build or source DeepFilterNet and RNNoise binaries for each supported platform.
- Package each binary with license/provenance/checksum metadata.
- Add platform dispatch and diagnostics for each target.
- Add runtime smoke tests for every packaged binary, not only command construction tests.

### 3. Generated runtime files are ignored by git and weakly validated

The add-on imports generated Python contracts at runtime through `contracts_generated.py`. That file is ignored by git and is produced by `scripts/generate_contracts.py`.

Plain `python3 scripts/release.py` usually produces it because `check` runs `contracts-generate`, but `python3 scripts/release.py --skip-checks` can package whatever generated file happens to be present locally. `_validate_archive()` does not require `contracts_generated.py`, so a skip-check archive can pass validation while missing a runtime import.

The webview bundles have better validation because they are in `REQUIRED_ARCHIVE_FILES`, but skip-check mode still skips freshness checks.

Missing work:

- Add `contracts_generated.py` to `REQUIRED_ARCHIVE_FILES`.
- Make release generate contracts and webview bundles as build steps, not as side effects of `check`.
- Keep freshness validation even when expensive tests are skipped, or split `--skip-checks` into a narrower flag that skips tests but never skips required artifact generation and archive validation.
- Add a clean-tree packaging test that starts from absent generated artifacts and proves release creates everything needed.

### 4. Release validation checks only a minimal manifest

`_validate_archive()` currently checks six required files and excludes Python/native extension byproducts. It does not verify most runtime-critical files or platform payload completeness.

Examples not required today:

- `contracts_generated.py`
- `audio_tools.py`
- `audio_commands.py`
- `audio_processor.py`
- `settings/__init__.py`
- `settings/commands.py`
- `editor_ui.py`
- `bin/README.md`
- native binary license files
- platform-specific binary matrix entries

The archive may still break at import time or during a feature path while passing release validation.

Missing work:

- Replace the small tuple with a generated or maintained manifest of runtime-required modules and assets.
- Add an import smoke test against the built archive in a temporary extraction directory.
- Add feature smoke checks that instantiate settings/editor HTML generation and audio tool discovery without relying on the source checkout.
- Validate that excluded directories such as `aqe_artifacts/`, logs, `meta.json`, `__pycache__/`, and local test leftovers are absent.

### 5. External Python packages are not vendored

Runtime imports are mostly standard library plus Anki-provided `aqt`/`anki`. There is one optional non-Anki dependency: `parselmouth`, imported only inside the optional Praat backend.

This is not currently a blocker for baseline runtime because `prosody_analyzer.py` falls back to the ffmpeg/PCM analyzer when `parselmouth` is unavailable. It does mean the preferred pitch/intensity backend is not self-sufficient.

Missing work if preferred-Praat behavior must be self-sufficient:

- Vendor `praat-parselmouth` and its native dependencies for every supported Anki Python/platform pair, or keep it explicitly optional and document that fallback prosody is the self-sufficient path.
- Add archive/import validation that proves no required non-Anki package is imported at startup or in required feature paths.

### 6. `debugpy` can be a startup dependency through environment

`__init__.py` imports `debugpy` when `DEBUG_ANKI` is set. `debugpy` is not vendored and is not guaranteed in a user's Anki Python.

This does not affect normal startup, but it creates a fragile environment-triggered import path in the shipped add-on.

Missing work:

- Guard the `debugpy` import with a clear `ImportError` diagnostic, or move debug attachment behind development-only code that is not shipped.
- Add a release import smoke test with and without `DEBUG_ANKI` if this behavior is intentionally shipped.

### 7. Licensing/provenance is incomplete for a self-contained binary distribution

RNNoise has a bundled license file. DeepFilterNet has source URL, checksum, and license names in `bin/README.md`, but the archive does not include full upstream license texts or a top-level third-party notice.

This is a distribution-quality gap even though it is not a runtime import gap.

Missing work:

- Add full third-party notices for every bundled native executable.
- Include exact upstream license files for DeepFilterNet and its redistributed binary payload.
- Add a release validation check that required notice/license files are present.

### 8. There is no cross-platform release matrix

The current release command builds one archive from the local checkout. It does not declare which OS/architecture combinations the archive supports, and the archive itself contains only macOS arm64 native helpers.

Missing work:

- Define the release target matrix.
- Decide whether one `.ankiaddon` contains all platform binaries or whether releases are platform-specific.
- If one archive contains all binaries, add platform directories and archive validation for the full matrix.
- If archives are platform-specific, include the platform in the artifact name and publish separate artifacts with clear compatibility metadata.

## Recommended Fix Order

1. Define the supported platform matrix and whether release artifacts are universal or platform-specific.
2. Make release artifact generation explicit: contracts first, webview bundles second, archive third.
3. Strengthen archive validation so missing generated contracts, missing bundles, unexpected local files, and missing platform binaries fail the release.
4. Bundle or otherwise solve ffmpeg/ffprobe for every supported platform.
5. Extend DeepFilterNet and RNNoise packaging to the same platform matrix.
6. Add archive smoke tests that install/extract the built `.ankiaddon` into a temporary directory and exercise imports, settings/editor bundle rendering, audio tool discovery, and bundled binary version checks.
7. Add third-party notices and validate them in release.

## Current Bottom Line

The current `.ankiaddon` is not self-sufficient on any platform in the strict sense because all meaningful audio paths still require `ffmpeg` and `ffprobe` outside the archive. It is closest on macOS arm64 because DeepFilterNet and RNNoise are bundled there, but even that platform still depends on external ffmpeg/ffprobe for rendering, probing, prosody fallback, and denoiser input/output conversion.

The release script is a useful packaging gate, but it currently validates the presence of a few artifacts rather than proving the archive can run standalone. The next release-hardening work should focus on explicit build artifacts, a real runtime manifest, and bundled platform binaries.

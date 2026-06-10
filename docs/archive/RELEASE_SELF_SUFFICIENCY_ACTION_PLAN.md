# Release Self-Sufficient Add-on Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `python3 scripts/release.py` produce a `.ankiaddon` that can run every advertised feature on Windows x86_64, macOS arm64, and macOS x86_64 without user-installed command-line tools, generated files, Python packages, Node packages, or first-run downloads.

**Architecture:** Build a staged release tree from source, inject generated contracts/webview bundles, inject a locked platform runtime payload, validate the archive against a manifest, and smoke-test the archive in isolation. Runtime tool discovery uses user overrides first, then bundled per-platform executables, then `PATH` as a compatibility fallback.

**Tech Stack:** Python 3.13, Anki add-on zip packaging, Svelte/Vite generated webview bundles, FFmpeg/ffprobe, DeepFilterNet, RNNoise, SHA-256 locked binary assets, stdlib `zipfile`, pytest/e2e.

---

## Scope And Definition Of Done

The supported release matrix is intentionally limited to:

| Target key | OS | CPU | Runtime executables |
| --- | --- | --- | --- |
| `macos-arm64` | macOS | Apple Silicon | `ffmpeg`, `ffprobe`, `deep-filter`, `rnnoise-cli` |
| `macos-x86_64` | macOS | Intel | `ffmpeg`, `ffprobe`, `deep-filter`, `rnnoise-cli` |
| `windows-x86_64` | Windows | 64-bit Intel/AMD | `ffmpeg.exe`, `ffprobe.exe`, `deep-filter.exe`, `rnnoise-cli.exe` |

Definition of done:

- `python3 scripts/release.py` produces an archive that contains generated Python contracts, generated settings/editor bundles, root add-on files, and all three platform runtime payloads.
- The archive does not require `ffmpeg`, `ffprobe`, `deep-filter`, `rnnoise-cli`, Node, quicktype, npm packages, or non-Anki Python packages on the user's machine.
- Runtime discovery resolves bundled `ffmpeg`/`ffprobe`, DeepFilterNet, and RNNoise on each supported platform with empty settings.
- A smoke test extracts the archive to a temporary add-on folder, blocks accidental `PATH` lookup, imports runtime-safe modules, validates settings/editor template availability, verifies current-platform bundled tool discovery, and runs current-platform `--version` checks.
- Platform acceptance scripts verify each target binary on its native platform before release approval.
- Third-party license texts, source links, build commands, and SHA-256 values are included in the archive and validated.
- `DEBUG_ANKI=1` no longer makes normal shipped startup depend on unvendored `debugpy`.

Out of scope:

- Linux self-sufficiency.
- Vendoring `praat-parselmouth`; the self-sufficient prosody path remains the ffmpeg/PCM fallback.
- First-run downloads. They are not self-sufficient and must not be used for release runtime payloads.

## Recommended Strategy

Use one universal `.ankiaddon` containing all three platform payloads.

Reasons:

- Anki add-on archives are plain zip-style `.ankiaddon` files whose contents should not include the top-level folder and should exclude `__pycache__`; this repository already follows that model in `scripts/release.py`.
- A universal archive gives a single install path and avoids asking users to identify CPU architecture.
- The current full third-party FFmpeg binary packages are too large for a universal archive, so the plan depends on custom minimal FFmpeg builds rather than copying full provider packages.

Fallback only if size proves impractical:

- Keep the universal archive as the primary target.
- If the compressed artifact exceeds the release size gate after custom FFmpeg minimization, add an explicit `--target {macos-arm64,macos-x86_64,windows-x86_64,universal}` release option and publish three platform-specific `.ankiaddon` files plus the universal file only where hosting permits.
- Do not use platform-specific artifacts as the first implementation path; they add support burden and user confusion.

## Source Findings To Carry Into Implementation

- FFmpeg publishes source code and points to third-party compiled builds; it does not itself publish official Windows/macOS binaries. The current stable source release observed for this plan is FFmpeg 8.1.1, released on 2026-05-04.
- FFmpeg license compliance depends on the build configuration. Avoid `--enable-gpl` and `--enable-nonfree` for our custom builds unless the project deliberately changes its distribution license posture.
- DeepFilterNet v0.5.6 already publishes the three executable assets this plan needs:
  - `deep-filter-0.5.6-aarch64-apple-darwin`
  - `deep-filter-0.5.6-x86_64-apple-darwin`
  - `deep-filter-0.5.6-x86_64-pc-windows-msvc.exe`
- RNNoise v0.2 publishes source only, so each `rnnoise-cli` executable must be built by us from `scripts/rnnoise_cli/rnnoise_cli.c` plus the upstream RNNoise source.
- BtbN publishes Windows x86_64 LGPL FFmpeg builds, and Martin Riedl publishes macOS arm64/x86_64 FFmpeg/ffprobe builds. Treat these as useful references or emergency bootstrap inputs, not the final default, because full builds are large and may include broader codec/license surface than needed.
- The current repository has no top-level `LICENSE` file. Before redistributing third-party binaries, choose and commit the add-on's own license and include a third-party notice file.

Sources consulted:

- FFmpeg download page: https://ffmpeg.org/download.html
- FFmpeg legal page: https://ffmpeg.org/legal.html
- BtbN FFmpeg builds: https://github.com/BtbN/FFmpeg-Builds
- Gyan Windows FFmpeg builds: https://www.gyan.dev/ffmpeg/builds/
- Martin Riedl FFmpeg builds: https://ffmpeg.martin-riedl.de/
- DeepFilterNet v0.5.6 release: https://github.com/Rikorose/DeepFilterNet/releases/tag/v0.5.6
- RNNoise v0.2 release: https://github.com/xiph/rnnoise/releases/tag/v0.2
- Anki add-on sharing docs: https://addon-docs.ankiweb.net/sharing.html

## Target File Structure

Create or modify these files:

| Path | Responsibility |
| --- | --- |
| `scripts/release.py` | Build generated artifacts, stage the add-on, inject runtime payloads, zip from staging, validate archive, run archive smoke tests. |
| `scripts/release_assets.py` | Fetch, build, checksum, stage, and validate platform runtime assets. |
| `scripts/dev.py` | Add `release-assets`, `release-smoke`, and narrowed release helper commands. |
| `scripts/ffmpeg_build/README.md` | Document FFmpeg build prerequisites, exact configure flags, and native platform commands. |
| `scripts/ffmpeg_build/build_macos.sh` | Build minimal FFmpeg/ffprobe for `macos-arm64` and `macos-x86_64`. |
| `scripts/ffmpeg_build/build_windows.ps1` | Build minimal FFmpeg/ffprobe for `windows-x86_64`, or run on the Windows machine when needed. |
| `scripts/rnnoise_cli/build_macos.sh` | Build `rnnoise-cli` for both macOS targets. |
| `scripts/rnnoise_cli/build_windows.ps1` | Build `rnnoise-cli.exe` on Windows x86_64. |
| `release_assets.lock.json` | Committed source of truth for targets, tool versions, source URLs, generated SHA-256 values, expected version output, and license files. |
| `addon/anki_audio_quick_editor/audio_tools.py` | Resolve bundled per-platform tools and expose testable platform mapping helpers. |
| `addon/anki_audio_quick_editor/diagnostics.py` | Report bundled tool source, version, and platform in settings health checks. |
| `addon/anki_audio_quick_editor/__init__.py` | Guard `debugpy` so shipped startup never crashes when `DEBUG_ANKI=1` and `debugpy` is absent. |
| `addon/anki_audio_quick_editor/manifest.json` | Support direct `.ankiaddon` installation outside AnkiWeb. |
| `addon/anki_audio_quick_editor/bin/README.md` | Explain generated runtime payload layout and how to refresh it. |
| `addon/anki_audio_quick_editor/bin/THIRD_PARTY_NOTICES.md` | Runtime third-party notices copied into the archive. |
| `tests/test_audio_tools.py` | Unit coverage for platform mapping and bundled discovery. |
| `tests/test_release.py` | Archive manifest, validation, staging, generated artifact, executable-bit, and negative-path tests. |
| `tests/test_release_assets.py` | Lock-file parsing, checksum validation, platform completeness, and source URL validation. |
| `tests/test_debug_startup.py` | `DEBUG_ANKI` import guard coverage. |
| `e2e/test_release_self_sufficient_workflow.py` | Current-platform archive install smoke test with external tool lookup blocked. |
| `README.md` | Replace user-installed ffmpeg requirement with bundled runtime statement and override details. |
| `DEVELOPMENT.md` | Document release asset setup and the two-Python implications. |
| `TESTING.md` | Document release smoke and native platform acceptance commands. |
| `WEBVIEW_AND_TEMPLATES.md` | State that release always regenerates contracts and bundles. |

Generated release staging layout inside the archive:

```text
__init__.py
manifest.json
config.json
config.schema.json
contracts_generated.py
templates/settings/settings_bundle.js
templates/settings/settings_bundle.css
templates/editor/editor_bundle.js
templates/editor/editor_bundle.css
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

## Implementation Tasks

### Task 1: Lock The Runtime Asset Contract


- [ ] Create `release_assets.lock.json` with schema version, target list, tool list, source URLs, license obligations, expected archive names, expected executable names, and SHA-256 fields.
- [ ] Represent unknown locally built checksums as absent keys, not placeholder strings. `scripts/release_assets.py verify` must fail until every target executable has a concrete SHA-256 after the binary build task.
- [ ] Include DeepFilterNet v0.5.6 download URLs for all three targets.
- [ ] Include RNNoise v0.2 source URL and note that binaries are built locally.
- [ ] Include FFmpeg 8.1.1 source URL and note that binaries are built locally from source with our configure flags.
- [ ] Add `tests/test_release_assets.py` assertions that the lock contains exactly `macos-arm64`, `macos-x86_64`, and `windows-x86_64`, and exactly `ffmpeg`, `ffprobe`, `deep-filter`, and `rnnoise-cli` for each target.
- [ ] Add a lock validation test that fails if a binary entry has no checksum after `release_assets.lock.json` is marked release-ready.

Acceptance command:

```bash
python3 scripts/dev.py test tests/test_release_assets.py
```

Expected result: tests pass once the parser exists and fail clearly while checksums are intentionally missing during early implementation.

### Task 2: Build Release Assets Into A Staging Cache

- [ ] Create `scripts/release_assets.py` with these subcommands:
  - `fetch-deepfilter --target all|macos-arm64|macos-x86_64|windows-x86_64`
  - `build-rnnoise --target current|macos-arm64|macos-x86_64|windows-x86_64`
  - `build-ffmpeg --target current|macos-arm64|macos-x86_64|windows-x86_64`
  - `lock-checksums`
  - `verify --target all|current`
  - `stage --target all --destination "$STAGING_BIN_DIR"`
- [ ] Store downloaded source archives and generated binaries under an ignored cache such as `.release-assets/`.
- [ ] Never download during normal runtime. Downloads happen only during release asset preparation.
- [ ] Require SHA-256 verification after every download and after every local build.
- [ ] Copy only the runtime executables and required notice files into staging. Do not stage `ffplay`, headers, static libraries, object files, build logs, or source archives inside the `.ankiaddon`.
- [ ] Add `python3 scripts/dev.py release-assets fetch-deepfilter|build-rnnoise|build-ffmpeg|lock-checksums|verify|stage` passthrough commands.
- [ ] Add unit tests for missing binary, checksum mismatch, unknown target, and staging path traversal rejection.

Acceptance commands:

```bash
python3 scripts/dev.py release-assets verify --target current
python3 scripts/dev.py test tests/test_release_assets.py
```

Expected result: `verify --target current` reports missing assets until the current-platform binaries are fetched/built; once present, it prints each tool path, version output, and checksum.

### Task 3: Build Minimal FFmpeg And FFprobe

Use custom FFmpeg builds for the final self-sufficient release. Full third-party packages are acceptable only as a temporary reference while validating feature behavior.

- [ ] Add `scripts/ffmpeg_build/README.md` with prerequisites for macOS and Windows.
- [ ] Build FFmpeg 8.1.1 from verified source.
- [ ] Build and link LAME because current commands encode MP3 with `-codec:a libmp3lame`.
- [ ] Configure without `--enable-gpl` and without `--enable-nonfree`.
- [ ] Disable everything by default and enable only the formats/codecs/protocols/filters required by supported extensions and current command builders.
- [ ] Minimum FFmpeg feature set to validate:
  - programs: `ffmpeg`, `ffprobe`
  - protocols: `file`, `pipe`
  - demuxers: `aac`, `flac`, `matroska`, `mov`, `mp3`, `ogg`, `wav`
  - muxers: `mp3`, `null`, `s16le`, `wav`
  - decoders: `aac`, `alac`, `flac`, `mp3`, `mp3float`, `opus`, `pcm_f32le`, `pcm_s16le`, `pcm_s24le`, `vorbis`
  - encoders: `libmp3lame`, `pcm_s16le`
  - parsers: `aac`, `flac`, `mpegaudio`, `opus`, `vorbis`
  - filters: `anull`, `aresample`, `asetpts`, `atempo`, `atrim`, `concat`, `silencedetect`, `volume`
- [ ] Add fixture smoke tests that generate or include tiny `.aac`, `.flac`, `.m4a`, `.mp3`, `.oga`, `.ogg`, `.opus`, `.wav`, and `.webm` files and prove each can be probed and rendered to MP3 by the bundled build.
- [ ] For macOS builds, produce separate arm64 and x86_64 executables and verify with `file`, `codesign -dv`, and `xattr -l`.
- [ ] For Windows builds, use the Windows machine if cross-building is unreliable. The Windows task is complete only when `ffmpeg.exe -version`, `ffprobe.exe -version`, and an MP3 render smoke test pass on Windows.
- [ ] Record the exact configure lines, source commit/release, LAME source/version, and SHA-256 values in `release_assets.lock.json` and `bin/THIRD_PARTY_NOTICES.md`.

Acceptance commands on macOS:

```bash
python3 scripts/dev.py release-assets build-ffmpeg --target macos-arm64
python3 scripts/dev.py release-assets build-ffmpeg --target macos-x86_64
python3 scripts/dev.py release-assets verify --target macos-arm64
python3 scripts/dev.py release-assets verify --target macos-x86_64
```

Acceptance commands on Windows:

```powershell
python scripts/dev.py release-assets build-ffmpeg --target windows-x86_64
python scripts/dev.py release-assets verify --target windows-x86_64
```

### Task 4: Fetch DeepFilterNet For Every Target

- [ ] Use upstream v0.5.6 executable assets for all three targets.
- [ ] Normalize staged names to `deep-filter` on macOS and `deep-filter.exe` on Windows.
- [ ] Preserve upstream source URL, release tag, original filename, normalized staged filename, SHA-256, and license names in `release_assets.lock.json`.
- [ ] Include upstream MIT and Apache-2.0 license texts in `bin/THIRD_PARTY_NOTICES.md` or adjacent license files referenced by that notice file.
- [ ] Verify `deep-filter --help` or `deep-filter --version` on each native platform. If the command has no stable version output, record the successful diagnostic command in the lock file and tests.
- [ ] Keep the user-configured `deep_filter_path` override working ahead of bundled lookup.

Acceptance commands:

```bash
python3 scripts/dev.py release-assets fetch-deepfilter --target all
python3 scripts/dev.py release-assets verify --target current
```

Expected result: current-platform DeepFilterNet binary is present, executable, checksum-verified, and selected by discovery when no override is configured.

### Task 5: Build RNNoise CLI For Every Target

- [ ] Keep `scripts/rnnoise_cli/rnnoise_cli.c` as the owned CLI wrapper source.
- [ ] Build RNNoise v0.2 static library from upstream source for each target.
- [ ] Build a standalone `rnnoise-cli` or `rnnoise-cli.exe` that supports:
  - `rnnoise-cli --version`
  - `rnnoise-cli denoise --input in.s16le --output out.s16le --overwrite --json`
- [ ] For macOS, build arm64 and x86_64 binaries separately with an explicit minimum macOS version.
- [ ] For Windows, build on the Windows machine if a reliable internet binary does not exist. Prefer MSYS2 UCRT64 or Visual Studio, but the final binary must not depend on MSYS2 DLLs.
- [ ] Verify dynamic dependencies:
  - macOS: `otool -L` should show only system libraries.
  - Windows: use `dumpbin /dependents` or an equivalent tool and reject unexpected non-system DLLs.
- [ ] Record build commands, upstream source URL, local CLI source checksum, executable checksums, and BSD-style RNNoise license text.

Acceptance commands on native platforms:

```bash
python3 scripts/dev.py release-assets build-rnnoise --target current
python3 scripts/dev.py release-assets verify --target current
```

Expected result: `rnnoise-cli --version` passes and a one-second raw PCM denoise smoke test produces output.

### Task 6: Change Runtime Tool Discovery


- [ ] Add a typed platform key helper in `audio_tools.py` that maps:
  - `("Darwin", "arm64")` and `("Darwin", "aarch64")` to `macos-arm64`
  - `("Darwin", "x86_64")` to `macos-x86_64`
  - `("Windows", "AMD64")`, `("Windows", "x86_64")`, and `("Windows", "64bit")`-style machine values to `windows-x86_64`
- [ ] Add `bundled_tool_path(tool_name: str) -> Path | None` or a stricter enum equivalent.
- [ ] Change `find_ffmpeg()` order to configured path, bundled current-platform ffmpeg, then `PATH`.
- [ ] Change `find_ffprobe(ffmpeg_path)` order to sibling of selected ffmpeg, bundled current-platform ffprobe, then `PATH`.
- [ ] Extend DeepFilterNet bundled lookup to all three platform keys.
- [ ] Extend RNNoise bundled lookup to all three platform keys and update the unsupported diagnostic to name the actual unsupported platform.
- [ ] Keep existing override behavior for `ffmpeg_path` and `deep_filter_path`.
- [ ] Update settings diagnostics to report whether each tool came from config, bundled payload, or `PATH`.
- [ ] Unit-test all platform mappings by monkeypatching `platform.system()` and `platform.machine()`.

Acceptance command:

```bash
python3 scripts/dev.py test tests/test_audio_tools.py tests/test_diagnostics.py
```

Expected result: tests prove bundled paths are chosen with empty config and `PATH` lookup disabled.

### Task 7: Make Release Build From A Staged Tree


- [ ] Stop zipping directly from `addon/anki_audio_quick_editor/`.
- [ ] Add a temporary staging directory.
- [ ] Copy allowed source/runtime files into staging.
- [ ] Always run contract generation before staging, even when quality checks are skipped.
- [ ] Always run frontend build before staging, even when quality checks are skipped.
- [ ] Keep bundle freshness validation or replace it with a stronger "generated during this release invocation" assertion.
- [ ] Stage runtime assets by calling `scripts/release_assets.py stage --target all`.
- [ ] Include root `manifest.json` for direct `.ankiaddon` installation outside AnkiWeb.
- [ ] Replace `--skip-checks` with a clearer option such as `--skip-quality-checks`, or keep the old flag as an alias that still runs required artifact generation, asset staging, archive validation, and release smoke.
- [ ] Ensure executable bits are preserved in the zip for macOS binaries.
- [ ] Fail if the archive contains `__pycache__`, `.pyc`, generated logs, `aqe_artifacts`, `meta.json`, `.DS_Store`, source build caches, `node_modules`, raw source archives, or unstaged legacy root binaries.

Acceptance command:

```bash
python3 scripts/release.py --skip-quality-checks
```

Expected result: the archive is built from staging, not from incidental ignored files in the source checkout.

### Task 8: Strengthen Archive Validation

- [ ] Replace the small `REQUIRED_ARCHIVE_FILES` tuple with a release manifest that includes runtime Python modules, generated files, templates, config, root manifest, notices, and every platform executable.
- [ ] Validate the full platform matrix:
  - all targets exist
  - all four tools exist per target
  - Windows executable names end in `.exe`
  - macOS executable names do not end in `.exe`
  - macOS entries have executable mode bits
  - every staged executable SHA-256 matches `release_assets.lock.json`
- [ ] Validate third-party notices:
  - FFmpeg/LAME notice and source link
  - DeepFilterNet MIT and Apache-2.0 notices
  - RNNoise BSD-style notice
- [ ] Add an artifact size gate. Start with a warning above 125 MB compressed and fail above 145 MB compressed unless `--allow-large-archive` is passed with a reason logged into the release output.
- [ ] Add tests that deliberately remove `contracts_generated.py`, one platform binary, one notice file, and one executable bit and confirm validation fails with actionable messages.

Acceptance command:

```bash
python3 scripts/dev.py test tests/test_release.py
```

Expected result: missing generated artifacts, incomplete platform payloads, bad executable permissions, and stale checksums fail release validation.

### Task 9: Add Archive Smoke Tests

- [ ] Add `python3 scripts/dev.py release-smoke "$ARCHIVE_PATH"`.
- [ ] Extract the archive into a temporary directory named like an installed add-on package.
- [ ] Put that extracted package on `sys.path` and run import-safe module checks.
- [ ] Mock minimal `aqt` only where needed; do not accidentally import from the source checkout.
- [ ] Set `PATH` to an empty temporary directory for discovery tests so the smoke test fails if bundled lookup is incomplete.
- [ ] Verify:
  - `contracts_generated.py` imports.
  - settings and editor bundle files are present and non-empty.
  - `find_ffmpeg("")`, `find_ffprobe(ffmpeg_path)`, `find_deep_filter("")`, and `find_rnnoise_bundle()` resolve under the extracted add-on for the current platform.
  - current-platform `ffmpeg -version`, `ffprobe -version`, `deep-filter` diagnostic command, and `rnnoise-cli --version` run successfully.
  - a tiny WAV can be rendered to MP3 with bundled ffmpeg.
  - fallback prosody can analyze a tiny clip using bundled ffmpeg.
- [ ] Add a native e2e workflow that installs the built archive into Anki's temporary e2e profile instead of symlinking the source checkout.

Acceptance commands:

```bash
python3 scripts/release.py --skip-quality-checks
VERSION=$(python3 -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')
python3 scripts/dev.py release-smoke "dist/anki-audio-quick-editor-${VERSION}.ankiaddon"
python3 scripts/dev.py test-e2e
```

Expected result: source checkout tools and system `PATH` are not needed for smoke success.

### Task 10: Fix The `DEBUG_ANKI` Startup Dependency


- [ ] Move debug attachment into a helper such as `_maybe_attach_debugger()`.
- [ ] Catch `ImportError` for `debugpy`.
- [ ] Log a clear warning and continue startup if `DEBUG_ANKI=1` but `debugpy` is not installed.
- [ ] Unit-test import behavior with `DEBUG_ANKI=1` and no `debugpy` in `sys.modules`.

Acceptance command:

```bash
python3 scripts/dev.py test tests/test_debug_startup.py
```

Expected result: shipped startup is not fragile when a user's environment contains `DEBUG_ANKI=1`.

### Task 11: Add Native Platform Acceptance Scripts

- [ ] Add `scripts/release_acceptance.py --archive "$ARCHIVE_PATH" --target current`.
- [ ] On macOS, verify `file`, `codesign -dv`, `otool -L`, executable bits, and no quarantine xattrs for staged binaries.
- [ ] On Windows, verify `where ffmpeg` is not used, run the bundled `.exe` files by absolute path, and check DLL dependencies.
- [ ] Run a short feature smoke on each native platform:
  - probe duration
  - trim/speed/volume render to MP3
  - playback segment WAV render
  - region delete render
  - DeepFilterNet prepare/denoise/encode path
  - RNNoise prepare/denoise/encode path
  - prosody fallback
- [ ] Save acceptance logs under `dist/release-acceptance/${VERSION}/${TARGET}.json`, where `VERSION` is read from `pyproject.toml` and `TARGET` is the native target key.
- [ ] Make release approval require all three target logs for the same archive checksum.

Acceptance commands:

```bash
VERSION=$(python3 -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')
python3 scripts/release_acceptance.py --archive "dist/anki-audio-quick-editor-${VERSION}.ankiaddon" --target current
```

Expected result: each native machine produces a JSON log that names the archive checksum and all tool versions.

### Task 12: Update Documentation And User-Facing Diagnostics

Use `$doc-maintain` after implementation because this changes release behavior, runtime requirements, diagnostics, and docs.

- [ ] Update `README.md` requirements:
  - Anki and Python remain requirements.
  - ffmpeg/ffprobe are bundled for supported platforms.
  - DeepFilterNet and RNNoise are bundled for supported platforms.
  - Optional overrides remain available for advanced users.
- [ ] Update `DEVELOPMENT.md` with release asset cache setup, native build prerequisites, and Windows machine handoff.
- [ ] Update `TESTING.md` with release smoke and native acceptance commands.
- [ ] Update `WEBVIEW_AND_TEMPLATES.md` to state release always regenerates contracts and bundles.
- [ ] Update `addon/anki_audio_quick_editor/bin/README.md` with the new generated layout and provenance policy.
- [ ] Add `bin/THIRD_PARTY_NOTICES.md` and make archive validation require it.
- [ ] Update settings diagnostics copy so users can tell whether a tool is bundled, overridden, or from `PATH`.

Acceptance command:

```bash
python3 scripts/dev.py check
```

Expected result: docs and tests agree with the new runtime dependency story.

## Release Flow After This Plan

Normal release:

```bash
python3 scripts/dev.py release-assets verify --target all
python3 scripts/release.py --full
VERSION=$(python3 -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')
python3 scripts/dev.py release-smoke "dist/anki-audio-quick-editor-${VERSION}.ankiaddon"
```

Fast local packaging without expensive checks:

```bash
python3 scripts/release.py --skip-quality-checks
VERSION=$(python3 -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')
python3 scripts/dev.py release-smoke "dist/anki-audio-quick-editor-${VERSION}.ankiaddon"
```

Native platform approval:

```bash
VERSION=$(python3 -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')
python3 scripts/release_acceptance.py --archive "dist/anki-audio-quick-editor-${VERSION}.ankiaddon" --target current
```

The archive is releasable only after `release_acceptance.py` has passed on macOS arm64, macOS x86_64, and Windows x86_64 for the same archive checksum.

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Universal archive becomes too large | Custom minimal FFmpeg builds, no `ffplay`, no headers/libs/source archives, compressed size gate, platform-specific fallback only if necessary. |
| FFmpeg codec set is too small | Fixture matrix for every supported source extension and every command builder; expand enabled demuxers/decoders only when a test proves the need. |
| License posture is unclear | Choose project license first, keep FFmpeg LGPL-only builds, include source links/build flags/notices, avoid GPL/nonfree builds unless intentionally approved. |
| Windows builds are not available from internet | Build FFmpeg/RNNoise on the Windows machine, lock checksums, and stage the resulting binaries through the same manifest. DeepFilterNet Windows asset already exists upstream. |
| macOS blocks unsigned downloaded executables | Prefer locally built/signable FFmpeg/RNNoise; inspect current DeepFilterNet signing status; sign/notarize command-line tools if native acceptance finds Gatekeeper failures. |
| Release accidentally uses local generated files | Generate contracts and bundles during release and stage from a temporary tree; smoke-test extracted archive with source checkout excluded. |
| User overrides break | Keep configured `ffmpeg_path` and `deep_filter_path` ahead of bundled lookup; unit-test configured, bundled, and `PATH` fallback order. |

## Implementation Order

1. Runtime asset lock and validation skeleton.
2. Staged release builder that still uses current binaries.
3. Bundled `ffmpeg`/`ffprobe` discovery and tests.
4. DeepFilterNet target expansion.
5. RNNoise target expansion.
6. Minimal FFmpeg builds.
7. Archive validation and smoke tests.
8. Native platform acceptance scripts.
9. Docs and third-party notices.

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

E2E tests must copy the add-on into their temporary `ANKI_BASE` instead of symlinking back to the repo. Otherwise, test-only config writes can leak into the real development add-on. The most visible symptom is manual Anki clicks on `Shorten Pauses` or `Denoise > Standard` failing with `fake deep-filter failed`, because an E2E fake `deep-filter` path was written into `addon/anki_audio_quick_editor/meta.json`.

If that happens, clear `deep_filter_path` in `addon/anki_audio_quick_editor/meta.json` or use the settings dialog to reset the DeepFilterNet path. The E2E fixture should keep excluding `meta.json`, logs, caches, and artifact directories from the copied add-on tree.

## Runtime Dependencies

Anki add-ons cannot rely on `pip install` at user runtime. Audio Quick Editor currently uses only the Python/Qt runtime bundled with Anki plus user-installed `ffmpeg`/`ffprobe` executables, so no Python runtime packages are vendored.

Noise removal and pause shortening use DeepFilterNet's `deep-filter` executable. The repository bundles the pinned macOS arm64 binary at `addon/anki_audio_quick_editor/bin/deep-filter-0.5.6-aarch64-apple-darwin`; see `addon/anki_audio_quick_editor/bin/README.md` for the upstream release URL and checksum. Other platforms can still configure `deep_filter_path` or provide `deep-filter` on `PATH`.

Pause-shortening runs retain provenance under `<addon_dir>/aqe_artifacts/<run_id>/`, including intermediate WAV files, raw silence metadata, timeline JSON, filter script, final output copy, and `manifest.json`. The directory is intentionally unbounded for now, so clean it manually during local testing if it grows large.

RNNoise denoising uses a bundled macOS arm64 CLI at `addon/anki_audio_quick_editor/bin/rnnoise-cli-macos-arm64/bin/rnnoise-cli`. The add-on uses ffmpeg to convert arbitrary source audio to raw 48 kHz mono signed 16-bit PCM, runs RNNoise over that raw stream, then uses ffmpeg to encode the result as MP3.

Prosody visualization can use `praat-parselmouth` when it is already available in Anki's Python, but the shipped add-on does not require it. The required cross-platform path is the built-in ffmpeg/PCM fallback. A dry-run compatibility check on this machine resolved `praat-parselmouth 0.4.7` and `numpy 2.4.4` for Anki Python 3.13, but those packages were not installed or vendored.

Local ffmpeg setup:

- Installed with Homebrew: `ffmpeg 8.1.1`
- Binaries: `/opt/homebrew/bin/ffmpeg` and `/opt/homebrew/bin/ffprobe`

When adding another external executable dependency, keep normal e2e coverage on the real binary where it is available, and use fake or mock executables only for exceptional cases that are hard to force with the real tool: missing binary, permission errors, bad arguments, malformed output, nonzero exits, or timeout-style behavior. Document the expected binary name, discovery order, supported override config, and the exact fake-binary scenarios covered by tests.

## Dev Dependencies

Python dev dependencies live in two places and must stay in sync:

1. `scripts/dev.py` -> `DEV_DEPS`
2. `pyproject.toml` -> `[dependency-groups].dev`

## Frontend Dependencies

The settings dialog and inline editor UI use Svelte 5 and Vite from `settings_ui/package.json`. Rebuild ignored generated bundles after editing `.svelte` or `.ts` files:

```bash
python3 scripts/dev.py build
```

`python3 scripts/dev.py test-svelte` and `python3 scripts/dev.py test-e2e` also run the frontend bundle build before their tests. Keep that dependency in `scripts/dev.py` so test callers do not need to remember it.

Do not treat `settings_ui/src/` as the runtime artifact. During Anki and e2e runs, the add-on reads `addon/anki_audio_quick_editor/templates/settings/settings_bundle.{js,css}` and `addon/anki_audio_quick_editor/templates/editor/editor_bundle.{js,css}`. Build output changes after `check`, `test-svelte`, or `test-e2e` are expected when source changed, but those generated files are ignored by git.

The generated webview bundles are runtime artifacts, but they should not be committed or indexed as source code by GitNexus. Keep `addon/anki_audio_quick_editor/templates/*/*_bundle.{js,css}` in `.gitignore` and `.gitnexusignore` so change detection stays focused on the TypeScript, Svelte, Python, schema, and test sources that produced them. If ignored bundle symbols still appear after changing `.gitnexusignore`, run a forced rebuild of the local index rather than relying on an incremental "already up to date" analyze pass.

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

## GitNexus Local Index Notes

The repo hook currently pins GitNexus through `GITNEXUS_VERSION` in `scripts/gitnexus_auto_analyze.sh`. Prefer the pinned version when refreshing the index manually:

```bash
npx -y gitnexus@1.6.4 analyze --force --skip-agents-md --no-stats
```

Using bare `npx gitnexus ...` may pick a newer package than the repo hook. If the latest package fails with a CLI/runtime error, retry the pinned version before treating GitNexus as unavailable.

## Type And Exception Policy

- Python runtime modules are checked with `disallow_untyped_defs` and `disallow_incomplete_defs`; annotate new function parameters and returns instead of relying on unchecked signatures.
- Python `Any` should stay at dynamic Anki/Qt seams, generated contract helpers, or intentionally JSON-like payload edges. Prefer concrete dataclasses, protocols, or generated contract DTOs for owned data.
- Svelte and TypeScript source must not use explicit `any`. Use `unknown` at external/bridge boundaries, then narrow before use.
- Broad `except Exception` handlers are allowed only at documented boundaries: Anki/Qt callbacks, background worker edges, per-note batch isolation, diagnostics/external-tool probes, and best-effort reveal/refresh paths. Additions require the allowlist in `tests/test_architecture/test_rule21_broad_exception_allowlist.py` with a reason.

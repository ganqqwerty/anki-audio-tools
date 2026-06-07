---
name: release
description: Build and validate this repository's add-on release artifacts across macOS and Windows. Use when Codex needs to prepare a public thin `.ankiaddon` release, run the runtime-pack release flow, verify runtime URLs or wheel locks, smoke-test a built archive, or summarize remaining publish steps.
---

# Release

Use the repo docs instead of memory. Read `DEVELOPMENT.md` at the `Release Workflow` section and the `Building A Release` section in `AGENTS.md` before running release commands.

## Host Launcher

Use the host-appropriate Python launcher in every command:

- macOS and Linux: `python3`
- Windows: `py -3.12`

When writing a command sequence in the response, keep the launcher consistent with the current host.

## Decide The Release Type

Choose the path before running anything expensive:

1. Use the runtime-pack flow when native runtime payloads, locked runtime binaries, or runtime model files changed.
2. Use the thin add-on flow when packaging and publishing the `.ankiaddon`.
3. Use `--embed-runtime` only for local or offline validation builds. Do not use it for public thin releases.

## Thin Add-On Release

Use this workflow for the public `.ankiaddon` release:

1. Confirm the version matches in:
   - `pyproject.toml`
   - `addon/anki_audio_quick_editor/_version.py`
   - `addon/anki_audio_quick_editor/manifest.json`
2. Run the preflight checks:
   - `<py> scripts/dev.py vendor-wheels verify`
   - `<py> scripts/dev.py check`
   - `<py> scripts/dev.py test-e2e`
   - `<py> scripts/release_runtime_cli.py verify --metadata runtime_release.lock.json`
3. Build the committed version:

```bash
<py> scripts/release.py --target all --verify-runtime-urls
<py> scripts/dev.py release-smoke dist/anki-audio-quick-editor-<version>.ankiaddon
```

4. Inspect the packaged archive before calling it ready:
   - `dist/anki-audio-quick-editor-<version>.ankiaddon` exists
   - `bin/runtime_manifest.json` points at immutable `runtime-vN` URLs
   - Only the `.ankiaddon` should be published with the add-on release
5. Call out remaining manual work:
   - native acceptance on each supported platform
   - GitHub release upload of the `.ankiaddon`
   - AnkiWeb upload of the same smoke-tested artifact
   - recorded SHA-256 of the published `.ankiaddon`

Treat `--target current` or single-target builds as private validation only unless the user explicitly wants a platform-limited package.

## Runtime Pack Release

Run this only when runtime payloads changed:

```bash
<py> scripts/dev.py release-assets verify --target all
<py> scripts/dev.py release-assets verify --target current --diagnostics
<py> scripts/dev.py release-runtime build --runtime-version <runtime-version> --target all
<py> scripts/dev.py release-runtime upload --metadata runtime_release.lock.json
<py> scripts/dev.py release-runtime verify --metadata runtime_release.lock.json
```

If remote verification is too quiet for the dev runner timeout, use:

```bash
<py> scripts/dev.py --idle-timeout 900 release-runtime verify --metadata runtime_release.lock.json
```

Do not overwrite an existing `runtime-vN` release. Runtime tags are immutable once published.

## Platform Notes

- On Windows, prefer `py -3.12` for repo commands. `scripts/dev.py release-smoke` already chooses Anki's Python 3.13 runtime internally.
- On Windows native acceptance, confirm bundled wheels import from `user_files/python_vendor/windows-x86_64/.../site-packages/` and that Graph/Pitch Hum uses `praat-parselmouth` without the ffmpeg/PCM fallback warning.
- On macOS, local Homebrew ffmpeg is useful for development and e2e baselines, but public thin releases still rely on runtime packs for ffmpeg and ffprobe.
- If frontend tooling is questionable on a fresh machine, run `<py> scripts/dev.py info` or `<py> scripts/dev.py setup` before release checks.

## Reporting

Report:

- which release path was used
- exact commands run
- pass or fail status for `check`, `test-e2e`, and release packaging
- produced artifact path
- any remaining manual publish or platform-acceptance steps

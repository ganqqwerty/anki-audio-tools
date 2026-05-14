# Testing

## Main Commands

```bash
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e
```

## What Gets Tested

- `tests/` covers sound-reference parsing, edit-state validation, ffmpeg filter construction, config migration, bootstrap behavior, editor bridge wiring, and settings command/state logic.
- `tests/test_architecture/` enforces layer boundaries, module classification, shell-thin settings rules, and DB access isolation.
- `settings_ui/tests/` covers bridge commands, async job plumbing, logging, and the settings UI.
- `e2e/` exercises the real add-on inside a live Anki runtime via `aqt._run(exec=False)`, including ffmpeg-backed audio processing when `ffmpeg` and `ffprobe` are installed.

## Feature Completion Rule

A feature is not complete until `python3 scripts/dev.py test-e2e` passes.

## Individual Checks

| Task | Command |
|------|---------|
| Unit + architecture tests | `python3 scripts/dev.py test` |
| Lint | `python3 scripts/dev.py lint` |
| Type checking | `python3 scripts/dev.py typecheck` |
| Import-linter | `python3 scripts/dev.py arch` |
| Dead code | `python3 scripts/dev.py deadcode` |
| Security | `python3 scripts/dev.py security` |
| Dependency audit | `python3 scripts/dev.py deps` |
| Complexity | `python3 scripts/dev.py complexity` |
| Settings UI tests | `python3 scripts/dev.py test-svelte` |

## E2E Notes

The e2e suite uses a temporary `ANKI_BASE`, symlinks the add-on under `1000000002`, and aliases modules so config resolution continues to work under both the numeric import path and the friendly package name.

Audio rendering unit and e2e tests require `ffmpeg` and `ffprobe`. On this machine they are installed with Homebrew as `ffmpeg 8.1.1` under `/opt/homebrew/bin/`; e2e tests prefer that Homebrew binary and do not use bundled app copies such as Migaku's ffmpeg.

# Testing

## Main Commands

```bash
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e
```

## What Gets Tested

- `tests/` covers sound-reference parsing, edit-state validation, ffmpeg filter construction, prosody analysis and serialization, config migration, bootstrap behavior, editor bridge wiring, and settings command/state logic.
- `tests/test_architecture/` enforces layer boundaries, module classification, Anki-import-safe helper modules, import-safe runtime modules, editor bridge command sync, prosody dependency isolation, shell-thin settings rules, and DB access isolation.
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

Audio rendering and fallback prosody tests require `ffmpeg` and `ffprobe`. On this machine they are installed with Homebrew as `ffmpeg 8.1.1` under `/opt/homebrew/bin/`; e2e tests prefer that Homebrew binary and do not use bundled app copies such as Migaku's ffmpeg.

Prosody visualization e2e coverage verifies that the real Anki editor renders intensity fill, pitch paths, Hertz labels, and cursor seeking, and that the graph refreshes after real ffmpeg-generated media changes.

Playback interval e2e tests patch Anki's `av_player` with a fake recorder instead of relying on speakers, microphone capture, or an audio-listening model. The recorder observes `play_tags()`, `seek_relative()`, `stop_and_clear_queue()`, and `toggle_pause()`, and derives the effective original-file `start_ms`/`end_ms` interval AQE asked Anki to play. Cursor playback should use temporary `aqe_playback_*__from_<ms>ms_*.mp3` segments instead of relative seek.

This verifies AQE's playback command contract deterministically. Physical audio output is intentionally outside the normal test gate.

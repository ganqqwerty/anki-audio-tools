# Testing

## Main Commands

```bash
python3 scripts/dev.py architecture-report
python3 scripts/dev.py test-anki-api
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e
```

## What Gets Tested

- `tests/` covers sound-reference parsing, edit-state validation, ffmpeg filter construction, DeepFilter-assisted pause pipeline planning and artifacts, external denoiser/restorer command construction, prosody analysis and serialization, SVG rendering, batch visualization decisions, Browser hook wiring, config migration, bootstrap behavior, editor bridge wiring, and settings command/state logic.
- `anki_api_contract/` discovers the Anki API surface from production add-on code and checks it against the real installed Anki Python runtime without launching a full Anki app.
- `tests/test_architecture/` enforces layer boundaries, module classification, Anki-import-safe helper modules, import-safe runtime modules, editor bridge command sync, prosody dependency isolation, shell-thin settings rules, and DB access isolation.
- `tests/test_anki_api_contract_mocks.py` checks the mocked unit-test Anki surface against the same generated contract so mocks cannot hide a missing real API.
- `tests/test_architecture/contracts.py` is the executable architecture source of truth; `tests/test_architecture/inspection.py` powers both the tests and the architecture report.
- `settings_ui/tests/` covers bridge commands, async job plumbing, logging, the settings UI, and the inline editor Svelte runtime with Anki cut off behind DOM/backend test doubles.
- `scripts/generate_contracts.py --check` verifies generated Python/TypeScript JSON communication contracts are in sync with `contracts/communication.schema.json`.
- `e2e/` exercises the real add-on inside a live Anki runtime via `aqt._run(exec=False)`, including ffmpeg-backed audio processing when `ffmpeg` and `ffprobe` are installed.

## Feature Completion Rule

A feature is not complete until `python3 scripts/dev.py test-e2e` passes.

## Individual Checks

| Task | Command |
|------|---------|
| Architecture report | `python3 scripts/dev.py architecture-report` |
| Real Anki API compatibility | `python3 scripts/dev.py test-anki-api` |
| Unit + architecture tests | `python3 scripts/dev.py test` |
| Lint | `python3 scripts/dev.py lint` |
| Type checking | `python3 scripts/dev.py typecheck` |
| JSON contract staleness | `python3 scripts/dev.py contracts-check` |
| JSON contract generation | `python3 scripts/dev.py contracts-generate` |
| Import-linter | `python3 scripts/dev.py arch` |
| Dead code | `python3 scripts/dev.py deadcode` |
| Security | `python3 scripts/dev.py security` |
| Dependency audit | `python3 scripts/dev.py deps` |
| Complexity | `python3 scripts/dev.py complexity` |
| Frontend Svelte/Vitest tests | `python3 scripts/dev.py test-svelte` |
| Mutation testing (advisory) | `python3 scripts/dev.py muttest run` |

## Focused Test Files

| Area | Files |
|------|-------|
| Real Anki API compatibility | `anki_api_contract/*.py`, `tests/test_anki_api_contract_mocks.py` |
| Batch visualization core | `tests/test_batch_visualization.py` |
| Browser menu/context integration | `tests/test_browser_integration.py` |
| Pause shortening pipeline | `tests/test_audio_pipeline.py`, `tests/test_audio_processor.py` |
| Prosody SVG media rendering | `tests/test_prosody_svg.py` |
| Shared prosody analysis/cache and editor integration | `tests/test_prosody_analyzer.py`, `tests/test_prosody_fallback.py`, `tests/test_editor_integration.py` |
| JSON contract generation | `tests/test_contract_generation.py` |
| Architecture boundaries | `tests/test_architecture/*.py` |

## Mutation Testing

Mutation testing is available as an advisory, opt-in workflow for the deterministic Python core. It is not part of `python3 scripts/dev.py check` and it is not a feature-completion gate.

Current first-wave mutation scope:

- `audio_state.py`
- `config_migration.py`
- `sound_refs.py`
- `settings_state.py`
- `batch_visualization.py`
- `prosody_svg.py`
- `audio_processor.py`

The mutmut run uses the Anki bundled Python environment via `scripts/dev.py`, mutates only covered lines, disables pytest randomization, and limits test selection to the matching focused unit-test files.

Useful commands:

```bash
python3 scripts/dev.py muttest run
python3 scripts/dev.py muttest results
python3 scripts/dev.py muttest show <mutant>
python3 scripts/dev.py muttest tests-for-mutant <mutant>
python3 scripts/dev.py muttest browse
python3 scripts/dev.py muttest print-time-estimates
```

Recommended workflow:

1. Run `python3 scripts/dev.py muttest run`.
2. Inspect survivors with `python3 scripts/dev.py muttest results`.
3. Use `show` and `tests-for-mutant` to understand each survivor.
4. Tighten deterministic unit tests or consciously classify equivalent/noisy survivors.

## Architecture Rules

| Rule | Purpose |
|------|---------|
| Module-level Anki import ban | Import-safe helpers, including batch and SVG modules, must not import `aqt` or `anki` at module load time. |
| Runtime import safety | UI layers must not leak into import-safe modules. |
| Editor bridge contract | Injected editor UI commands and registered bridge commands must stay in sync. |
| Module classification | Every production module must be listed in one architecture layer. |
| Prosody boundaries | Optional Parselmouth/Praat dependencies stay isolated and do not become package-level imports. |
| Settings/backend isolation | Settings backend modules do not import UI modules; the settings shell remains thin. |
| DB access restriction | Direct collection/database access remains isolated to approved helpers. |
| Broad exception allowlist | `except Exception` handlers are limited to documented boundary functions with a reason. |

## Architecture Workflow

When changing module boundaries or side effects, use this order:

1. Refresh the local GitNexus index if policy and environment allow it.
2. Run `python3 scripts/dev.py test-e2e` to establish baseline runtime behavior.
3. Run `python3 scripts/dev.py architecture-report`.
4. Run `python3 scripts/dev.py arch`.
5. Run `python3 scripts/dev.py test-anki-api`.
6. Run `python3 scripts/dev.py test`.

If `test-e2e` fails before the architecture change, treat that as a baseline bug to classify before tightening contracts.

## Import-Linter Contracts

| Contract | Enforced Boundary |
|----------|-------------------|
| `import-safe-no-upper-layers` | Import-safe helpers cannot import Browser/editor UI modules or settings backend modules. |
| `settings-backend-no-ui` | Settings backend modules cannot import editor integration. |

## E2E Notes

The e2e suite uses a temporary `ANKI_BASE`, symlinks the add-on under `1000000002`, and aliases modules so config resolution continues to work under both the numeric import path and the friendly package name.

Audio rendering and fallback prosody tests require `ffmpeg` and `ffprobe`. On this machine they are installed with Homebrew as `ffmpeg 8.1.1` under `/opt/homebrew/bin/`; e2e tests prefer that Homebrew binary and do not use bundled app copies such as Migaku's ffmpeg.

Prosody visualization e2e coverage verifies that the real Anki editor renders intensity fill, pitch paths, Hertz labels, and cursor seeking, and that the graph refreshes after real ffmpeg-generated media changes.

The inline editor has an additional in-between integration layer in `settings_ui/tests/editor-inline.*.test.ts`: tests mount fake Anki editor fields in jsdom, replace `pycmd` with a bridge double, provide deterministic prosody/audio payloads, and drive the public `window.__aqe*` contract without loading Anki. The editor-inline coverage gate enforces at least 90% lines/statements/functions for `settings_ui/src/editor-inline/`; branch coverage is enforced separately for defensive DOM guards.

Browser batch visualization is currently covered by unit tests for hook registration, dialog entry behavior, batch progress/cancel semantics, SVG media writes, skip/failure handling, and target-field appends. Add real Browser dialog e2e coverage before making risky UI changes to that workflow.

Playback interval e2e tests patch Anki's `av_player` with a fake recorder instead of relying on speakers, microphone capture, or an audio-listening model. The recorder observes `play_tags()`, `seek_relative()`, `stop_and_clear_queue()`, and `toggle_pause()`, and derives the effective original-file `start_ms`/`end_ms` interval AQE asked Anki to play. Cursor playback should use temporary `aqe_playback_*__from_<ms>ms_*.mp3` segments instead of relative seek.

This verifies AQE's playback command contract deterministically. Physical audio output is intentionally outside the normal test gate.

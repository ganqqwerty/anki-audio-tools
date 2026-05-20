# Testing

## Main Commands

```bash
python3 scripts/dev.py architecture-report
python3 scripts/dev.py test-anki-api
python3 scripts/dev.py check
python3 scripts/dev.py coverage
python3 scripts/dev.py qodana
python3 scripts/dev.py sonar
python3 scripts/dev.py test-e2e
```

## What Gets Tested

- `tests/` covers sound-reference parsing, edit-state validation, ffmpeg filter construction, DeepFilter-assisted pause pipeline planning and artifacts, external denoiser command construction, prosody analysis and serialization, SVG rendering, batch visualization decisions, Browser hook wiring, config migration, bootstrap behavior, editor bridge wiring, and settings command/state logic.
- `anki_api_contract/` discovers the Anki API surface from production add-on code and checks it against the real installed Anki Python runtime without launching a full Anki app.
- `tests/test_architecture/` enforces layer boundaries, module classification, Anki-import-safe helper modules, import-safe runtime modules, editor bridge command sync, prosody dependency isolation, shell-thin settings rules, and DB access isolation.
- `tests/test_anki_api_contract_mocks.py` checks the mocked unit-test Anki surface against the same generated contract so mocks cannot hide a missing real API.
- `tests/test_architecture/contracts.py` is the executable architecture source of truth; `tests/test_architecture/inspection.py` powers both the tests and the architecture report.
- `settings_ui/tests/` covers bridge envelopes, async job plumbing, logging, frontend independence guardrails, the settings UI, Browser batch UI, and the inline editor Svelte runtime with Anki cut off behind DOM/backend test doubles. `python3 scripts/dev.py test-svelte` rebuilds the ignored generated frontend bundles, then runs the frontend validation chain: `svelte-check`, ESLint, `tsc --noEmit`, and Vitest coverage thresholds.
- `scripts/generate_contracts.py --check` verifies generated Python/TypeScript JSON communication contracts are in sync with `contracts/communication.schema.json`.
- `python3 scripts/dev.py coverage` runs Python unit tests with branch coverage and fails below 80%.
- `python3 scripts/dev.py qodana` runs JetBrains Qodana with `qodana.yaml` and fails on any reported problem.
- `python3 scripts/dev.py sonar` regenerates Python XML coverage and frontend LCOV from scratch, waits for the Sonar quality gate, and fails on missing reports or a failed quality gate.
- `e2e/` exercises the real add-on inside a live Anki runtime via `aqt._run(exec=False)`, including ffmpeg-backed audio processing when `ffmpeg` and `ffprobe` are installed.

## Feature Completion Rule

A feature is not complete until `python3 scripts/dev.py test-e2e` passes. The e2e command rebuilds the frontend bundles first so Anki tests never depend on stale webview output.

## Frontend Build Notes

The settings, inline editor, and Browser batch frontends are compiled into ignored generated files under `addon/anki_audio_quick_editor/templates/`. Anki e2e tests load those generated bundles, not the TypeScript or Svelte source in `settings_ui/src/`.

Use `python3 scripts/dev.py test-svelte` for frontend work and `python3 scripts/dev.py test-e2e` for Anki runtime checks. Both commands intentionally run `python3 scripts/dev.py build` first. Do not commit generated `templates/*_bundle.{js,css}` files.

Avoid running `npm run validate` or `pytest e2e` directly as the only verification after frontend changes. Direct commands are useful for focused debugging, but they bypass the repository rule that bundle freshness is part of the test command.

`python3 scripts/dev.py check` reaches frontend validation through `test-svelte`, so it can also regenerate ignored bundle files.

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
| Python file length policy | `python3 scripts/dev.py file-lines` |
| Frontend hard file length policy | `cd settings_ui && npm run lint:max-lines` |
| Import-linter | `python3 scripts/dev.py arch` |
| Dead code | `python3 scripts/dev.py deadcode` |
| Security | `python3 scripts/dev.py security` |
| Dependency audit | `python3 scripts/dev.py deps` |
| Complexity | `python3 scripts/dev.py complexity` |
| Frontend validation | `python3 scripts/dev.py test-svelte` |
| E2E tests with frontend rebuild | `python3 scripts/dev.py test-e2e` |
| Python branch coverage | `python3 scripts/dev.py coverage` |
| Qodana code quality | `python3 scripts/dev.py qodana` |
| SonarQube quality gate | `python3 scripts/dev.py sonar` |
| Mutation testing (advisory) | `python3 scripts/dev.py muttest run` |

## Quality Gates

`python3 scripts/dev.py check` is the reusable local QC gate. It runs schema validation, generates and verifies JSON contracts, architecture reporting, Ruff, mypy, Bandit, Vulture, Deptry, Radon, Qodana, import-linter, Anki API contract tests, Python unit/architecture tests, and frontend validation. Its frontend validation step rebuilds bundles through `test-svelte`.

The Radon complexity and maintainability commands fail on hand-maintained add-on code at the configured thresholds. Generated communication-contract output is excluded from the fail decision; contract freshness is enforced separately by `contracts-check`. Ruff also enforces McCabe complexity with `max-complexity = 10`.

Qodana uses `qodana-python-community` in native mode and `failThreshold: 0`, so any Qodana problem fails the standard check. The CLI is an external developer tool and must be available as `qodana` on `PATH`.

The file-length policy warns above 400 physical lines and fails above 500 physical lines for hand-maintained Python, TypeScript, and Svelte files. Generated contract output and committed webview bundle output are excluded by explicit generated-file predicates, and contract freshness remains covered by `python3 scripts/dev.py contracts-check`.

Python coverage uses branch coverage and fails below 80%. Frontend coverage thresholds are enforced by Vitest: 80% lines/functions/statements, 70% branches, and 90% lines/functions/statements for `settings_ui/src/editor-inline/`.

SonarQube is opt-in because it needs `sonar-scanner` and `SONAR_TOKEN`, but when run it is a hard gate: coverage reports must be freshly generated and the scanner waits for the server quality gate. Generated contracts are excluded from Sonar issue and coverage accounting. The inline editor bundle intentionally keeps the browser `window.__aqe*` bridge contract, so Sonar's `typescript:S7764` global-object preference is ignored only under `settings_ui/src/editor-inline/**`.

`python3 scripts/release.py --full` runs the normal release checks plus `test-e2e` and Sonar before packaging. Plain `python3 scripts/release.py` keeps the faster release path: `check`, required artifact generation, runtime asset staging, archive creation, and archive validation.

Release self-sufficiency has its own checks:

| Task | Command |
|------|---------|
| Verify cached runtime payloads | `python3 scripts/dev.py release-assets verify --target all` |
| Fast current-platform packaging without expensive QC | `python3 scripts/release.py --skip-quality-checks --target current` |
| Extracted archive smoke test | `python3 scripts/dev.py release-smoke dist/anki-audio-quick-editor-<version>-<target>.ankiaddon` |
| Native platform acceptance | `python3 scripts/release_acceptance.py --archive dist/anki-audio-quick-editor-<version>-<target>.ankiaddon --target current` |

`--skip-quality-checks` still regenerates contracts and webview bundles, stages locked runtime assets, validates the archive manifest, and enforces the native payload matrix. It only skips the expensive quality suite. A platform-targeted release is not approved until native acceptance logs exist for each platform archive in the release set.

Third-party static FFmpeg makes the universal `--target all` archive larger
than the normal size gate. Build platform-targeted archives for standard
distribution; use `--allow-large-archive "<reason>"` only for intentional direct
distribution of a universal archive.

## Focused Test Files

| Area | Files |
|------|-------|
| Real Anki API compatibility | `anki_api_contract/*.py`, `tests/test_anki_api_contract_mocks.py` |
| Batch visualization core | `tests/test_batch_visualization.py` |
| Browser menu/context integration | `tests/test_browser_integration.py` |
| Browser batch WebView shell/state | `tests/test_browser_dialog.py`, `tests/test_browser_dialog_state.py` |
| Shared WebView bridge/shell/log helpers | `tests/test_webview_bridge.py`, `tests/test_webview_shell.py`, `tests/test_frontend_logs.py` |
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
| Runtime import safety | UI layers must not leak into import-safe modules, including shared WebView bridge/shell and frontend log helpers. |
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

E2E tests run in randomized order and Anki config is persistent inside the temporary add-on profile for the duration of a test. When adding a config key, update the e2e default-config helpers so the new setting is explicitly reset to its production default unless a test opts into another value. This prevents one settings-dialog test from silently changing later editor tests.

Audio rendering and fallback prosody tests require `ffmpeg` and `ffprobe`. On this machine they are installed with Homebrew as `ffmpeg 8.1.1` under `/opt/homebrew/bin/`; e2e tests prefer that Homebrew binary and do not use bundled app copies such as Migaku's ffmpeg.

External binary features should have two kinds of tests: normal-path coverage that runs the real executable in e2e when the binary is available, and focused unit/e2e fixtures with fake executables for exceptional behavior. Use fakes for missing tools, permission errors, invalid arguments, malformed output, and nonzero exits; do not replace the normal real-binary smoke path with a fake when the feature depends on actual media processing.

Prosody visualization e2e coverage verifies that the real Anki editor renders intensity fill, pitch paths, Hertz labels, and cursor seeking, and that the graph refreshes after real ffmpeg-generated media changes.

Settings that affect editor startup behavior need at least one same-session e2e check: open the real settings dialog, save the changed value, then load a later editor note in the same Anki runtime. Unit and Svelte tests can prove state plumbing, but only the Anki e2e path catches whether saved add-on config is read again without restarting Anki.

The inline editor has an additional in-between integration layer in `settings_ui/tests/editor-inline.*.test.ts`: tests mount fake Anki editor fields in jsdom, replace `pycmd` with a bridge double, provide deterministic prosody/audio payloads, and drive the public `window.__aqe*` contract without loading Anki. The editor-inline coverage gate enforces at least 90% lines/statements/functions for `settings_ui/src/editor-inline/`; branch coverage is enforced separately for defensive DOM guards. This gate runs as part of `python3 scripts/dev.py test-svelte` because that command uses `npm run validate`.

Browser batch operations are covered by Python unit tests for hook registration, WebView shell behavior, state/contract decoding, batch progress/cancel semantics, SVG media writes, skip/failure handling, and target-field appends. The Svelte batch UI is covered in `settings_ui/tests/`. There is still no dedicated real Browser batch dialog e2e workflow, so add one before making risky executor or Browser-selection changes.

Playback interval e2e tests patch Anki's `av_player` with a fake recorder instead of relying on speakers, microphone capture, or an audio-listening model. The recorder observes `play_tags()`, `seek_relative()`, `stop_and_clear_queue()`, and `toggle_pause()`, and derives the effective original-file `start_ms`/`end_ms` interval AQE asked Anki to play. Cursor playback should use temporary `aqe_playback_*__from_<ms>ms_*.mp3` segments instead of relative seek.

This verifies AQE's playback command contract deterministically. Physical audio output is intentionally outside the normal test gate.

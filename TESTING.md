# Testing

## Main Commands

```bash
python3 scripts/dev.py architecture-report
python3 scripts/dev.py graphs-archive
python3 scripts/dev.py test-anki-api
python3 scripts/dev.py check
python3 scripts/dev.py coverage
python3 scripts/dev.py qodana
python3 scripts/dev.py sonar
python3 scripts/dev.py runtime-install
python3 scripts/dev.py test-e2e
python3 scripts/dev.py test-e2e-parallel
```

## What Gets Tested

- `tests/` covers sound-reference parsing, edit-state validation, ffmpeg filter construction, managed runtime download/extract/verify behavior, thin release/runtime-pack packaging, unified Silencedetect/Silero pause-removal planning and artifacts, external denoiser command/render/error paths for DeepFilterNet, RNNoise, and DPDFNet, prosody analysis and serialization, SVG rendering, batch visualization decisions, Browser hook wiring, config migration, generated lifecycle bridges, application-scoped recorder model/service behavior, editor bridge wiring, and settings command/state logic.
- `anki_api_contract/` discovers the Anki API surface from production add-on code and checks it against the real installed Anki Python runtime without launching a full Anki app.
- `tests/test_architecture/` enforces layer boundaries, module classification, Anki-import-safe helper modules, import-safe runtime modules, editor bridge command sync, prosody dependency isolation, shell-thin settings rules, DB access isolation, frontend transport/practice ownership, recorder handle ownership, generated lifecycle contracts, deleted playback-mirror tombstones, and invariant-validator wiring.
- `tests/test_runtime_package_imports.py` and the runtime-import architecture rule guard against hard-coded lazy imports of the friendly source package name, which would fail when Anki loads the add-on as a numeric package.
- `tests/test_anki_api_contract_mocks.py` checks the mocked unit-test Anki surface against the same generated contract so mocks cannot hide a missing real API.
- `tests/test_architecture/contracts.py` is the executable architecture source of truth; `tests/test_architecture/inspection.py` powers both the tests and the architecture report.
- `settings_ui/tests/` covers bridge envelopes, async job plumbing, logging, frontend independence guardrails, the settings UI, Browser batch UI, HTML-audio transport transition/identity/resource behavior, pure practice programs, recorder snapshot projection, and the inline editor Svelte runtime with Anki cut off behind DOM/backend test doubles. `python3 scripts/dev.py test-svelte` rebuilds the ignored generated frontend bundles, then runs the frontend validation chain: `svelte-check`, ESLint, `tsc --noEmit`, dependency-cruiser, and Vitest coverage thresholds.
- `scripts/generate_contracts.py --check` verifies generated Python/TypeScript JSON communication contracts are in sync with `contracts/communication.schema.json`.
- `python3 scripts/dev.py coverage` runs Python unit tests with branch coverage, fails below 80% aggregate coverage, and enforces conservative per-file floors for critical runtime, region-delete, and Reviewer orchestration modules.
- `python3 scripts/dev.py qodana` runs JetBrains Qodana with `qodana.yaml` and fails on any reported problem.
- `python3 scripts/dev.py sonar` regenerates Python XML coverage and frontend LCOV from scratch, waits for the Sonar quality gate, and fails on missing reports or a failed quality gate.
- `e2e/` exercises the real add-on inside a live Anki runtime via `aqt._run(exec=False)`, including ffmpeg-backed audio processing through the same runtime-aware tool discovery used in production.

## Feature Completion Rule

A feature is not complete until `python3 scripts/dev.py test-e2e` passes. Run
`python3 scripts/dev.py runtime-install` first when the managed runtime is not
ready. The e2e command preflights managed runtime assets and vendored Python
wheels, then rebuilds the frontend bundles so Anki tests never depend on stale
webview output. Missing dependency-backed tools, models, archives, or wheels
are failures, not skips.

`python3 scripts/dev.py test-e2e-parallel` is available for faster local e2e
feedback. It rebuilds the frontend once, collects e2e tests once, then runs
balanced file shards in isolated pytest subprocesses. Clipboard-using tests stay
in one shared-desktop shard. `DEV_E2E_JOBS=N` controls the worker count; invalid
values fall back to the default of up to three workers.

## Race Condition Hardening Tests

Race-sensitive workflows use targeted tests with barrier-controlled fake workers. Run these before and after changing editor async processing, Browser batch execution, prosody analysis caching, or editor bridge pending-request handling.

Use the focused checks while developing:

```bash
python3 scripts/dev.py test tests/test_editor_async_race_guards.py tests/test_browser_integration_hooks.py tests/test_prosody_cache.py
cd settings_ui && npm test -- editor-inline.bridge-queue-race.test.ts --run
python3 scripts/dev.py test-e2e e2e/test_editor_async_race_workflow.py
python3 scripts/dev.py test-e2e e2e/test_browser_batch_race_workflow.py
```

Before merging race-condition mitigation work, run:

```bash
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e
```

## Frontend Build Notes

The settings, inline editor, and Browser batch frontends are compiled into ignored generated files under `addon/anki_audio_quick_editor/templates/`. Anki e2e tests load those generated bundles, not the TypeScript or Svelte source in `settings_ui/src/`.

Use `python3 scripts/dev.py test-svelte` for frontend work and `python3 scripts/dev.py test-e2e` for canonical Anki runtime checks. Use `python3 scripts/dev.py test-e2e-parallel` for faster local e2e feedback before the serial gate. These commands intentionally run `python3 scripts/dev.py build` first. Do not commit generated `templates/*_bundle.{js,css}` files.

Avoid running `npm run validate` or `pytest e2e` directly as the only verification after frontend changes. Direct commands are useful for focused debugging, but they bypass the repository rule that bundle freshness is part of the test command.

`python3 scripts/dev.py check` reaches frontend validation through `test-svelte`, so it can also regenerate ignored bundle files.

## Individual Checks

| Task | Command |
|------|---------|
| Architecture report | `python3 scripts/dev.py architecture-report` |
| Architecture archive for docs/LLM audits | `python3 scripts/dev.py graphs-archive` |
| Architecture diagrams freshness | `python3 scripts/dev.py graphs-check` |
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
| Managed runtime install/repair | `python3 scripts/dev.py runtime-install` |
| E2E tests with frontend rebuild | `python3 scripts/dev.py test-e2e` |
| Parallel local e2e feedback | `python3 scripts/dev.py test-e2e-parallel` |
| Python branch coverage | `python3 scripts/dev.py coverage` |
| Qodana code quality | `python3 scripts/dev.py qodana` |
| SonarQube quality gate | `python3 scripts/dev.py sonar` |
| Mutation testing (advisory) | `python3 scripts/dev.py muttest run` |

## Quality Gates

`python3 scripts/dev.py check` is the reusable local QC gate. It runs schema validation, generates and verifies JSON contracts, architecture reporting, Ruff, mypy, Bandit, Vulture, Deptry, Radon, Qodana, import-linter, Anki API contract tests, Python unit/architecture tests, and frontend validation. Its frontend validation step rebuilds bundles through `test-svelte`.

The Radon complexity and maintainability commands fail on hand-maintained add-on code at the configured thresholds. Generated communication-contract output is excluded from the fail decision; contract freshness is enforced separately by `contracts-check`. Ruff also enforces McCabe complexity with `max-complexity = 10`.

Qodana uses `qodana-python-community` in native mode and `failThreshold: 0`, so any Qodana problem fails the standard check. The CLI is an external developer tool and must be available as `qodana` on `PATH`.

The file-length policy warns above 400 physical lines and fails above 500 physical lines for hand-maintained Python, TypeScript, and Svelte files. Generated contract output and committed webview bundle output are excluded by explicit generated-file predicates, and contract freshness remains covered by `python3 scripts/dev.py contracts-check`.

Python coverage uses branch coverage and fails below 80% overall, then applies
the risk-file floors declared in `scripts/dev_tasks/coverage.py`. Recorder
model and service floors are 95% and 90% respectively. Frontend coverage
thresholds are enforced by Vitest both globally and for named high-risk
modules: the HTML-audio reducer and pure practice programs require at least
95% lines/functions and 90% branches, while the transport package has a 90%
lines/functions and 85% branch ratchet. These floors protect lifecycle
semantics; aggregate coverage remains a secondary signal.

SonarQube is opt-in because it needs `sonar-scanner` and `SONAR_TOKEN`, but when run it is a hard gate: coverage reports must be freshly generated and the scanner waits for the server quality gate. Generated contracts are excluded from Sonar issue and coverage accounting. The inline editor bundle intentionally keeps the browser `window.__aqe*` bridge contract, so Sonar's `typescript:S7764` global-object preference is ignored only under `settings_ui/src/editor-inline/**`.

`python3 scripts/release.py --full` runs the normal release checks plus `test-e2e` and Sonar before packaging. Plain `python3 scripts/release.py` keeps the faster release path: `check`, required artifact generation, runtime asset staging, runtime pack creation, thin archive creation, and archive validation.

Release runtime packaging has its own checks:

| Task | Command |
|------|---------|
| Verify runtime source payloads plus cached FFmpeg | `python3 scripts/dev.py release-assets verify --target all` |
| Run current-host runtime probes after verification | `python3 scripts/dev.py release-assets verify --target current --diagnostics` |
| Fast current-platform packaging without expensive QC | `python3 scripts/release.py --skip-quality-checks --target current` |
| Public thin packaging with all runtime packs | `python3 scripts/release.py --target all` |
| Verify uploaded runtime URLs | `python3 scripts/release.py --verify-runtime-urls` |
| Local/offline embedded-runtime packaging | `python3 scripts/release.py --skip-quality-checks --target current --embed-runtime` |
| Extracted archive smoke test | `python3 scripts/dev.py release-smoke dist/anki-audio-quick-editor-<version>.ankiaddon` |
| Native platform acceptance | `python3 scripts/release_acceptance.py --archive dist/anki-audio-quick-editor-<version>.ankiaddon --target current` |

`--skip-quality-checks` still regenerates contracts and webview bundles, stages locked runtime assets, builds runtime packs in thin mode, validates the archive manifest, and enforces the native payload matrix. It only skips the expensive quality suite. A public release is not approved until runtime pack URLs are verified and native acceptance logs exist for each supported platform.

Run archive smoke tests with Anki's Python 3.13 runtime, not the macOS system Python. The add-on can use APIs that exist in Anki's supported runtime, such as `datetime.UTC`, and `python3 scripts/dev.py release-smoke ...` may fail under Apple's older Python even when the archive is valid for Anki.

Thin archives are size-gated separately from runtime packs. Runtime packs have warning thresholds, while the `.ankiaddon` hard size gate continues to apply to the AnkiWeb artifact.

## Focused Test Areas

Test files are named by subsystem. To find tests for a given area:

| Area | Test files |
|------|------------|
| Real Anki API compatibility | `anki_api_contract/*.py`, `tests/test_anki_api_contract_mocks.py` |
| Audio processing (operations, pipeline, denoise, pitch hum, rendering, recording) | [`tests/test_audio_*.py`](tests/) |
| Editor (actions, bridge, playback, recording, status, sharing, integration) | [`tests/test_editor_*.py`](tests/) |
| Playback/practice/recorder lifecycle | `settings_ui/tests/html-audio-session-*.test.ts`, `settings_ui/tests/practice-program*.test.ts`, `settings_ui/tests/editor-inline.recording.integration.test.ts`, `tests/test_recorder_model.py`, `tests/test_recorder_service.py`, `tests/test_editor_lifecycle_bridge.py` |
| Browser batch operations | [`tests/test_browser_*.py`](tests/), [`tests/test_batch_*.py`](tests/) |
| Config & migration | [`tests/test_config_*.py`](tests/) |
| Prosody (analyzer, cache, fallback, SVG, settings) | [`tests/test_prosody_*.py`](tests/) |
| Managed runtime | [`tests/test_runtime_*.py`](tests/) |
| Release packaging | [`tests/test_release_*.py`](tests/) |
| WebView bridge & shell | [`tests/test_webview_*.py`](tests/), [`tests/test_frontend_logs.py`](tests/test_frontend_logs.py) |
| Settings dialog | [`tests/test_settings_*.py`](tests/) |
| Reviewer integration | [`tests/test_reviewer_*.py`](tests/) |
| Architecture boundaries | [`tests/test_architecture/`](tests/test_architecture/) |
| Frontend (Svelte/Vitest) | [`settings_ui/tests/`](settings_ui/tests/) |
| E2E (real Anki + Qt) | [`e2e/`](e2e/) |

## Pause Shortening Invariants

Pause removal has focused unit tests because it combines detector-specific commands with shared timeline planning:

- `tests/test_audio_operation_params.py` verifies preset values, active operation-local overrides, clamping, and config immutability.
- `tests/test_audio_pipeline.py` verifies interval invariants: `min_silence_seconds` is the minimum removable duration, `min_speech_seconds` merges only too-short speech islands, generated keep segments are non-negative/non-overlapping/in bounds, empty detections leave the render plan unchanged, and full-clip pause detection keeps a minimal valid segment.
- `tests/test_audio_pause_pipeline.py` verifies both algorithms render final audio from `working_original`, optional DPDFNet preprocessing changes detector input only, Silencedetect receives threshold/min-silence and post-processes min-speech, Silero receives threshold/min-silence/min-speech and inverts speech intervals at clip boundaries, output timelines contain only cut/keep segments with no sped-up pauses, and manifests record algorithm, active params, preprocessing, detected intervals, removed intervals, timeline, and output.
- `settings_ui/tests/` verifies Settings, inline editor quick settings, and Browser Bulk keep Advanced Params collapsed by default, preserve algorithm-specific values across detector switches, apply preset clicks to active params, and include manual advanced edits in editor/Bulk command payloads.

## Mutation Testing

Mutation testing has a cheap collection smoke in `python3 scripts/dev.py check`.
Full mutation execution remains scheduled/advisory because of its cost.

Python mutation uses the dedicated `mutmut-pyproject.toml` configuration with a
fixed random seed. Focused groups cover architecture detectors, config,
region deletion, release, runtime, prosody, and recorder model/service
lifecycle. Stryker mutates the HTML-audio reducer, transport identity/
validation policy, and pure practice programs against their real Vitest
transition matrices. Scheduled jobs publish all mutmut outcome categories and
`mutation-diff.json`, which compares the current counts with the previous
successful workflow artifact when one exists.

Useful commands:

```bash
python3 scripts/dev.py muttest run
python3 scripts/dev.py muttest smoke
python3 scripts/dev.py muttest group architecture
python3 scripts/dev.py muttest group runtime
python3 scripts/dev.py muttest state-management
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
| Editor panel button settings | Configurable editor panel command buttons must be accepted by settings visibility and display-mode config. |
| Inline editor canonical state | Rule 33 and Rule 34 require field, control, recording, and visualizer runtime behavior to read typed stores instead of DOM `dataset` projections. |
| Module classification | Every production module must be listed in one architecture layer. |
| Prosody boundaries | Optional Parselmouth/Praat dependencies stay isolated and do not become package-level imports. |
| Settings/backend isolation | Settings backend modules do not import UI modules; the settings shell remains thin. |
| DB access restriction | Direct collection/database access remains isolated to approved helpers. |
| Broad exception allowlist | `except Exception` handlers are limited to documented boundary functions with a reason. |
| Rules 39-50: playback/recording ownership | Dependency direction, direct media capability ownership, sole transport writes, pure practice programs, DOM tombstones, exhaustive identities, recorder package/handle ownership, generated lifecycle contracts, deleted mirror tombstones, public APIs, and validator wiring stay enforced together. |

## Architecture Workflow

When changing module boundaries or side effects, use this order:

1. Run `python3 scripts/dev.py test-e2e` to establish baseline runtime behavior.
2. Run `python3 scripts/dev.py architecture-report`.
3. Run `python3 scripts/dev.py graphs-archive` if documentation or dependency diagrams need to be interpreted or updated.
4. Run `python3 scripts/dev.py arch`.
5. Run `python3 scripts/dev.py test-anki-api`.
6. Run `python3 scripts/dev.py test`.

If `test-e2e` fails before the architecture change, treat that as a baseline bug to classify before tightening contracts.

## Import-Linter Contracts

| Contract | Enforced Boundary |
|----------|-------------------|
| `import-safe-no-upper-layers` | Import-safe helpers cannot import Browser/editor UI modules or settings backend modules. |
| `settings-backend-no-ui` | Settings backend modules cannot import editor integration. |

## Architecture Graphs

`python3 scripts/dev.py graphs-archive` creates a date-stamped JSON snapshot under [`docs/archive/architecture_diagrams/`](docs/archive/architecture_diagrams/) for documentation and review work. Use it to understand current module, Svelte, bridge, WebView, and relationship shape before writing prose.

The archive explains what currently connects. The source of truth for what is allowed remains the executable contracts in [`tests/test_architecture/`](tests/test_architecture/) and import-linter config in [`pyproject.toml`](pyproject.toml).

## E2E Notes

The e2e suite uses a temporary `ANKI_BASE`, copies the add-on under `addons21/1000000002`, and imports add-on modules through `e2e.conftest.import_runtime_addon_module(...)`. It intentionally does not alias `1000000002.*` to `anki_audio_quick_editor.*`, so numeric-package runtime import bugs stay visible.

Reviewer e2e tests should remain user-reachable: actions are exercised through context menu commands and visible controls. Assertions that depend on private reviewer hook output are intentionally kept in focused unit tests under `tests/test_reviewer_integration_*.py` so the e2e boundary remains "observable behavior only."

E2E tests run in randomized order. Before and after every ordinary item, the
harness builds the complete baseline from production config defaults,
`migrate_config()`, and the Settings Save backend. This resets config plus its
logging/debug side effects without a hand-maintained E2E dictionary. The
`preserve_e2e_config(reason)` marker is reserved for reviewed same-session
persistence workflows and requires a reason during collection.

Audio rendering and fallback prosody tests require `ffmpeg` and `ffprobe`. Shared e2e defaults intentionally leave `ffmpeg_path` empty so those tests exercise the same lookup order as production: configured path when set, then managed runtime, package `bin/` as a source-tree fallback, then `PATH` as a compatibility fallback. Do not pin machine-specific Homebrew or Windows paths in the shared e2e defaults.

External binary features should have two kinds of tests: normal-path coverage that runs the real executable in e2e when the binary is available, and focused unit/e2e fixtures with fake executables for exceptional behavior. Use fakes for missing tools, permission errors, invalid arguments, malformed output, timeout handling, and nonzero exits; do not replace the normal real-binary smoke path with a fake when the feature depends on actual media processing.

Prosody visualization e2e coverage verifies that the real Anki editor renders intensity fill, pitch paths, Hertz labels, cursor seeking, horizontal zoom controls, and selection-aware zooming, and that the graph refreshes after real ffmpeg-generated media changes.

Settings that affect editor startup behavior need at least one same-session e2e check: open the real settings dialog, save the changed value, then load a later editor note in the same Anki runtime. Unit and Svelte tests can prove state plumbing, but only the Anki e2e path catches whether saved add-on config is read again without restarting Anki.

The inline editor has an additional in-between integration layer in `settings_ui/tests/editor-inline.*.test.ts`: tests mount fake Anki editor fields in jsdom, replace `pycmd` with a bridge double, provide deterministic prosody/audio payloads, and drive the public `window.__aqe*` contract without loading Anki. The editor-inline coverage gate enforces at least 90% lines/statements/functions for `settings_ui/src/editor-inline/`; branch coverage is enforced separately for defensive DOM guards. This gate runs as part of `python3 scripts/dev.py test-svelte` because that command uses `npm run validate`.

When adding or changing editor toolbar or selection-panel command buttons, update [`EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md`](EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md) and keep the settings visibility/display-mode architecture guard passing. It maps current editor commands to behavior expectations, e2e/unit coverage, and known buttons that intentionally diverge from standard modification-button rules.

Browser batch operations are covered by Python unit tests for hook registration,
WebView shell behavior, state/contract decoding, progress/cancel semantics, SVG
media writes, denoise routing, skip/failure handling, and target-field appends.
The Svelte UI is covered in `settings_ui/tests/`. Real Browser selection,
dialog, decoded output, race, and close cleanup paths live in
`e2e/test_browser_batch_workflow.py` and
`e2e/test_browser_batch_race_workflow.py`. Decoded semantic coverage for
convert, speed, volume, denoise, pause removal, size reduction, graph, and
preset workflows lives in `e2e/test_browser_batch_operations_workflow.py`;
multi-note partial failure, missing media, multi-field isolation, and
barrier-driven cancellation remain in `e2e/test_browser_batch_workflow.py`.

The E2E harness restores the complete production-default migrated config and
process-global state for every unmarked item. Unexpected native playback and
Python/JavaScript/Qt error channels fail closed. Use the narrow
`allow_native_playback` and `allow_error_log` markers only when the operation or
message is itself part of the asserted contract. The click helper refuses
hidden, disabled, covered, offscreen, or wrong-hit-target elements; direct DOM
activation belongs only in explicitly marked `in_anki_component` tests.

Every collected test receives exactly one primary classification: `unit`,
`component`, `in_anki_component`, or `e2e`. Runtime-backed tests additionally
carry `external_runtime`; real Qt/WebEngine input carries `trusted_input`; and
desktop-global workflows carry `shared_desktop`. Collection rejects ambiguous
or invalid combinations, empty `test_*.py` modules, unreasoned persistence
markers, and runtime skips/xfails. Shared synchronous thread behavior comes
from `tests/thread_fakes.py` so callback arguments and one-shot execution do not
vary between test modules.

`.github/workflows/quality.yml` runs deterministic PR gates and platform runtime
tests, real-Anki E2E on protected/non-PR runs, serial E2E for release tags, and
scheduled focused Python plus HTML-audio mutation jobs. E2E artifacts contain
the random seed, shard JUnit files, failing node IDs, and exact one-process
rerun commands.

Most playback interval E2E tests use a fake browser driver or patch Anki's
`av_player` to cover UI and command-state transitions quickly. Rule 36 prevents
those doubles from making claims about native browser decoding, codec support,
or real media events.

`e2e/test_editor_audible_playback_workflow.py` is the independent acoustic
layer. It drives the real HTML media element with trusted Qt clicks, captures
bounded PCM through a test-only AudioWorklet, and checks source position with
the deterministic addressable fixture and oracle under
`settings_ui/tests/audible/`. It currently covers full-prefix playback,
selected-region seeking, selected one-shot playback, and bounded selected repeat
with a real silence gap and terminal stop. These tests prove the WebView
media signal, not the final operating-system output device; device loopback
remains outside the default gate.

Real microphone permission prompts, physical input-device enumeration, device
loss, and operating-system loopback belong to an opt-in hardware recorder lane
on each supported platform. They are not permitted to skip inside PR jobs. The
required deterministic gate uses fake native adapters against the same
application-scoped recorder service for permission, start/stop, cancellation,
timeout, duplicate completion, replacement, probe, and failure behavior. A
release candidate that changes native recording must additionally record the
hardware-lane OS, device, permission state, cancellation/stop result, and
emitted file probe metadata. Unavailable hardware is release evidence to note,
not a reason to replace the deterministic merge gate with optional skips.

### When addressable audio is required

Add an addressable-audio E2E test when the acceptance criterion contains an
audible fact that state, events, or `currentTime` cannot independently prove.
It is mandatory for changes that can affect:

- the emitted source position or playback boundary;
- seeking, cursor movement, selection replacement/resize/clear, or resume while
  audio is already playing;
- repeat pass count, repeat gaps, cancellation, or terminal silence;
- source or note replacement, processing during playback, post-edit autoplay,
  or survival of an old timer/media element;
- codec/container decoding in Qt WebEngine;
- absence of an old prefix, duplicate range, overlap, dropout, unexpected
  output, or audio after stop/navigation/failure.

Use the deterministic addressable fixture for at least one representative
real-Anki path through the changed behavior. Keep faster reducer, jsdom, and
fake-driver tests for permutations and state-machine detail; addressability is
an additional boundary test, not a requirement to convert every playback test.
The expected acoustic region must come from the user gesture or test input,
never from the graph cursor, playback state, media `currentTime`, or another
observation owned by the system under test.

Addressable audio is normally unnecessary for pure reducers, DOM projection,
layout, configuration, button visibility, command payloads, and failure paths
that cannot have prior or pending playback. A failure/navigation test does need
it when proving that already-started or queued audio becomes and remains silent.

Tests making these claims must include `audible`, `acoustic`, or `emitted_pcm`
in the test name. Rule 36 uses that declaration to require
`install_audible_capture` and `analyze_audible_capture` and to reject fake audio
drivers. If a transform changes the addressable signal itself, first add an
independent transform-aware reference/model; do not weaken the oracle or infer
the verdict from application state.

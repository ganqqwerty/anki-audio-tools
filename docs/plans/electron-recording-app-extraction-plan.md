# Electron Practice App Extraction Plan

**Status:** Proposed  
**Plan date:** 2026-07-11  
**Architecture dependency revised:** 2026-07-16
**Source baseline inspected:** `anki-audio-quick-editor` `1.9.0rc2`, commit `8f25fb39c0c0a3808ee950eb21f2edeca3a02b35`  
**Developer working repository:** `/Users/iuriikatkov/IdeaProjects/shadowing-pratice`  
**Read-only source repository:** `/Users/iuriikatkov/IdeaProjects/anki-audio-tools`  
**Target:** A separate Electron repository that runs without Anki and preserves the current chorusing, shadowing-by-composition, learner recording, playback, and prosody-comparison behavior.

The inspected commit above is historical planning evidence, not an eligible
extraction baseline. `import-source` must select and record a commit containing
the implemented 2026-07-16 state-management mitigation: one frontend
transport owner, pure practice programs, the application-scoped recorder
service, and generated lifecycle/source-mutation contracts. Do not copy the
older Python playback mirror, global boundary callbacks, DOM state bags, or
editor-specific recording bundle into the standalone core.

## 1. Outcome

Create a standalone desktop practice application while leaving the Anki add-on functional and free to continue evolving.

The extraction is a copy-and-adapt operation, not a removal from the add-on. No Anki feature is deleted during this project. The developer performs all implementation, commits, builds, and tests in `/Users/iuriikatkov/IdeaProjects/shadowing-pratice`. `/Users/iuriikatkov/IdeaProjects/anki-audio-tools` is evidence and copy source only unless a separate task explicitly authorizes an add-on change.

The new repository must have no runtime or build-time dependency on an Anki installation, the add-on directory, `anki`, `aqt`, or PyQt. After source files and fixtures are imported, normal setup, build, test, and release commands must succeed even when `/Users/iuriikatkov/IdeaProjects/anki-audio-tools` is unavailable.

The standalone app will let a user:

1. Open one target audio file through a native file picker.
2. Analyze and display the same pitch/intensity prosody graph.
3. Seek, zoom, select regions, play, pause, repeat, and use repeat pauses.
4. Place and remove chorusing markers, navigate progressively longer or shorter suffixes, and auto-advance after the configured number of repetitions.
5. Start a learner recording at the current graph cursor after the configured countdown.
6. Stop and save the learner recording as a sidecar WAV without modifying the target file.
7. Analyze the learner recording and overlay its pitch contour at the recording start cursor.
8. Play/pause the learner recording, reveal it in the OS file manager, and use the existing share action.

There is no separately named shadowing implementation in the current repository. Today, shadowing is the composition of target playback, cursor/selection positioning, learner recording, and target-versus-learner comparison. The standalone app must preserve that composition without adding a new mode, workflow, or product concept.

## 2. Scope decisions

### In scope

- The current graph, HTML-audio playback, selection, zoom, chorusing, repeat, repeat-pause, and auto-advance behavior needed for practice.
- The current recording countdown and lifecycle: `idle -> countdown -> recording -> stopping -> analyzing -> ready|failed`.
- Target and learner prosody analysis, including Praat/Parselmouth when packaged and the ffmpeg/PCM fallback.
- The current graph settings and practice settings that affect these workflows.
- Sidecar recording persistence, playback, reveal, and existing share behavior.
- macOS arm64, macOS x86_64, and Windows x86_64, matching the add-on's current release matrix.
- A separate build, CI, release, diagnostics, and test system owned by the new repository.

### Out of scope

- Anki notes, fields, `[sound:...]` parsing, collection/media APIs, editor hooks, reviewer hooks, WebView injection, and `pycmd` bridge behavior.
- Browser batch operations, audio modification buttons, denoisers, pause shortening, undo/redo of note edits, settings for unrelated add-on features, and reviewer/card-template behavior.
- A media library, playlist, course model, spaced repetition, recent-files screen, accounts, cloud sync, telemetry, or a new shadowing mode.
- Linux support until it is added deliberately with native audio, sidecar, packaging, and E2E coverage.
- Sharing code at runtime with the add-on through a submodule, filesystem lookup, editable install, or unpublished package.

### Necessary standalone replacements, not new product features

Anki currently supplies a source audio path, a media directory, a WebView, configuration storage, and a process/thread host. The standalone app needs minimal replacements:

- Native **Open Audio** dialog for selecting the target.
- App-owned recordings directory under Electron's `userData` directory.
- App-owned JSON settings with schema validation and atomic writes.
- Electron main/preload boundary for file, permission, recording-finalization, sidecar, reveal, share, and diagnostics operations.
- A packaged prosody-analysis sidecar and bundled ffmpeg/ffprobe.

The initial app opens one audio file at a time and does not add project/library management.

## 3. Current implementation inventory

### Reusable behavior

| Area | Current owners | Extraction treatment |
|---|---|---|
| Transport contracts and HTML audio | `settings_ui/src/editor-inline/transport/`, `html-audio-session-machine.ts`, controller/port/resource collaborators | Import the model, exhaustive identities, validators, reducer, and port contracts first. Replace editor field ordinals with a standalone session/asset identity while preserving one transport writer and one direct media-capability adapter. |
| Practice programs | `settings_ui/src/editor-inline/practice/` | Import the pure once/repeat/chorusing/record-once reducers and transition matrices unchanged where possible. Replace only the runtime ports and scheduler adapter. |
| Chorusing UI projection | `chorusing-state.ts`, `chorusing-dom.ts`, `chorusing-toolbar.ts` | Retain projection/marker editing behavior, but let the imported chorusing program own pass/gap/suffix decisions. Rebuild Anki DOM bindings for one standalone practice surface. |
| Selection, cursor, zoom, visualizer rendering | `field-state-store.ts`, `visualizer-*`, `selection-*`, `viewport-*` | Reuse typed state and render logic; remove Anki field scanning, injected control mounting, and dataset-based discovery. |
| Learner recording frontend projection | `recording-state-store.ts`, `recording-actions-*`, `learner-recording-playback-*` | Reuse generated recorder snapshots and transport-backed learner-take playback; replace editor bridge calls with the typed preload API. |
| Recording lifecycle/state semantics | `addon/anki_audio_quick_editor/recorder/model.py`, `recorder/service.py`, `recorder/native_types.py` | Preserve attempts, takes, exact ownership, cancellation/finalization, validators, stale/duplicate rejection, and probed duration. Replace Qt/macOS native adapters and editor target lookup. |
| Lifecycle message contracts | `contracts/communication.schema.json`, generated TypeScript/Python types, `editor_lifecycle_bridge.py` | Derive versioned preload/main IPC messages from the recorder/transport/program values. Reuse schemas or generators, not WebView globals or raw dict payloads. |
| Prosody analysis | `prosody_types.py`, `prosody_settings.py`, `prosody_analyzer.py`, `prosody_praat.py`, `prosody_fallback.py`, `prosody_cache.py` | Package as an Anki-free Python sidecar behind a versioned JSON contract. Do not rewrite the analysis algorithm during extraction. |
| Configuration | `config.schema.json`, editor injection defaults, split-button state | Copy only practice-related keys into a new app schema and settings store. |
| Localization | Shared/editor locale keys used by the selected UI | Copy only reachable keys, retain all currently supported translations, and add an unused/missing-key check. |

### Anki-specific code to replace, not copy as architecture

| Current dependency | Standalone replacement |
|---|---|
| `editor_recording_requests.py` reads the active Anki field and collection media directory | Main-process session service resolves an opaque asset ID to an allowlisted target path and creates a recording output path. |
| `editor_recording.py` adapts editor/session targets to the application-scoped recorder service and frontend snapshots | Electron composition root plus main/preload IPC adapters around the imported recorder contracts. |
| `NativeRecordingController` uses `aqt._macos_helper` or PyQt6 multimedia | Chromium `getUserMedia`/`MediaRecorder` capture adapter, followed by ffmpeg normalization to PCM WAV. |
| `editor_lifecycle_bridge.py` and editor WebView callbacks deliver generated messages through Anki | Structured preload/main IPC messages validated on both sides with the same lifecycle identities. |
| `editor_ui.py` and WebView injection mount controls beside Anki fields | A normal Svelte route/component rendered once in the Electron window. |
| `resolve_requested_field_media()` and Anki media writes | Asset registry owned by the main process; the target remains read-only and recordings are written under app data. |
| `editor.mw.taskman` and Python threads | Electron main-process jobs with cancellable child processes and renderer events. |
| Anki config/meta storage | Versioned app settings JSON under `userData`, written through a temp file plus atomic rename. |

### Existing coverage that defines the baseline

The extraction baseline is behavior, not only a coverage percentage.

- Recording backend and validation:
  - `tests/test_audio_recording.py`
  - `tests/test_audio_recording_native.py`
  - `tests/test_audio_recording_qt.py`
- Recording orchestration and stale-generation behavior:
  - `tests/test_editor_recording.py`
  - `tests/test_editor_recording_state.py`
  - `tests/test_recorder_model.py`
  - `tests/test_recorder_service.py`
- Prosody algorithms and serialization:
  - `tests/test_prosody_analyzer.py`
  - `tests/test_prosody_fallback.py`
  - `tests/test_prosody_cache.py`
  - `tests/test_prosody_settings.py`
  - `tests/test_prosody_types.py`
  - `tests/test_prosody_language_contours.py`
- Frontend recording and playback:
  - `settings_ui/tests/editor-inline.recording.integration.test.ts`
  - `settings_ui/tests/editor-inline.learner-recording-playback.test.ts`
  - `settings_ui/tests/recording-state-store.test.ts`
- Portable transport and practice behavior:
  - `settings_ui/tests/html-audio-session-transition-matrix.test.ts`
  - `settings_ui/tests/transport-identity.test.ts`
  - `settings_ui/tests/transport-validation.test.ts`
  - `settings_ui/tests/practice-programs.test.ts`
  - `settings_ui/tests/practice-program-transition-matrix.test.ts`
- Frontend chorusing:
  - `settings_ui/tests/editor-inline.chorusing-state.test.ts`
  - `settings_ui/tests/editor-inline.chorusing.integration.test.ts`
- Real application behavior:
  - `e2e/test_editor_voice_recording_comparison_workflow.py`
  - `e2e/test_editor_chorusing_markers_workflow.py`
  - `e2e/test_editor_chorusing_playback_workflow.py`
  - `e2e/test_editor_chorusing_auto_advance_pause_workflow.py`
  - the region-loop, cursor-selection, visualizer, and playback E2E files used by those workflows.

Current numeric gates that must not be weakened in the new repository:

- Python: 80% minimum with branch coverage enabled.
- Frontend overall: 80% lines/statements/functions and 75% branches.
- Current `editor-inline` scope: 90% lines/statements/functions and 75% branches.

## 4. Target repository architecture

Use one independent repository with explicit process boundaries:

```text
practice-desktop/
  apps/desktop/
    main/                 Electron main process
    preload/              contextBridge API only
    renderer/             Svelte application shell and practice screen
  packages/
    practice-core/        Pure TS state machines and decisions
    practice-ui/          Reusable visualizer/practice Svelte components
    contracts/            Schemas plus generated TS/Python contract types
  sidecar/
    prosody/              Anki-free Python analysis package and CLI
  tests/
    fixtures/             Audio and golden payload/state-trace fixtures
    integration/
    e2e/
  scripts/
    build-sidecar/
    package/
    verify-artifact/
```

Exact repository and product names can be chosen when the repository is created; paths above describe ownership, not branding.

### Renderer

- Svelte 5, TypeScript, Vite, and the existing UI dependencies are the lowest-risk starting point.
- `practice-core` owns canonical state. The DOM remains a projection, preserving the existing Rule 33/34 design principle.
- Reuse the current pure playback machines and HTML audio session ownership. Do not reintroduce native/renderer dual playback.
- Replace field ordinal maps with a `PracticeSessionId` and one active target asset.
- Replace globals such as `window.__aqe*`, `window.__aqeActiveField`, and `pycmd` with an injected `window.practiceDesktop` API defined by the preload.

### Preload and IPC

Expose a narrow, typed API through `contextBridge`. The renderer must never receive arbitrary filesystem access or Node primitives.

Initial commands/events:

```text
openTargetAudio() -> TargetAsset
analyzeTarget(assetId, settings, generation) -> jobId
beginRecording(sessionId, mimeType) -> recordingId
appendRecordingChunk(recordingId, sequence, bytes)
finishRecording(recordingId, generation) -> RecordingAsset
cancelRecording(recordingId)
analyzeLearner(assetId, settings, generation) -> jobId
revealAsset(assetId)
shareAsset(assetId, target) -> url
loadSettings() / saveSettings(patch)
cancelJob(jobId)

events: analysisCompleted, analysisFailed, recordingFailed, diagnostics
```

Every request and response is schema-validated. Asset IDs and job IDs are opaque. Only the main process maps IDs to canonical paths.

Electron security defaults are release gates:

- `contextIsolation: true`
- `nodeIntegration: false`
- renderer sandbox enabled
- strict Content Security Policy
- no remote module
- no generic `runCommand`, `readFile`, `writeFile`, `openPath`, or arbitrary URL IPC
- navigation and new-window requests denied unless explicitly allowlisted

### Local audio delivery

Register an app-owned protocol such as `practice-audio://asset/<opaque-id>`. The handler resolves only main-process registered assets and supports byte ranges so seeking works. Do not expose absolute local paths to the renderer or accept paths from renderer URLs.

### Recording

Keep the current frontend lifecycle and generation checks, but replace the capture backend:

1. Request microphone permission from Electron/Chromium.
2. Create a `MediaStream` with audio only.
3. Select a supported `MediaRecorder` MIME type at runtime.
4. Stream ordered chunks through a dedicated recording session to a main-process temporary file.
5. On stop, close all tracks and finalize the chunk stream.
6. Normalize the capture with bundled ffmpeg into 16-bit PCM WAV.
7. Validate that the WAV exists, is non-empty, and has readable duration.
8. Atomically promote it into the app recordings directory.
9. Publish a result carrying the same generation used to start the attempt.

The source audio is never modified. Partial and failed captures use `.part` files and are cleaned on the next startup after diagnostics are retained.

Preserve these current behaviors:

- Countdown occurs before permission/capture dispatch in the same visible state flow.
- Starting recording stops target playback and clears the previous learner overlay.
- Recording begins at the clamped current target cursor.
- A recording longer than the target expands the visible timeline.
- Late completion or analysis for an old generation is ignored.
- Stop/failure always closes microphone tracks and clears blocking state.

### Prosody sidecar

Do not port the Python prosody algorithm to TypeScript during extraction. Package a small, app-owned, one-shot Python executable per target platform.

The sidecar contract contains only:

- canonical input path supplied by the main process
- validated prosody settings
- request/generation ID
- structured success payload matching the current `ProsodyPayload`
- structured error code/message/diagnostic context

Recommended execution model:

- Spawn one sidecar process per analysis job.
- Read one validated request and emit one JSON response.
- Send logs to stderr; reserve stdout for the response.
- Kill the child process on cancellation or app shutdown.
- Apply a bounded timeout and include exit status/stderr in local diagnostics.

Refactor or copy these modules behind a new `ProsodyAnalysisConfig` rather than importing the add-on-wide `AudioProcessingConfig`. Keep Parselmouth imports lazy and isolated. Preserve ffmpeg fallback behavior and cache keys, but place the cache under the app's `userData` directory.

Package the sidecar as a per-platform `onedir` distribution rather than a self-extracting single file unless an implementation spike proves the single-file form reliable with NumPy and Parselmouth. Bundle only the practice runtime: sidecar, ffmpeg, and ffprobe. Do not carry the add-on's denoisers, VAD, source-separation models, or unrelated runtime payloads.

### Main-process state

Use typed services with one responsibility each:

- `AssetRegistry`: opaque IDs, canonical paths, read-only target versus owned recording distinction.
- `AnalysisJobService`: sidecar lifecycle, cancellation, stale generation, cache, structured failures.
- `RecordingFileService`: chunk order, temp files, ffmpeg normalization, atomic promotion, cleanup.
- `SettingsService`: schema versioning, defaults, validation, atomic persistence.
- `ShareService`: current provider behavior only.
- `DiagnosticsService`: redacted logs, breadcrumbs, child-process failures, permission status.

The practice lifecycle remains a pure state machine in `practice-core`; services perform effects and report facts back to it.

## 5. Developer working model

The implementation agent starts in the target repository and reads the source repository by absolute path:

```bash
export SHADOWING_REPO=/Users/iuriikatkov/IdeaProjects/shadowing-pratice
export AQE_SOURCE_REPO=/Users/iuriikatkov/IdeaProjects/anki-audio-tools
cd "$SHADOWING_REPO"
```

Rules for the implementation context:

1. Initialize Git, install dependencies, create branches, edit files, and commit only under `$SHADOWING_REPO`.
2. Treat `$AQE_SOURCE_REPO` as read-only. Reading files, querying CodeGraph, running its tests, and copying allowlisted content are permitted; editing it is not part of this plan.
3. Record the source commit before copying anything:

   ```bash
   git -C "$AQE_SOURCE_REPO" rev-parse HEAD
   git -C "$AQE_SOURCE_REPO" status --short
   ```

4. Refuse an automated import when the requested source commit does not match the checked-out commit. A dirty source tree may be inspected, but imported files must come from committed content using `git show <commit>:<path>` so uncommitted source changes cannot leak into the new repository.
5. Never hardcode either developer path in production code, packaged assets, source maps, generated contracts, tests, or release manifests. Development commands accept `--source-repo` or `AQE_SOURCE_REPO`; normal app commands do not require it.
6. Copy this plan into `$SHADOWING_REPO/docs/plans/electron-recording-app-extraction-plan.md` as the first documentation commit. Once copied, the target-repository version becomes the implementation source of truth; this source-repository copy remains a planning record.
7. Build an explicit allowlist manifest rather than copying directories wholesale. Each entry records source path, source commit, destination path, SHA-256, license/provenance treatment, and whether the file is copied, adapted, used only as a fixture, or used only as behavioral reference.
8. Any missing source characterization is recorded in `$SHADOWING_REPO/docs/source-gaps.md`. It may create a separate future add-on task, but the standalone extraction must not silently mutate the source repository.

The following source documents are required reading before their corresponding work:

| Target work | Read from `/Users/iuriikatkov/IdeaProjects/anki-audio-tools` |
|---|---|
| Architecture and boundaries | `AGENTS.md`, `ARCHITECTURE.md` |
| Frontend extraction | `WEBVIEW_AND_TEMPLATES.md`, `EDITOR_MODIFICATION_BUTTON_BEHAVIOR_RULES.md` |
| Recording behavior | `docs/superpowers/specs/2026-05-23-voice-recording-comparison-new-main-design.md`, `docs/superpowers/plans/2026-06-04-record-own-voice-enhancements.md`, `docs/superpowers/specs/2026-06-04-recording-countdown-overlay-design.md` |
| Chorusing behavior | `docs/superpowers/specs/2026-06-13-chorusing-autoadvance-design.md`, `docs/superpowers/plans/2026-06-13-chorusing-autoadvance.md` |
| Playback state machines | `docs/reviews/2026-06-18-playback-state-machine-design.md`, `docs/architecture/html-audio-observability.md` |
| Tests and E2E | `TESTING.md`, `E2E_TESTING.md` |
| Native/runtime packaging | `DEVELOPMENT.md`, `addon/anki_audio_quick_editor/bin/THIRD_PARTY_NOTICES.md` |
| Diagnostics | `DEBUGGING.md`, `docs/archive/ERROR_HANDLING_AND_DIAGNOSTICS.md` |

Do not copy those Markdown files wholesale. Extract relevant decisions, replace Anki terminology and paths, remove obsolete instructions, and link the resulting target documentation to its source commit in `EXTRACTION_PROVENANCE.md`.

## 6. Electron development runner and local infrastructure

The new repository needs an Electron-specific equivalent of the source repository's `scripts/dev.py`. Keep the same developer ergonomics: one discoverable entry point, concise success output, failure-focused diagnostics, `--verbose`, `--idle-timeout`, commands that work from any current directory, and nonzero exit codes on every failed gate.

Use `python3 scripts/dev.py` as the canonical orchestration interface in the target repository. Python is already required to build and test the prosody sidecar, and retaining the command shape reduces migration friction. The application itself must not depend on this development runner at runtime.

Suggested runner layout:

```text
scripts/
  dev.py
  dev_cli.py
  dev_commands/
    setup.py
    source.py
    quality.py
    tests.py
    sidecar.py
    electron.py
    release.py
    docs.py
    graphs.py
  dev_tasks/
    process.py
    node_tools.py
    python_tools.py
    paths.py
```

Do not build a second orchestration layer in shell scripts. Package-manager scripts remain small primitives called by `scripts/dev.py`; CI calls the same dev-runner commands developers use locally.

### Required commands

| Command | Responsibility |
|---|---|
| `setup` | Verify pinned Node/Python versions, run `npm ci`, create the sidecar virtual environment, install locked Python dev dependencies, install Playwright Electron test dependencies, initialize the repository CodeGraph index when available, and verify required local build tools. Must be idempotent. |
| `info` | Print repository root, Node/npm/Electron/Python versions, platform/arch, sidecar/runtime status, relevant cache paths, and source baseline status when `AQE_SOURCE_REPO` is set. Never print secrets. |
| `source-baseline` | Read the source Git commit/version/config/test inventory, optionally run source `check`/E2E, and write `tests/parity/source-baseline.json`. This is extraction-only and must not run during normal builds. |
| `import-source` | Copy only manifest-allowlisted committed source files/tests/fixtures, verify hashes, update `EXTRACTION_PROVENANCE.md`, and fail on unknown or changed inputs. Support `--dry-run`. |
| `dev` | Build/watch main, preload, renderer, and contracts; launch Electron with an isolated development `userData` directory; restart safely when main/preload code changes. |
| `build` | Produce deterministic main/preload/renderer output and build the current-platform prosody sidecar. |
| `lint` | Run ESLint for TS/Svelte, Ruff for sidecar/dev Python, and formatting checks without hiding changes. Separate `format` may perform mechanical writes. |
| `typecheck` | Run `tsc --noEmit`, `svelte-check`, and Python static typing for the sidecar/dev runner. |
| `arch` | Enforce Electron process boundaries, IPC ownership, portable-core import rules, renderer Node isolation, and sidecar Anki/PyQt isolation. |
| `security` | Audit Electron `BrowserWindow` defaults/CSP/IPC allowlists, scan Python, run dependency audits, and reject generic shell/filesystem IPC. |
| `deps` | Verify lockfile consistency, unused/missing dependencies, forbidden runtime dependencies, and license policy. |
| `i18n` | Require locale key parity, placeholder parity, and no unreachable copied keys. |
| `file-lines` | Apply the target repository's maintainability thresholds to hand-maintained TS, Svelte, and Python files. |
| `config-schema` | Validate defaults, examples, migrations, and persisted settings against the app schema. |
| `contracts-generate` | Generate TS and Python types/validators for IPC and sidecar contracts. |
| `contracts-check` | Regenerate in a temp directory or inspect Git diff and fail when committed generated files are stale. |
| `test` | Run fast TS/Svelte/Python unit and integration suites, including architecture tests; accept scoped test arguments. |
| `test-renderer` | Run renderer unit/integration tests with jsdom and fake preload API. |
| `test-main` | Run main/preload/service integration tests with temporary filesystem roots and fake child processes. |
| `test-sidecar` | Run sidecar unit/integration tests, including real fixture analysis where dependencies are available. |
| `coverage` | Run and merge renderer/main/preload TS coverage plus Python sidecar coverage, enforce per-scope thresholds, and emit LCOV/Cobertura reports. |
| `test-e2e` | Build the app, launch Electron through Playwright, run deterministic media-device journeys in an isolated `userData`, and retain traces/screenshots/logs only on failure by default. |
| `test-e2e-parallel` | Shard E2E by isolated worker directories with separate `userData`, recordings, caches, temp files, ports, and logs. Never share an Electron profile between workers. |
| `sidecar-build` | Build the current target's locked `onedir` sidecar and verify imports/native libraries. |
| `runtime-verify` | Verify ffmpeg/ffprobe/sidecar hashes, executable permissions, versions, licenses, and target manifest. |
| `package` | Produce the current target's unpacked app and installer from locked inputs. |
| `release-smoke` | Install or unpack the actual artifact into a clean temp root and exercise launch, file open, analysis, playback, and fake recording. |
| `docs-check` | Check required docs, internal links, referenced files/commands, generated diagrams, source provenance, and documentation freshness markers. |
| `graphs-ts` | Generate the renderer/main/preload/package dependency graph. |
| `graphs-ipc` | Generate a command/event diagram from the contract registry. |
| `graphs-processes` | Generate the renderer/preload/main/sidecar/runtime data-flow diagram. |
| `graphs-all` | Generate all human-readable and machine-readable architecture outputs. |
| `graphs-check` | Regenerate graphs and fail if committed outputs differ. |
| `check` | Reusable QC gate: schema, contracts, docs, graphs, lint, typecheck, architecture, security, dependencies, i18n, file limits, unit/integration tests, and coverage. It does not substitute for full Electron E2E. |
| `verify` | Release-completeness gate: `check`, sidecar/runtime verification, package, Electron E2E, and release smoke for the current platform. |

### Runner behavior requirements

- Resolve the repository root from `scripts/dev.py`, never from the caller's current working directory.
- Use argument arrays instead of shell command strings. Avoid platform-specific quoting and shell features.
- Stream full output with `--verbose`; otherwise print one line per task and show complete captured output for failures.
- Support an idle-output timeout rather than a fixed whole-command timeout. E2E and packaging commands must emit periodic progress.
- Forward `SIGINT`/termination to Electron, Vite, Playwright, ffmpeg, and sidecar child processes, then wait and force-kill only after a bounded grace period.
- Track processes created by the current command only; never kill arbitrary Electron or Python processes.
- Keep setup/build outputs under repository-local ignored directories and runtime app data under test-specific temp roots.
- Make destructive cleanup explicit and scoped. No command may delete user recordings or the normal Electron `userData` directory.
- Pin Node, npm, Electron, Python, Playwright, Python wheels, ffmpeg/ffprobe, and packaging tools. `setup` and `info` report deviations.
- Add unit tests for CLI parsing, command registration, failure propagation, timeout behavior, path handling, and process cleanup.

### Development configuration

Commit and document:

- a Node version file and `package-lock.json`
- a Python version file plus an exact sidecar/dev lock
- Electron-builder/packager configuration checked into source control
- Playwright configuration with deterministic artifact locations
- Vitest configurations that separate renderer DOM, Node main/preload, and pure-package environments
- pytest configuration for the sidecar
- coverage merge configuration and exclusions
- runtime asset lock/manifest with URL, size, SHA-256, executable bit, and license metadata
- `.env.example` containing names and safe examples only; no credentials or developer-absolute paths
- `.gitignore` entries for dev profiles, recordings, caches, traces, sidecars, installers, logs, coverage, and signing material

## 7. Documentation set and maintenance

The new context cannot rely on knowledge stored only in the add-on repository. Documentation is part of the extraction deliverable and is validated by `python3 scripts/dev.py docs-check`.

### Required target-repository Markdown files

| File | Required content |
|---|---|
| `AGENTS.md` | Canonical repository rules, working-directory assumptions, CodeGraph search/refactoring policy, architecture/test commands, source-repository read-only rule, and completion gates. |
| `CLAUDE.md` | A pointer to `AGENTS.md`, not a duplicated rules document. |
| `README.md` | Product scope, supported platforms, install/run basics, screenshots only after the UI exists, and links to developer docs. |
| `ARCHITECTURE.md` | Renderer/preload/main/sidecar boundaries, canonical state ownership, asset IDs, recording flow, analysis flow, failure/cancellation, and diagrams. |
| `DEVELOPMENT.md` | Exact setup, pinned runtimes, `scripts/dev.py` command catalog, environment variables, source import workflow, and platform prerequisites. |
| `TESTING.md` | Test pyramid, coverage gates, fixture policy, fake versus real media rules, parity artifacts, common scoped commands, and CI mapping. |
| `E2E_TESTING.md` | Playwright Electron harness, fake mic setup, worker isolation, debugging traces, packaged-app tests, and native acceptance limits. |
| `DEBUGGING.md` | Log locations, verbose runner use, Electron DevTools, main/preload debugging, sidecar/ffmpeg diagnostics, permission failures, and incident bundle contents. |
| `SECURITY.md` | Threat model, Electron hardening, IPC/path/URL rules, dependency reporting, supported versions, and vulnerability contact/process. |
| `RELEASE.md` | Versioning, runtime/sidecar builds, artifact matrix, signing/notarization, smoke tests, checksums, third-party notices, and rollback. |
| `CONFIG_SCHEMA.md` | Every persisted setting, default, bounds, migration, and renderer/main ownership. |
| `IPC_CONTRACTS.md` | Command/event catalog, payload schemas, trust boundary, validation, cancellation/generation semantics, and error envelope. |
| `RECORDING_AND_AUDIO.md` | Capture MIME negotiation, chunk protocol, WAV normalization, source immutability, output paths, cleanup, playback protocol, and permissions. |
| `EXTRACTION_PROVENANCE.md` | Source repository/commit, import manifest, copied/adapted modules, test provenance, licenses, and known deviations. |
| `UPSTREAM_SYNC.md` | Later add-on commits reviewed, behavior changes, port decision, app commit, and parity result. |
| `THIRD_PARTY_NOTICES.md` | Electron/Chromium, ffmpeg, Python, NumPy, Parselmouth/Praat, UI libraries, and all bundled binary licenses. |
| `CHANGELOG.md` | User-visible standalone releases; do not copy the add-on changelog. |
| `docs/source-gaps.md` | Missing source coverage, ambiguous behavior, deferred source-repository tasks, and resolution status. |
| `docs/architecture/html-audio-observability.md` | Adapted canonical logging/invariant contract for app HTML audio. |
| `docs/plans/electron-recording-app-extraction-plan.md` | This execution plan, updated as phases complete or assumptions change. |

### Generated architecture documentation

Commit generated diagrams and a machine-readable architecture archive for:

- TypeScript/Svelte module dependencies
- renderer -> preload -> main IPC commands and events
- main -> prosody sidecar requests/responses/cancellation
- target/recording asset lifecycle and trust boundaries
- recording and analysis state transitions
- test-layer ownership of parity-matrix behaviors

`graphs-check` prevents stale generated diagrams. Generated files carry a header naming their generator and must not be hand-edited.

### Documentation maintenance rules

- Update docs in the same PR as changes to IPC, settings schema, process boundaries, recording formats, asset locations, runtime packaging, coverage policy, supported platforms, or release commands.
- Add a documentation-impact checklist to the PR template.
- `docs-check` verifies internal links and file references, checks that documented `scripts/dev.py` commands exist, validates code snippets marked as executable, and rejects references to obsolete Anki-only commands outside provenance/source-comparison sections.
- Do not copy historical add-on plans into the new repository unless they are required evidence. Prefer a short provenance link and current standalone decision.
- Keep one canonical location per topic; other docs link to it instead of duplicating operational checklists.
- Record intentional deviations from the source behavior in the parity matrix, `EXTRACTION_PROVENANCE.md`, and the changelog entry for the affected release.

## 8. Cross-repository ownership and drift policy

Independence is more important than automatic source sharing.

1. Record the exact source commit, version, copied paths, and license notices in `EXTRACTION_PROVENANCE.md` in the new repository.
2. Copy code and tests into the new repository in reviewable groups. Do not use a git submodule or a runtime link to this repository.
3. Version imported behavior fixtures and standalone contract schemas in the new repository. Do not require matching uncommitted files to be added to the source repository.
4. After parity release, each repository owns its implementation. A fix intended for both products is ported explicitly with a commit reference in both directions.
5. Add a lightweight `UPSTREAM_SYNC.md` log in the app repository with source/add-on commit, affected behavior, port status, and parity-test result.
6. Do not block either product's release on the other repository. Shared behavior changes require an explicit compatibility decision, not implicit synchronized releases.

This policy allows the add-on to keep developing during extraction without forcing the new app to embed Anki assumptions or wait for add-on releases.

## 9. Implementation phases

Each phase ends with executable verification and can be reviewed independently.

### Phase 0 — Freeze the behavioral baseline

Goal: make “same functionality and coverage” measurable before moving code.

Tasks:

1. From `/Users/iuriikatkov/IdeaProjects/shadowing-pratice`, run `python3 scripts/dev.py source-baseline --source-repo /Users/iuriikatkov/IdeaProjects/anki-audio-tools --source-commit 8f25fb39c0c0a3808ee950eb21f2edeca3a02b35` after that command exists. Until then, record the same facts manually in `tests/parity/source-baseline.json`.
2. Run and archive source results without changing the source checkout:

   ```bash
   cd /Users/iuriikatkov/IdeaProjects/anki-audio-tools
   python3 scripts/dev.py check
   python3 scripts/dev.py test-e2e-parallel
   cd /Users/iuriikatkov/IdeaProjects/shadowing-pratice
   ```

3. In the target repository, create a parity matrix listing every visible control, state transition, setting, error, and side effect in scope.
4. Generate deterministic target and learner WAV fixtures covering:
   - shorter learner than target
   - longer learner than target
   - recording from cursor zero and a non-zero cursor
   - voiced/unvoiced regions and intensity changes
5. Save golden normalized `ProsodyPayload` files and state-transition traces for chorusing and recording in the target repository, with their source commit and generator recorded.
6. If a parity-matrix row has no source test, record it in `docs/source-gaps.md` and add a target-repository characterization test based on observed source behavior. Do not edit the add-on as part of this execution plan.

Exit gate:

- Baseline QC and E2E are green.
- Every in-scope behavior maps to a source test or an explicit source gap plus a target characterization test.
- Golden fixtures are stable across two consecutive runs on the same platform.

### Phase 1 — Bootstrap the independent repository and its infrastructure

Goal: make `/Users/iuriikatkov/IdeaProjects/shadowing-pratice` independently buildable and testable before application logic is copied.

Tasks:

1. Initialize the target Git repository and copy this plan into `docs/plans/`.
2. Add `AGENTS.md`, `CLAUDE.md`, `README.md`, `DEVELOPMENT.md`, `TESTING.md`, and `EXTRACTION_PROVENANCE.md` before the first production-code PR.
3. Implement the modular `scripts/dev.py` runner, starting with `setup`, `info`, `docs-check`, `test`, `lint`, `typecheck`, `check`, and tested command/process infrastructure.
4. Pin Node, npm, Electron, Python, Vite/Svelte, Vitest, Playwright, packaging, and sidecar dependency versions.
5. Configure TypeScript strict mode, separate main/preload/renderer builds, Python sidecar packaging, lockfiles, linting, formatting, and coverage reporting.
6. Add Vitest, pytest, and Playwright Electron harnesses with isolated temp/user-data roots.
7. Add secure `BrowserWindow` defaults and architecture tests before renderer functionality.
8. Implement typed contract generation/validation and its `scripts/dev.py` commands.
9. Add macOS and Windows CI jobs that call the same runner commands used locally.

Exit gate:

- `python3 scripts/dev.py setup`, `info`, `docs-check`, `test`, and `check` pass from the target repository.
- A packaged empty shell launches on current-platform development and CI runners.
- Renderer code cannot access Node APIs and an IPC contract round-trip test passes.
- No target setup/build/test command requires the source repository or an Anki installation.

### Phase 2 — Import and isolate portable behavior in the target repository

Goal: import from the recorded source commit, then establish clean standalone seams without changing the source repository.

Tasks:

1. Implement `import-source` with a reviewed allowlist manifest and import the selected TypeScript, Python, locale, fixture, and test files from committed source content.
2. Record every imported/adapted path and hash in `EXTRACTION_PROVENANCE.md`.
3. Import the source transport model/identities/validators, pure practice programs, recorder model contracts, and normalized visualizer types into `packages/practice-core`; implement Electron-specific transport, scheduler, and recorder ports around them instead of re-deriving lifecycle rules.
4. Separate DOM rendering from Anki field discovery and bridge dispatch; delete copied Anki adapters once their behavior has a standalone owner.
5. Introduce an Anki-free `ProsodyAnalysisConfig` in the sidecar and make the entry point accept a path plus focused config.
6. Preserve lazy Parselmouth imports and ffmpeg fallback.
7. Port source tests first, then adapt implementation until they pass. Keep commit history/provenance references in test modules where their origin would otherwise be unclear.
8. Add architecture tests that portable and sidecar modules cannot import `anki`, `aqt`, PyQt, editor session/integration modules, or WebView helpers.
9. Configure the coverage gates from Section 10 on the first commit containing imported production code.

Exit gate:

- `python3 scripts/dev.py import-source --dry-run` reports no unexplained drift.
- Imported pure TypeScript and Python tests pass in the target repository.
- Portable modules and the sidecar load without Anki or Qt.
- `python3 scripts/dev.py check` passes at or above the required coverage thresholds.
- Removing or renaming `/Users/iuriikatkov/IdeaProjects/anki-audio-tools` does not affect target setup, build, tests, or packaged output after import.

### Phase 3 — Migrate pure practice logic and visualizer

Goal: run target-audio graph/playback/chorusing in Electron without recording yet.

Tasks:

1. Integrate the imported transport contracts, pure practice programs, and their transition/identity/validator tests into the standalone renderer and practice UI.
2. Build a single-session Svelte practice surface from the reusable visualizer components.
3. Replace field ordinals, field scanning, and injected globals with session/asset state.
4. Implement the asset registry, Open Audio dialog, and `practice-audio://` protocol with byte-range support.
5. Package the Python sidecar plus ffmpeg/ffprobe and implement target analysis.
6. Port graph settings, cursor/selection, zoom, playback, repeat, pause, markers, navigation, and auto-advance.
7. Keep the target path read-only and verify no write handle is opened for it.

Exit gate:

- Golden target prosody payload matches the baseline within documented numeric tolerance.
- Existing pure chorusing and playback tests pass in the new repository.
- Electron E2E opens real audio, renders the graph, seeks, selects, repeats, edits markers, navigates suffixes, and auto-advances.
- Source file hash and modification time remain unchanged.

### Phase 4 — Replace recording and comparison adapters

Goal: reproduce the complete learner recording workflow.

Tasks:

1. Implement microphone permission and device-error handling.
2. Implement chunked MediaRecorder capture and the main-process recording file service.
3. Normalize capture to WAV and validate duration/file integrity.
4. Port `RecordOnce` countdown/stop-before-capture ordering and the recorder attempt/take reducer semantics, then add live cursor, timeline expansion, normalization, analysis, failure, cancellation, and stale/duplicate completion behavior through Electron adapters.
5. Analyze the learner WAV with the same sidecar and render the offset learner overlay.
6. Port learner HTML-audio play/pause.
7. Add reveal and existing share actions through narrow main-process services.
8. Clean partial recordings on failure/startup and redact absolute paths from renderer-facing errors.

Exit gate:

- The Electron equivalent of `test_editor_voice_recording_comparison_workflow.py` passes.
- Fake-device E2E covers deterministic successful capture.
- Permission denied, missing device, stop failure, empty output, ffmpeg failure, analysis failure, and stale completion are covered.
- Closing the window during countdown, capture, normalization, and analysis leaves no live mic track or child process.

### Phase 5 — Parity, resilience, and native acceptance

Goal: prove that the standalone result matches the selected add-on behavior and is operationally independent.

Tasks:

1. Run the complete parity matrix against both products at their recorded commits.
2. Compare golden prosody payloads and pure state traces automatically.
3. Add startup recovery tests for `.part` files, invalid settings, sidecar crash, and corrupt cache.
4. Test Unicode, spaces, and long paths without exposing renderer filesystem access.
5. Test rapid open/switch/close sequences and stale async completions.
6. Run real-device manual acceptance on each supported OS/architecture:
   - first permission prompt
   - denied then re-enabled permission
   - record/stop/play through actual hardware
   - reveal and share
7. Re-run the recorded source baseline only when the selected source commit changes. Do not compare a moving source checkout implicitly.

Exit gate:

- All automated suites and coverage gates pass.
- Native acceptance evidence exists for macOS arm64, macOS x86_64, and Windows x86_64.
- The app launches, analyzes, records, and compares on a clean machine with no Anki installation.
- No open parity-matrix differences remain unless explicitly accepted and documented as platform constraints.

### Phase 6 — Package and release independently

Goal: create verifiable standalone artifacts with no add-on release coupling.

Tasks:

1. Produce separate macOS arm64, macOS x86_64, and Windows x86_64 installers.
2. Bundle only Electron, the practice app, ffmpeg/ffprobe, and the prosody sidecar runtime.
3. Include third-party licenses for Electron/Chromium, ffmpeg, Python, NumPy, Parselmouth/Praat, and copied frontend dependencies.
4. Implement artifact inspection behind `python3 scripts/dev.py runtime-verify` and reject Anki/PyQt imports, missing sidecar files, unexpected binaries, and unsigned manifest changes.
5. Smoke-test the installed artifact through `python3 scripts/dev.py release-smoke`, not only the development build.
6. Configure macOS signing/notarization and Windows signing when release credentials are available.
7. Publish checksums and a machine-readable artifact manifest.

Exit gate:

- Installed artifacts pass the smoke and minimal practice workflow on each target.
- Artifact verification proves that no file is loaded from the add-on repository or an Anki installation.
- The app has its own version, changelog, issue tracker, and release process.

## 10. Test and coverage plan

Coverage percentages are necessary but insufficient. Maintain both numeric gates and behavior ownership.

### Numeric gates

| Scope | Lines | Statements | Functions | Branches |
|---|---:|---:|---:|---:|
| Repository-wide TS/Svelte | 80% | 80% | 80% | 75% |
| `packages/practice-core` | 90% | 90% | 90% | 75% |
| Practice renderer feature modules | 90% | 90% | 90% | 75% |
| Main/preload security and lifecycle services | 90% | 90% | 90% | 80% |
| Python prosody sidecar | 80% | 80% | 80% | branch coverage enabled, 80% aggregate |

Do not exclude new production adapter files merely to satisfy a gate. Generated contract files, entry-point glue with no logic, and test fixtures may be excluded explicitly.

### Test repository layout

Create the test layout before feature migration so imported tests have intentional destinations:

```text
apps/desktop/main/**/*.test.ts
apps/desktop/preload/**/*.test.ts
apps/desktop/renderer/**/*.test.ts
packages/practice-core/**/*.test.ts
packages/practice-ui/**/*.test.ts
sidecar/tests/unit/
sidecar/tests/integration/
tests/architecture/
tests/contracts/
tests/integration/
tests/e2e/specs/
tests/e2e/fixtures/
tests/e2e/support/
tests/parity/
tests/fixtures/audio/
tests/fixtures/prosody/
tests/fixtures/state-traces/
```

Test support must be reusable but not become an alternate implementation of production behavior. Keep pure fixture builders separate from assertions and avoid broad mocks that bypass IPC, asset authorization, state transitions, or actual media processing.

### Hermetic test setup

- Every test creates its own temporary `userData`, recordings, cache, log, and temp roots. Tests never read the developer's real Electron profile.
- Freeze clocks and IDs only at explicit adapters; do not make production state machines depend on wall-clock timing in unit tests.
- Generate small WAV fixtures deterministically or commit them with checksums and provenance. Do not rely on microphones, speakers, network, or source-repository files in the normal gate.
- Test the real ffmpeg and sidecar on representative integration/E2E paths. Use fakes for exceptional exits, malformed responses, timeouts, and permissions, not for every happy path.
- Serve share tests through a local fake HTTP server with no external network dependency.
- Give each parallel E2E worker unique directories, port allocations, app identifiers, and profile names.
- Disable automatic retries in the main local gate. CI may retain a trace-producing diagnostic rerun, but the original failure remains a failed result and is reported as flaky.
- Set timeouts per operation type and log the last state transition, pending IPC jobs, child processes, active media tracks, and asset registry summary on timeout.
- Ensure tests pass with `/Users/iuriikatkov/IdeaProjects/anki-audio-tools` absent after the import phase.

### Contract and architecture tests

- Generate TypeScript and Python types from one schema source and test representative encode/decode round trips.
- Snapshot the complete IPC command/event registry so an unreviewed channel cannot appear silently.
- Assert renderer imports cannot reach Node/Electron main APIs and preload exposes only the reviewed surface.
- Assert path-taking services accept opaque asset IDs from the renderer and canonical paths only from trusted main-process code.
- Assert the sidecar imports no Anki, `aqt`, or PyQt modules.
- Assert playback transitions and timers remain in their designated state-machine/controller owners.
- Assert canonical state is not reconstructed from DOM attributes.
- Assert all production background jobs have cancellation, terminal cleanup, and stale-generation tests.

### CI test lanes

| Lane | Platforms | Runner command | Purpose |
|---|---|---|---|
| Fast QC | macOS and Windows | `python3 scripts/dev.py check` | Schema/contracts/docs, static analysis, unit/integration tests, and coverage. |
| Electron E2E | macOS and Windows | `python3 scripts/dev.py test-e2e-parallel` | Deterministic fake-media application journeys. |
| Sidecar/runtime | Each supported architecture | `python3 scripts/dev.py sidecar-build` then `runtime-verify` | Native wheel, ffmpeg/ffprobe, manifest, and process smoke. |
| Package smoke | Each release target | `python3 scripts/dev.py package` then `release-smoke` | Test actual unpacked/installed artifacts. |
| Release | Protected tags/manual approval | `python3 scripts/dev.py verify` | Full current-platform release-completeness gate before signing/publishing. |

Cache npm, Playwright, and Python downloads by lockfile hash, but never cache generated contracts as authoritative output. Do not share mutable runtime/user-data directories between CI jobs.

### Test layers

#### Pure unit tests

- Chorusing marker defaults, normalization, insert/remove tolerance, suffix navigation, base-region changes, and repeat counters.
- Playback and learner playback state machines, pause/resume/restart, repeat wait, auto-advance, cancellation, and terminal events.
- Recording state transitions, monotonic generation, clamping, invalid transitions, and stale-result rejection.
- Settings schema/defaults/migrations.
- Asset registry authorization and path canonicalization.
- Recording chunk ordering, duplicate/missing chunks, finalization, cleanup, and atomic promotion.
- Sidecar request/response validation and prosody algorithm tests copied from the add-on.

#### Renderer integration tests

- Mount the real Svelte practice surface in jsdom with a fake `window.practiceDesktop`.
- Port current editor-inline recording, learner playback, chorusing, selection, visualizer, and playback tests.
- Drive only visible controls or the typed public test contract; do not recreate `window.__aqe*` as production architecture.
- Verify focus, disabled states, status messages, countdown, cursor motion, timeline expansion, overlay offsets, marker hit targets, and toolbar behavior.

#### Main/preload integration tests

- Invoke the public preload API against a temporary user-data directory.
- Use fake child processes for timeout, malformed JSON, nonzero exit, cancellation, and large stderr.
- Use real ffmpeg for at least one normalization and real sidecar analysis path.
- Verify that arbitrary paths, URLs, shell commands, and unknown IPC channels are rejected.

#### Electron E2E

Use Playwright's Electron support with deterministic media flags/fixtures for CI and real packaged binaries for smoke tests.

Required journeys:

1. Open real audio -> analyze -> graph -> seek/zoom/select -> play/pause.
2. Add/remove markers -> shorter/longer suffix navigation -> normal selected playback.
3. Repeat with pause -> pause/resume -> auto-advance after N passes -> manual navigation and marker edits during the sequence.
4. Countdown -> record from non-zero cursor -> stop -> WAV exists -> analyze -> learner overlay -> expanded timeline when learner is longer.
5. Play/pause learner -> reveal -> share through a fake server/provider.
6. Denied microphone -> recovery without stuck busy state.
7. Switch target or close window during every async stage -> stale results ignored and resources closed.
8. Relaunch after an interrupted recording -> partial file recovery and clear diagnostic.

#### Native acceptance

Automated fake-media tests do not prove microphone permission prompts, hardware capture, speaker output, signing, or notarization. Keep a short release checklist and evidence for each supported platform. Native acceptance supplements, but does not replace, automated E2E.

### Parity artifacts

Maintain these machine-readable files in the new repository:

- `tests/parity/behavior-matrix.json`
- `tests/parity/source-baseline.json`
- `tests/fixtures/prosody/*.json`
- `tests/fixtures/state-traces/chorusing/*.json`
- `tests/fixtures/state-traces/recording/*.json`

`source-baseline.json` records the source repository URL, commit, add-on version, config defaults, contract version, and fixture hashes.

## 11. Planned pull-request sequence

Keep PRs small enough that every merge leaves its repository green.

### Source add-on repository

No source-repository PR is part of this execution plan. The developer reads and runs `/Users/iuriikatkov/IdeaProjects/anki-audio-tools` at the recorded commit. Any desirable add-on refactor or missing source test is recorded in `docs/source-gaps.md` and handled only through a separately authorized task.

### Standalone repository

1. Repository bootstrap, canonical Markdown set, secure Electron shell, and basic `scripts/dev.py` runner.
2. Contracts, architecture guards, CI, test harnesses, coverage gates, and complete dev-runner QC commands.
3. Source baseline/import manifest, copied pure cores, provenance, fixtures, and ported unit tests.
4. Asset registry, file dialog, custom audio protocol, and target playback.
5. Packaged prosody sidecar, runtime locks, and target graph.
6. Selection, zoom, repeat, chorusing markers/navigation/auto-advance.
7. Microphone capture and WAV finalization.
8. Learner analysis/overlay and learner playback.
9. Reveal/share, diagnostics, failure recovery, settings, and documentation updates.
10. Complete E2E/parity matrix, graphs/archive, native acceptance, packaging, artifact verification, signing, and release documentation.

## 12. Risks and mitigations

| Risk | Consequence | Mitigation / gate |
|---|---|---|
| Copying the whole editor-inline bundle carries hidden Anki assumptions | Standalone code remains coupled and hard to test | Isolate pure cores first; use forbidden-import/literal guards for `pycmd`, `__aqe`, field scanning, Anki sound refs, and editor globals. |
| Rewriting prosody in Node changes results | Comparison graphs drift despite similar UI | Keep the Python algorithm and compare golden payloads; defer any rewrite to a separate future project. |
| Browser recording format varies by OS | Invalid or inconsistent learner media | Stream capture to temp storage and normalize every result to validated PCM WAV with bundled ffmpeg. |
| Mic permission or window closure leaks capture | Privacy/resource bug and stuck state | Central cleanup in every terminal transition; E2E close/cancel tests; native permission acceptance. |
| Local file URLs expose arbitrary files | Security vulnerability | Opaque asset IDs and allowlisted custom protocol with range support; never expose renderer paths. |
| Sidecar packaging fails with native Python wheels | App works in dev but not installed artifacts | Per-target `onedir` builds, artifact smoke tests, and CI/native verification on every target. |
| Long-running extraction conflicts with ongoing add-on changes | Silent behavioral divergence from a moving source | Record one immutable baseline, import committed blobs by hash, and review later add-on changes explicitly through `UPSTREAM_SYNC.md`. |
| New repository lacks the source project's development discipline | Different local/CI commands, stale contracts/docs, and unrepeatable releases | Build the Electron `scripts/dev.py` equivalent in Phase 1 and require CI to call the same `check`, E2E, package, and smoke commands. |
| New context loses architectural and operational knowledge | Future changes repeat Anki-era mistakes or break process boundaries | Create the canonical Markdown set, generated diagrams, `docs-check`, and same-PR documentation rules before feature migration. |
| Coverage percentage hides lost workflows | Apparent quality parity without behavior parity | Make the behavior matrix and golden state traces release gates in addition to percentages. |
| App accidentally includes the add-on's large runtime pack | Oversized release and unrelated maintenance | Build a minimal practice runtime containing only ffmpeg/ffprobe and the prosody sidecar. |
| New persistence behavior expands product scope | Extraction turns into a redesign | One active source, app-owned recordings directory, existing settings only; defer library/project UX. |

## 13. Definition of done

The extraction is complete only when all of the following are true:

- The standalone application performs every in-scope row of the parity matrix.
- It launches and completes the workflow on a clean supported machine without Anki installed.
- It contains no runtime/build dependency on Anki, `aqt`, PyQt, the add-on ID, the add-on media directory, or the source repository checkout.
- Target audio is never modified; recordings are independent sidecars.
- Chorusing, repeat, pause, auto-advance, countdown, recording, stale-result handling, prosody analysis, overlay, learner playback, reveal, and share match the selected baseline.
- Numeric coverage gates meet or exceed the current levels, with no inappropriate production exclusions.
- Unit, renderer integration, main/preload integration, Electron E2E, packaged-artifact smoke, and native acceptance gates pass.
- The recorded source baseline results and any source gaps are preserved without requiring source-repository modifications.
- `python3 scripts/dev.py check`, `test-e2e-parallel`, `package`, `release-smoke`, and `verify` provide reproducible target-repository gates and are used by CI.
- The new repository includes provenance, license notices, architecture, development, testing, release, diagnostics, and cross-repository sync documentation.
- `python3 scripts/dev.py docs-check` and `graphs-check` pass, and documented commands match the implemented command registry.
- The new app and add-on can version, build, test, release, and fail independently.

## 14. First execution checklist

When implementation begins:

1. `cd /Users/iuriikatkov/IdeaProjects/shadowing-pratice` and initialize/inspect the target repository.
2. Confirm the source commit at `/Users/iuriikatkov/IdeaProjects/anki-audio-tools` and record its clean/dirty status without editing it.
3. Copy this plan into the target repository and create the initial canonical Markdown files.
4. Implement and test the minimal `scripts/dev.py` runner plus `setup`, `info`, `docs-check`, `test`, and `check`.
5. Run the source add-on baseline QC/E2E and create the target behavior matrix, source-gap log, fixtures, and provenance manifest.
6. Implement `import-source`, dry-run it, then import only reviewed committed files and tests.
7. Establish portable-core and sidecar boundaries in the target repository and make ported tests pass.
8. Build target playback/graph/chorusing as the first standalone vertical slice.
9. Add recording only after the asset, sidecar, IPC, test isolation, and cleanup boundaries are proven.
10. Keep `DEVELOPMENT.md`, `TESTING.md`, `ARCHITECTURE.md`, and generated graphs current as each phase lands.

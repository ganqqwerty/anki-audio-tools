# Full Test Suite Audit

Date: 2026-07-11

Scope:

- Python unit and component tests under `tests/`
- architecture and source-policy tests under `tests/test_architecture/`
- real-Anki tests under `e2e/`
- Svelte/TypeScript tests under `settings_ui/tests/`
- Anki API contract tests, test runners, fixtures, coverage configuration, mutation configuration, and CI enforcement

Audit standard:

1. A test should fail for a relevant product regression.
2. A test should not fail for an equivalent internal refactor unless it explicitly protects an architectural boundary.
3. Test setup and expected results must not come from the same production implementation.
4. Async and race tests must prove that the intended interleaving occurred and completed.
5. E2E tests should finish on observable user, media, or persistence outcomes; internal state may aid diagnosis but should not be the sole oracle.

## Executive Summary

The repository has a large and generally serious test suite, but its headline size and aggregate coverage overstate the confidence it provides in several high-risk areas.

The most important problems are not missing `assert` statements. They are false oracles and false boundaries:

- architecture rules and reports omit real dynamic dependencies, then agree with each other on the same incomplete graph;
- live-Anki tests share mutable configuration under randomized ordering, and the hand-maintained E2E baseline is already incompatible with production defaults;
- the native playback guard suppresses an unexpected playback path instead of failing;
- several tests accept both the correct and incorrect result, assert the object they constructed themselves, or only prove that a file exists;
- Python visualizer tests run a stale reimplementation instead of the shipped TypeScript renderer;
- release tests derive fixtures and expected archive members from the same production selectors;
- aggregate coverage thresholds hide critical individual files at 22-78% coverage;
- the documented mutation workflow is currently unusable;
- no GitHub workflow enforces the unit, frontend, architecture, coverage, or real-Anki suites.

This is not a recommendation to replace the suite. Many tests are strong. The priority is to remove false confidence, make state isolation deterministic, and strengthen oracles at the public boundaries already covered by the suite.

## Inventory and Method

The audit combined full-suite static inventory, AST/source-policy analysis, CodeGraph dependency inspection, coverage reports, runner execution, prior-audit comparison, and deep review of high-risk audio, editor, Browser, Reviewer, runtime, release, and concurrency paths.

| Layer | Inventory | Notes |
|---|---:|---|
| Python tests | 230 `test_*.py` modules | 192 non-architecture modules plus 38 architecture modules |
| Python test declarations | 1,497 | Before parametrization and imported aliases; imported aliases add duplicate collection |
| Frontend tests | 106 `.test.ts` files, 637 declarations | 2,318 `expect()` calls |
| Real-Anki E2E | 63 test modules, 173 functions, 204 collected items | 101 functions use synthetic DOM clicks; 96 use graph/test-state helpers |
| Anki API contract | 1 test module | Three declared contract tests |
| Test/harness source | roughly 70,000 lines | Excludes bundled media payloads |

Systematic checks found:

- no skipped, xfailed, focused, retried, or snapshot-only tests;
- no module-level Vitest mocks;
- 12 Python tests without inline assertions, all reviewed individually; most are legitimate “does not raise” tests, assertion-helper delegates, or sentinel-fake tests;
- 311 `MagicMock` constructions, 893 `monkeypatch.setattr` lines, and no `spec`, `spec_set`, or autospec use in non-architecture Python tests;
- 293 bare `await Promise.resolve()` flushes in 39 frontend test files;
- 330 frontend `*ForTest` references across 37 files;
- four E2E `test_*.py` modules and at least four Python `test_*.py` wrapper/helper modules that declare no tests.

Severity used below:

- **P0**: the test or gate can directly report success for a critical broken behavior.
- **P1**: material confidence gap or brittleness that should be fixed before risky work in the area.
- **P2**: maintenance, performance, or narrower reliability issue.

## P0 — False Confidence

### F-01: Architecture rules omit real dependencies and have no detector-level tests

Evidence:

- `tests/test_architecture/inspection.py:114-131` collects only a subset of AST import shapes. It does not model dynamic `import_module()` calls and does not descend through all statement containers.
- Real dynamic imports in `addon/anki_audio_quick_editor/__init__.py:245,277,285,290-298,308` and `addon/anki_audio_quick_editor/audio_processor_rendering_portal.py:15-16` are absent from the observed dependency graph.
- Rules 17 and 31, the architecture report, and archived graph data all consume the same incomplete observation, so they corroborate each other without an independent oracle.
- Core detector functions such as `_collect_imports`, `_detect_side_effects`, and `collect_private_cross_module_imports` have no table-driven positive and negative tests using synthetic source snippets.

Why a bug passes:

A forbidden dependency introduced through a dynamic import or an unhandled statement shape is invisible to every downstream rule and report.

Required fix:

1. Extract the analyzers into pure functions that accept source/AST.
2. Cover `if`, `try`, `with`, `for`, `while`, `match`, nested definitions, aliases, relative imports, and supported dynamic imports.
3. Add violating canaries and benign near-misses for every detector.
4. Regenerate and compare architecture catalogs only after the detector tests pass.

### F-02: E2E configuration is shared, randomized, partial, and already stale

Evidence:

- `e2e/conftest.py:203-232` creates one Anki main window per pytest process and writes a baseline config once per session.
- `_default_config()` at `e2e/conftest.py:39-120` is hand-maintained and partial. It declares `_config_version = 23`, while production declares `CURRENT_CONFIG_VERSION = 2` at `addon/anki_audio_quick_editor/config_migration.py:23`.
- The E2E dictionary omits current keys including trigger rules, editor history, graph settings, size-reduction settings, reviewer enablement, and button entries.
- `_configure_ffmpeg()` at `e2e/editor_note_helpers.py:105-126` reads the current shared config and updates only a subset of keys.
- `pyproject.toml:33-44` requires `pytest-randomly`.
- Tests leave values such as DPDFNet attenuation, trigger rules, logging, presets, and toolbar visibility behind. Serial and parallel runs have different contamination boundaries because each parallel shard gets a separate profile.
- The audit's full parallel run confirmed the problem: one shard failed four Reviewer/filtered-deck items after 91 items had passed. Anki's WebView still showed the deck browser, and logs from an earlier Browser batch audio source continued to emit metadata-timeout events during the Reviewer test. Both failing files passed when rerun in fresh pytest processes.

Why a bug passes or flakes:

A test can inherit a setting from whichever randomized test ran first. A default/migration regression may not be exercised because E2E bypasses the canonical production default-and-migration path.

Required fix:

1. Derive the baseline from the production default loader plus `migrate_config()`.
2. Add a function-scoped autouse fixture that restores a complete config through the same refresh path as Settings Save.
3. Wait for or cancel background work before restoration.
4. Add explicit opt-out markers only for tests intentionally proving same-session persistence.
5. Reset other process-global state: support incidents, clipboard, theme, dialogs, Reviewer state, and trigger jobs.

### F-03: Unexpected native playback is silently suppressed

Evidence:

- `e2e/conftest.py:248-273` replaces `av_player.play_tags()`.
- Outside the explicit fake-playback context, it returns `None` unless `AQE_STRICT_NATIVE_PLAYBACK_GUARD=1`.
- `stop_and_clear_queue()` is swallowed as cleanup; seek and pause/toggle are not intercepted or validated.

Why a bug passes:

An accidental HTML-to-native fallback is neutralized by the test fixture. The workflow can continue without proving which engine production selected.

Required fix:

- Fail by default on every unexpected native playback start.
- Add an explicit marker/context for the few tests that intentionally exercise the native seam.
- Record or validate stop/seek/toggle operations where the tested behavior depends on them.
- Run the playback E2E subset once with the strict policy before making it the default.

### F-04: “Mid-render Undo” does not test a mid-render request and accepts either result

Evidence:

- `e2e/test_editor_processing_busy_workflow.py:261-290` starts volume processing, then calls `click_selector()` on Undo.
- `click_selector()` at `e2e/helpers.py:120-160` waits until a disabled button becomes enabled, so Undo is commonly clicked only after rendering finishes.
- The final assertion accepts either “Increased volume” or “Undid,” and accepts either the original or generated file accordingly.

Why a bug passes:

Both sides of the intended race are treated as success. A missing mid-render guard, a late click, or a completely serialized implementation all pass.

Required fix:

- Use a barrier-controlled renderer.
- Prove rendering started and Undo was dispatched while busy.
- Release the renderer, await a positive completion/callback signal, and assert one deterministic policy outcome.

### F-05: Python visualizer tests run a stale clone, not shipped code

Evidence:

- `tests/test_prosody_language_contours.py:148-219` claims visualizer rendering coverage but calls `render_pitch_points()`.
- `tests/prosody_visualizer_harness.py:7-88` reimplements normalization, coordinates, segmentation, and SVG path construction.
- The clone uses `left=44, top=10`; shipped `settings_ui/src/editor-inline/plot.ts:14` uses `left=10, top=28`.

Why a bug passes:

The clone and product can diverge while the Python tests remain green. They already disagree on geometry.

Required fix:

- Keep analyzer/window semantics in Python.
- Serialize representative analysis payloads.
- Move pixel/path/gap assertions to Vitest using the real `pitchSegments`, `xForMs`, `yForPitch`, and renderer.
- Delete the Python renderer clone.

### F-06: Release fixtures and expected results share the production selector

Evidence:

- `tests/release_archive_fixtures.py:56-73` obtains archive and executable members from production `release_manifest_files` and `release_runtime_executables`.
- `tests/test_release_archive_validation.py:25-60,140-156` feeds those results back into the validator.
- `tests/test_release_archive_validation.py:109-116` builds the expected set with the same selectors.

Why a bug passes:

Deleting a locked tool/support mapping from the selector removes it from both the archive fixture and the expected set.

Required fix:

- Create a small literal lock fixture with independently written expected target/tool/support/shared paths.
- Traverse raw lock data independently in the test oracle.
- Add a mutation/canary that deletes one mapping and must fail validation.

## P1 — High-Priority Gaps

### F-07: There is no CI quality workflow

The workflows under `.github/workflows/` build runtime assets or deploy Pages; none runs Python tests, architecture checks, frontend tests, coverage, or E2E.

Impact:

All documented gates are voluntary local steps. A large suite cannot prevent regressions if merges do not execute it.

Required fix:

- Add PR jobs for deterministic Python/API/architecture checks and frontend validation.
- Add macOS and Windows jobs for platform-specific runtime code.
- Run real-Anki E2E on protected-branch/nightly/release workflows if PR latency is too high.
- Upload seeds, coverage, logs, and exact rerun commands.

### F-08: The documented mutation workflow is broken and its configured scope is misleading

Confirmed command failure:

```text
python3 scripts/dev.py --verbose muttest run
BadTestExecutionCommandsException ... pytest ... -p no:randomly ...
```

Cause:

- pytest requires `pytest-randomly` at `pyproject.toml:42-44`;
- mutmut disables it at `pyproject.toml:555-560`, causing pytest collection to exit with a usage/configuration error.

Additional scope problems:

- mutation selection lists only seven test files at `pyproject.toml:561-569`;
- `tests/test_config_migration.py` contains no tests;
- several high-risk editor, Browser, settings, runtime, and prosody modules are excluded at `pyproject.toml:535-552`;
- mutation testing is advisory and absent from CI/check.

Required fix:

- Keep `pytest-randomly` loaded with a fixed seed, or give mutmut a dedicated pytest config without a conflicting `required_plugins` rule.
- Point selection at the real split test modules.
- Add a cheap collection smoke test and a scheduled focused mutation job.
- Publish killed/survived/timeout statistics by risk area.

### F-09: Aggregate coverage thresholds hide critical weak files

Python:

- Coverage passes at 85.24% combined coverage with only a global `fail_under = 80` at `pyproject.toml:260-276`; the same report contains 88.09% statement coverage but only 71.97% branch coverage.
- Examples below the global threshold include `editor_frontend/refresh.py` 46%, `editor_playback_bounds.py` 50%, `runtime_platform.py` 55%, `editor_region_delete.py` 57%, `editor_region_delete_worker.py` 63%, `runtime_install.py` 64%, `runtime_lookup.py` 64%, and `reviewer_template_filter_integration.py` 65%.

Frontend:

- `settings_ui/vitest.config.ts:19-30` defines aggregate global and editor-glob thresholds without `perFile` enforcement.
- The isolated report passed at 92.97% global lines and 93.66% editor lines.
- Individual files still passed at `preset-settings-helpers.ts` 22.73%, `playback-controller-audio.ts` 55.56%, `trigger-settings-state.ts` 71.85% lines/40.74% branches, `region-delete-state.ts` 70.30%, `playback-controller.ts` 77.05%, and `html-audio-session-machine.ts` 78.45%.

Required fix:

- Add risk-tier per-file or per-area floors rather than immediately applying one universal floor.
- First cover runtime rollback, region deletion, reviewer filters, presets/triggers, and playback transitions.
- Exclude truly thin entrypoints and generated/test-contract code explicitly instead of letting them distort the aggregate.
- Measure `scripts/` release/dev tooling separately.

### F-10: Architecture contracts are over-permissive and source guards are bypassable

Evidence:

- Rule 17 checks `observed - allowed`, but never fails on stale `allowed - observed` dependencies.
- Twenty of 181 module contracts currently allow 51 dependencies the detector does not observe. At least seven are real dependencies hidden by F-01's detector defect; the remaining stale-permission count must be recomputed after import extraction is fixed. `editor_processing` appears to retain nine moved-away dependencies.
- Rule 30 bans one exact double-quoted substring.
- Rule 26 uses regex and brace counting on TypeScript.
- Rule 3 treats raw `aqe:` text in comments/dead constants as a command.
- Rule 34 can misclassify a comparison beginning with `=` as a dataset projection write.
- frontend architecture helpers miss re-exports, default exports, dynamic imports, bracket access, and equivalent syntax; their negative scans have no violating canaries.
- Rule 38 grants privileged ownership to three nonexistent files.

Required fix:

- Enforce unused permissions or require documented waivers.
- Use Python/TypeScript AST and dependency-cruiser instead of source substrings.
- Require allowlisted paths to exist and actually contain the owned behavior.
- Unit-test every detector against violating and benign syntax.

### F-11: Local Anki mocks are permissive enough to hide API and async bugs

Evidence:

- `tests/test_anki_api_contract_mocks.py:52-56` checks only that a resolved callable use is not `None`; a non-callable value passes.
- It relies on private `MagicMock._mock_children` at `:24-28`.
- `aqt.mw`, `mw.taskman`, and `mw.col` are unrestricted `MagicMock` objects in `tests/_anki_test_mocks_environment.py:125,194-208`; the `mw.taskman` double only wires `run_on_main` synchronously.
- A separate concrete synchronous `_TaskManager` is exposed as `aqt.taskman.TaskManager`, so the suite has two different task-manager semantics and production code commonly receives the permissive `mw.taskman` mock.
- No mocks use spec/autospec, and test code is outside the mypy target.
- the task-manager fake runs synchronously and does not preserve production callback/argument semantics.

Required fix:

- Use typed concrete fakes or autospecced objects for the shared `mw` tree.
- Assert `callable()` and bind observed arguments against signatures.
- Provide a controllable Future/task-manager fake with explicit scheduling and completion.
- Type-check shared test doubles.

### F-12: Region-delete tests bypass the public orchestration entry point

`tests/test_editor_region_delete_integration.py` tests private parsing, renderer selection, and replacement helpers, but no test calls `delete_selection_with_request()`.

Uncovered public behavior includes malformed requests, busy sessions, active-field mismatch, unresolved or changed media, whole-clip rejection, worker failure/cleanup, and replacement failure. Current coverage is 57% for orchestration and 63% for the worker.

Required fix:

- Add component tests through the public entry point for every rejection and failure branch.
- Verify status, busy-state release, stale-result behavior, temp cleanup, and persistence.
- Retain parser/router tests as explicitly named unit tests.

### F-13: Runtime rollback and concurrency are not tested

`tests/test_runtime_manager_state.py:69-99` is named as if it proves the old runtime is not deleted before replacement, but checks the old directory only before the call and the new directory only afterward.

It does not observe the old root during installation or after download, extraction, promotion, or state-write failure. `ensure_runtime_async()` single-flight behavior is also uncovered.

Required fix:

- Inject failures at every install phase and assert the previously ready runtime/state survives where required.
- Observe the old directory during the promote operation.
- Test cancellation after data has arrived and during verification.
- Race two callers and prove one worker plus consistent notifications/results.

### F-14: E2E processing and export assertions often prove only file creation

Examples:

- `e2e/test_editor_processing_workflow.py:118-141` applies six operations but checks filenames, statuses, and source immutability.
- the pause-removal case uses a continuous sine with no pause;
- split-button volume and preset speed tests do not measure loudness or duration;
- size-reduction tests accept any smaller byte sequence without probing decodability/duration;
- export tests often assert only member names or nonempty output.

Required fix:

Create reusable media oracles:

- ffprobe codec/channel/sample-rate/duration checks;
- decoded PCM RMS/dB assertions for volume;
- duration ratios for speed;
- tone-silence-tone fixtures for pause removal;
- pitch/spectral assertions for pitch-hum and denoise;
- decoded entry and total-duration/silence checks for export archives.

Keep exact command construction in unit tests, not as the final real-binary oracle. `tests/test_audio_rendering_real_ffmpeg.py:122-146` should likewise measure the ±6 dB output instead of reasserting the command string.

### F-15: The codec matrix uses a fake playback driver

`e2e/test_editor_region_loop_playback_one_shot_workflow.py:36-106` parametrizes many formats, but `_open_tone_editor()` installs the same fake HTML playback driver at `e2e/editor_region_loop_helpers.py:28-43`.

It proves state-machine behavior and analysis, not that Qt WebEngine can load/play every codec.

Required fix:

- Keep region-boundary behavior on one representative format.
- Add a separate real, no-driver readiness/playback matrix with explicit platform expectations.

### F-16: Async race tests do not prove completion was delivered

`e2e/test_editor_async_race_workflow.py:48-65,89-114` releases a delayed renderer, pumps events for one second, and asserts nothing changed. The delayed renderer exposes a “started” event but no completed/callback-consumed event.

A worker whose completion is lost forever produces the expected unchanged state and passes.

`tests/test_prosody_cache.py:92-151` has the same class of problem: `second_miss.wait(0.2)` ignores whether the rendezvous occurred.

Required fix:

- Add worker-completed and callback-observed events.
- Await backend/frontend idle before asserting intentional stale-result discard.
- Use explicit lock/barrier rendezvous for cache concurrency; do not use ignored timed waits.

### F-17: The DPDFNet dialog test asserts its own setup object

`e2e/test_dpdfnet_attenuation_integration.py:62-103` writes config, constructs `AudioProcessingConfig` itself, passes it into the dialog, then asserts `config.dpdfnet_attn_limit_db == 18.0`.

It never proves that the dialog displays or emits the value. A dropped request parameter passes.

Required fix:

- Open through the Browser menu, select the relevant operation, start it, capture the emitted request, and assert the request contains 18 dB.

### F-18: The HTML-audio reducer lacks a transition matrix

The event type declares 18 events. Direct reducer tests omit at least `ResumeRequested`, `SourceCleared`, `MetadataTimeout`, and `RuntimeDisposed`, leaving important branches at `html-audio-session-machine.ts:183-199,295-307,374-388` without focused assertions.

Required fix:

- Build a state-by-event legality table.
- Assert effects, state invariants, stale-event no-ops, timer cancellation, and disposal from every reachable state.
- Add focused TypeScript mutation testing for the reducer.

### F-19: E2E interaction and observability are more synthetic than the label implies

Evidence:

- 101 of 173 E2E functions use `click_selector()`, which dispatches untrusted DOM events and does not prove hit testing, geometry, overlays, focus, scrolling, or real input behavior.
- 96 functions use graph/test-state helpers as an oracle.
- `test_graph_area_settings_redraw_active_graph` checks internal stores/state but not that analysis reran or the rendered path changed.
- the E2E fixture has no autouse assertion for package ERROR logs, Qt critical messages, JavaScript console errors, or unhandled rejections; `e2e/conftest.py:213-223` swallows core import exceptions.

Required fix:

- Classify synthetic WebView tests as in-Anki component tests.
- Add a small trusted-input smoke layer using Qt/WebEngine coordinates for critical workflows.
- Harden synthetic clicks with visibility, geometry, and `elementFromPoint()` checks.
- Make internal state supplemental, not the final oracle.
- Fail on core import errors and unexpected Python/JS error channels.

### F-20: E2E runner failure behavior is incomplete

Evidence:

- parallel collection uses an unbounded subprocess call while serial collection has a timeout;
- forced teardown uses `pgrep`, direct-child `SIGKILL`, broad exception swallowing, and `os._exit`, which is nonportable and bypasses normal cleanup;
- rerun hints omit original node IDs, random seed, and shard composition;
- shared-desktop classification is a duplicated hardcoded file list that cannot detect a new clipboard test omitted from both copies.

Required fix:

- Supervise collection with the same idle/absolute timeout policy as serial collection.
- Move process-group/job-object cleanup to the parent runner.
- print exact single-process node IDs and seed on failure.
- derive shared-desktop classification from pytest markers or verified static capabilities.

## P2 — Cleanup and Maintainability

### F-21: Exact timing and microtask counts are coupled to implementation

- Frontend tests contain 293 bare `await Promise.resolve()` flushes across 39 files, often repeated to encode an exact internal microtask depth.
- an optional E2E processing-state helper waits up to two seconds, catches the timeout, and continues, so callers do not prove the intermediate state occurred.
- negative E2E assertions use arbitrary one-second quiet windows.

Fix: use Svelte `tick()`, controlled deferred promises, state-specific `waitFor`, and explicit “initialization settled”/worker-idle signals.

### F-22: Test-only contracts dominate frontend assertions and ship with product code

`src/editor-inline/test-contract.ts` is a 358-line shipped adapter. Frontend tests make 330 `*ForTest` references, including 288 graph-state reads, and the file participates in product coverage.

Fix:

- exclude test instrumentation from product coverage;
- wrap it behind one typed driver;
- fail clearly when unavailable;
- migrate integration assertions toward DOM, bridge messages, media, and persistence.

### F-23: Duplicate and empty test modules inflate the suite

- `tests/test_editor_playback_state.py:3-37` rebinds 11 tests already collected from three companion modules, so they run twice.
- exact duplicate Python tests exist for support reporting and DeepFilter output selection.
- Mandarin/Vietnamese E2E slope bodies are identical and can share one data table.
- four E2E wrapper/helper modules collect zero tests, including `test_reviewer_audio_editor_workflow.py`.
- Python wrapper/helper modules such as `test_config_migration.py`, `test_reviewer_integration.py`, `test_runtime_manager.py`, and `test_settings_commands_diagnostics.py` declare no tests.
- Rule 1 is substantially subsumed by Rule 16, Rule 5 by Rule 15, and Rule 20 reruns Rules 16-18 through the report.

Fix: remove imported aliases, rename helpers outside the `test_` namespace, and consolidate exact duplicates while preserving genuinely different data fixtures.

### F-24: Private dependency synchronization makes audio tests refactor-hostile

`tests/conftest.py:15-27` invokes six private `_sync_*` functions after every test, and AST inspection finds 201 patch calls targeting `audio_processor.*` across 13 files. Identity tests prove module-global aliasing more than behavior.

Fix: inject a typed dependency object or patch the leaf symbol actually used; keep one public-facade behavior test and remove private identity/sync coupling.

### F-25: Test resources and process state leak

- `tests/test_audio_rendering.py:91` and `tests/test_audio_rendering_real_ffmpeg.py:65` leave `aqe_final_*` temporary directories outside `tmp_path`;
- several settings tests leave QWebEngine dialogs open;
- Browser and some Reviewer tests do not guarantee cleanup on failure;
- dependency availability is cached at import time and broad `Exception` handling converts programming failures into misleading “dependency unavailable” outcomes.

Fix: route temp roots through fixtures, use context-managed windows, add an autouse top-level-window cleanup assertion, and catch only expected missing-tool exceptions in session fixtures.

### F-26: Several tests lock representation instead of behavior

Examples include inspecting `find_ffmpeg.__defaults__`, exact JavaScript injection statements, object identity in the audio injection seam, exact CSS design tokens, and file-name-scoped architecture permissions.

Fix: retain exact serialization only for documented boundary contracts; otherwise assert public output, invocation semantics, accessibility, or architectural capability.

### F-27: Smaller tests and helpers contain concrete silent-bypass paths

- the delayed Edit Current test rewrites Anki JavaScript with `str.replace("setFields(", ...)` but never proves the replacement occurred; upstream formatting changes turn it into an ordinary fast-path test;
- visualizer readiness checks “any enabled button” across the whole document instead of the requested field, so one ready field can make another look ready;
- Reviewer tooltip isolation creates a fabricated tooltip-like div rather than hovering the real provider component;
- one Browser export test clicks the generic selector `"button"`, so DOM reordering can redirect the test;
- Browser helpers replace modal `exec()` with `show()` plus an immediate return, bypassing real modal completion behavior;
- `tests/test_dependency_skips.py` recognizes only a subset of skip/xfail mechanisms and has no runtime assertion that collected items were not skipped;
- config-default migration tests repeat generic merge behavior key by key instead of maintaining one schema-wide invariant;
- 23 immediate-thread fakes and the absence of unit/component/external-runtime markers make “integration” an inconsistent label.

Fix each at the narrowest boundary: assert injection counts/markers, scope readiness per field, interact with the real tooltip, use stable selectors, preserve one true modal smoke test, inspect the pytest report for skips, use schema-driven default coverage, and standardize async doubles/test classifications.

## Missing Workflows and Coverage

The following gaps deserve explicit tests after the false-confidence fixes:

1. Browser batch real workflows for operations other than Reduce Size, plus multi-note/multi-field, partial failure, cancellation, missing media, and collection close.
2. Export content correctness: decoded entries, combined duration/silence, normalization level, and corrupt/missing input handling.
3. Real codec readiness/playback across supported platforms.
4. Reviewer transform semantics, not just creation of a generated file.
5. Startup cleanliness: bootstrap, hook boundaries, JS console, and unhandled promise rejection assertions.
6. Real recorder/permission/device coverage, documented separately from deterministic fake-recorder tests.
7. Profile/collection close-reopen and add-on restart persistence for settings, triggers, runtime state, and persistent history.
8. Runtime install rollback, cancellation after partial download, single-flight concurrency, and notification ordering.
9. Public region-delete failure and stale-completion paths.
10. HTML audio transition-matrix and timer/disposal behavior.

## Positive Findings

The audit also found strong practices worth preserving:

- no skips, xfails, retries, or missing-dependency skips hide failures;
- strict warnings and randomized ordering are enabled;
- `data-testid` is used consistently as a stable selector contract;
- most editor E2E tests close editors in `finally`;
- real-media repeat tests, direct DeepFilter byte comparison, tone-silence-tone pause tests, and region-delete duration assertions have meaningful behavioral oracles;
- bridge envelope and trusted URL tests are appropriately exact because the serialized value is the contract;
- pure audio/state logic has substantial branch and negative-path coverage;
- no snapshot-only or module-mock-heavy frontend culture was found;
- the suite already has the necessary ingredients—real Anki, real ffmpeg, barriers, fake schedulers, and real browser audio—to implement the fixes without a wholesale rewrite.

## Prioritized Remediation Plan

### Phase 0: Stop false greens

1. Fix architecture import extraction and add analyzer canary tests.
2. Replace the E2E session config with a canonical function-scoped reset fixture.
3. Make native playback and unexpected Python/JS errors fail closed.
4. Rewrite the mid-render Undo, DPDFNet dialog, and async race tests around deterministic barriers and one outcome.
5. Replace the visualizer clone and release self-oracles.
6. Repair mutation-test collection and add a smoke check.

Exit criterion: each issue above has a deliberately broken canary/mutation that fails the intended test.

### Phase 1: Strengthen high-risk public boundaries

1. Test region delete through its public entry point.
2. Add runtime rollback/single-flight/cancellation tests.
3. Add decoded media assertions for E2E processing and export.
4. Add the HTML-audio state/event transition matrix.
5. Tighten typed Anki fakes and async task-manager semantics.
6. Add per-area coverage floors after the new tests land.

Exit criterion: high-risk modules no longer rely on aggregate coverage or private helper tests for their principal behavior.

### Phase 2: Enforce and simplify

1. Add PR/nightly/release CI jobs.
2. Add trusted-input smoke coverage and classify synthetic in-Anki tests accurately.
3. Replace microtask counts and quiet windows with observable waits.
4. Remove duplicate collection, empty wrappers, stale allowlists, and exact duplicate cases.
5. Add reproducible E2E reruns, portable process supervision, and duration-aware sharding.

Exit criterion: every required gate is automated, failures are reproducible, and test count reflects independent fault detection rather than aliases/duplication.

## Validation Performed During This Audit

- clean, non-overlapping `python3 scripts/dev.py check`: passed all steps.
- `python3 scripts/dev.py test`: passed.
- `python3 scripts/dev.py test-svelte`: passed in an isolated run.
- `python3 scripts/dev.py coverage`: passed at 85.24% combined coverage (88.09% statements, 71.97% branches).
- Frontend coverage: passed at 92.97% lines / 85.43% branches globally and 93.66% lines / 84.84% branches for `src/editor-inline/`.
- `python3 scripts/dev.py --verbose muttest run`: failed during pytest setup because the required randomization plugin is disabled by the mutmut config.
- `python3 scripts/dev.py test-e2e-parallel`: failed with 4 failures and 91 passes in one shard; the other two shards passed. The failures were in filtered-deck/Reviewer opening and reproduced cross-test state leakage. Both affected files passed when rerun in fresh processes.
- canonical serial `python3 scripts/dev.py test-e2e`: passed. Its different process/order boundary compared with the failing parallel run is further evidence that the suite is not isolated consistently.

One initial `scripts/dev.py check` run overlapped another frontend coverage process and produced a shared `coverage/.tmp` collision. An isolated frontend rerun passed, so that collision is not counted as a repository defect.

## Definition of Done for the Test-Suite Repair

The remediation is complete only when:

- every P0 has a regression/canary that demonstrably fails before the fix;
- architecture analyzers themselves have positive and negative tests;
- E2E state is restored between randomized tests;
- real processing tests measure media semantics, not only paths/commands;
- mutation testing runs and publishes results;
- per-area coverage gates protect critical modules;
- required checks run automatically in CI;
- canonical serial E2E and platform-specific jobs pass without hidden skips or fail-open guards.

## Mitigation Implementation Status

Implementation date: 2026-07-13. Detailed requirements and exit criteria remain in
[`2026-07-12-full-test-suite-audit-mitigation-plan.md`](../plans/2026-07-12-full-test-suite-audit-mitigation-plan.md).

| Findings | State | Primary checked-in proof |
|---|---|---|
| F-01, F-10 | Implemented | AST import and TypeScript architecture-detector canaries, near-miss matrices, and regenerated graph catalogs |
| F-02, F-25 | Implemented | canonical migrated-config restoration through the production save path; randomized config, logging, clipboard, theme, support-state, Anki-state, and leaked-window sentinels |
| F-03, F-19, F-27 | Implemented | fail-closed native playback/import/Python/JavaScript/Qt channels, narrow explicit bypass validation, trusted pointer interaction on shipped controls, and collection-policy checks |
| F-04, F-16 | Implemented | barrier-controlled renderer and callback-observed completion tests proving Undo and cancellation timing |
| F-05 | Implemented | assertions against the shipped TypeScript visualizer renderer rather than a Python clone |
| F-06, F-17 | Implemented | literal release-lock fixture with deletion canary and DPDFNet assertions over the request captured from the real dialog flow |
| F-07, F-20 | Implemented | PR, protected-branch quality, nightly mutation/platform, and release workflows; portable supervision, deterministic seeds, duration-aware shards, and exact rerun commands |
| F-08 | Implemented | working mutation groups for runtime, prosody, frontend, and architecture detectors; collection smoke; risk-area JSON reports and previous-run diffs |
| F-09 | Implemented | checked-in statement/branch floors for critical Python and frontend areas in addition to informational aggregate coverage |
| F-11 | Implemented | signature-checked Anki fakes plus a shared controllable immediate-thread double with delivery and failure behavior tests |
| F-12 | Implemented | public region-delete orchestration matrix covering accepted, rejected, failed, and stale completions |
| F-13 | Implemented | runtime phase-fault, rollback, cancellation, and two-caller single-flight barrier coverage |
| F-14 | Implemented | decoded duration, loudness, codec, silence-removal, denoise, graph-SVG, and preset assertions across Browser, Reviewer, and export workflows |
| F-15 | Implemented | real WebEngine/no-driver codec and audible PCM coverage; hardware recorder/device cases remain an explicit platform lane |
| F-18 | Implemented | HTML-audio state/event/effect transition matrix with frontend mutation protection |
| F-21, F-22 | Implemented | state-specific waits, typed frontend drivers, production tooltip interaction, and external behavior/media oracles |
| F-23 | Implemented | empty wrappers and duplicate collectors removed; AST inventory/duplicate policy and mutation/coverage baselines prevent count-only cleanup |
| F-24, F-26 | Implemented | public typed audio dependency seam and behavior/boundary assertions replacing private synchronization and representation locks |

Validation on the implementation state:

- `python3 scripts/dev.py muttest group architecture`: passed; the exported baseline records killed, survived, timeout, and untested mutants.
- `python3 scripts/dev.py test-e2e-parallel`: passed all three shards after an exact seeded Browser-lifecycle regression rerun.
- `python3 scripts/dev.py test-e2e`: passed in one canonical Anki process.
- `python3 scripts/dev.py graphs-archive`: regenerated the 2026-07-13 machine-readable architecture archive.

Repository workflows define the required status checks, but protected-branch rule assignment and hosted macOS/Windows execution are external GitHub state and must be confirmed when the change is published.

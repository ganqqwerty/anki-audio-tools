# Test Anti-Pattern Audit

Reviewed suites:
- `tests/`
- `settings_ui/tests/`
- `e2e/`

Audit standard:
- A good test should fail for a real product regression.
- It should not fail for a harmless refactor.
- Observable behavior beats private implementation details unless the test is explicitly protecting a boundary contract or harness seam.

## Clear Anti-Pattern Findings

### 1. Some Svelte integration tests assert private frontend internals instead of behavior

Files:
- `settings_ui/tests/editor-inline.integration.graph-queue.test.ts:92-107`
- `settings_ui/tests/editor-inline.integration.graph-queue.test.ts:115-136`
- `settings_ui/tests/editor-inline.post-edit-playback.integration.test.ts:154-165`
- `settings_ui/tests/editor-inline.post-edit-playback.integration.test.ts:179-195`
- `settings_ui/tests/editor-inline.post-edit-playback.integration.test.ts:211-223`
- `settings_ui/tests/frontend-architecture.test.ts:56-66`

Category:
- Testing implementation details

Why this is a problem:
- These tests assert `window.__aqePendingGraphRedrawField`, `window.__aqePendingGraphRedrawSource`, and `window.__aqePendingCommandPayload` directly.
- The suite itself classifies those names as internal window state in `settings_ui/tests/frontend-architecture.test.ts:56-66`.
- A harmless refactor that moves pending state out of `window` or renames these fields would fail the tests even if graph replay and post-edit playback still behaved correctly.

What stronger tests would assert instead:
- Graph redraw requests are replayed through the bridge when the right observable conditions occur.
- Busy state, visible graph state, and final post-edit-ready command emission happen in the correct order.
- Rendered graph / playback UI transitions occur without depending on the private storage location of pending state.

### 2. The visualizer layout integration test is locked to exact SVG rendering math

Files:
- `settings_ui/tests/editor-inline.layout.integration.test.ts:61-69`

Category:
- Testing implementation details

Why this is a problem:
- The test asserts exact `path` content, exact clip-rect width, and exact last tick coordinates after resize.
- That is brittle to harmless renderer refactors such as path generation changes, float formatting changes, tick-generation changes, or equivalent SVG structure updates.
- The real behavior worth protecting is “the graph redraws correctly after resize and keeps the cursor aligned,” not the literal serialized path string.

What stronger tests would assert instead:
- The graph redraws after resize.
- Key layers remain present and non-empty.
- Cursor position stays proportionally aligned after width changes.
- The visualizer still spans the resized viewport without asserting exact SVG command strings.

### 3. Two Python tests only prove that a warning API was called, not what the user saw

Files:
- `tests/test_browser_integration_hooks.py:41-46`
- `tests/test_runtime_installer_dialog.py:133-141`
- Relevant product code: `addon/anki_audio_quick_editor/browser_integration.py:51-63`
- Relevant product code: `addon/anki_audio_quick_editor/runtime_installer_dialog.py:85`

Category:
- Assertion-only-on-mock-calls

Why this is a problem:
- `test_empty_selection_shows_warning()` passes if any warning is shown, even if the warning text is wrong, blank, or attached to the wrong parent.
- `test_runtime_installer_reject_cancels_and_warns()` passes if any warning dialog fires, even if the cancel warning title/message regresses.
- These are user-visible flows, so asserting only that the mock was called hides real product regressions.

What stronger tests would assert instead:
- Exact warning title/message or translated key outcome.
- Correct `parent` argument where relevant.
- For the runtime installer dialog, the warning content associated with incomplete cancellation, not just that some warning occurred.

### 4. One e2e workflow stages its scenario by mutating private window globals and intercepting `pycmd`

Files:
- `e2e/test_editor_post_edit_playback_workflow.py:61`
- `e2e/test_editor_post_edit_playback_workflow.py:89`
- `e2e/test_editor_post_edit_playback_workflow.py:101-150`
- Internal state reference: `settings_ui/tests/frontend-architecture.test.ts:56-66`

Category:
- Testing implementation details

Why this is a problem:
- `_delay_post_edit_playback_ready_event()` rewires `window.pycmd` and reaches into `window.__aqePendingCommandPayload`.
- `_install_post_edit_ready_probe_with_stale_graph_marker()` mutates `window.__aqePendingGraphRedrawField` and `window.__aqePendingGraphRedrawSource`, which the frontend architecture test explicitly treats as internal state.
- This makes the e2e workflow sensitive to the exact async plumbing implementation rather than the user-visible post-edit playback behavior.

What stronger tests would assert instead:
- Delay or stale-redraw conditions should be staged through a supported test driver seam or backend seam, not by mutating private globals.
- The test should then assert observable outcomes: generated audio playback eventually starts, stale redraw markers do not block it, and user-visible status/log output matches expectations.

## Borderline Smells Worth Discussion

### 1. Several hook-registration tests only assert append counts, not handler identity or effect

Files:
- `tests/test_browser_integration_hooks.py:23-29`
- `tests/test_editor_integration.py:28-34`
- `tests/test_reviewer_integration.py:112-129`

Category:
- Assertion-only-on-mock-calls

Why this is only a smell:
- These are boundary tests, so asserting registration is legitimate.
- The weakness is that `.append.assert_called_once()` does not prove the right callable was registered or that it produces the right behavior when invoked.
- A wrong callback could still satisfy the current assertions.

Stronger version:
- Assert the registered callable identity where stable.
- Or capture the appended callback and invoke it against a small fake to prove the registration actually wires the intended behavior.

### 2. The inline-editor integration layer often prefers test-contract state over visible DOM behavior

Representative files:
- `settings_ui/tests/editor-inline.cursor-selection-playback.integration.test.ts:38-52`
- `settings_ui/tests/editor-inline.selection-playback.integration.test.ts:52-60`
- `settings_ui/tests/editor-inline.selection-playback.integration.test.ts:76-81`
- `settings_ui/tests/editor-inline.playback.integration.test.ts:185-201`
- Repo guidance: `TESTING.md:245`

Category:
- Borderline implementation-detail reliance

Why this is only a smell:
- The repo explicitly documents the `window.__aqe*` contract as a legitimate middle integration layer, so this is not a blanket bug.
- The risk is overuse: when most of a test’s confidence comes from `__aqeGraphStateForTest`, `__aqeGetPlaybackRequest`, or `__aqeGetCursorIntent`, the test can end up confirming the test contract more than the visible editor behavior.

Stronger version:
- Keep the test-contract helpers for hard-to-drive graph behavior.
- Add more assertions on button labels, disabled states, status text, visible toolbar state, and rendered selection/playback affordances where feasible.

### 3. The e2e editor helpers synthesize large internal state objects from DOM datasets and test-only hooks

Files:
- `e2e/editor_graph_helpers.py:10-88`
- `e2e/editor_graph_helpers.py:104-123`
- `e2e/test_editor_region_loop_workflow.py:35-118`
- `e2e/test_editor_playback_resume_behavior.py:62-77`

Category:
- Borderline implementation-detail reliance

Why this is only a smell:
- For Anki webview e2e, some JS-side state inspection is practical and likely unavoidable.
- The downside is that `_visualizer_js()` reconstructs a wide internal state object from datasets, labels, and DOM fragments. Many tests then predicate on that synthetic object instead of narrower user-visible outcomes.
- This can make e2e failures track DOM/data-attribute churn more than workflow regressions.

Stronger version:
- Keep the helper for complex graph workflows.
- Narrow each test to the minimum state needed, and prefer visible status/buttons/generated files/fake playback intervals over broad synthetic state bundles when possible.

## Justified Exceptions / Acceptable Patterns

### 1. Bridge and trusted-URL contract tests are appropriately specific

Files:
- `settings_ui/tests/bridge.test.ts:97-191`
- `settings_ui/tests/error-message.test.ts:34-49`
- `tests/test_editor_external_links.py:31-60`

Why these are acceptable:
- Here the serialized bridge payload or trusted external URL check is the product contract.
- Asserting the exact command envelope or URL handoff is appropriate because the observable behavior is the message sent across the boundary.

### 2. Shared Qt polling sleeps are harness support, not scenario-level fixed waits

Files:
- `e2e/helpers.py:16-18`
- `e2e/conftest.py:118-126`
- `e2e/race_helpers.py:62-69`

Why these are acceptable:
- These `time.sleep(...)` calls live inside event-loop polling helpers, not inside scenario assertions.
- I did not find Playwright-style `waitForTimeout` usage or raw sleep-based scenario sequencing in the browser-facing tests themselves.

### 3. Stable `data-testid` usage in frontend and e2e tests is intentional in this repo

Files:
- `WEBVIEW_AND_TEMPLATES.md` documents stable `data-testid` use for controls that e2e must click.

Why this is acceptable:
- I did not treat `data-testid` or `document.querySelector(...)` as findings on their own.
- For SVG/Anki webview interaction, these selectors are often the most practical stable seam.

### 4. I did not find some common low-value patterns

Non-findings:
- No snapshot-only tests found in `settings_ui/tests/`.
- No `waitForTimeout` usage found in `e2e/`.
- No explicit test-order markers such as `pytest.mark.order` found.
- No obvious dependency-style test chaining found.

## Bottom Line

The suite is generally more disciplined than the raw mock volume suggests. The highest-risk issues are concentrated in two places:
- tests that assert explicitly internal frontend window state
- tests that only prove a warning/mock side effect happened without checking the user-visible content

The inline-editor and Anki e2e layers do have repo-specific reasons to use test contracts and DOM probes. Those patterns should be tightened, not removed wholesale.

# E2E Test Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move non-UI checks out of `e2e/`, replace direct internal e2e calls with real UI workflows where practical, and prevent accidental real audio playback during e2e.

**Architecture:** Keep e2e for real Anki and WebView workflows. Keep processor, runtime, hook-registration, and algorithm contracts in `tests/`, using `pytest.mark.allow_managed_runtime` only for real external-binary smoke tests. Add Browser workflow helpers so Browser batch/export tests open the real Browser, select real rows, and drive the add-on menu/dialog UI.

**Tech Stack:** Python 3.13, pytest, real Anki `aqt`, PyQt6, Svelte WebView bundles, managed ffmpeg/ffprobe/DPDFNet runtime, `scripts/dev.py`.

---

## File Structure

- Create `e2e/browser_workflow_helpers.py`: Browser opening, row selection, menu action triggering, non-blocking dialog exec patch, batch/export WebView helpers.
- Create `e2e/test_browser_batch_workflow.py`: full Browser row-selection to batch reduce-size workflow.
- Modify `e2e/test_browser_audio_export_workflow.py`: open export from real Browser menu and click WebView controls; mock only the OS save-file dialog.
- Create `e2e/test_editor_convert_workflow.py`: true UI smoke test for editor Convert.
- Modify `e2e/test_audio_processing_ffmpeg.py`: remove after migrating its cases.
- Modify existing unit/integration files under `tests/`: move real-binary contract tests into focused audio/runtime modules.
- Modify selected e2e files to remove `writeConfig` spies, redundant `SESSIONS` assertions, and direct bridge calls where a UI path exists.
- Modify `e2e/conftest.py` and `e2e/editor_playback_helpers.py`: add native playback leak guard and explicit fake-playback allow flag.
- Modify `E2E_TESTING.md`: document what belongs in e2e and which fakes are intentional.

## Task 1: Add Real Browser Workflow Helpers

**Files:**
- Create: `e2e/browser_workflow_helpers.py`
- Test: `e2e/test_browser_batch_workflow.py`

- [ ] **Step 1: Add helper module**

Create `e2e/browser_workflow_helpers.py` with these responsibilities:

```python
"""Helpers for real Anki Browser E2E workflows."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

import aqt
from anki.collection import SearchNode
from PyQt6.QtWidgets import QApplication

from e2e.helpers import click_selector, wait_for_condition, wait_for_js_condition


def open_browser_for_note(anki_mw: Any, note: Any) -> Any:
    browser = aqt.dialogs.open("Browser", anki_mw, search=(SearchNode(nid=int(note.id)),))
    wait_for_condition(
        lambda: browser.isVisible() and browser.table.len() >= 1,
        timeout=10.0,
        message="Browser did not open with the target note search",
    )
    return browser


def select_browser_note_row(browser: Any, note_id: int) -> None:
    card_ids = browser.col.get_note(note_id).card_ids()
    assert card_ids, "Browser workflow fixture note must have at least one card"
    browser.table.select_single_card(card_ids[0])
    QApplication.processEvents()
    wait_for_condition(
        lambda: int(note_id) in [int(value) for value in browser.selected_notes()],
        timeout=5.0,
        message="Browser row selection did not select the expected note",
    )


def trigger_cards_menu_action(browser: Any, label: str) -> None:
    action = next(
        (action for action in browser.form.menu_Cards.actions() if action.text() == label),
        None,
    )
    labels = [action.text() for action in browser.form.menu_Cards.actions()]
    assert action is not None, f"Cards menu action {label!r} not found; saw {labels!r}"
    action.trigger()
    QApplication.processEvents()


@contextmanager
def non_blocking_dialog_exec(dialog_class: type[Any]) -> Iterator[list[Any]]:
    opened: list[Any] = []
    original_exec = dialog_class.exec

    def fake_exec(self: Any) -> int:
        opened.append(self)
        self._dialog.show()
        QApplication.processEvents()
        return 0

    dialog_class.exec = fake_exec
    try:
        yield opened
    finally:
        dialog_class.exec = original_exec
        for dialog in opened:
            if getattr(dialog, "_running", False):
                dialog.cancel_event.set()
            dialog._dialog.close()


def wait_for_batch_dialog_ready(dialog: Any) -> None:
    wait_for_js_condition(
        dialog._webview,
        "Boolean(document.querySelector('[data-testid=\"batch-operation\"]'))",
        lambda value: value is True,
        timeout=10.0,
    )


def select_batch_operation(dialog: Any, operation: str) -> None:
    wait_for_js_condition(
        dialog._webview,
        f"""
        (() => {{
          const operation = document.querySelector('[data-testid="batch-operation"]');
          if (!operation) return false;
          operation.value = {operation!r};
          operation.dispatchEvent(new Event('change', {{ bubbles: true }}));
          return operation.value;
        }})()
        """,
        lambda value: value == operation,
        timeout=5.0,
    )


def click_batch_start(dialog: Any) -> None:
    click_selector(dialog._webview, '[data-testid="batch-start"]', timeout=5.0)


def wait_for_dialog_finished(dialog: Any, *, timeout: float = 30.0) -> None:
    wait_for_condition(
        lambda: getattr(dialog, "_finished", False) is True,
        timeout=timeout,
        message=f"Dialog did not finish; log={getattr(dialog, '_log_lines', [])!r}",
    )
```

- [ ] **Step 2: Run targeted e2e import check**

Run:

```bash
python3 -m pytest e2e/test_browser_batch_size_reduction_workflow.py --collect-only -q
```

Expected: collection succeeds. The new helper module imports under the real Anki e2e Python environment.

- [ ] **Step 3: Commit helper foundation**

```bash
git add e2e/browser_workflow_helpers.py
git commit -m "test: add Browser workflow e2e helpers" -m "Browser batch and export coverage needs to drive real row selection and menu actions. These helpers isolate the Qt harness details so later tests can stop calling batch/export internals directly."
```

If full checks have not been run, add this sentence to the commit body:

```text
Full check and e2e routines were not run for this helper-only checkpoint.
```

## Task 2: Replace Direct Browser Batch Size Test With Real Browser E2E

**Files:**
- Create: `e2e/test_browser_batch_workflow.py`
- Delete: `e2e/test_browser_batch_size_reduction_workflow.py`
- Use: `e2e/browser_workflow_helpers.py`

- [ ] **Step 1: Write the real Browser batch workflow**

Create `e2e/test_browser_batch_workflow.py`:

```python
"""E2E tests for Browser batch operations through the real Browser UI."""

from __future__ import annotations

from pathlib import Path

from e2e.browser_workflow_helpers import (
    click_batch_start,
    non_blocking_dialog_exec,
    open_browser_for_note,
    select_batch_operation,
    select_browser_note_row,
    trigger_cards_menu_action,
    wait_for_batch_dialog_ready,
    wait_for_dialog_finished,
)
from e2e.editor_audio_generation_helpers import _generate_high_bitrate_mp3
from e2e.editor_note_helpers import _basic_audio_note, _configure_ffmpeg, _sound_filename
from e2e.helpers import click_selector, wait_for_js_condition


def test_browser_batch_reduce_size_renders_smaller_mp3_from_selected_row(
    anki_mw,
    ffmpeg_config,
) -> None:
    browser_dialog = __import__("1000000002.browser_dialog", fromlist=["BatchOperationsDialog"])
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "browser_batch_size_reduce_source.mp3"
    _generate_high_bitrate_mp3(ffmpeg_config, source)
    original_bytes = source.read_bytes()
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, size_reduction_mode="normal")

    browser = open_browser_for_note(anki_mw, note)
    select_browser_note_row(browser, int(note.id))

    with non_blocking_dialog_exec(browser_dialog.BatchOperationsDialog) as opened:
        trigger_cards_menu_action(browser, "Run Audio Batch Operation...")
        assert len(opened) == 1
        dialog = opened[0]
        wait_for_batch_dialog_ready(dialog)
        select_batch_operation(dialog, "reduce_size")
        click_selector(
            dialog._webview,
            '[data-testid="batch-size-reduction-mode-aggressive"]',
            timeout=5.0,
        )
        wait_for_js_condition(
            dialog._webview,
            "document.querySelector('[data-testid=\"batch-size-reduction-mode-aggressive\"]')?.getAttribute('aria-checked')",
            lambda value: value == "true",
            timeout=5.0,
        )
        click_batch_start(dialog)
        wait_for_dialog_finished(dialog, timeout=30.0)

    reloaded = anki_mw.col.get_note(int(note.id))
    generated_name = _sound_filename(reloaded["Front"])
    generated_path = media_dir / generated_name

    assert generated_name != source.name
    assert generated_name.endswith(".mp3")
    assert generated_path.is_file()
    assert generated_path.stat().st_size < len(original_bytes)
    assert source.read_bytes() == original_bytes
```

- [ ] **Step 2: Delete the direct processor e2e file**

Delete `e2e/test_browser_batch_size_reduction_workflow.py`. Its processor behavior is already covered by `tests/test_batch_conversion.py::test_process_note_batch_operation_reduces_audio_size_to_mp3`; the new e2e covers Browser selection/menu/dialog/runner/writes.

- [ ] **Step 3: Run targeted e2e**

Run:

```bash
python3 scripts/dev.py test-e2e -- e2e/test_browser_batch_workflow.py
```

Expected: the test passes and no direct call to `process_note_batch_operation()` remains in `e2e/`.

- [ ] **Step 4: Commit Browser batch replacement**

```bash
git add e2e/browser_workflow_helpers.py e2e/test_browser_batch_workflow.py e2e/test_browser_batch_size_reduction_workflow.py
git commit -m "test: cover Browser batch compression through UI" -m "The old e2e test called the batch processor directly, so it missed Browser selection, menu wiring, dialog state, and result application. The replacement selects a real Browser row and drives the batch dialog while keeping the media processing real."
```

## Task 3: Convert Browser Audio Export E2E To Real Browser Menu Flow

**Files:**
- Modify: `e2e/test_browser_audio_export_workflow.py`
- Use: `e2e/browser_workflow_helpers.py`

- [ ] **Step 1: Replace direct `AudioExportDialog(...)` construction**

In `e2e/test_browser_audio_export_workflow.py`, replace `_run_export_dialog(...)` with a helper that:

1. Opens the real Browser with `open_browser_for_note(anki_mw, note)`.
2. Selects the note row with `select_browser_note_row(browser, int(note.id))`.
3. Patches `QFileDialog.getSaveFileName` to return the destination path.
4. Uses `non_blocking_dialog_exec(AudioExportDialog)` around `trigger_cards_menu_action(browser, "Export Audio...")`.
5. Clicks the dialog's visible destination button.
6. Clicks `batch-start`.
7. Waits for `_finished`.

Use this code shape:

```python
def _run_export_dialog_from_browser(anki_mw, note, output: Path, *, mode: str, silence_seconds: float = 1.0):
    export_dialog_module = import_runtime_addon_module(".browser_audio_export_dialog")
    from aqt.qt import QFileDialog

    browser = open_browser_for_note(anki_mw, note)
    select_browser_note_row(browser, int(note.id))

    original_get_save_file_name = QFileDialog.getSaveFileName
    QFileDialog.getSaveFileName = lambda *_args, **_kwargs: (str(output), "")
    try:
        with non_blocking_dialog_exec(export_dialog_module.AudioExportDialog) as opened:
            trigger_cards_menu_action(browser, "Export Audio...")
            assert len(opened) == 1
            dialog = opened[0]
            wait_for_js_condition(
                dialog._webview,
                "Boolean(document.querySelector('[data-testid=\"audio-export-controls\"]'))",
                lambda value: value is True,
                timeout=10.0,
            )
            if mode == "combined_mp3":
                wait_for_js_condition(
                    dialog._webview,
                    """
                    (() => {
                      const radios = Array.from(document.querySelectorAll('input[type="radio"]'));
                      const radio = radios.find((node) => node.value === 'combined_mp3');
                      if (!radio) return false;
                      radio.click();
                      return radio.checked;
                    })()
                    """,
                    lambda value: value is True,
                    timeout=5.0,
                )
                wait_for_js_condition(
                    dialog._webview,
                    f"""
                    (() => {{
                      const input = document.querySelector('[data-testid="audio-export-silence"]');
                      if (!input) return false;
                      input.value = {str(silence_seconds)!r};
                      input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                      input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                      return Number(input.value);
                    }})()
                    """,
                    lambda value: value == silence_seconds,
                    timeout=5.0,
                )
            click_selector(dialog._webview, "button", timeout=5.0)
            wait_for_js_condition(
                dialog._webview,
                "document.querySelector('[data-testid=\"audio-export-destination\"]')?.value",
                lambda value: value == str(output),
                timeout=5.0,
            )
            click_batch_start(dialog)
            wait_for_dialog_finished(dialog, timeout=30.0)
            return dialog
    finally:
        QFileDialog.getSaveFileName = original_get_save_file_name
```

Adjust imports at the top of the file to use the Browser helpers and remove `json` and direct snapshot imports if unused.

- [ ] **Step 2: Keep assertions user-visible**

Keep these assertions:

```python
assert _front_field(anki_mw, int(note.id)) == original_html
```

Keep zip archive name assertions and combined MP3 existence assertions. Do not assert `dialog.snapshots` or other dialog internals.

- [ ] **Step 3: Run targeted e2e**

Run:

```bash
python3 scripts/dev.py test-e2e -- e2e/test_browser_audio_export_workflow.py
```

Expected: both export tests pass with real Browser opening and row selection.

- [ ] **Step 4: Commit Browser export replacement**

```bash
git add e2e/browser_workflow_helpers.py e2e/test_browser_audio_export_workflow.py
git commit -m "test: drive Browser audio export through menu UI" -m "Audio export e2e coverage should verify the user path from selected Browser rows through the export dialog. The file chooser remains a harness boundary, while dialog state, bridge decoding, export runner, and note-field preservation stay real."
```

## Task 4: Migrate `test_audio_processing_ffmpeg.py` Out Of E2E

**Files:**
- Delete: `e2e/test_audio_processing_ffmpeg.py`
- Modify: `tests/test_audio_rendering.py`
- Modify: `tests/test_audio_rendering_regions.py`
- Modify: `tests/test_audio_rendering_convert.py`
- Modify: `tests/test_audio_pitch_hum_rendering.py`
- Modify: `tests/test_audio_dpdfnet.py`
- Modify: `tests/audio_fixtures.py`

- [ ] **Step 1: Move shared fixture helpers**

Move the following helpers from `e2e/test_audio_processing_ffmpeg.py` into `tests/audio_fixtures.py`:

```python
FORMAT_FIXTURES = (
    ("aac", ("-c:a", "aac", "-f", "adts")),
    ("flac", ("-c:a", "flac")),
    ("m4a", ("-c:a", "aac", "-f", "mp4")),
    ("mp3", ("-c:a", "libmp3lame")),
    ("oga", ("-ac", "2", "-c:a", "vorbis", "-strict", "-2", "-f", "ogg")),
    ("ogg", ("-ac", "2", "-c:a", "vorbis", "-strict", "-2", "-f", "ogg")),
    ("opus", ("-ar", "48000", "-c:a", "opus", "-strict", "-2", "-f", "opus")),
    ("wav", ("-c:a", "pcm_s16le")),
    ("webm", ("-ar", "48000", "-c:a", "opus", "-strict", "-2", "-f", "webm")),
)
```

Also move `_generate_audio_fixture`, `_write_voiced_silence_voiced_wav`, `_write_rich_pitch_wav`, `_decode_mono_pcm`, `_read_wav_pcm`, `_region`, `_region_rms`, `_goertzel_power`, and `_upper_harmonic_ratio`. Replace e2e `ffmpeg_config` usage with `AudioProcessingConfig()` plus `find_ffmpeg(...)` from `anki_audio_quick_editor.audio_processor`.

- [ ] **Step 2: Add real render smoke tests to `tests/test_audio_rendering_regions.py`**

Add migrated tests:

```python
@pytest.mark.allow_managed_runtime
def test_render_audio_trim_left_renders_shorter_recording(tmp_path: Path) -> None:
    source = tmp_path / "sentence with spaces.wav"
    output = tmp_path / "trimmed.mp3"
    _run_ffmpeg("-f", "lavfi", "-i", "sine=frequency=440:duration=2.0", str(source))

    original_duration_ms = probe_duration_ms(source, AudioProcessingConfig())
    render_audio(
        source,
        AudioEditState(source_file=source.name, left_trim_ms=500),
        AudioProcessingConfig(),
        output_path=output,
    )
    trimmed_duration_ms = probe_duration_ms(output, AudioProcessingConfig())

    assert 1900 <= original_duration_ms <= 2100
    assert 1350 <= trimmed_duration_ms <= 1650
    assert trimmed_duration_ms < original_duration_ms - 350
```

Do not add a separate UI e2e for `left_trim_ms`; there is no direct toolbar command for that exact state. Region delete/keep e2e already covers user-facing trimming.

- [ ] **Step 3: Keep speed and volume as unit/integration only**

Do not add new e2e for speed or volume. Existing `e2e/test_editor_processing_workflow.py::test_each_processing_button_updates_field_to_new_real_audio` drives those toolbar buttons. Keep exact ffmpeg command/filter checks in `tests/test_audio_rendering.py`.

- [ ] **Step 4: Move common input format rendering into `tests/test_audio_rendering_convert.py` or a new `tests/test_audio_rendering_real_formats.py`**

Add a parametrized real-binary test marked `allow_managed_runtime`:

```python
@pytest.mark.parametrize(("extension", "output_args"), FORMAT_FIXTURES)
@pytest.mark.allow_managed_runtime
def test_common_audio_input_format_renders_to_mp3(extension: str, output_args: tuple[str, ...], tmp_path: Path) -> None:
    source = tmp_path / f"common-input.{extension}"
    output = tmp_path / f"rendered-{extension}.mp3"
    _generate_audio_fixture(source, output_args)

    result = render_audio(
        source,
        AudioEditState(source_file=source.name, volume_db=-1.0),
        AudioProcessingConfig(),
        output_path=output,
    )

    assert output.is_file()
    assert result.output_path == output
    assert result.output_path.suffix == ".mp3"
    assert "libmp3lame" in result.command
    assert probe_duration_ms(output, AudioProcessingConfig()) > 0
```

- [ ] **Step 5: Move pitch-hum quality checks to `tests/test_audio_pitch_hum_rendering.py`**

Add both migrated pitch-hum tests with `pytest.mark.allow_managed_runtime`. Keep `importlib.import_module("parselmouth")`; let missing dependency fail because dependency skips are forbidden by `tests/test_dependency_skips.py`.

- [ ] **Step 6: Move DPDFNet managed runtime rendering to `tests/test_audio_dpdfnet.py`**

Add migrated DPDFNet test with `pytest.mark.allow_managed_runtime`:

```python
@pytest.mark.allow_managed_runtime
def test_dpdfnet_renders_from_locked_source_release_asset(tmp_path: Path) -> None:
    platform_key = current_platform_key()
    assert platform_key is not None
    dpdfnet_path = find_dpdfnet_bundle()
    assert dpdfnet_path.name == runtime_platform.tool_executable_name("dpdfnet", platform_key)
    assert platform_key in dpdfnet_path.parts
    assert tool_source_label(dpdfnet_path) == "managed"

    source = tmp_path / "dpdfnet-source.wav"
    output = tmp_path / "dpdfnet-rendered.mp3"
    _run_ffmpeg("-f", "lavfi", "-i", "sine=frequency=440:duration=0.8", str(source))

    result = render_dpdfnet_audio(source, AudioProcessingConfig(), output_path=output)

    assert result.output_path == output
    assert result.command[:2] == (str(dpdfnet_path), "enhance")
    assert output.is_file()
    assert output.suffix == ".mp3"
    assert probe_duration_ms(output, AudioProcessingConfig()) > 0
```

- [ ] **Step 7: Delete old e2e file and run targeted tests**

Run:

```bash
python3 scripts/dev.py test -- tests/test_audio_rendering.py tests/test_audio_rendering_regions.py tests/test_audio_rendering_convert.py tests/test_audio_pitch_hum_rendering.py tests/test_audio_dpdfnet.py
python3 scripts/dev.py test-e2e -- --collect-only e2e
```

Expected: unit/integration tests pass; e2e collection no longer includes `test_audio_processing_ffmpeg.py`.

- [ ] **Step 8: Commit audio migration**

```bash
git add tests/audio_fixtures.py tests/test_audio_rendering.py tests/test_audio_rendering_regions.py tests/test_audio_rendering_convert.py tests/test_audio_pitch_hum_rendering.py tests/test_audio_dpdfnet.py e2e/test_audio_processing_ffmpeg.py
git commit -m "test: move audio processor contracts out of e2e" -m "The migrated tests verify real ffmpeg, pitch-hum, and DPDFNet behavior without pretending to exercise user workflows. E2E remains focused on toolbar and Browser UI paths, while exact processor contracts live in faster targeted tests."
```

## Task 5: Add Editor Convert UI Smoke Test

**Files:**
- Create: `e2e/test_editor_convert_workflow.py`

- [ ] **Step 1: Add UI convert test**

Create `e2e/test_editor_convert_workflow.py`:

```python
"""E2E tests for editor audio conversion through the toolbar."""

from __future__ import annotations

from pathlib import Path

from e2e.editor_note_helpers import (
    _basic_audio_note,
    _button_selector,
    _configure_ffmpeg,
    _open_editor,
    _wait_for_generated_mp3,
    _wait_for_status_flow,
)
from e2e.helpers import click_selector, generate_tone, wait_for_selector


def test_convert_button_renders_mp3_and_preserves_original_media(anki_mw, ffmpeg_config) -> None:
    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_convert_source.wav"
    generate_tone(ffmpeg_config, source, duration_s=1.0)
    original_bytes = source.read_bytes()
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config, output_format="mp3")

    editor, parent = _open_editor(anki_mw, note)
    try:
        wait_for_selector(editor.web, _button_selector("aqe:convert"), timeout=10.0)
        click_selector(editor.web, _button_selector("aqe:convert"), timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, source.name)
        status = _wait_for_status_flow(
            editor,
            lambda value: value["text"] == "Converted audio to MP3.",
            timeout=10.0,
        )

        generated_path = media_dir / generated_name
        assert status["text"] == "Converted audio to MP3."
        assert generated_name.endswith(".mp3")
        assert generated_path.is_file()
        assert source.read_bytes() == original_bytes
    finally:
        editor.set_note(None)
        parent.close()
```

If the actual status text differs, read `addon/anki_audio_quick_editor/locales/en.json` for `editor.status.operation.convert` and update only the assertion text.

- [ ] **Step 2: Run targeted e2e**

```bash
python3 scripts/dev.py test-e2e -- e2e/test_editor_convert_workflow.py
```

Expected: test passes and proves the `aqe:convert` toolbar command reaches real ffmpeg through UI.

- [ ] **Step 3: Commit convert UI coverage**

```bash
git add e2e/test_editor_convert_workflow.py
git commit -m "test: cover editor convert through toolbar UI" -m "Convert had bridge and renderer tests but no real Anki editor workflow. This e2e check verifies the visible command, real rendering, field replacement, and non-destructive media behavior."
```

## Task 6: Remove Unnecessary Spies And White-Box E2E Assertions

**Files:**
- Modify: `e2e/test_settings_save_flows.py`
- Modify: `e2e/test_editor_graph_workflow.py`
- Modify: `e2e/test_editor_integration.py`
- Modify: `e2e/test_dpdfnet_attenuation_integration.py`
- Modify: `e2e/test_settings_dialog_shell.py`
- Modify: `e2e/test_editor_playback_workflow.py`
- Modify: `e2e/test_editor_processing_split_buttons_workflow.py`
- Modify: `e2e/test_editor_processing_split_buttons_parameter_workflow.py`
- Modify: `e2e/test_editor_processing_busy_workflow.py`

- [ ] **Step 1: Replace `writeConfig` spies**

For each save-flow test, replace this pattern:

```python
with patch.object(anki_mw.addonManager, "writeConfig", wraps=anki_mw.addonManager.writeConfig) as mock_write:
    click_selector(dialog, save_selector, timeout=5.0)
    wait_for_condition(lambda: mock_write.called, timeout=5.0)

saved_config = mock_write.call_args.args[1]
```

with:

```python
click_selector(dialog, save_selector, timeout=5.0)
wait_for_condition(
    lambda: not dialog.isVisible(),
    timeout=5.0,
    message="Timed out waiting for settings dialog to close after save",
)
saved_config = anki_mw.addonManager.getConfig("1000000002") or {}
```

Use `ADDON_NUMERIC_ID` where the file already imports it.

- [ ] **Step 2: Delete duplicate settings initial-state e2e tests**

Remove these two tests from `e2e/test_settings_dialog_shell.py`:

```python
test_initial_state_is_embedded
test_initial_state_shape
```

Also remove now-unused imports `json` and `import_runtime_addon_module` from that file.

- [ ] **Step 3: Delete e2e hook registry assertion**

Remove `test_editor_hooks_are_registered` from `e2e/test_editor_integration.py`. Keep `tests/test_editor_integration.py::test_register_editor_hooks` as the boundary test and keep editor visible-control e2e tests as behavior coverage.

- [ ] **Step 4: Remove redundant `SESSIONS` assertions**

In `e2e/test_editor_playback_workflow.py::test_cursor_drag_updates_session_and_play_uses_html_audio`, delete the `SESSIONS` import and the `wait_for_condition(...)` that directly inspects `session.cursor_ms`. Keep `_wait_for_visualizer_track(... cursorMs >= 1000)` because it observes DOM state.

In split-button tests, replace session-state assertions with existing generated-file/status/duration/config assertions. Examples:

```python
assert (media_dir / generated_name).is_file()
```

and:

```python
assert probe_duration_ms(media_dir / slower_name, ffmpeg_config) > probe_duration_ms(media_dir / volume_name, ffmpeg_config)
assert probe_duration_ms(media_dir / speed_name, ffmpeg_config) < probe_duration_ms(media_dir / slower_name, ffmpeg_config)
```

Do not add a new public test-only endpoint just to observe `EditorSession`.

- [ ] **Step 5: Replace direct bridge undo test or move it**

For `e2e/test_editor_processing_busy_workflow.py::test_still_processing_status_is_replaced_after_mid_render_undo_request`:

1. Try replacing `editor.onBridgeCmd("aqe:undo")` with:

```python
click_selector(editor.web, _button_selector("aqe:undo"), timeout=5.0)
```

2. If the button is disabled during processing and cannot be clicked, move the assertion to a unit test in `tests/test_editor_processing_guard.py` that calls the command handler directly against a fake busy editor. Then delete this e2e test, because a disabled button means the scenario is not user-reachable.

- [ ] **Step 6: Replace direct blur command**

In `e2e/test_editor_graph_workflow.py::test_manual_graph_after_clearing_default_graph_field_shows_error_without_analyzing`, first rely on the existing DOM `field.blur()` and wait for `note.fields[0]` to clear. Delete:

```python
editor.onBridgeCmd(f"blur:0:{note.id}:")
```

If the note does not update from the DOM blur, use Anki's editor save/lifecycle path available on the editor object rather than calling the bridge handler. Keep the final assertion on visible error/status.

- [ ] **Step 7: Run targeted tests**

```bash
python3 scripts/dev.py test-e2e -- e2e/test_settings_save_flows.py e2e/test_settings_dialog_shell.py e2e/test_editor_graph_workflow.py e2e/test_editor_integration.py e2e/test_editor_playback_workflow.py e2e/test_editor_processing_split_buttons_workflow.py e2e/test_editor_processing_split_buttons_parameter_workflow.py e2e/test_editor_processing_busy_workflow.py e2e/test_dpdfnet_attenuation_integration.py
```

Expected: all targeted tests pass. `rg "writeConfig|SESSIONS|get\\(editor\\)|onBridgeCmd|_render_settings_html|build_initial_state" e2e -g '*.py'` shows only setup writes and justified lifecycle cases.

- [ ] **Step 8: Commit white-box cleanup**

```bash
git add e2e/test_settings_save_flows.py e2e/test_editor_graph_workflow.py e2e/test_editor_integration.py e2e/test_dpdfnet_attenuation_integration.py e2e/test_settings_dialog_shell.py e2e/test_editor_playback_workflow.py e2e/test_editor_processing_split_buttons_workflow.py e2e/test_editor_processing_split_buttons_parameter_workflow.py e2e/test_editor_processing_busy_workflow.py tests/test_editor_processing_guard.py
git commit -m "test: remove white-box assertions from e2e flows" -m "E2E should fail on user-visible regressions, not on harmless internal refactors. These changes replace config spies, session peeks, hook registry checks, and direct bridge calls with saved config, DOM state, generated media, and focused unit coverage."
```

## Task 7: Improve Reviewer E2E Lifecycle Where UI Paths Exist

**Files:**
- Modify: `e2e/test_reviewer_audio_editor_workflow.py`
- Modify: `e2e/test_reviewer_audio_editor_workflow_answer_actions.py`
- Modify: `e2e/test_reviewer_audio_editor_workflow_template_filters.py`

- [ ] **Step 1: Open reviewer through normal review state without private web init**

In `_open_reviewer_for_note`, keep deck selection and `moveToState("review")`, but remove direct calls to:

```python
reviewer._initWeb()
reviewer._showQuestion()
```

Wait for `reviewer.card` to become the created note's card. If Anki loads a different card, ensure the fixture deck contains only the target card before review state starts.

- [ ] **Step 2: Show answer through reviewer WebView command**

Replace `_show_answer(reviewer)` implementation with a UI command:

```python
def _show_answer(reviewer) -> None:
    run_js(reviewer.web, "pycmd('ans')")
    wait_for_condition(
        lambda: reviewer.state == "answer",
        timeout=5.0,
        message="Reviewer did not reveal the answer",
    )
```

If Anki 25.09 uses a different bridge command for the answer button, confirm from installed `aqt/reviewer.py` and use the public WebView command emitted by the actual Show Answer button.

- [ ] **Step 3: Cleanup by answering or moving state, not firing hooks**

Replace direct `gui_hooks.reviewer_did_answer_card(...)` in `_cleanup_reviewer_session` with a UI answer command when the reviewer is in answer state:

```python
if getattr(reviewer, "state", "") == "answer":
    run_js(reviewer.web, "pycmd('ease3')")
    wait_for_condition(
        lambda: reviewer.mw.state in {"review", "deckBrowser"},
        timeout=5.0,
        message="Reviewer did not accept the answer during cleanup",
    )
reviewer.mw.moveToState("deckBrowser")
```

- [ ] **Step 4: Replace direct reviewer side-refresh call**

In answer-action tests, replace direct `_on_reviewer_did_show_card_side(reviewer.card)` with a user-reachable action:

1. Toggle the setting via config setup.
2. Move away from the card side and back using reviewer UI commands where possible.
3. If no user path exists for this exact refresh, move the direct hook invocation assertion to `tests/test_reviewer_integration_visibility.py`.

- [ ] **Step 5: Run reviewer e2e**

```bash
python3 scripts/dev.py test-e2e -- e2e/test_reviewer_audio_editor_workflow.py e2e/test_reviewer_audio_editor_workflow_answer_actions.py e2e/test_reviewer_audio_editor_workflow_template_filters.py
```

Expected: reviewer tests pass without `_initWeb`, `_showQuestion`, `_showAnswer`, or direct `reviewer_did_answer_card` calls in e2e helpers.

- [ ] **Step 6: Commit reviewer lifecycle cleanup**

```bash
git add e2e/test_reviewer_audio_editor_workflow.py e2e/test_reviewer_audio_editor_workflow_answer_actions.py e2e/test_reviewer_audio_editor_workflow_template_filters.py tests/test_reviewer_integration_visibility.py
git commit -m "test: drive reviewer e2e through review UI" -m "Reviewer e2e coverage should exercise Anki's visible question, answer, and cleanup flow. Private reviewer methods remain covered by focused integration tests only where no user command exists."
```

## Task 8: Add Playback Leak Guards

**Files:**
- Modify: `e2e/conftest.py`
- Modify: `e2e/editor_playback_helpers.py`
- Modify: HTML playback e2e files that call `_wait_for_html_playback`

- [ ] **Step 1: Add native playback allow flag**

In `e2e/editor_playback_helpers.py`, add:

```python
_FAKE_PLAYBACK_ACTIVE = 0


def fake_playback_active() -> bool:
    return _FAKE_PLAYBACK_ACTIVE > 0
```

Update `_record_fake_playback(...)` to increment/decrement this flag:

```python
global _FAKE_PLAYBACK_ACTIVE
_FAKE_PLAYBACK_ACTIVE += 1
try:
    with (...):
        yield recorder
finally:
    _FAKE_PLAYBACK_ACTIVE -= 1
```

- [ ] **Step 2: Add autouse native playback guard**

In `e2e/conftest.py`, add a function-scoped autouse fixture:

```python
@pytest.fixture(autouse=True)
def _fail_on_unfaked_native_playback(monkeypatch):
    from aqt.sound import av_player
    from e2e.editor_playback_helpers import fake_playback_active

    original_play_tags = av_player.play_tags
    original_stop = av_player.stop_and_clear_queue

    def guarded_play_tags(tags):
        if not fake_playback_active():
            pytest.fail(f"Real native playback leaked in e2e: {tags!r}")
        return original_play_tags(tags)

    def guarded_stop_and_clear_queue():
        if fake_playback_active():
            return original_stop()
        return None

    monkeypatch.setattr(av_player, "play_tags", guarded_play_tags)
    monkeypatch.setattr(av_player, "stop_and_clear_queue", guarded_stop_and_clear_queue)
```

If this conflicts with `_record_fake_playback` patch ordering, keep the same policy but implement it as an allow-list wrapper in `_record_fake_playback` and a fixture that patches only tests not inside the context.

- [ ] **Step 3: Require HTML playback test driver**

In `e2e/editor_graph_helpers.py::_wait_for_html_playback`, add:

```python
and state["audioPlaybackTestDriver"] is True
```

Then run:

```bash
rg -n "_wait_for_html_playback" e2e -g '*.py'
rg -n "_install_html_audio_test_driver" e2e -g '*.py'
```

For every test that reaches `_wait_for_html_playback`, ensure `_install_html_audio_test_driver(editor, ord_=...)` is called first for the same field ordinal.

- [ ] **Step 4: Run playback-focused e2e**

```bash
python3 scripts/dev.py test-e2e -- e2e/test_editor_playback_workflow.py e2e/test_editor_playback_resume_behavior.py e2e/test_editor_region_loop_graph_repeat_workflow.py e2e/test_editor_region_loop_resume_workflow.py e2e/test_editor_selection_toolbar_workflow.py
```

Expected: tests pass without audible native playback. A deliberately removed `_record_fake_playback` context should fail with "Real native playback leaked in e2e".

- [ ] **Step 5: Commit playback guard**

```bash
git add e2e/conftest.py e2e/editor_playback_helpers.py e2e/editor_graph_helpers.py e2e/test_editor_playback_workflow.py e2e/test_editor_playback_resume_behavior.py e2e/test_editor_region_loop_graph_repeat_workflow.py e2e/test_editor_region_loop_resume_workflow.py e2e/test_editor_selection_toolbar_workflow.py
git commit -m "test: fail e2e on real playback leaks" -m "Playback tests should be observable without speakers. The guard preserves fake native playback and explicit HTML audio drivers while making accidental real audio output fail fast."
```

## Task 9: Reclassify Direct Dialog Race Tests

**Files:**
- Modify or move: `e2e/test_browser_batch_race_workflow.py`
- Modify: `tests/test_browser_dialog.py`

- [ ] **Step 1: Move duplicate-start race behavior to unit dialog tests**

The tests in `e2e/test_browser_batch_race_workflow.py` construct `BatchOperationsDialog` directly and send bridge commands. Move their assertions to `tests/test_browser_dialog.py`, where direct bridge-level behavior is appropriate.

Keep one e2e Browser batch happy-path test from Task 2. Do not keep direct dialog construction in e2e unless the test renders real WebView UI and clicks the visible Start button.

- [ ] **Step 2: Preserve one real-WebView UI race if valuable**

If a race needs Qt WebView rendering, keep a single e2e test that:

1. Opens the batch dialog from the real Browser menu with `non_blocking_dialog_exec`.
2. Selects an operation through the visible select.
3. Double-clicks the visible Start button using `click_selector`.
4. Asserts only one run starts.

The run callback may be a fake only for this race test; document it inline as the behavior under test.

- [ ] **Step 3: Run dialog tests**

```bash
python3 scripts/dev.py test -- tests/test_browser_dialog.py
python3 scripts/dev.py test-e2e -- e2e/test_browser_batch_workflow.py e2e/test_browser_batch_race_workflow.py
```

Expected: unit dialog race coverage passes; e2e does not contain direct bridge command duplicate-start tests unless they are driven through visible controls.

- [ ] **Step 4: Commit dialog race reclassification**

```bash
git add tests/test_browser_dialog.py e2e/test_browser_batch_race_workflow.py
git commit -m "test: reclassify batch dialog race coverage" -m "Duplicate-start behavior is a dialog contract, not a full Browser workflow. Moving most checks to unit tests keeps e2e focused while retaining one rendered-control path if Qt behavior matters."
```

## Task 10: Update Documentation

**Files:**
- Modify: `E2E_TESTING.md`
- Optionally modify: `TESTING.md`

- [ ] **Step 1: Document test classification**

Add a section to `E2E_TESTING.md`:

```markdown
## What Does Not Belong In E2E

Pure calls into audio processors, batch processors, settings state builders, hook-registration functions, or renderer algorithms belong in `tests/`, not `e2e/`. If such tests need managed runtime binaries, mark them with `pytest.mark.allow_managed_runtime` and keep them targeted.

E2E tests may create fixture notes/media/config programmatically, but the operation under test should be driven through the same Anki or WebView controls a user can reach.
```

Add a section for intentional fakes:

```markdown
## Intentional Fakes

Fake native playback, fake microphone recording, upload/network fakes, save-file-dialog selection, and delayed renderers for race tests are allowed harness boundaries. They must make otherwise non-deterministic external systems observable without replacing the product behavior under test.

Native playback is guarded during e2e. Tests that need to observe playback must use the fake playback recorder or the HTML audio test driver.
```

- [ ] **Step 2: Update Browser note**

Replace the existing note that says there is no full Browser selection-to-dialog e2e workflow with the new Browser batch/export coverage.

- [ ] **Step 3: Run doc-adjacent checks**

```bash
python3 scripts/dev.py test -- tests/test_dependency_skips.py tests/test_e2e_parallel_runner.py
```

Expected: tests pass.

- [ ] **Step 4: Commit docs**

```bash
git add E2E_TESTING.md TESTING.md
git commit -m "docs: define e2e boundaries for audio workflows" -m "The suite now separates UI workflows from processor contracts and blocks accidental real playback. The documentation records those boundaries so future tests stay realistic without becoming hardware or network dependent."
```

## Task 11: Final Verification And Cleanup

**Files:**
- All files touched by previous tasks.

- [ ] **Step 1: Search for remaining anti-patterns**

Run:

```bash
rg -n "process_note_batch_operation|BatchOperationsDialog\\(|AudioExportDialog\\(|_render_settings_html|build_initial_state|SESSIONS|get\\(editor\\)|editor\\.onBridgeCmd|_initWeb|_showQuestion|_showAnswer|reviewer_did_answer_card" e2e -g '*.py'
rg -n "patch\\.object\\([^\\n]*writeConfig|wraps=.*writeConfig" e2e -g '*.py'
```

Expected: no matches except justified setup writes, modal shim helper references, or lifecycle cases documented in comments.

- [ ] **Step 2: Run targeted migrated tests**

```bash
python3 scripts/dev.py test -- tests/test_audio_rendering.py tests/test_audio_rendering_regions.py tests/test_audio_rendering_convert.py tests/test_audio_pitch_hum_rendering.py tests/test_audio_dpdfnet.py tests/test_browser_dialog.py tests/test_browser_audio_export_dialog.py tests/test_editor_integration.py tests/test_reviewer_integration.py tests/test_reviewer_integration_visibility.py
```

Expected: all pass.

- [ ] **Step 3: Run targeted e2e tests**

```bash
python3 scripts/dev.py test-e2e -- e2e/test_browser_batch_workflow.py e2e/test_browser_audio_export_workflow.py e2e/test_editor_convert_workflow.py e2e/test_settings_save_flows.py e2e/test_editor_playback_workflow.py e2e/test_reviewer_audio_editor_workflow.py
```

Expected: all pass.

- [ ] **Step 4: Run full e2e and full check**

```bash
python3 scripts/dev.py test-e2e-parallel
python3 scripts/dev.py check
```

Expected: both pass. If `test-e2e-parallel` exposes order sensitivity around Browser windows, close any open Browser/dialog in helper finalizers and rerun the failing target before rerunning the full parallel suite.

- [ ] **Step 5: Final commit**

```bash
git status --short
git add e2e tests E2E_TESTING.md TESTING.md
git commit -m "test: align e2e suite with user workflows" -m "This cleanup moves processor contracts to targeted tests, adds real Browser row-selection coverage, removes e2e assertions on private implementation state, and blocks accidental real playback. The suite now better distinguishes product workflows from lower-level integration contracts."
```

If `python3 scripts/dev.py check` or `python3 scripts/dev.py test-e2e-parallel` was not run before the final commit, add this sentence to the final commit body:

```text
Full check and e2e routines were not run before this commit.
```

## Acceptance Criteria

- `e2e/` no longer contains pure calls to audio processors or batch processors as the primary behavior under test.
- Browser batch size reduction is covered from real Browser row selection through menu action, WebView dialog, real processing, and note update.
- Browser audio export is covered from real Browser row selection through menu action and real export output; only the OS file picker is mocked.
- Editor convert has a real toolbar e2e smoke test.
- Settings save e2e tests assert saved config or visible refresh behavior instead of spying on `writeConfig`.
- E2E playback tests fail on accidental native real playback and require explicit HTML audio drivers for HTML playback assertions.
- Reviewer e2e avoids private reviewer methods wherever a WebView/user command exists.
- Full targeted tests, `test-e2e-parallel`, and `check` pass or any remaining failures are documented with exact failing commands and reasons.

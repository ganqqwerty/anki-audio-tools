# Delete The Rest Button Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a selection-scoped **Delete the rest** graph button that keeps only the selected audio region through the existing non-destructive generated-file workflow.

**Architecture:** Extend the existing region-delete pipeline with an explicit operation discriminator. The frontend reveals a second selection button and sends the same bridge command with `operation: "delete-rest"`; Python reuses the current validation, media replacement, Undo/Redo, and graph redraw path while routing rendering to a new keep-selection ffmpeg plan.

**Tech Stack:** Svelte 5 + TypeScript + Vitest for the inline editor UI, Python 3.13 + pytest for add-on logic, ffmpeg filter-complex rendering, Anki e2e tests through `scripts/dev.py`.

---

## File Structure

- Modify `settings_ui/src/editor-inline/types.ts` to add `RegionDeleteOperation`, add `operation` to `RegionDeleteRequest`, add `aqe:delete-rest` as a UI-only command, and expose delete-rest state in `GraphStateForTest`.
- Modify `settings_ui/src/editor-inline/commands.ts` to add the delete-rest test slug and processing message.
- Modify `settings_ui/src/editor-inline/region-delete-state.ts` to synchronize both selection operation buttons and build operation-specific requests.
- Modify `settings_ui/src/editor-inline/region-delete.ts` to accept an operation argument for button clicks while keeping Backspace mapped to delete-selection.
- Modify `settings_ui/src/editor-inline/EditorControls.svelte` to render the new revealed button beside **Delete Region** and update help text.
- Modify `settings_ui/src/editor-inline/test-contract.ts` to expose delete-rest button state to tests.
- Modify `settings_ui/tests/editor-inline.selection.integration.test.ts` and `settings_ui/tests/editor-inline.integration.test.ts` for frontend behavior coverage.
- Modify `addon/anki_audio_quick_editor/audio_types.py` to add a keep-selection plan type.
- Modify `addon/anki_audio_quick_editor/audio_commands.py` to add `build_region_keep_plan`.
- Modify `addon/anki_audio_quick_editor/audio_rendering.py` and `addon/anki_audio_quick_editor/audio_processor.py` to expose `render_audio_region_kept`.
- Modify `addon/anki_audio_quick_editor/editor_session.py` to carry the selected operation in `RegionDeleteRequest`.
- Modify `addon/anki_audio_quick_editor/editor_region_delete.py` to parse, validate, log, label, and route operations.
- Modify `addon/anki_audio_quick_editor/editor_dependencies.py` to provide the new renderer dependency.
- Modify `tests/test_audio_commands.py`, `tests/test_audio_rendering.py`, and `tests/test_editor_integration.py` for Python unit coverage.
- Modify `e2e/editor_graph_helpers.py` and `e2e/test_editor_region_delete_workflow.py` for end-to-end coverage.

## Task 1: Frontend Button, Request Payload, And Tests

**Files:**
- Modify: `settings_ui/tests/editor-inline.selection.integration.test.ts`
- Modify: `settings_ui/tests/editor-inline.integration.test.ts`
- Modify: `settings_ui/src/editor-inline/types.ts`
- Modify: `settings_ui/src/editor-inline/commands.ts`
- Modify: `settings_ui/src/editor-inline/region-delete-state.ts`
- Modify: `settings_ui/src/editor-inline/region-delete.ts`
- Modify: `settings_ui/src/editor-inline/EditorControls.svelte`
- Modify: `settings_ui/src/editor-inline/test-contract.ts`


Run these MCP calls and record the risk summaries in your work log:

```text
```

Expected: existing frontend tests and e2e helpers are direct consumers; no backend Python symbols are reached by the local TypeScript graph.

- [ ] **Step 2: Write failing frontend selection tests**

In `settings_ui/tests/editor-inline.selection.integration.test.ts`, update the existing valid-selection request expectation to include the current operation:

```ts
expect(window.__aqePopPendingRegionDeleteRequest?.()).toEqual({
  operation: "delete-selection",
  ord: 0,
  sourceFilename: "clip one.mp3",
  selectionStartMs: 200,
  selectionEndMs: 600,
  cursorMs: 200,
  durationMs: 1000,
  trigger: "button",
  playbackActive: false,
});
```

Add this new test after the existing **Delete Region** button test:

```ts
it("shows Delete the rest for valid selections and queues a keep-selection request", () => {
  initializeEditorRuntime({ audioFieldIndices: [0] });
  scan({ audioFieldIndices: [0] });
  window.__aqeSetVisualizer?.(0, track, 250);
  const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
  const button = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-delete-rest"]')!;
  setGraphBounds(svg);

  expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
    regionDeleteRestButtonHidden: true,
  });

  dragGraphSelection(svg, 0.2, 0.6);
  expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
    regionDeleteRestButtonHidden: false,
    regionDeleteRestButtonDisabled: false,
  });

  button.click();

  expect(window.__aqePopPendingRegionDeleteRequest?.()).toEqual({
    operation: "delete-rest",
    ord: 0,
    sourceFilename: "clip one.mp3",
    selectionStartMs: 200,
    selectionEndMs: 600,
    cursorMs: 200,
    durationMs: 1000,
    trigger: "button",
    playbackActive: false,
  });
  expect(bridgeCommands()).toEqual(expect.arrayContaining(["focus:0", "aqe:delete-selection"]));
  expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
    busy: false,
    playbackState: "stopped",
    selectionActive: true,
    allButtonsDisabled: true,
  });
});
```

Update the Backspace test to assert that Backspace still requests `operation: "delete-selection"`:

```ts
expect(window.__aqePopPendingRegionDeleteRequest?.()).toMatchObject({
  operation: "delete-selection",
  ord: 0,
  sourceFilename: "clip one.mp3",
  selectionStartMs: 200,
  selectionEndMs: 600,
  trigger: "backspace",
});
```

Update the whole-clip test to verify both revealed buttons are disabled and no request is queued:

```ts
expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
  selectionActive: true,
  regionDeleteButtonHidden: false,
  regionDeleteButtonDisabled: true,
  regionDeleteRestButtonHidden: false,
  regionDeleteRestButtonDisabled: true,
});
```

In `settings_ui/tests/editor-inline.integration.test.ts`, update the help text assertion to include both actions:

```ts
expect(help).toHaveTextContent("Delete Region removes the selected region; Delete the rest keeps only the selected region.");
```

- [ ] **Step 3: Run frontend tests to confirm they fail**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.selection.integration.test.ts editor-inline.integration.test.ts
```

Expected: FAIL because `aqe-button-0-delete-rest`, `operation`, and `regionDeleteRestButtonHidden` do not exist yet.

- [ ] **Step 4: Update frontend types and command metadata**

In `settings_ui/src/editor-inline/types.ts`, add the command, operation type, request field, and test-state fields:

```ts
export type EditorCommand =
  | "aqe:play"
  | "aqe:analyze"
  | "aqe:show-file"
  | "aqe:delete-selection"
  | "aqe:delete-rest"
  | "aqe:remove-pauses"
  | "aqe:denoise-standard"
  | "aqe:rnnoise"
  | "aqe:slower"
  | "aqe:faster"
  | "aqe:volume-down"
  | "aqe:volume-up"
  | "aqe:undo"
  | "aqe:redo"
  | "aqe:settings";

export type RegionDeleteOperation = "delete-selection" | "delete-rest";

export interface RegionDeleteRequest {
  cursorMs: number;
  durationMs: number;
  operation: RegionDeleteOperation;
  ord: number;
  playbackActive: boolean;
  selectionEndMs: number;
  selectionStartMs: number;
  sourceFilename: string;
  trigger: "button" | "backspace";
}
```

Add these fields to `GraphStateForTest`:

```ts
regionDeleteRestButtonDisabled: boolean;
regionDeleteRestButtonHidden: boolean;
```

In `settings_ui/src/editor-inline/commands.ts`, add slug and processing message support:

```ts
export const COMMAND_SLUGS: Readonly<Record<EditorCommand, string>> = {
  "aqe:play": "play",
  "aqe:analyze": "graph",
  "aqe:show-file": "show-file",
  "aqe:delete-selection": "delete-selection",
  "aqe:delete-rest": "delete-rest",
  "aqe:remove-pauses": "remove-pauses",
  "aqe:denoise-standard": "denoise-standard",
  "aqe:rnnoise": "rnnoise",
  "aqe:slower": "slower",
  "aqe:faster": "faster",
  "aqe:volume-down": "volume-down",
  "aqe:volume-up": "volume-up",
  "aqe:undo": "undo",
  "aqe:redo": "redo",
  "aqe:settings": "settings",
};

export function processingMessage(command: EditorCommand): string {
  if (command === "aqe:denoise-standard") return "Denoising with Standard...";
  if (command === "aqe:rnnoise") return "Denoising with RNNoise...";
  if (command === "aqe:delete-selection") return "Deleting region...";
  if (command === "aqe:delete-rest") return "Deleting rest...";
  return "Processing...";
}
```

- [ ] **Step 5: Update button synchronization and request creation**

Replace `settings_ui/src/editor-inline/region-delete-state.ts` with operation-aware helpers. Keep the imports at the top consistent with the existing file:

```ts
import { allVisualizers, controlsForOrd } from "./dom-selectors.js";
import { logger } from "./logger.js";
import type { PlaybackRegion } from "./playback-state.js";
import { selectionForVisualizer } from "./selection-controller.js";
import type { RegionDeleteOperation, RegionDeleteRequest, VisualizerElement } from "./types.js";
import { isPlaybackState } from "./types.js";

function anyBusy(): boolean {
  return document.body.dataset.aqeBusy === "true";
}

function regionDeleteButtonForOrd(ord: number): HTMLButtonElement | null {
  return controlsForOrd(ord)?.querySelector<HTMLButtonElement>(".aqe-delete-region-button") ?? null;
}

function regionDeleteRestButtonForOrd(ord: number): HTMLButtonElement | null {
  return controlsForOrd(ord)?.querySelector<HTMLButtonElement>(".aqe-delete-rest-button") ?? null;
}

function isWholeSelection(region: PlaybackRegion, durationMs: number): boolean {
  return region.startMs <= 0 && region.endMs >= durationMs;
}

function isValidRegionDeleteSelection(region: PlaybackRegion | null, durationMs: number): boolean {
  return !!region && region.endMs > region.startMs && !isWholeSelection(region, durationMs);
}

function unavailableTitle(operation: RegionDeleteOperation): string {
  return operation === "delete-rest"
    ? "Selection already covers the whole audio clip"
    : "Cannot delete the whole audio clip";
}

function availableTitle(operation: RegionDeleteOperation): string {
  return operation === "delete-rest"
    ? "Delete the rest of the audio"
    : "Delete selected region";
}

function syncRegionDeleteButton(
  button: HTMLButtonElement | null,
  region: PlaybackRegion | null,
  durationMs: number,
  operation: RegionDeleteOperation,
): void {
  if (!button) return;
  const hasSelection = region !== null;
  const valid = isValidRegionDeleteSelection(region, durationMs);
  button.hidden = !hasSelection;
  button.disabled = anyBusy() || !valid;
  button.dataset.aqeButtonState = valid ? "default" : "unavailable";
  button.title = valid ? availableTitle(operation) : unavailableTitle(operation);
  button.setAttribute("aria-disabled", button.disabled ? "true" : "false");
}

export function syncRegionDeleteControl(visualizer: VisualizerElement): void {
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const region = selectionForVisualizer(visualizer);
  const durationMs = Number(visualizer.dataset.durationMs || "0");
  syncRegionDeleteButton(regionDeleteButtonForOrd(ord), region, durationMs, "delete-selection");
  syncRegionDeleteButton(regionDeleteRestButtonForOrd(ord), region, durationMs, "delete-rest");
}

export function syncAllRegionDeleteControls(): void {
  allVisualizers().forEach(syncRegionDeleteControl);
}

export function regionDeleteRequestFor(
  visualizer: VisualizerElement,
  trigger: RegionDeleteRequest["trigger"],
  operation: RegionDeleteOperation = "delete-selection",
): RegionDeleteRequest | null {
  const ord = Number(visualizer.dataset.aqeFieldOrd || "0");
  const durationMs = Number(visualizer.dataset.durationMs || "0") || 0;
  const region = selectionForVisualizer(visualizer);
  if (!region || !isValidRegionDeleteSelection(region, durationMs)) {
    if (region && isWholeSelection(region, durationMs)) {
      logger.warn("region delete rejected whole clip", {
        ord,
        operation,
        sourceFilename: visualizer.dataset.sourceFilename || "",
        selectionStartMs: region.startMs,
        selectionEndMs: region.endMs,
        durationMs,
        trigger,
      });
    }
    return null;
  }
  const sourceFilename = visualizer.dataset.sourceFilename || "";
  if (!sourceFilename) return null;
  const playbackState = visualizer.dataset.playbackState;
  return {
    operation,
    ord,
    sourceFilename,
    selectionStartMs: Math.round(region.startMs),
    selectionEndMs: Math.round(region.endMs),
    cursorMs: Math.round(Number(visualizer.dataset.cursorMs || "0") || 0),
    durationMs: Math.round(durationMs),
    trigger,
    playbackActive: isPlaybackState(playbackState) && playbackState !== "stopped",
  };
}
```

- [ ] **Step 6: Update frontend sending and rendering**

In `settings_ui/src/editor-inline/region-delete.ts`, update `sendRegionDelete` and keep Backspace defaulting to delete-selection:

```ts
import { processingMessage } from "./commands.js";
import { focusAndSendCommand, setPendingRegionDeleteRequest } from "./bridge.js";
import { logger } from "./logger.js";
import { setControlsBusy, stopProgressClock } from "./actions.js";
import { regionDeleteRequestFor, syncRegionDeleteControl } from "./region-delete-state.js";
import { visualizerForOrd } from "./dom-selectors.js";
import type { RegionDeleteOperation, RegionDeleteRequest } from "./types.js";

function anyBusy(): boolean {
  return document.body.dataset.aqeBusy === "true";
}

function commandForOperation(operation: RegionDeleteOperation): "aqe:delete-rest" | "aqe:delete-selection" {
  return operation === "delete-rest" ? "aqe:delete-rest" : "aqe:delete-selection";
}

export function sendRegionDelete(
  trigger: RegionDeleteRequest["trigger"],
  node: HTMLElement,
  ord: number,
  operation: RegionDeleteOperation = "delete-selection",
): void {
  if (anyBusy()) return;
  const visualizer = visualizerForOrd(ord);
  if (!visualizer) return;
  const request = regionDeleteRequestFor(visualizer, trigger, operation);
  syncRegionDeleteControl(visualizer);
  if (!request) return;
  if (typeof node.focus === "function") node.focus();
  stopProgressClock(visualizer, { clearAudio: true });
  setPendingRegionDeleteRequest(request);
  window.__aqeActiveField = ord;
  logger.info("region delete request queued", {
    ord,
    operation: request.operation,
    sourceFilename: request.sourceFilename,
    selectionStartMs: request.selectionStartMs,
    selectionEndMs: request.selectionEndMs,
    durationMs: request.durationMs,
    trigger,
    playbackActive: request.playbackActive,
  });
  setControlsBusy(ord, true, processingMessage(commandForOperation(operation)));
  focusAndSendCommand(ord, "aqe:delete-selection");
}

export function handleVisualizerKeyDown(event: KeyboardEvent, ord: number): void {
  if (event.key !== "Backspace") return;
  const visualizer = visualizerForOrd(ord);
  if (!visualizer || document.activeElement !== visualizer || anyBusy()) return;
  if (!regionDeleteRequestFor(visualizer, "backspace", "delete-selection")) {
    syncRegionDeleteControl(visualizer);
    return;
  }
  event.preventDefault();
  sendRegionDelete("backspace", visualizer, ord, "delete-selection");
}
```

In `settings_ui/src/editor-inline/EditorControls.svelte`, keep the existing **Delete Region** button and add this adjacent button immediately after it:

```svelte
<button
  type="button"
  class="aqe-button aqe-delete-rest-button"
  data-aqe-command="aqe:delete-rest"
  data-aqe-button-state="default"
  data-testid={testId(target.ord, "aqe:delete-rest")}
  title="Delete the rest of the audio"
  aria-label="Delete the rest of the audio"
  hidden
  onmousedown={(event) => event.preventDefault()}
  onclick={() => sendRegionDelete("button", target.node, target.ord, "delete-rest")}
>
  <EditorCommandIcon icon="trash-2" />
  <span class="aqe-button-label">Delete the rest</span>
</button>
```

Update the graph help item to one sentence that includes both actions:

```svelte
<li>Delete Region removes the selected region; Delete the rest keeps only the selected region. Backspace deletes the selected region when the graph is focused.</li>
```

- [ ] **Step 7: Update test contract state**

In `settings_ui/src/editor-inline/test-contract.ts`, query both buttons:

```ts
const regionDelete = controlsForOrd(ord)?.querySelector<HTMLButtonElement>(".aqe-delete-region-button") ?? null;
const regionDeleteRest = controlsForOrd(ord)?.querySelector<HTMLButtonElement>(".aqe-delete-rest-button") ?? null;
```

Return both delete-rest fields near the existing delete-region fields:

```ts
regionDeleteButtonDisabled: !!regionDelete?.disabled,
regionDeleteButtonHidden: regionDelete ? !!regionDelete.hidden : true,
regionDeleteRestButtonDisabled: !!regionDeleteRest?.disabled,
regionDeleteRestButtonHidden: regionDeleteRest ? !!regionDeleteRest.hidden : true,
```

- [ ] **Step 8: Run frontend tests**

Run:

```bash
cd settings_ui
npm run test -- editor-inline.selection.integration.test.ts editor-inline.integration.test.ts
```

Expected: PASS.

- [ ] **Step 9: Detect changes and commit frontend task**


```text
```

Expected: changed frontend symbols are limited to the inline editor selection-operation path.

Then commit only the files from this task:

```bash
git add settings_ui/src/editor-inline/types.ts \
  settings_ui/src/editor-inline/commands.ts \
  settings_ui/src/editor-inline/region-delete-state.ts \
  settings_ui/src/editor-inline/region-delete.ts \
  settings_ui/src/editor-inline/EditorControls.svelte \
  settings_ui/src/editor-inline/test-contract.ts \
  settings_ui/tests/editor-inline.selection.integration.test.ts \
  settings_ui/tests/editor-inline.integration.test.ts
git commit -m "Add delete-rest frontend request flow"
```

## Task 2: Audio Keep-Selection Plan And Renderer

**Files:**
- Modify: `tests/test_audio_commands.py`
- Modify: `tests/test_audio_rendering.py`
- Modify: `addon/anki_audio_quick_editor/audio_types.py`
- Modify: `addon/anki_audio_quick_editor/audio_commands.py`
- Modify: `addon/anki_audio_quick_editor/audio_rendering.py`
- Modify: `addon/anki_audio_quick_editor/audio_processor.py`


Run:

```text
```

Expected: direct consumers include audio rendering tests and editor region-delete rendering; the new keep-selection path should not change existing delete-selection output.

- [ ] **Step 2: Write failing audio command tests**

In `tests/test_audio_commands.py`, add `build_region_keep_plan` to the existing import from `anki_audio_quick_editor.audio_processor`.

Add these tests after the existing region-delete plan tests:

```python
def test_build_region_keep_plan_keeps_middle_selection() -> None:
    plan = build_region_keep_plan(500, 1250, 2000)

    assert plan.kept_duration_ms == 750
    assert plan.removed_duration_ms == 1250
    assert plan.expected_duration_ms == 750
    assert plan.filter_complex == (
        "[0:a]atrim=start=0.500:end=1.250,asetpts=PTS-STARTPTS[out]"
    )


def test_build_region_keep_plan_handles_edge_selections() -> None:
    assert build_region_keep_plan(0, 400, 2000).filter_complex == (
        "[0:a]atrim=start=0.000:end=0.400,asetpts=PTS-STARTPTS[out]"
    )
    assert build_region_keep_plan(1400, 2000, 2000).filter_complex == (
        "[0:a]atrim=start=1.400:end=2.000,asetpts=PTS-STARTPTS[out]"
    )


def test_build_region_keep_plan_rejects_empty_and_whole_audio_selection() -> None:
    with pytest.raises(AudioProcessingError, match="Select a region"):
        build_region_keep_plan(500, 500, 2000)
    with pytest.raises(AudioProcessingError, match="already covers the whole audio clip"):
        build_region_keep_plan(0, 2000, 2000)
```

- [ ] **Step 3: Write failing audio rendering test**

In `tests/test_audio_rendering.py`, add `render_audio_region_kept` to the existing import from `anki_audio_quick_editor.audio_processor`.

Add this test after `test_render_audio_region_deleted_uses_concat_filter`:

```python
def test_render_audio_region_kept_uses_single_trim_filter(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[list[str], bool, bool, bool]] = []
    durations = iter([2000, 750])
    commands: list[tuple[str, ...]] = []

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.find_ffmpeg", lambda _path: Path("/bin/ffmpeg"))
    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.probe_duration_ms", lambda *_args: next(durations))

    def fake_run(cmd: list[str], capture_output: bool, text: bool, check: bool) -> SimpleNamespace:
        calls.append((cmd, capture_output, text, check))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("anki_audio_quick_editor.audio_processor.subprocess.run", fake_run)

    output = tmp_path / "kept.mp3"
    result = render_audio_region_kept(
        tmp_path / "source.wav",
        500,
        1250,
        AudioProcessingConfig(),
        output_path=output,
        on_command=commands.append,
    )

    filter_complex = "[0:a]atrim=start=0.500:end=1.250,asetpts=PTS-STARTPTS[out]"
    expected_command = (
        "/bin/ffmpeg",
        "-y",
        "-i",
        str(tmp_path / "source.wav"),
        "-vn",
        "-filter_complex",
        filter_complex,
        "-map",
        "[out]",
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "4",
        str(output),
    )
    assert calls == [(list(expected_command), True, True, False)]
    assert commands == [expected_command]
    assert result.output_path == output
    assert result.command == expected_command
    assert result.duration_ms == 750
```

- [ ] **Step 4: Run audio tests to confirm they fail**

Run:

```bash
python3 scripts/dev.py test tests/test_audio_commands.py tests/test_audio_rendering.py
```

Expected: FAIL because `build_region_keep_plan` and `render_audio_region_kept` do not exist yet.

- [ ] **Step 5: Add the keep-selection plan type**

In `addon/anki_audio_quick_editor/audio_types.py`, add this dataclass below `RegionDeletePlan`:

```python
@dataclass(frozen=True)
class RegionKeepPlan:
    """Filter plan for keeping one selected region from a clip timeline."""

    selection_start_ms: int
    selection_end_ms: int
    duration_ms: int
    filter_complex: str

    @property
    def kept_duration_ms(self) -> int:
        """Return the selected duration kept by this plan."""
        return self.selection_end_ms - self.selection_start_ms

    @property
    def removed_duration_ms(self) -> int:
        """Return the approximate duration removed by this plan."""
        return self.duration_ms - self.kept_duration_ms

    @property
    def expected_duration_ms(self) -> int:
        """Return the approximate output duration before encoder tolerance."""
        return self.kept_duration_ms
```

- [ ] **Step 6: Add the ffmpeg keep-selection plan builder**

In `addon/anki_audio_quick_editor/audio_commands.py`, import `RegionKeepPlan`:

```python
from .audio_types import RegionDeletePlan, RegionKeepPlan
```

Add this function after `build_region_delete_plan`:

```python
def build_region_keep_plan(
    selection_start_ms: int,
    selection_end_ms: int,
    duration_ms: int,
) -> RegionKeepPlan:
    """Return a trim plan for keeping one selected region from a clip."""
    duration = max(0, int(round(duration_ms)))
    start = max(0, min(int(round(selection_start_ms)), duration))
    end = max(0, min(int(round(selection_end_ms)), duration))
    if end <= start:
        raise AudioProcessingError("Select a region before deleting the rest.")
    if start <= 0 and end >= duration:
        raise AudioProcessingError("Selection already covers the whole audio clip.")

    start_s = start / 1000
    end_s = end / 1000
    filter_complex = f"[0:a]atrim=start={start_s:.3f}:end={end_s:.3f},asetpts=PTS-STARTPTS[out]"
    return RegionKeepPlan(start, end, duration, filter_complex)
```

- [ ] **Step 7: Add renderer and processor facade**

In `addon/anki_audio_quick_editor/audio_rendering.py`, import `build_region_keep_plan` and add a shared helper plus keep renderer:

```python
from .audio_commands import (
    build_audio_filters,
    build_ffmpeg_command,
    build_playback_segment_filters,
    build_region_delete_command,
    build_region_delete_plan,
    build_region_keep_plan,
)
```

Add this helper near `render_audio_region_deleted`:

```python
def _render_region_filter_complex(
    source_path: Path,
    filter_complex: str,
    config: AudioProcessingConfig,
    output_path: Path,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    ffmpeg_path = find_ffmpeg(config.ffmpeg_path)
    cmd = build_region_delete_command(ffmpeg_path, source_path, filter_complex, output_path)
    if on_command:
        on_command(cmd)
    result = subprocess.run(list(cmd), capture_output=True, text=True, check=False)  # nosec B603
    if result.returncode != 0:
        raise AudioProcessingError(result.stderr.strip() or "Audio processing failed.")
    return AudioProcessingResult(
        output_path=output_path,
        command=cmd,
        duration_ms=probe_duration_ms(output_path, config),
    )
```

Update `render_audio_region_deleted` to use the helper:

```python
def render_audio_region_deleted(
    source_path: Path,
    selection_start_ms: int,
    selection_end_ms: int,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    """Render an MP3 with one selected region removed from ``source_path``."""
    duration_ms = probe_duration_ms(source_path, config)
    plan = build_region_delete_plan(selection_start_ms, selection_end_ms, duration_ms)

    if output_path is None:
        output_path = Path(tempfile.mkstemp(prefix="aqe_region_delete_", suffix=".mp3")[1])

    return _render_region_filter_complex(source_path, plan.filter_complex, config, output_path, on_command)
```

Add the new renderer:

```python
def render_audio_region_kept(
    source_path: Path,
    selection_start_ms: int,
    selection_end_ms: int,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    """Render an MP3 with only one selected region kept from ``source_path``."""
    duration_ms = probe_duration_ms(source_path, config)
    plan = build_region_keep_plan(selection_start_ms, selection_end_ms, duration_ms)

    if output_path is None:
        output_path = Path(tempfile.mkstemp(prefix="aqe_region_keep_", suffix=".mp3")[1])

    return _render_region_filter_complex(source_path, plan.filter_complex, config, output_path, on_command)
```

In `addon/anki_audio_quick_editor/audio_processor.py`, import/export `RegionKeepPlan`, `build_region_keep_plan`, and `render_audio_region_kept`, then add this facade:

```python
def render_audio_region_kept(
    source_path: Path,
    selection_start_ms: int,
    selection_end_ms: int,
    config: AudioProcessingConfig,
    output_path: Path | None = None,
    on_command: Callable[[tuple[str, ...]], None] | None = None,
) -> AudioProcessingResult:
    _sync_rendering_dependencies()
    return _audio_rendering.render_audio_region_kept(
        source_path,
        selection_start_ms,
        selection_end_ms,
        config,
        output_path,
        on_command,
    )
```

- [ ] **Step 8: Run audio tests**

Run:

```bash
python3 scripts/dev.py test tests/test_audio_commands.py tests/test_audio_rendering.py
```

Expected: PASS.

- [ ] **Step 9: Detect changes and commit audio task**

Run:

```text
```

Expected: changed symbols are limited to audio plan/rendering helpers and tests.

Commit:

```bash
git add addon/anki_audio_quick_editor/audio_types.py \
  addon/anki_audio_quick_editor/audio_commands.py \
  addon/anki_audio_quick_editor/audio_rendering.py \
  addon/anki_audio_quick_editor/audio_processor.py \
  tests/test_audio_commands.py \
  tests/test_audio_rendering.py
git commit -m "Add keep-selection audio rendering"
```

## Task 3: Python Bridge Operation Routing

**Files:**
- Modify: `tests/test_editor_integration.py`
- Modify: `addon/anki_audio_quick_editor/editor_session.py`
- Modify: `addon/anki_audio_quick_editor/editor_region_delete.py`
- Modify: `addon/anki_audio_quick_editor/editor_dependencies.py`


Run:

```text
```

Expected: direct consumers include editor callbacks, integration tests, and region-delete replacement flow.

- [ ] **Step 2: Write failing parser and routing tests**

In `tests/test_editor_integration.py`, update `test_region_delete_request_parser_normalizes_payload` to include and assert the default operation:

```python
assert request.operation == "delete-selection"
```

Add these tests after it:

```python
def test_region_delete_request_parser_accepts_delete_rest_operation() -> None:
    request = _parse_region_delete_request(
        {
            "operation": "delete-rest",
            "ord": 0,
            "sourceFilename": "clip.wav",
            "selectionStartMs": 250,
            "selectionEndMs": 750,
            "cursorMs": 300,
            "durationMs": 1000,
            "trigger": "button",
            "playbackActive": False,
        }
    )

    assert request is not None
    assert request.operation == "delete-rest"
    assert request.selection_start_ms == 250
    assert request.selection_end_ms == 750


def test_delete_rest_removed_duration_counts_outside_selection() -> None:
    request = _parse_region_delete_request(
        {
            "operation": "delete-rest",
            "ord": 0,
            "sourceFilename": "clip.wav",
            "selectionStartMs": 250,
            "selectionEndMs": 700,
            "cursorMs": 300,
            "durationMs": 1000,
            "trigger": "button",
        }
    )

    assert request is not None
    assert request.selected_duration_ms == 450
    assert request.removed_duration_ms == 550


def test_region_delete_request_parser_rejects_unknown_operation() -> None:
    request = _parse_region_delete_request(
        {
            "operation": "replace-with-silence",
            "ord": 0,
            "sourceFilename": "clip.wav",
            "selectionStartMs": 250,
            "selectionEndMs": 750,
            "cursorMs": 300,
            "durationMs": 1000,
            "trigger": "button",
        }
    )

    assert request is None
```

Add this routing test near the parser tests:

```python
def test_region_operation_renderer_routes_delete_rest_to_keep_renderer(tmp_path: Path) -> None:
    from anki_audio_quick_editor.editor_region_delete import render_region_operation

    calls: list[tuple[str, int, int]] = []
    request = _parse_region_delete_request(
        {
            "operation": "delete-rest",
            "ord": 0,
            "sourceFilename": "clip.wav",
            "selectionStartMs": 250,
            "selectionEndMs": 750,
            "cursorMs": 300,
            "durationMs": 1000,
            "trigger": "button",
        }
    )
    assert request is not None

    expected = object()
    deps = SimpleNamespace(
        render_audio_region_deleted=lambda *_args, **_kwargs: calls.append(("delete", _args[1], _args[2])),
        render_audio_region_kept=lambda *_args, **_kwargs: calls.append(("keep", _args[1], _args[2])) or expected,
    )

    result = render_region_operation(
        deps,
        tmp_path / "clip.wav",
        request,
        AudioProcessingConfig(),
        output_path=tmp_path / "out.mp3",
        on_command=None,
    )

    assert result is expected
    assert calls == [("keep", 250, 750)]
```

Ensure `tests/test_editor_integration.py` imports `AudioProcessingConfig` if it does not already:

```python
from anki_audio_quick_editor.audio_state import AudioEditState, AudioProcessingConfig
```

- [ ] **Step 3: Run integration tests to confirm they fail**

Run:

```bash
python3 scripts/dev.py test tests/test_editor_integration.py
```

Expected: FAIL because `operation`, `render_region_operation`, and `render_audio_region_kept` dependency routing do not exist yet.

- [ ] **Step 4: Add operation type to editor session request**

In `addon/anki_audio_quick_editor/editor_session.py`, import `Literal` and define the operation alias:

```python
from typing import Literal

RegionDeleteOperation = Literal["delete-selection", "delete-rest"]
```

Add `operation` to the dataclass:

```python
@dataclass(frozen=True)
class RegionDeleteRequest:
    """Frontend request to delete or keep a selected graph region."""

    field_index: int
    source_filename: str
    selection_start_ms: int
    selection_end_ms: int
    cursor_ms: int
    duration_ms: int
    trigger: str
    playback_active: bool
    operation: RegionDeleteOperation = "delete-selection"

    @property
    def selected_duration_ms(self) -> int:
        """Return the normalized selected duration."""
        return self.selection_end_ms - self.selection_start_ms

    @property
    def removed_duration_ms(self) -> int:
        """Return the approximate duration removed by this operation."""
        if self.operation == "delete-rest":
            return self.duration_ms - self.selected_duration_ms
        return self.selected_duration_ms
```

- [ ] **Step 5: Parse and validate operation in Python**

In `addon/anki_audio_quick_editor/editor_region_delete.py`, import the alias:

```python
from .editor_session import EditorSession, RegionDeleteOperation, RegionDeleteRequest
```

Add operation constants and helper near the trigger helper:

```python
REGION_DELETE_OPERATION: RegionDeleteOperation = "delete-selection"
REGION_KEEP_OPERATION: RegionDeleteOperation = "delete-rest"
REGION_DELETE_OPERATIONS = {REGION_DELETE_OPERATION, REGION_KEEP_OPERATION}
```

```python
def region_delete_operation(request: dict[str, Any]) -> RegionDeleteOperation | None:
    """Return the normalized selected-region operation."""
    operation = str(request.get("operation") or REGION_DELETE_OPERATION)
    if operation not in REGION_DELETE_OPERATIONS:
        return None
    return cast(RegionDeleteOperation, operation)
```

In `parse_region_delete_request`, compute the operation after the source filename check and reject unknown values:

```python
    operation = region_delete_operation(request)
    if operation is None:
        return None
    return RegionDeleteRequest(
        field_index=field_index,
        source_filename=source_filename,
        selection_start_ms=start,
        selection_end_ms=end,
        cursor_ms=max(0, min(cursor_ms, duration_ms)),
        duration_ms=duration_ms,
        trigger=region_delete_trigger(request),
        playback_active=bool(request.get("playbackActive")),
        operation=operation,
    )
```

- [ ] **Step 6: Route rendering by operation and label busy state**

In `addon/anki_audio_quick_editor/editor_region_delete.py`, add these helpers before `delete_selection_async`:

```python
def region_operation_busy_message(request: RegionDeleteRequest) -> str:
    """Return the frontend busy message for a selected-region operation."""
    return "Deleting rest..." if request.operation == REGION_KEEP_OPERATION else "Deleting region..."
```

```python
def region_operation_command_status(request: RegionDeleteRequest) -> str:
    """Return the ffmpeg status prefix for a selected-region operation."""
    return "Deleting rest with ffmpeg" if request.operation == REGION_KEEP_OPERATION else "Deleting region with ffmpeg"
```

```python
def region_operation_whole_clip_message(request: RegionDeleteRequest) -> str:
    """Return the warning shown when the selected operation would be a no-op."""
    return (
        "Selection already covers the whole audio clip."
        if request.operation == REGION_KEEP_OPERATION
        else "Cannot delete the whole audio clip."
    )
```

```python
def render_region_operation(
    deps: Any,
    source_path: Path,
    request: RegionDeleteRequest,
    config: AudioProcessingConfig,
    output_path: Path,
    on_command: Any,
) -> Any:
    """Render the requested selected-region operation."""
    renderer = (
        deps.render_audio_region_kept
        if request.operation == REGION_KEEP_OPERATION
        else deps.render_audio_region_deleted
    )
    return renderer(
        source_path,
        request.selection_start_ms,
        request.selection_end_ms,
        config,
        output_path=output_path,
        on_command=on_command,
    )
```

In `delete_selection_async`, replace hardcoded busy/status text:

```python
deps.set_busy_for_field(editor, request.field_index, True, region_operation_busy_message(request))
```

In `delete_selection_with_request`, replace the whole-clip warning text with the operation-specific helper:

```python
deps.eval_status(editor, region_operation_whole_clip_message(parsed), kind="warning")
```

Inside `_show_command`, replace:

```python
status_message = region_operation_command_status(request)
```

Replace the call to `deps.render_audio_region_deleted(...)` with:

```python
result = render_region_operation(
    deps,
    source_path,
    request,
    config,
    output_path,
    _show_command,
)
```

In `region_delete_log_context`, include the operation:

```python
"operation": request.operation,
```

- [ ] **Step 7: Provide the new renderer dependency**

In `addon/anki_audio_quick_editor/editor_dependencies.py`, import `render_audio_region_kept` from `audio_processor` and add it to `region_delete_deps`:

```python
render_audio_region_kept=render_audio_region_kept,
```

- [ ] **Step 8: Run Python integration tests**

Run:

```bash
python3 scripts/dev.py test tests/test_editor_integration.py
```

Expected: PASS.

- [ ] **Step 9: Detect changes and commit bridge task**

Run:

```text
```

Expected: changed symbols are limited to selected-region request parsing/routing and tests.

Commit:

```bash
git add addon/anki_audio_quick_editor/editor_session.py \
  addon/anki_audio_quick_editor/editor_region_delete.py \
  addon/anki_audio_quick_editor/editor_dependencies.py \
  tests/test_editor_integration.py
git commit -m "Route delete-rest region requests"
```

## Task 4: End-To-End Workflow Coverage

**Files:**
- Modify: `e2e/editor_graph_helpers.py`
- Modify: `e2e/test_editor_region_delete_workflow.py`


Run:

```text
```

Expected: blast radius is limited to e2e tests.

- [ ] **Step 2: Update the e2e graph helper state**

In `e2e/editor_graph_helpers.py`, add the delete-rest button query:

```python
const deleteRestButton = document.querySelector(`[data-testid="aqe-button-${ord}-delete-rest"]`);
```

Add these state fields near `regionDeleteButtonDisabled`:

```python
regionDeleteRestButtonDisabled: deleteRestButton ? deleteRestButton.disabled : true,
regionDeleteRestButtonHidden: deleteRestButton ? deleteRestButton.hidden : true,
```

- [ ] **Step 3: Add the failing e2e workflow test**

In `e2e/test_editor_region_delete_workflow.py`, add this test after the existing delete-region workflow test:

```python
def test_delete_rest_button_keeps_selected_middle_region_and_redraws_graph(
    anki_mw,
    ffmpeg_config,
) -> None:
    from anki_audio_quick_editor.audio_processor import (
        AudioProcessingConfig,
        probe_duration_ms,
    )

    media_dir = Path(anki_mw.col.media.dir())
    source = media_dir / "editor_delete_rest_middle.wav"
    generate_tone(ffmpeg_config, source, duration_s=2.0)
    original_bytes = source.read_bytes()
    note = _basic_audio_note(anki_mw, source.name)
    _configure_ffmpeg(anki_mw, ffmpeg_config)

    editor, parent = _open_editor(anki_mw, note)
    try:
        track = _click_graph_and_wait(editor, lambda value: value["sourceFilename"] == source.name)
        assert 1900 <= track["durationMs"] <= 2100

        _shift_drag_region(editor, 0.25, 0.625)
        selected = wait_for_js_condition(
            editor.web,
            _graph_state_js(),
            lambda state: state is not None
            and state["selectionActive"] is True
            and state["regionDeleteRestButtonHidden"] is False
            and state["regionDeleteRestButtonDisabled"] is False,
            timeout=5.0,
        )
        assert selected["selectionStartMs"] == 500
        assert selected["selectionEndMs"] == 1250

        previous_name = _sound_filename(note.fields[0])
        click_selector(editor.web, _button_selector("aqe:delete-rest"), timeout=5.0)
        generated_name = _wait_for_generated_mp3(note, media_dir, previous_name)
        redrawn = _wait_for_visualizer_track(
            editor,
            lambda value: value["sourceFilename"] == generated_name
            and value["selectionActive"] is False
            and value["cursorMs"] == 0,
            timeout=10.0,
        )

        generated_duration = probe_duration_ms(media_dir / generated_name, AudioProcessingConfig.from_config({}))
        assert source.read_bytes() == original_bytes
        assert generated_name.startswith("editor_delete_rest_middle__aqe_")
        assert 600 <= generated_duration <= 900
        assert redrawn["sourceFilename"] == generated_name
        assert redrawn["playbackState"] == "stopped"
    finally:
        editor.set_note(None)
        parent.close()
```

- [ ] **Step 4: Run e2e workflow to confirm it fails before implementation is complete**

If Tasks 1-3 are already complete, this may pass immediately. If running before those tasks, run:

```bash
python3 scripts/dev.py test-e2e
```

Expected before implementation: FAIL because the generated editor bundle does not yet expose the new button or Python route. Expected after Tasks 1-3 and a frontend build: PASS.

- [ ] **Step 5: Run full e2e after Tasks 1-3 are complete**

Run:

```bash
python3 scripts/dev.py test-e2e
```

Expected: PASS. This command builds frontend bundles first.

- [ ] **Step 6: Detect changes and commit e2e task**

Run:

```text
```

Expected: changed symbols are limited to e2e helper/test coverage.

Commit:

```bash
git add e2e/editor_graph_helpers.py e2e/test_editor_region_delete_workflow.py
git commit -m "Cover delete-rest editor workflow"
```

## Task 5: Final Verification And Cleanup

**Files:**
- Review all files changed by Tasks 1-4.
- Generated ignored frontend bundles may change during build commands; do not stage ignored artifacts unless `git status --short` shows committed source files that intentionally changed.

- [ ] **Step 1: Run frontend validation**

Run:

```bash
python3 scripts/dev.py test-svelte
```

Expected: PASS. This builds settings/editor bundles, runs Svelte check, ESLint including max-lines, TypeScript typecheck, and Vitest coverage.

- [ ] **Step 2: Run Python unit and architecture tests**

Run:

```bash
python3 scripts/dev.py test
```

Expected: PASS.

- [ ] **Step 3: Run e2e tests**

Run:

```bash
python3 scripts/dev.py test-e2e
```

Expected: PASS.

- [ ] **Step 4: Run the reusable QC gate**

Run:

```bash
python3 scripts/dev.py check
```

Expected: PASS. If Qodana or Sonar-specific local prerequisites block the gate, capture the exact failing prerequisite and still report the passing targeted checks from Steps 1-3.


Run:

```text
```

Expected: affected flows are the selected-region delete/edit flow, audio keep-selection renderer, and e2e tests only.

- [ ] **Step 6: Inspect final diff**

Run:

```bash
git status --short
git diff --stat
```

Expected: only intended source and test files are modified. Existing unrelated local changes such as `DEBUGGING.md`, `ERROR_HANDLING_AND_DIAGNOSTICS.md`, or `docs/superpowers/notes/` remain untouched and unstaged unless the user explicitly asks to include them.

- [ ] **Step 7: Final commit if any verification fixes were added**


```text
```

Then commit only the intended files:

```bash
git add settings_ui/src/editor-inline/types.ts \
  settings_ui/src/editor-inline/commands.ts \
  settings_ui/src/editor-inline/region-delete-state.ts \
  settings_ui/src/editor-inline/region-delete.ts \
  settings_ui/src/editor-inline/EditorControls.svelte \
  settings_ui/src/editor-inline/test-contract.ts \
  settings_ui/tests/editor-inline.selection.integration.test.ts \
  settings_ui/tests/editor-inline.integration.test.ts \
  addon/anki_audio_quick_editor/audio_types.py \
  addon/anki_audio_quick_editor/audio_commands.py \
  addon/anki_audio_quick_editor/audio_rendering.py \
  addon/anki_audio_quick_editor/audio_processor.py \
  addon/anki_audio_quick_editor/editor_session.py \
  addon/anki_audio_quick_editor/editor_region_delete.py \
  addon/anki_audio_quick_editor/editor_dependencies.py \
  tests/test_audio_commands.py \
  tests/test_audio_rendering.py \
  tests/test_editor_integration.py \
  e2e/editor_graph_helpers.py \
  e2e/test_editor_region_delete_workflow.py
git commit -m "Finalize delete-rest editor flow"
```

Expected: final commit contains only cleanup required by verification.

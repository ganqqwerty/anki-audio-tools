import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  clearQueuedAnimationFrames,
  dispatchHandlePointer,
  dragGraphSelection,
  graphClientX,
  mockAnimationFrames,
  muteConsole,
  prepareHtmlAudio,
  renderFields,
  setRepeatMode,
  setGraphBounds,
  track,
} from "./editor-inline.integration.helpers.js";

describe("editor inline selection playback resize integration", () => {
  let restoreConsole: () => void;

  beforeEach(() => {
    restoreConsole = muteConsole();
    renderFields();
  });

  afterEach(() => {
    disposeEditorRuntime();
    restoreConsole();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("uses resized repeat boundaries after handle resize", async () => {
    const frames = mockAnimationFrames();
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.25, 0.75);
    await setRepeatMode(true);
    clearQueuedAnimationFrames(frames);
    const audio = prepareHtmlAudio();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();
    audio.currentTime = 0.5;
    frames.shift()?.(performance.now() + 500);
    const handle = document.querySelector('[data-testid="aqe-selection-resize-end-0"]')!;

    dispatchHandlePointer(handle, "pointerdown", graphClientX(svg, 0.75));
    dispatchHandlePointer(handle, "pointermove", graphClientX(svg, 0.9));
    dispatchHandlePointer(handle, "pointerup", graphClientX(svg, 0.9));
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "playing",
      playbackStartMs: 250,
      playbackEndMs: 900,
      repeatEnabled: true,
    });
    expect(audio.pause).toHaveBeenCalled();
    expect(audio.play).toHaveBeenCalledTimes(2);

    audio.currentTime = 0.91;
    frames.shift()?.(performance.now() + 900);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "playing",
      cursorMs: 250,
      playbackStartMs: 250,
      playbackEndMs: 900,
      repeatEnabled: true,
    });
  });

  it("keeps selection, repeat, and playback isolated between mounted audio fields", async () => {
    document.body.innerHTML = `
      <div class="field-container" data-index="0">
        <div contenteditable="true" id="f0">[sound:first.mp3]</div>
      </div>
      <div class="field-container" data-index="1">
        <div contenteditable="true" id="f1">[sound:second.wav]</div>
      </div>
    `;
    initializeEditorRuntime({ audioFieldIndices: [0, 1] });
    scan({ audioFieldIndices: [0, 1] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "first.mp3" }, 0);
    window.__aqeSetVisualizer?.(1, { ...track, durationMs: 2000, sourceFilename: "second.wav" }, 0);
    const firstSvg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    const secondSvg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-1"]')!;
    setGraphBounds(firstSvg);
    setGraphBounds(secondSvg);
    dragGraphSelection(firstSvg, 0.2, 0.6);
    await setRepeatMode(true);
    dragGraphSelection(secondSvg, 0.3, 0.5);
    const firstAudio = prepareHtmlAudio(0);
    const secondAudio = prepareHtmlAudio(1);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({ playbackState: "playing" });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-1-play"]')!.click();
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "stopped",
      selectionStartMs: 200,
      selectionEndMs: 600,
      repeatEnabled: true,
    });
    expect(window.__aqeGraphStateForTest?.(1)).toMatchObject({
      playbackState: "playing",
      selectionStartMs: 600,
      selectionEndMs: 1000,
      repeatEnabled: false,
    });
    expect(firstAudio.pause).toHaveBeenCalled();
    expect(secondAudio.play).toHaveBeenCalled();
  });
});

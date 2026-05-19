import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  bridgeCommands,
  dispatchHandlePointer,
  dispatchGraphPointer,
  dragGraphSelection,
  dragSelectionHandle,
  graphClientX,
  mockAnimationFrames,
  muteConsole,
  prepareHtmlAudio,
  renderFields,
  setGraphBounds,
  track,
} from "./editor-inline.integration.helpers.js";

describe("editor inline selection playback integration", () => {

let restoreConsole: () => void;

beforeEach(() => {
  restoreConsole = muteConsole();
  renderFields();
});

afterEach(() => {
  disposeEditorRuntime();
  restoreConsole();
  vi.restoreAllMocks();
});

  it("clamps cursor drags to the selected repeat region", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.2, 0.6);
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-repeat-0"]')!.click();

    dispatchGraphPointer(svg, "pointerdown", graphClientX(svg, 0.9));
    dispatchGraphPointer(svg, "pointerup", graphClientX(svg, 0.9));

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      cursorMs: 600,
      selectionStartMs: 200,
      selectionEndMs: 600,
      repeatEnabled: true,
    });
    expect(window.__aqeGetCursorIntent?.()).toMatchObject({
      cursorMs: 600,
      previousPlaybackState: "stopped",
      restartPlayback: false,
    });
  });

  it("marks paused cursor drags for playback restart", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    window.__aqeSetPlaybackState?.(0, "paused", 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);

    dispatchGraphPointer(svg, "pointerdown", graphClientX(svg, 0.4));
    dispatchGraphPointer(svg, "pointerup", graphClientX(svg, 0.4));

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      cursorMs: 400,
      playbackState: "paused",
      resumeRequiresRestart: true,
    });
    expect(window.__aqeGetCursorIntent?.()).toMatchObject({
      cursorMs: 400,
      previousPlaybackState: "paused",
      restartPlayback: false,
    });
  });

  it("keeps selected repeat playback running across an HTML loop boundary", async () => {
    const frames = mockAnimationFrames();
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.25, 0.75);
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-repeat-0"]')!.click();
    const audio = prepareHtmlAudio();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();
    audio.currentTime = 0.76;
    frames.shift()?.(performance.now() + 800);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "playing",
      playButtonLabel: "Pause",
      cursorMs: 250,
      playbackStartMs: 250,
      playbackEndMs: 750,
      playbackRegionMode: "selection",
    });
    expect(bridgeCommands()).not.toContain("aqe:play-ended");
  });

  it("stops at the selected boundary after repeat is unchecked during playback", async () => {
    const frames = mockAnimationFrames();
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.25, 0.75);
    const repeat = document.querySelector<HTMLButtonElement>('[data-testid="aqe-repeat-0"]')!;
    repeat.click();
    const audio = prepareHtmlAudio();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();
    repeat.click();
    audio.currentTime = 0.76;
    frames.shift()?.(performance.now() + 800);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "stopped",
      playButtonLabel: "Play",
      cursorMs: 250,
      repeatEnabled: false,
    });
    expect(bridgeCommands()).toContain("aqe:play-ended");
  });

  it("keeps stopped selections during processing and clears them on successful redraw", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.25, 0.75);
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-repeat-0"]')!.click();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-volume-up"]')!.click();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      allButtonsDisabled: true,
      playbackState: "stopped",
      selectionActive: true,
      repeatEnabled: true,
    });

    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "processed.mp3" }, 0);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      sourceFilename: "processed.mp3",
      selectionActive: false,
      repeatEnabled: true,
      playbackRegionMode: "full",
      playbackStartMs: 0,
      playbackEndMs: 1000,
    });
  });

  it("freezes active selected playback during resize and restarts from the resized start", async () => {
    const frames = mockAnimationFrames();
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.25, 0.75);
    const audio = prepareHtmlAudio();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();
    audio.currentTime = 0.5;
    frames.shift()?.(performance.now() + 500);
    const handle = document.querySelector('[data-testid="aqe-selection-resize-end-0"]')!;

    dispatchHandlePointer(handle, "pointerdown", graphClientX(svg, 0.75));
    dispatchHandlePointer(handle, "pointermove", graphClientX(svg, 0.9));

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "stopped",
      cursorMs: 500,
      selectionDraftActive: true,
      selectionDraftStartMs: 250,
      selectionDraftEndMs: 900,
    });

    dispatchHandlePointer(handle, "pointerup", graphClientX(svg, 0.9));
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "playing",
      playButtonLabel: "Pause",
      cursorMs: 250,
      selectionStartMs: 250,
      selectionEndMs: 900,
      playbackStartMs: 250,
      playbackEndMs: 900,
      playbackRegionMode: "selection",
    });
    expect(audio.play).toHaveBeenCalledTimes(2);
  });

  it("keeps paused playback paused after resize and requires restart from resized start", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.25, 0.75);
    window.__aqeSetPlaybackState?.(0, "paused", 500);

    dragSelectionHandle(svg, "start", 0.1);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "paused",
      playButtonLabel: "Play",
      resumeRequiresRestart: true,
      selectionStartMs: 100,
      selectionEndMs: 750,
      playbackStartMs: 100,
      playbackEndMs: 750,
    });

    const audio = prepareHtmlAudio();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "playing",
      cursorMs: 100,
      playbackStartMs: 100,
      playbackEndMs: 750,
    });
    expect(audio.play).toHaveBeenCalledTimes(1);
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
    dragSelectionHandle(svg, "end", 0.9);
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-repeat-0"]')!.click();
    const audio = prepareHtmlAudio();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();
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
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-repeat-0"]')!.click();
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

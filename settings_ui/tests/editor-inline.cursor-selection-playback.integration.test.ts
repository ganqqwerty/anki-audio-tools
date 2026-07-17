import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  bridgeCommands,
  dispatchGraphPointer,
  dragGraphSelection,
  graphClientX,
  muteConsole,
  prepareHtmlAudio,
  renderFields,
  setFullGraphViewport,
  setGraphBounds,
  setRepeatMode,
  track,
} from "./editor-inline.integration.helpers.js";

describe("editor inline cursor, selection, playback integration", () => {
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

  it("plays full-cover repeated playback from a moved cursor", async () => {
    const { audio } = await setupGraph();
    window.__aqeSetCursorForTest?.(0, 500, false);
    await setRepeatMode(true);

    playButton().click();
    await flushPlaybackStart();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      cursorMs: 500,
      playbackEndMs: 1000,
      playbackStartMs: 500,
      playbackState: "playing",
      repeatEnabled: true,
      selectionActive: true,
    });
    expect(bridgeCommands()).not.toContain("aqe:play");
    expect(audio.play).toHaveBeenCalledTimes(1);
  });

  it("restarts paused selected one-shot playback from a repositioned cursor and resets at completion", async () => {
    const { audio, svg } = await setupGraph();
    dragGraphSelection(svg, 0.25, 0.75);

    playButton().click();
    await flushPlaybackStart();
    playButton().click();
    await Promise.resolve();
    dragCursor(svg, 0.5);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      cursorMs: 500,
      playbackState: "paused",
      resumeRequiresRestart: true,
      selectionEndMs: 750,
      selectionStartMs: 250,
    });

    playButton().click();
    await flushPlaybackStart();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackEndMs: 750,
      playbackRegionMode: "selection",
      playbackStartMs: 500,
      playbackState: "playing",
    });

    audio.currentTime = 0.76;
    audio.dispatchEvent(new Event("ended"));
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      cursorMs: 250,
      playbackState: "stopped",
      selectionEndMs: 750,
      selectionStartMs: 250,
    });
  });

  it("uses a newly created selection start after pausing full playback", async () => {
    const { svg } = await setupGraph();
    window.__aqeSetCursorForTest?.(0, 400, false);

    playButton().click();
    await flushPlaybackStart();
    playButton().click();
    await Promise.resolve();
    dragGraphSelection(svg, 0.2, 0.6);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      cursorMs: 200,
      playbackState: "paused",
      resumeRequiresRestart: true,
      selectionEndMs: 600,
      selectionStartMs: 200,
    });

    playButton().click();
    await flushPlaybackStart();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      cursorMs: 200,
      playbackEndMs: 600,
      playbackRegionMode: "selection",
      playbackStartMs: 200,
      playbackState: "playing",
    });
  });

  it("plays full audio from the paused cursor after clearing the active selection", async () => {
    const { svg } = await setupGraph();
    dragGraphSelection(svg, 0.2, 0.6);

    playButton().click();
    await flushPlaybackStart();
    playButton().click();
    await Promise.resolve();
    dragCursor(svg, 0.4);
    shiftClick(svg, 0.5);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      cursorMs: 400,
      playbackRegionMode: "full",
      playbackState: "paused",
      selectionActive: false,
    });

    playButton().click();
    await flushPlaybackStart();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackEndMs: 1000,
      playbackRegionMode: "full",
      playbackStartMs: 400,
      playbackState: "playing",
    });
  });

  it("pans a zoomed viewport to a selected playback start without changing selection state", async () => {
    const { svg } = await setupGraph();
    dragGraphSelection(svg, 0.2, 0.6);
    window.__aqeSetTimeViewportForTest?.(0, 700, 1000);

    playButton().click();
    await flushPlaybackStart();
    const state = window.__aqeGraphStateForTest?.(0);

    expect(state).toMatchObject({
      playbackEndMs: 600,
      playbackRegionMode: "selection",
      playbackStartMs: 200,
      playbackState: "playing",
      selectionEndMs: 600,
      selectionStartMs: 200,
      timecodeFlagVisible: true,
    });
    expect(state?.viewportStartMs).toBeLessThanOrEqual(200);
    expect(state?.viewportEndMs).toBeGreaterThanOrEqual(200);
  });

  it("stops zoomed selected repeat playback before a transformation and redraws without a stale loop", async () => {
    const { svg } = await setupGraph();
    dragGraphSelection(svg, 0.25, 0.7);
    await setRepeatMode(true);
    window.__aqeSetTimeViewportForTest?.(0, 250, 750);

    playButton().click();
    await flushPlaybackStart();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-volume-up"]')!.click();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      allButtonsDisabled: true,
      playbackState: "stopped",
      repeatEnabled: true,
      selectionActive: true,
    });
    const stopped = window.__aqeGraphStateForTest?.(0);
    expect((stopped?.viewportEndMs ?? 0) - (stopped?.viewportStartMs ?? 0)).toBe(500);

    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "processed.mp3" }, 0);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      allButtonsDisabled: false,
      cursorMs: 0,
      playbackState: "stopped",
      repeatEnabled: true,
      selectionActive: true,
      selectionEndMs: 1000,
      selectionStartMs: 0,
      sourceFilename: "processed.mp3",
      viewportStartMs: 0,
    });
    expect(window.__aqeGraphStateForTest?.(0)?.viewportEndMs).toBe(track.durationMs);
  });
});

async function setupGraph(): Promise<{ audio: HTMLAudioElement; svg: SVGSVGElement }> {
  initializeEditorRuntime({ audioFieldIndices: [0] });
  scan({ audioFieldIndices: [0] });
  await Promise.resolve();
  window.__aqeSetVisualizer?.(0, track, 0);
  const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
  setGraphBounds(svg);
  setFullGraphViewport();
  const audio = prepareHtmlAudio();
  return { audio, svg };
}

function playButton(): HTMLButtonElement {
  return document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!;
}

async function flushPlaybackStart(): Promise<void> {
  await Promise.resolve();
  await Promise.resolve();
}

function dragCursor(svg: SVGSVGElement, ratio: number): void {
  dispatchGraphPointer(svg, "pointerdown", graphClientX(svg, ratio));
  dispatchGraphPointer(svg, "pointerup", graphClientX(svg, ratio));
}

function shiftClick(svg: SVGSVGElement, ratio: number): void {
  dispatchGraphPointer(svg, "pointerdown", graphClientX(svg, ratio), true);
  dispatchGraphPointer(svg, "pointerup", graphClientX(svg, ratio), true);
}

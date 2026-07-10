import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { readHtmlAudioSessionState } from "../src/editor-inline/html-audio-session-controller.js";
import { disposeEditorRuntime } from "../src/editor-inline/runtime.js";
import {
  clickMarkerRail,
  configureSelectedRepeatAutoAdvance,
  configureSelectedRepeatOnly,
  dragGraphCursor,
  enableSelectedAutoAdvance,
  forceAudioEndedBoundary,
  forceSelectedPlaybackBoundary,
  flushPlaybackWork,
  installChorusingVisualizerStyles,
  longerSuffixButton,
  pauseSelectedPlayback,
  prepareChorusingGraph,
  shorterSuffixButton,
  startSelectedPlayback,
} from "./editor-inline.selected-repeat-auto-advance.helpers.js";
import {
  clearQueuedAnimationFrames,
  dragGraphSelection,
  dragSelectionHandle,
  mockAnimationFrames,
  muteConsole,
  renderFields,
} from "./editor-inline.integration.helpers.js";

describe("editor inline selected-repeat auto-advance interactions", () => {
  let restoreConsole: () => void;

  beforeEach(() => {
    installChorusingVisualizerStyles();
    restoreConsole = muteConsole();
    renderFields();
  });

  afterEach(() => {
    disposeEditorRuntime();
    restoreConsole();
    vi.restoreAllMocks();
  });

  it("longer suffix initializes the rightmost suffix without starting playback", async () => {
    await prepareChorusingGraph();
    const audio = await configureSelectedRepeatAutoAdvance();

    longerSuffixButton().click();
    await flushPlaybackWork();

    expect(audio.play).not.toHaveBeenCalled();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingRepeatPassesCompleted: 0,
      playbackState: "stopped",
      selectionEndMs: 1000,
      selectionStartMs: 500,
    });
  });

  it("auto-advances through suffixes without navigation clicks", async () => {
    await prepareChorusingGraph();
    const audio = await configureSelectedRepeatAutoAdvance(2);
    longerSuffixButton().click();
    await flushPlaybackWork();
    await startSelectedPlayback();

    expect(audio.play).toHaveBeenCalledTimes(1);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackStartMs: 500,
      playbackState: "playing",
      repeatEnabled: true,
      selectionEndMs: 1000,
      selectionStartMs: 500,
    });

    await forceSelectedPlaybackBoundary();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingRepeatPassesCompleted: 1,
      playbackState: "playing",
      selectionEndMs: 1000,
      selectionStartMs: 500,
    });
    expect(audio.play).toHaveBeenCalledTimes(1);

    await forceSelectedPlaybackBoundary();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingRepeatPassesCompleted: 0,
      playbackStartMs: 0,
      playbackState: "playing",
      selectionEndMs: 1000,
      selectionStartMs: 0,
    });
    expect(audio.play).toHaveBeenCalledTimes(2);
  });

  it("auto-advances on live HTML progress boundaries", async () => {
    const frames = mockAnimationFrames();
    await prepareChorusingGraph();
    const audio = await configureSelectedRepeatAutoAdvance(3);
    longerSuffixButton().click();
    await flushPlaybackWork();
    clearQueuedAnimationFrames(frames);

    await startSelectedPlayback();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackStartMs: 500,
      playbackState: "playing",
      selectionEndMs: 1000,
      selectionStartMs: 500,
    });

    await runLiveBoundaryFrame(frames, audio, 1000);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingRepeatPassesCompleted: 1,
      playbackStartMs: 500,
      selectionStartMs: 500,
    });

    await runLiveBoundaryFrame(frames, audio, 1000);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingRepeatPassesCompleted: 2,
      playbackStartMs: 500,
      selectionStartMs: 500,
    });

    await runLiveBoundaryFrame(frames, audio, 1000);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingRepeatPassesCompleted: 0,
      playbackStartMs: 0,
      playbackState: "playing",
      selectionEndMs: 1000,
      selectionStartMs: 0,
    });
  });

  it("manual next and previous reset auto-advance counting", async () => {
    await prepareChorusingGraph();
    await configureSelectedRepeatAutoAdvance(2);
    longerSuffixButton().click();
    await startSelectedPlayback();
    await forceSelectedPlaybackBoundary();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingRepeatPassesCompleted: 1,
      selectionStartMs: 500,
    });

    longerSuffixButton().click();
    await flushPlaybackWork();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingRepeatPassesCompleted: 0,
      playbackStartMs: 0,
      selectionStartMs: 0,
    });

    shorterSuffixButton().click();
    await flushPlaybackWork();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingRepeatPassesCompleted: 0,
      playbackStartMs: 500,
      selectionStartMs: 500,
    });

    await forceSelectedPlaybackBoundary();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingRepeatPassesCompleted: 1,
      selectionStartMs: 500,
    });

    await forceSelectedPlaybackBoundary();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingRepeatPassesCompleted: 0,
      selectionStartMs: 0,
    });
  });

  it("cursor movement does not re-anchor selected-repeat auto-advance", async () => {
    const { svg } = await prepareChorusingGraph();
    await configureSelectedRepeatAutoAdvance(2);
    longerSuffixButton().click();
    await startSelectedPlayback();
    await forceSelectedPlaybackBoundary();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingRepeatPassesCompleted: 1,
      selectionEndMs: 1000,
      selectionStartMs: 500,
    });

    dragGraphCursor(svg, 0.75);
    await flushPlaybackWork();

    expect(readHtmlAudioSessionState(0)).toMatchObject({
      kind: "playing",
      request: {
        cursorMs: 750,
        resetCursorMs: 500,
        source: "user",
      },
    });
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingRepeatPassesCompleted: 1,
      cursorMs: 750,
      selectionEndMs: 1000,
      selectionStartMs: 500,
    });

    await forceAudioEndedBoundary();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingRepeatPassesCompleted: 0,
      selectionEndMs: 1000,
      selectionStartMs: 0,
    });
  });

  it("selection edits keep playback active, re-anchor the right limit, and reset counting", async () => {
    const { svg } = await prepareChorusingGraph();
    await configureSelectedRepeatAutoAdvance(2);
    longerSuffixButton().click();
    await startSelectedPlayback();
    await forceSelectedPlaybackBoundary();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingRepeatPassesCompleted: 1,
      selectionStartMs: 500,
    });

    dragGraphSelection(svg, 0.3, 0.8);
    await flushPlaybackWork();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingMarkersMs: [0, 500],
      chorusingRepeatPassesCompleted: 0,
      playbackEndMs: 800,
      playbackStartMs: 300,
      playbackState: "playing",
      selectionEndMs: 800,
      selectionStartMs: 300,
    });

    await forceSelectedPlaybackBoundary();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingRepeatPassesCompleted: 1,
      selectionEndMs: 800,
      selectionStartMs: 300,
    });

    await forceSelectedPlaybackBoundary();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingRepeatPassesCompleted: 0,
      selectionEndMs: 800,
      selectionStartMs: 0,
    });
  });

  it("auto-advances after being enabled while selected repeat playback is paused", async () => {
    const { svg } = await prepareChorusingGraph();
    const audio = await configureSelectedRepeatOnly();
    dragGraphSelection(svg, 0.3, 0.8);
    await flushPlaybackWork();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingMarkersMs: [0, 500],
      repeatEnabled: true,
      selectionEndMs: 800,
      selectionStartMs: 300,
    });

    await startSelectedPlayback();
    await pauseSelectedPlayback();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "paused",
      selectionEndMs: 800,
      selectionStartMs: 300,
    });

    enableSelectedAutoAdvance(2);
    await startSelectedPlayback();
    expect(readHtmlAudioSessionState(0)).toMatchObject({
      kind: "playing",
      request: {
        cursorMs: 300,
        resetCursorMs: 300,
        source: "user",
      },
    });
    expect(audio.play).toHaveBeenCalledTimes(2);

    await forceSelectedPlaybackBoundary();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingRepeatPassesCompleted: 1,
      selectionEndMs: 800,
      selectionStartMs: 300,
    });

    await forceSelectedPlaybackBoundary();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingRepeatPassesCompleted: 0,
      playbackStartMs: 0,
      playbackState: "playing",
      selectionEndMs: 800,
      selectionStartMs: 0,
    });
  });

  it("uses newly-added left markers on later auto-advance without resetting the counter", async () => {
    const { svg } = await prepareChorusingGraph();
    await configureSelectedRepeatAutoAdvance(2);
    longerSuffixButton().click();
    await startSelectedPlayback();
    await forceSelectedPlaybackBoundary();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingRepeatPassesCompleted: 1,
      selectionStartMs: 500,
    });

    clickMarkerRail(svg, 0.25);
    await flushPlaybackWork();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingMarkersMs: [0, 250, 500],
      chorusingRepeatPassesCompleted: 1,
      playbackStartMs: 500,
      selectionStartMs: 500,
    });

    await forceSelectedPlaybackBoundary();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingRepeatPassesCompleted: 0,
      selectionStartMs: 250,
    });
  });

  it("keeps inside and right-side marker edits from disturbing current auto-advance", async () => {
    const { svg } = await prepareChorusingGraph();
    await configureSelectedRepeatAutoAdvance(2);
    longerSuffixButton().click();
    await startSelectedPlayback();

    dragSelectionHandle(svg, "end", 0.8);
    await flushPlaybackWork();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingRepeatPassesCompleted: 0,
      selectionEndMs: 800,
      selectionStartMs: 500,
    });

    clickMarkerRail(svg, 0.65);
    await flushPlaybackWork();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingMarkersMs: [0, 500, 650],
      chorusingRepeatPassesCompleted: 0,
      playbackStartMs: 500,
      selectionEndMs: 800,
      selectionStartMs: 500,
    });

    clickMarkerRail(svg, 0.9);
    await flushPlaybackWork();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingMarkersMs: [0, 500, 650, 900],
      chorusingRepeatPassesCompleted: 0,
      playbackStartMs: 500,
      selectionEndMs: 800,
      selectionStartMs: 500,
    });

    shorterSuffixButton().click();
    await flushPlaybackWork();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingRepeatPassesCompleted: 0,
      selectionEndMs: 800,
      selectionStartMs: 650,
    });
  });

  it("removing the current-left marker finishes the current cycle before jumping left", async () => {
    const { svg } = await prepareChorusingGraph();
    await configureSelectedRepeatAutoAdvance(2);
    longerSuffixButton().click();
    await startSelectedPlayback();
    await forceSelectedPlaybackBoundary();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingRepeatPassesCompleted: 1,
      selectionStartMs: 500,
    });

    clickMarkerRail(svg, 0.5);
    await flushPlaybackWork();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingMarkersMs: [0],
      chorusingRepeatPassesCompleted: 1,
      playbackStartMs: 500,
      selectionStartMs: 500,
    });

    await forceSelectedPlaybackBoundary();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      chorusingRepeatPassesCompleted: 0,
      selectionStartMs: 0,
    });
  });
});

async function runLiveBoundaryFrame(
  frames: Array<Parameters<typeof window.requestAnimationFrame>[0]>,
  audio: HTMLAudioElement,
  progressMs: number,
): Promise<void> {
  audio.currentTime = progressMs / 1000;
  const frame = frames.shift();
  if (!frame) throw new Error("expected a queued playback progress frame");
  frame(performance.now() + progressMs);
  await flushPlaybackWork();
}

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import {
  dragGraphSelection,
  muteConsole,
  prepareHtmlAudio,
  renderFields,
  setGraphBounds,
  track,
} from "./editor-inline.integration.helpers.js";

describe("editor inline selection marker shift playback integration", () => {
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

  it("restarts active playback from the committed selection after a marker shift click", async () => {
    initializeEditorRuntime({
      audioFieldIndices: [0],
      repeatPlaybackByDefault: false,
      selectionMarkerShiftButtonsEnabled: true,
    });
    scan({
      audioFieldIndices: [0],
      repeatPlaybackByDefault: false,
      selectionMarkerShiftButtonsEnabled: true,
    });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 0);
    await Promise.resolve();
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0, 1 / 3);
    const audio = prepareHtmlAudio();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "playing",
      selectionStartMs: 0,
      selectionEndMs: 333,
    });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-selection-shift-end-next-0"]')!.click();
    await Promise.resolve();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      cursorMs: 0,
      playbackEndMs: 667,
      playbackStartMs: 0,
      playbackState: "playing",
      selectionEndMs: 667,
      selectionStartMs: 0,
    });
    expect(audio.pause).toHaveBeenCalled();
    expect(audio.play).toHaveBeenCalledTimes(2);
  });
});

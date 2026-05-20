import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  disposeEditorRuntime,
  initializeEditorRuntime,
  scan,
} from "../src/editor-inline/runtime.js";
import { requestDefaultGraph } from "../src/editor-inline/actions.js";
import { enqueueDefaultGraphs } from "../src/editor-inline/default-graph-queue.js";
import {
  bridgeCommands,
  muteConsole,
  renderFields,
  renderTwoAudioFields,
  track,
} from "./editor-inline.integration.helpers.js";

const defaultGraphSettings = {
  connectShortDropoutsMs: 0,
  recordingCondition: "auto",
  smoothness: "balanced",
  voiceLock: "balanced",
  voiceRange: "general",
};

describe("editor inline graph queue integration", () => {
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

  it("requests graphs, accepts backend graph payloads, and exposes graph state", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-graph"]')!.click();

    expect(bridgeCommands()).toContain("aqe:analyze-field");
    expect(window.__aqePopPendingGraphAnalysisRequest?.()).toEqual({
      graphSettings: defaultGraphSettings,
      ord: 0,
      sourceFilename: "clip one.mp3",
    });
    expect(window.__aqeGraphStateForTest?.(0)?.busy).toBe(true);

    window.__aqeSetVisualizer?.(0, track, 200);
    const state = window.__aqeGraphStateForTest?.(0);

    expect(state?.hidden).toBe(false);
    expect(state?.durationMs).toBe(1000);
    expect(state?.cursorMs).toBe(200);
    expect(state?.pitchPaths).toBe(2);
    expect(state?.intensity).toMatch(/^M /);
    expect(state?.audioClockSrc).toBe("clip%20one.mp3");
    expect(state?.graphButtonTitle).toBe("Redraw the pitch graph");
    expect(state?.allButtonsDisabled).toBe(false);
  });

  it("keeps a rendered graph when a delayed scan sees the updated source", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    const controls = document.querySelector(".aqe-controls");

    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "updated.mp3" }, 0);
    document.getElementById("f0")!.innerHTML = "[sound:updated.mp3]";
    scan({ audioFieldIndices: [0] });

    expect(document.querySelector(".aqe-controls")).toBe(controls);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      hidden: false,
      hasTrack: true,
      sourceFilename: "updated.mp3",
    });
  });

  it("replays a pending graph redraw after the editor runtime remounts", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    expect(window.__aqeResetGraphAfterEdit?.(0)).toBe(true);
    expect(window.__aqePendingGraphRedrawField).toBe(0);

    disposeEditorRuntime();
    renderFields();
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      busy: true,
      hidden: false,
    });
    expect(bridgeCommands().filter((command) => command === "aqe:analyze-field")).toHaveLength(2);

    window.__aqeSetVisualizer?.(0, track, 0);
    expect(window.__aqePendingGraphRedrawField).toBeNull();
  });

  it("auto-queues default graphs for all mounted audio fields", async () => {
    renderTwoAudioFields();
    initializeEditorRuntime({ audioFieldIndices: [0, 1], showGraphByDefault: true });
    scan({ audioFieldIndices: [0, 1], showGraphByDefault: true });
    scan({ audioFieldIndices: [0, 1], showGraphByDefault: true });

    expect(bridgeCommands().filter((command) => command === "aqe:analyze-field")).toHaveLength(1);
    expect(bridgeCommands()).not.toContain("focus:0");
    expect(window.__aqePopPendingGraphAnalysisRequest?.()).toEqual({
      graphSettings: defaultGraphSettings,
      ord: 0,
      sourceFilename: "clip one.mp3",
    });
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({ busy: true, hidden: false });

    window.__aqeSetVisualizer?.(0, { ...track, sourceFilename: "clip one.mp3" }, 0);
    await Promise.resolve();
    await Promise.resolve();

    expect(bridgeCommands().filter((command) => command === "aqe:analyze-field")).toHaveLength(2);
    expect(bridgeCommands()).not.toContain("focus:1");
    expect(window.__aqePopPendingGraphAnalysisRequest?.()).toEqual({
      graphSettings: defaultGraphSettings,
      ord: 1,
      sourceFilename: "clip two.mp3",
    });
    expect(window.__aqeGraphStateForTest?.(1)).toMatchObject({ busy: true, hidden: false });
  });

  it("continues the default graph queue after an analysis error", async () => {
    renderTwoAudioFields();
    initializeEditorRuntime({ audioFieldIndices: [0, 1], showGraphByDefault: true });
    scan({ audioFieldIndices: [0, 1], showGraphByDefault: true });

    window.__aqeSetBusy?.(0, false);
    window.__aqeSetVisualizerStatus?.(0, "Audio visualization failed.", "error");
    await Promise.resolve();
    await Promise.resolve();

    expect(bridgeCommands().filter((command) => command === "aqe:analyze-field")).toHaveLength(2);
    expect(bridgeCommands()).not.toContain("focus:1");
    expect(window.__aqeGraphStateForTest?.(1)).toMatchObject({ busy: true, hidden: false });
  });

  it("retries a default graph request after delayed controls mount", async () => {
    vi.useFakeTimers();
    try {
      initializeEditorRuntime({ audioFieldIndices: [] });
      document.body.innerHTML = "";

      enqueueDefaultGraphs(
        [{ ord: 0, sourceFilename: "clip one.mp3" }],
        {
          anyBusy: () => false,
          requestDefaultGraph,
        },
      );

      expect(bridgeCommands()).not.toContain("aqe:analyze-field");

      renderFields();
      scan({ audioFieldIndices: [0] });
      vi.runOnlyPendingTimers();
      await Promise.resolve();

      expect(bridgeCommands()).toContain("aqe:analyze-field");
      expect(window.__aqePopPendingGraphAnalysisRequest?.()).toEqual({
        graphSettings: defaultGraphSettings,
        ord: 0,
        sourceFilename: "clip one.mp3",
      });
      expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({ busy: true, hidden: false });
    } finally {
      vi.useRealTimers();
    }
  });
});

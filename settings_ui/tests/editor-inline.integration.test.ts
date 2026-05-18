import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  audioSourceForNode,
  disposeEditorRuntime,
  explicitFieldTargets,
  fieldIndex,
  fieldNodes,
  initializeEditorRuntime,
  scan,
} from "../src/editor-inline/runtime.js";
import { pycmdMock } from "./setup.js";

const track = {
  analyzerName: "praat",
  durationMs: 1000,
  pitchMaxHz: 300,
  pitchMinHz: 100,
  points: [
    [0, 120, 0.1, true],
    [200, 180, 0.8, true],
    [400, null, 0, false],
    [600, 260, 0.4, true],
    [1000, 280, 1, true],
  ],
  sourceFilename: "clip one.mp3",
};

function commandLog(): string[] {
  return pycmdMock.mock.calls.map(([command]) => command);
}

function bridgeCommands(): string[] {
  return commandLog().filter((command) => command.startsWith("focus:") || command.startsWith("aqe:"));
}

function renderFields(): void {
  document.body.innerHTML = `
    <div class="field-container" data-index="0">
      <div contenteditable="true" id="f0">[sound:clip one.mp3]</div>
    </div>
    <div class="field-container" data-index="1">
      <div contenteditable="true" id="f1">plain text</div>
    </div>
  `;
}

function renderTwoAudioFields(): void {
  document.body.innerHTML = `
    <div class="field-container" data-index="0">
      <div contenteditable="true" id="f0">[sound:clip one.mp3]</div>
    </div>
    <div class="field-container" data-index="1">
      <div contenteditable="true" id="f1">[sound:clip two.mp3]</div>
    </div>
  `;
}

function graphClientX(svg: SVGSVGElement, ratio: number): number {
  const rect = svg.getBoundingClientRect();
  return 44 + 566 * ratio + rect.left;
}

function dispatchGraphPointer(svg: SVGSVGElement, type: string, clientX: number, shiftKey = false): void {
  const EventCtor = window.PointerEvent || window.MouseEvent;
  const rect = svg.getBoundingClientRect();
  const event = new EventCtor(type, {
    bubbles: true,
    clientX,
    clientY: rect.top + 20,
    shiftKey,
  });
  if (type === "pointerdown") {
    svg.dispatchEvent(event);
    return;
  }
  window.dispatchEvent(event);
}

function dragGraphSelection(svg: SVGSVGElement, startRatio: number, endRatio: number): void {
  dispatchGraphPointer(svg, "pointerdown", graphClientX(svg, startRatio), true);
  dispatchGraphPointer(svg, "pointermove", graphClientX(svg, endRatio), true);
  dispatchGraphPointer(svg, "pointerup", graphClientX(svg, endRatio), true);
}

function setGraphBounds(svg: SVGSVGElement): void {
  svg.getBoundingClientRect = () => ({
    bottom: 150,
    height: 150,
    left: 0,
    right: 620,
    top: 0,
    width: 620,
    x: 0,
    y: 0,
    toJSON: () => ({}),
  });
}

function prepareHtmlAudio(ord = 0): HTMLAudioElement {
  const audio = document.querySelector<HTMLAudioElement>(`[data-testid="aqe-audio-clock-${ord}"]`)!;
  Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
  audio.play = vi.fn<() => Promise<void>>(() => Promise.resolve());
  audio.pause = vi.fn<() => void>(() => undefined);
  audio.dispatchEvent(new Event("loadedmetadata"));
  return audio;
}

function mockAnimationFrames(): Array<Parameters<typeof window.requestAnimationFrame>[0]> {
  const frames: Array<Parameters<typeof window.requestAnimationFrame>[0]> = [];
  vi.spyOn(window, "requestAnimationFrame").mockImplementation((callback) => {
    frames.push(callback);
    return frames.length;
  });
  vi.spyOn(window, "cancelAnimationFrame").mockImplementation(() => undefined);
  return frames;
}

describe("editor inline Svelte integration", () => {
  let warnSpy: ReturnType<typeof vi.spyOn>;
  let errorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    warnSpy = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    errorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
    renderFields();
  });

  afterEach(() => {
    disposeEditorRuntime();
    warnSpy.mockRestore();
    errorSpy.mockRestore();
    vi.restoreAllMocks();
  });

  it("mounts one Svelte control surface per explicit audio field", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    expect(document.querySelectorAll(".aqe-controls")).toHaveLength(1);
    const graphButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-graph"]')!;
    const settingsButton = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-settings"]')!;
    expect(graphButton).toHaveClass("aqe-icon-only");
    expect(graphButton).toHaveAttribute("aria-label", "Analyze and show pitch/intensity graph");
    expect(settingsButton).toHaveClass("aqe-icon-only");
    expect(document.querySelector('[data-testid="aqe-button-0-denoise-standard"]')).toHaveTextContent("Standard");
    expect(document.querySelector('[data-testid="aqe-button-0-rnnoise"]')).toHaveTextContent("RNNoise");
    expect(audioSourceForNode(document.getElementById("f0")!)).toBe("clip one.mp3");
    expect(fieldIndex(document.getElementById("f0")!, 7)).toBe(0);
  });

  it.each(["aac", "flac", "m4a", "mp3", "oga", "ogg", "opus", "wav", "webm"])(
    "detects %s sound references as supported audio",
    (extension) => {
      document.body.innerHTML = `<div id="format-field">[sound:clip one.${extension.toUpperCase()}]</div>`;

      expect(audioSourceForNode(document.getElementById("format-field")!)).toBe(
        `clip one.${extension.toUpperCase()}`,
      );
    },
  );

  it("does not detect mp4 sound references as supported audio", () => {
    document.body.innerHTML = '<div id="video-field">[sound:clip.mp4]</div>';

    expect(audioSourceForNode(document.getElementById("video-field")!)).toBe("");
  });

  it("dispatches denoise menu commands and renders collapsed help", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    const help = document.querySelector<HTMLDetailsElement>('[data-testid="aqe-help-0"]')!;
    expect(help.open).toBe(false);
    expect(help.querySelectorAll(".aqe-help-command")).toHaveLength(14);
    expect(help).toHaveTextContent("Shift-drag on the graph to select a region.");
    expect(help).toHaveTextContent("Delete Region removes only the selected region.");
    expect(help).toHaveTextContent("Every edit creates a new media file and updates the field to point at it.");
    expect(help).toHaveTextContent("grey is loudness and lines are pitch of the voice.");

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-denoise-standard"]')!.click();
    expect(bridgeCommands()).toContain("aqe:denoise-standard");

    window.__aqePrepareForNewNote?.();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-rnnoise"]')!.click();
    expect(bridgeCommands()).toContain("aqe:rnnoise");
  });

  it("dispatches trim commands with the field-local split value", () => {
    window.__AQE_EDITOR_CONFIG__ = {
      audioFieldIndices: [0],
      splitButtonDefaults: {
        denoiseAlgorithm: "standard",
        pauseAggressiveness: "normal",
        speedStep: 0.05,
        trimStepMs: 200,
        volumeStepDb: 3,
      },
    };
    initializeEditorRuntime(window.__AQE_EDITOR_CONFIG__);
    scan(window.__AQE_EDITOR_CONFIG__);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-trim-left"]')!.click();

    expect(bridgeCommands()).toContain("focus:0");
    const payload = JSON.parse(commandLog().find((command) => command.startsWith("{")) ?? "{}");
    expect(payload).toEqual({
      command: "aqe:trim-left",
      fieldOrd: 0,
      overrides: {
        trimStepMs: 200,
      },
    });
  });

  it("keeps trim split values isolated across audio fields", async () => {
    renderTwoAudioFields();
    window.__AQE_EDITOR_CONFIG__ = {
      audioFieldIndices: [0, 1],
      splitButtonDefaults: {
        denoiseAlgorithm: "standard",
        pauseAggressiveness: "normal",
        speedStep: 0.05,
        trimStepMs: 100,
        volumeStepDb: 3,
      },
    };
    initializeEditorRuntime(window.__AQE_EDITOR_CONFIG__);
    scan(window.__AQE_EDITOR_CONFIG__);

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-trim-left-menu"]')!.click();
    await Promise.resolve();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-trim-left-preset-200"]')!.click();
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-trim-left"]')!.click();
    window.__aqeSetBusy?.(0, false);
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-1-trim-left"]')!.click();

    const payloads = commandLog()
      .filter((command) => command.startsWith("{"))
      .map((command) => JSON.parse(command));
    expect(payloads.map((payload) => payload.overrides.trimStepMs)).toEqual([200, 100]);
  });

  it("removes orphaned controls from previous bundle instances before mounting", () => {
    document.body.insertAdjacentHTML(
      "afterbegin",
      `
        <div class="aqe-mount-host">
          <div class="aqe-controls" data-aqe-field-ord="0">
            <div class="aqe-visualizer" data-aqe-field-ord="0" hidden data-graph-active="false"></div>
          </div>
        </div>
      `,
    );

    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 0);

    const visualizers = document.querySelectorAll<HTMLElement>('.aqe-visualizer[data-aqe-field-ord="0"]');
    expect(document.querySelectorAll(".aqe-controls")).toHaveLength(1);
    expect(visualizers).toHaveLength(1);
    expect(document.querySelector<HTMLElement>('.aqe-visualizer[data-aqe-field-ord="0"]')?.dataset.sourceFilename).toBe(
      "clip one.mp3",
    );
  });

  it("cancels delayed scans when the runtime is disposed", () => {
    vi.useFakeTimers();
    try {
      initializeEditorRuntime({ audioFieldIndices: [0] });
      disposeEditorRuntime();

      vi.runAllTimers();

      expect(document.querySelectorAll(".aqe-controls")).toHaveLength(0);
    } finally {
      vi.useRealTimers();
    }
  });

  it("preserves an existing explicit mount when a reload scan has no visible sound text", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    const controls = document.querySelector(".aqe-controls");

    document.getElementById("f0")!.textContent = "";
    scan({ audioFieldIndices: [0] });

    expect(document.querySelectorAll(".aqe-controls")).toHaveLength(1);
    expect(document.querySelector(".aqe-controls")).toBe(controls);
  });

  it("auto-detects supported audio fields, dedupes rescans, and remounts changed sources", () => {
    document.body.innerHTML = `
      <div>
        <div contenteditable="true" data-field-ord="2">[sound:first.wav]</div>
      </div>
      <div>
        <div contenteditable="true" data-field-ord="3">[sound:video.mp4]</div>
      </div>
      <div><div contenteditable="true"></div></div>
    `;

    scan({ audioFieldIndices: [] });
    scan({ audioFieldIndices: [] });

    expect(document.querySelectorAll(".aqe-controls")).toHaveLength(1);
    expect(document.querySelector(".aqe-controls")?.getAttribute("data-aqe-source-filename")).toBe("first.wav");
    expect(fieldNodes()).toHaveLength(2);
    expect(explicitFieldTargets([99])).toEqual([]);

    const field = document.querySelector<HTMLElement>('[data-field-ord="2"]')!;
    field.innerHTML = "[sound:second.ogg]";
    scan({ audioFieldIndices: [] });

    expect(document.querySelectorAll(".aqe-controls")).toHaveLength(1);
    expect(document.querySelector(".aqe-controls")?.getAttribute("data-aqe-source-filename")).toBe("second.ogg");
  });

  it("requests graphs, accepts backend graph payloads, and exposes graph state", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-graph"]')!.click();

    expect(bridgeCommands()).toContain("focus:0");
    expect(bridgeCommands()).toContain("aqe:analyze");
    expect(window.__aqeGraphStateForTest?.(0)?.busy).toBe(true);

    window.__aqeSetVisualizer?.(0, track, 200);
    const state = window.__aqeGraphStateForTest?.(0);

    expect(state?.hidden).toBe(false);
    expect(state?.durationMs).toBe(1000);
    expect(state?.cursorMs).toBe(200);
    expect(state?.pitchPaths).toBe(2);
    expect(state?.intensity).toMatch(/^M /);
    expect(state?.audioClockSrc).toBe("clip%20one.mp3");
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
    expect(bridgeCommands().filter((command) => command === "aqe:analyze")).toHaveLength(2);

    window.__aqeSetVisualizer?.(0, track, 0);
    expect(window.__aqePendingGraphRedrawField).toBeNull();
  });

  it("renders repeat next to play and initializes it from runtime config", () => {
    initializeEditorRuntime({ audioFieldIndices: [0], repeatPlaybackByDefault: true });
    scan({ audioFieldIndices: [0], repeatPlaybackByDefault: true });

    const repeat = document.querySelector<HTMLButtonElement>('[data-testid="aqe-repeat-0"]');
    expect(repeat).toHaveAttribute("aria-pressed", "true");
    expect(repeat).toHaveClass("aqe-icon-only");

    repeat?.click();

    expect(window.__aqeGraphStateForTest?.(0)?.repeatEnabled).toBe(false);
    expect(repeat).toHaveAttribute("aria-pressed", "false");
  });

  it("auto-queues default graphs for all mounted audio fields", async () => {
    renderTwoAudioFields();
    initializeEditorRuntime({ audioFieldIndices: [0, 1], showGraphByDefault: true });
    scan({ audioFieldIndices: [0, 1], showGraphByDefault: true });
    scan({ audioFieldIndices: [0, 1], showGraphByDefault: true });

    expect(bridgeCommands().filter((command) => command === "aqe:analyze-field")).toHaveLength(1);
    expect(bridgeCommands()).not.toContain("focus:0");
    expect(window.__aqePopPendingGraphAnalysisRequest?.()).toEqual({
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

  it("creates, replaces, and clears graph selections with Shift gestures", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);

    dragGraphSelection(svg, 0.2, 0.6);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionStartMs: 200,
      selectionEndMs: 600,
      cursorMs: 200,
    });
    expect(document.querySelector('[data-testid="aqe-selection-0"]')).toHaveAttribute("visibility", "visible");

    dragGraphSelection(svg, 0.8, 0.3);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionStartMs: 300,
      selectionEndMs: 800,
    });

    dispatchGraphPointer(svg, "pointerdown", graphClientX(svg, 0.5), true);
    dispatchGraphPointer(svg, "pointerup", graphClientX(svg, 0.5), true);
    expect(window.__aqeGraphStateForTest?.(0)?.selectionActive).toBe(false);
    expect(document.querySelector('[data-testid="aqe-selection-0"]')).toHaveAttribute("visibility", "hidden");
  });

  it("shows Delete Region for valid selections and queues a scoped button request", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 250);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    const button = document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-delete-selection"]')!;
    setGraphBounds(svg);

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      regionDeleteButtonHidden: true,
    });

    dragGraphSelection(svg, 0.2, 0.6);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      regionDeleteButtonHidden: false,
      regionDeleteButtonDisabled: false,
    });

    button.click();

    expect(window.__aqePopPendingRegionDeleteRequest?.()).toEqual({
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

  it("handles Backspace only when the focused graph has a valid selection", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 250);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    const graph = document.querySelector<HTMLElement>('[data-testid="aqe-graph-0"]')!;
    const field = document.getElementById("f0")!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.2, 0.6);

    field.focus();
    field.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, key: "Backspace" }));
    expect(window.__aqePopPendingRegionDeleteRequest?.()).toBeNull();

    graph.focus();
    graph.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, cancelable: true, key: "Backspace" }));

    expect(window.__aqePopPendingRegionDeleteRequest?.()).toMatchObject({
      ord: 0,
      sourceFilename: "clip one.mp3",
      selectionStartMs: 200,
      selectionEndMs: 600,
      trigger: "backspace",
    });
    expect(bridgeCommands()).toEqual(expect.arrayContaining(["focus:0", "aqe:delete-selection"]));
  });

  it("disables Delete Region for whole-clip selections without dispatching", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 0);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    const graph = document.querySelector<HTMLElement>('[data-testid="aqe-graph-0"]')!;
    setGraphBounds(svg);

    dragGraphSelection(svg, 0, 1);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      regionDeleteButtonHidden: false,
      regionDeleteButtonDisabled: true,
    });

    graph.focus();
    graph.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, cancelable: true, key: "Backspace" }));

    expect(window.__aqePopPendingRegionDeleteRequest?.()).toBeNull();
    expect(bridgeCommands()).not.toContain("aqe:delete-selection");
  });

  it("shows and updates a draft selection during Shift-drag before commit", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    const band = document.querySelector('[data-testid="aqe-selection-0"]')!;
    setGraphBounds(svg);

    dispatchGraphPointer(svg, "pointerdown", graphClientX(svg, 0.2), true);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: false,
      selectionDraftActive: false,
      selectionDraftStartMs: null,
      selectionDraftEndMs: null,
      cursorMs: 100,
    });
    expect(band).toHaveAttribute("visibility", "hidden");

    dispatchGraphPointer(svg, "pointermove", graphClientX(svg, 0.6), true);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: false,
      selectionDraftActive: true,
      selectionDraftStartMs: 200,
      selectionDraftEndMs: 600,
      cursorMs: 100,
    });
    expect(band).toHaveAttribute("visibility", "visible");
    expect(band).toHaveClass("aqe-selection-draft");

    dispatchGraphPointer(svg, "pointermove", graphClientX(svg, 0.8), true);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: false,
      selectionDraftActive: true,
      selectionDraftStartMs: 200,
      selectionDraftEndMs: 800,
    });

    dispatchGraphPointer(svg, "pointerup", graphClientX(svg, 0.8), true);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionStartMs: 200,
      selectionEndMs: 800,
      selectionDraftActive: false,
      selectionDraftStartMs: null,
      selectionDraftEndMs: null,
      cursorMs: 200,
    });
    expect(band).not.toHaveClass("aqe-selection-draft");
  });

  it("discards draft selection on pointer cancel without replacing the committed selection", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    const band = document.querySelector('[data-testid="aqe-selection-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.2, 0.6);

    dispatchGraphPointer(svg, "pointerdown", graphClientX(svg, 0.7), true);
    dispatchGraphPointer(svg, "pointermove", graphClientX(svg, 0.9), true);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionStartMs: 200,
      selectionEndMs: 600,
      selectionDraftActive: true,
      selectionDraftStartMs: 700,
      selectionDraftEndMs: 900,
    });
    expect(band).toHaveClass("aqe-selection-draft");

    dispatchGraphPointer(svg, "pointercancel", graphClientX(svg, 0.9), true);
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionStartMs: 200,
      selectionEndMs: 600,
      selectionDraftActive: false,
      selectionDraftStartMs: null,
      selectionDraftEndMs: null,
    });
    expect(band).toHaveAttribute("visibility", "visible");
    expect(band).not.toHaveClass("aqe-selection-draft");
  });

  it("discards draft selection on pointer capture loss", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    const band = document.querySelector('[data-testid="aqe-selection-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.2, 0.6);

    dispatchGraphPointer(svg, "pointerdown", graphClientX(svg, 0.7), true);
    dispatchGraphPointer(svg, "pointermove", graphClientX(svg, 0.9), true);
    expect(band).toHaveClass("aqe-selection-draft");

    const EventCtor = window.PointerEvent || window.MouseEvent;
    svg.dispatchEvent(new EventCtor("lostpointercapture", { bubbles: true, clientX: graphClientX(svg, 0.9), shiftKey: true }));

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionStartMs: 200,
      selectionEndMs: 600,
      selectionDraftActive: false,
      selectionDraftStartMs: null,
      selectionDraftEndMs: null,
    });
    expect(band).toHaveAttribute("visibility", "visible");
    expect(band).not.toHaveClass("aqe-selection-draft");
  });

  it("keeps selection stable through normal click and drag gestures", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 100);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);

    dragGraphSelection(svg, 0.2, 0.6);
    dispatchGraphPointer(svg, "pointerdown", graphClientX(svg, 0.8));
    dispatchGraphPointer(svg, "pointerup", graphClientX(svg, 0.8));

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionActive: true,
      selectionStartMs: 200,
      selectionEndMs: 600,
      cursorMs: 800,
    });

    dispatchGraphPointer(svg, "pointerdown", graphClientX(svg, 0.1));
    dispatchGraphPointer(svg, "pointermove", graphClientX(svg, 0.9));
    dispatchGraphPointer(svg, "pointerup", graphClientX(svg, 0.9));

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      selectionStartMs: 200,
      selectionEndMs: 600,
      cursorMs: 900,
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

  it("disables controls during processing commands and resets note state", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-volume-up"]')!.click();

    expect(bridgeCommands()).toContain("aqe:volume-up");
    expect(window.__aqeGraphStateForTest?.(0)?.allButtonsDisabled).toBe(true);
    expect(window.__aqeGraphStateForTest?.(0)?.repeatControlDisabled).toBe(true);
    expect(document.querySelector('[data-testid="aqe-status-0"]')).toHaveTextContent("Processing...");

    window.__aqePrepareForNewNote?.();

    expect(window.__aqeGraphStateForTest?.(0)?.allButtonsDisabled).toBe(false);
    expect(window.__aqeGraphStateForTest?.(0)?.repeatControlDisabled).toBe(false);
    expect(document.querySelector('[data-testid="aqe-status-0"]')).toHaveTextContent("");
  });

  it("uses HTML audio playback and queues the Python bridge request", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 400);
    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
    audio.play = vi.fn<() => Promise<void>>(() => Promise.resolve());
    audio.pause = vi.fn<() => void>(() => undefined);
    audio.dispatchEvent(new Event("loadedmetadata"));

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();

    const request = window.__aqeGetPlaybackRequest?.();
    expect(request).toEqual({
      action: "start",
      cursorMs: 400,
      endMs: 1000,
      engine: "html",
      loop: false,
      ord: 0,
      regionMode: "full",
    });
    expect(window.__aqeGraphStateForTest?.(0)?.playbackState).toBe("playing");
    expect(window.__aqeGraphStateForTest?.(0)?.playbackEngine).toBe("html");
  });

  it("starts HTML playback from an explicit selected region", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 400);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    svg.getBoundingClientRect = () => ({
      bottom: 150,
      height: 150,
      left: 0,
      right: 620,
      top: 0,
      width: 620,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    });
    dragGraphSelection(svg, 0.25, 0.75);
    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
    audio.play = vi.fn<() => Promise<void>>(() => Promise.resolve());
    audio.pause = vi.fn<() => void>(() => undefined);
    audio.dispatchEvent(new Event("loadedmetadata"));

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();

    expect(window.__aqeGetPlaybackRequest?.()).toEqual({
      action: "start",
      cursorMs: 250,
      endMs: 750,
      engine: "html",
      loop: false,
      ord: 0,
      regionMode: "selection",
    });
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackStartMs: 250,
      playbackEndMs: 750,
      playbackRegionMode: "selection",
    });
  });

  it("stops HTML playback immediately before processing commands", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 400);
    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
    audio.play = vi.fn<() => Promise<void>>(() => Promise.resolve());
    audio.pause = vi.fn<() => void>(() => undefined);
    audio.dispatchEvent(new Event("loadedmetadata"));

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();
    expect(window.__aqeGraphStateForTest?.(0)?.playbackState).toBe("playing");

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-volume-up"]')!.click();

    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "stopped",
      playButtonLabel: "Play",
      allButtonsDisabled: true,
    });
    expect(bridgeCommands()).not.toContain("aqe:play-ended");
  });

  it("falls back to native playback when HTML play rejects", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 700);
    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
    audio.play = vi.fn<() => Promise<void>>(() => Promise.reject(new Error("blocked")));
    audio.pause = vi.fn<() => void>(() => undefined);
    audio.dispatchEvent(new Event("loadedmetadata"));

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();
    await Promise.resolve();

    expect(window.__aqeGetPlaybackRequest?.()).toEqual({
      action: "start",
      cursorMs: 700,
      endMs: 1000,
      engine: "native",
      loop: false,
      ord: 0,
      regionMode: "full",
    });
    expect(window.__aqeGraphStateForTest?.(0)?.playbackState).toBe("stopped");
  });

  it("does not claim native selected playback when HTML play rejects", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 700);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.25, 0.75);
    const audio = document.querySelector<HTMLAudioElement>('[data-testid="aqe-audio-clock-0"]')!;
    Object.defineProperty(audio, "readyState", { configurable: true, value: 1 });
    audio.play = vi.fn<() => Promise<void>>(() => Promise.reject(new Error("blocked")));
    audio.pause = vi.fn<() => void>(() => undefined);
    audio.dispatchEvent(new Event("loadedmetadata"));

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-play"]')!.click();
    await Promise.resolve();
    await Promise.resolve();

    expect(bridgeCommands()).not.toContain("aqe:play");
    expect(document.querySelector('[data-testid="aqe-status-0"]')).toHaveTextContent(
      "Selected repeat playback needs browser audio.",
    );
    expect(window.__aqeGraphStateForTest?.(0)).toMatchObject({
      playbackState: "stopped",
      selectionStartMs: 250,
      selectionEndMs: 750,
      playbackRegionMode: "selection",
    });
  });

  it("commits cursor intents from rendered graph coordinates", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    window.__aqeSetVisualizer?.(0, track, 0);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    svg.getBoundingClientRect = () => ({
      bottom: 150,
      height: 150,
      left: 0,
      right: 620,
      top: 0,
      width: 620,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    });

    const result = window.__aqeSetCursorByClientXForTest?.(0, 44 + 566 * 0.6, true);

    expect(result?.cursorMs).toBe(600);
    expect(window.__aqeGetCursorIntent?.()).toMatchObject({
      cursorMs: 600,
      previousPlaybackState: "stopped",
      restartPlayback: false,
    });
    expect(bridgeCommands()).toContain("aqe:set-cursor");
  });

  it("exposes editor frontend logs through a pop queue", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-show-file"]')!.click();

    const payloads = Array.from({ length: 20 }, () => window.__aqePopFrontendLog?.());
    const payload = payloads.find((item) => item?.message === "command dispatched");
    expect(payload).toMatchObject({
      level: "info",
      message: "command dispatched",
    });
  });
});

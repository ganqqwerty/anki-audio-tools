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
  });

  it("mounts one Svelte control surface per explicit audio field", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    expect(document.querySelectorAll(".aqe-controls")).toHaveLength(1);
    expect(document.querySelector('[data-testid="aqe-button-0-graph"]')).toHaveTextContent("Graph");
    expect(document.querySelector('[data-testid="aqe-button-0-mp-senet"]')).toHaveTextContent("MP-SENet");
    expect(audioSourceForNode(document.getElementById("f0")!)).toBe("clip one.mp3");
    expect(fieldIndex(document.getElementById("f0")!, 7)).toBe(0);
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

  it("disables controls during processing commands and resets note state", () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-volume-up"]')!.click();

    expect(bridgeCommands()).toContain("aqe:volume-up");
    expect(window.__aqeGraphStateForTest?.(0)?.allButtonsDisabled).toBe(true);
    expect(document.querySelector('[data-testid="aqe-status-0"]')).toHaveTextContent("Processing...");

    window.__aqePrepareForNewNote?.();

    expect(window.__aqeGraphStateForTest?.(0)?.allButtonsDisabled).toBe(false);
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
    expect(request).toEqual({ action: "start", cursorMs: 400, engine: "html", ord: 0 });
    expect(window.__aqeGraphStateForTest?.(0)?.playbackState).toBe("playing");
    expect(window.__aqeGraphStateForTest?.(0)?.playbackEngine).toBe("html");
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
      engine: "native",
      ord: 0,
    });
    expect(window.__aqeGraphStateForTest?.(0)?.playbackState).toBe("stopped");
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

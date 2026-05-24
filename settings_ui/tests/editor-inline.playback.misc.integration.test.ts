import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";
import { bridgeCommands, dragGraphSelection, muteConsole, renderFields, setRepeatMode, setGraphBounds, track } from "./editor-inline.integration.helpers.js";

describe("editor inline playback fallback and diagnostics", () => {
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

  it("keeps selected repeat playback on browser audio when HTML play rejects", async () => {
    initializeEditorRuntime({ audioFieldIndices: [0] });
    scan({ audioFieldIndices: [0] });
    await Promise.resolve();
    window.__aqeSetVisualizer?.(0, track, 700);
    const svg = document.querySelector<SVGSVGElement>('[data-testid="aqe-graph-svg-0"]')!;
    setGraphBounds(svg);
    dragGraphSelection(svg, 0.25, 0.75);
    await setRepeatMode(true);
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
    setGraphBounds(svg);

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

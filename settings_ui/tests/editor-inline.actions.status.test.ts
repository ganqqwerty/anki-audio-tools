import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  getCursorIntent,
  getCursorMs,
  resetGraphAfterEdit,
  setCursor,
  setControlsBusy,
  setVisualizerStatusFromPython,
} from "../src/editor-inline/actions.js";
import { PLOT, xForMs } from "../src/editor-inline/plot.js";
import { disposeEditorRuntime } from "../src/editor-inline/runtime.js";
import { PRODUCT_LINKS } from "../src/lib/product-links.js";
import { bridgeCommands, mountTrack, track } from "./editor-inline.actions.helpers.js";
import { peekPendingCommandPayload, setFullGraphViewport } from "./editor-inline.integration.helpers.js";

describe("editor inline status workflows", () => {
  let warnSpy: ReturnType<typeof vi.spyOn>;
  let errorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    warnSpy = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    errorSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
  });

  afterEach(() => {
    disposeEditorRuntime();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("updates visualizer status, redraw state, cursor helpers, and test driver", async () => {
    const visualizer = await mountTrack(0);

    setVisualizerStatusFromPython(0, "Analyzing...", "processing");
    expect(visualizer.dataset.hasTrack).toBe("false");
    expect(window.__aqeGraphStateForTest?.(0)?.spinnerVisible).toBe(true);

    setVisualizerStatusFromPython(
      0,
      { code: "AQE-GRAPH-001", message: "Audio visualization failed." },
      "error",
    );
    const graphStatus = visualizer.closest<HTMLElement>(".aqe-controls")?.querySelector<HTMLElement>(".aqe-status");
    expect(graphStatus).toHaveTextContent("AQE-GRAPH-001: Audio visualization failed. Help");

    window.__aqeActiveField = 0;
    expect(window.__aqeSetCursorForTest?.(0, 450, false)).toBe(true);
    expect(getCursorMs()).toBe(450);
    expect(window.__aqeSetCursorForTest?.(99, 450, false)).toBe(false);
    expect(window.__aqeInstallAudioPlaybackTestDriverForTest?.(0)).toBe(true);
    expect(window.__aqeGraphStateForTest?.(0)?.audioPlaybackTestDriver).toBe(true);
    const audio = visualizer.querySelector<HTMLAudioElement>(".aqe-audio-clock")!;
    const frames: Array<(time: number) => void> = [];
    vi.spyOn(window, "requestAnimationFrame").mockImplementation((callback) => {
      frames.push(callback);
      return frames.length;
    });
    vi.spyOn(window, "cancelAnimationFrame").mockImplementation(() => undefined);
    await audio.play();
    expect(frames).toHaveLength(1);
    audio.currentTime = 1;
    frames.shift()?.(performance.now() + 1100);
    const testAudio = audio as HTMLAudioElement & { __aqeTestPlaying?: boolean };
    expect(testAudio.__aqeTestPlaying).toBe(false);
    expect(window.__aqeInstallAudioPlaybackTestDriverForTest?.(99)).toBe(false);
    window.__aqeLastCursorIntent = null;
    expect(getCursorIntent()).toMatchObject({
      cursorMs: 450,
      previousPlaybackState: "stopped",
      restartPlayback: false,
    });
    expect(resetGraphAfterEdit(0)).toBe(true);
    expect(resetGraphAfterEdit(99)).toBe(false);
  });

  it("renders graph fallback warnings delivered with the graph payload", async () => {
    const visualizer = await mountTrack(0);

    window.__aqeSetVisualizer?.(
      0,
      {
        ...track,
        analyzerName: "ffmpeg-pcm",
        analysisWarning: "Graph used the ffmpeg/PCM fallback.",
      },
      0,
    );

    const status = visualizer.closest<HTMLElement>(".aqe-controls")?.querySelector<HTMLElement>(".aqe-status");
    expect(status).toHaveTextContent("Graph used the ffmpeg/PCM fallback.");
    expect(status?.dataset.kind).toBe("warning");
  });

  it("restores a stable operation status after a graph fallback warning", async () => {
    vi.useFakeTimers();
    const visualizer = await mountTrack(0);
    setControlsBusy(0, false, "Cleaned audio with RNNoise.", "");

    window.__aqeSetVisualizer?.(
      0,
      {
        ...track,
        analyzerName: "ffmpeg-pcm",
        analysisWarning: "Graph used the ffmpeg/PCM fallback.",
      },
      0,
    );

    const status = visualizer.closest<HTMLElement>(".aqe-controls")?.querySelector<HTMLElement>(".aqe-status");
    expect(status).toHaveTextContent("Graph used the ffmpeg/PCM fallback.");
    vi.advanceTimersByTime(4000);
    expect(status).toHaveTextContent("Cleaned audio with RNNoise.");
    expect(status?.dataset.kind).toBe("info");
  });

  it("keeps graph-owned statuses transient and restores edit-owned status", async () => {
    const visualizer = await mountTrack(0);
    setControlsBusy(0, false, "Increased volume by 15 dB.", "");

    setVisualizerStatusFromPython(0, "Analyzing...", "processing");
    const status = visualizer.closest<HTMLElement>(".aqe-controls")?.querySelector<HTMLElement>(".aqe-status")!;
    expect(status).toHaveTextContent("Analyzing...");
    expect(status.dataset.statusOwner).toBe("graph");
    expect(status.dataset.stableMessage).toBe("Increased volume by 15 dB.");

    window.__aqeSetVisualizer?.(0, track, 0);

    expect(status).toHaveTextContent("Increased volume by 15 dB.");
    expect(status.dataset.statusOwner).toBe("edit");
  });

  it("renders a timecode flag at the cursor and clamps it inside the plot", async () => {
    const visualizer = await mountTrack(0);
    window.__aqeSetVisualizer?.(0, { ...track, durationMs: 6000 }, 750);
    setFullGraphViewport();
    const cursor = visualizer.querySelector<HTMLElement>('[data-testid="aqe-css-cursor-0"]')!;
    const flag = cursor.querySelector<HTMLElement>(".aqe-css-cursor-flag")!;
    const current = flag.querySelector<HTMLElement>(".aqe-css-cursor-flag-current")!;
    const pitch = flag.querySelector<HTMLElement>(".aqe-css-cursor-flag-pitch")!;

    expect(cursor.style.display).toBe("block");
    expect(cursor.style.transform).toBe(`translate3d(${xForMs(750, 6000).toFixed(2)}px, 0, 0)`);
    expect(flag.style.transform).toBe("translateX(-41.00px)");
    expect(current.textContent).toBe("0.75s");
    expect(pitch.textContent).toBe(" / 200 Hz");
    expect(visualizer.querySelector(".aqe-cursor-label")).toHaveTextContent("0.75s / 200 Hz");

    setCursor(visualizer, 0, false);
    expect(cursor.style.transform).toBe(`translate3d(${PLOT.left.toFixed(2)}px, 0, 0)`);
    expect(flag.style.transform).toBe("translateX(0.00px)");

    setCursor(visualizer, 6000, false);
    expect(cursor.style.transform).toBe(`translate3d(${(PLOT.width - PLOT.right).toFixed(2)}px, 0, 0)`);
    expect(flag.style.transform).toBe("translateX(-82.00px)");
    expect(current.textContent).toBe("6.00s");
  });

  it("renders coded editor status errors with visible help links", async () => {
    const visualizer = await mountTrack(0);
    window.__aqeActiveField = 0;

    window.__aqeSetStatus?.(
      { code: "AQE-MEDIA-001", message: "No [sound:...] reference found." },
      "error",
    );

    const controls = visualizer.closest<HTMLElement>(".aqe-controls")!;
    const status = controls.querySelector<HTMLElement>(".aqe-status")!;
    const link = status.querySelector<HTMLAnchorElement>("a")!;

    expect(status).toHaveTextContent("AQE-MEDIA-001: No [sound:...] reference found. Help");
    expect(status).not.toHaveAttribute("data-aqe-tooltip-content");
    expect(link.href).toBe(`${PRODUCT_LINKS.githubPages}errors/AQE-MEDIA-001/`);

    const click = new MouseEvent("click", { bubbles: true, cancelable: true });
    expect(link.dispatchEvent(click)).toBe(false);
    expect(bridgeCommands()).toContain("aqe:command-payload");
    expect(peekPendingCommandPayload()).toEqual({
      command: "aqe:open-url",
      url: `${PRODUCT_LINKS.githubPages}errors/AQE-MEDIA-001/`,
    });
  });

  it("keeps status tooltips reserved for explicit command details", async () => {
    const visualizer = await mountTrack(0);
    const controls = visualizer.closest<HTMLElement>(".aqe-controls")!;
    const status = controls.querySelector<HTMLElement>(".aqe-status")!;

    setControlsBusy(0, true, "Processing with ffmpeg", "");
    expect(status).toHaveTextContent("Processing with ffmpeg");
    expect(status).not.toHaveAttribute("data-aqe-tooltip-content");

    setControlsBusy(0, true, "Processing with ffmpeg: /usr/bin/ffmpeg -i input", "/usr/bin/ffmpeg -i input");
    expect(status).toHaveAttribute("data-aqe-tooltip-content", "/usr/bin/ffmpeg -i input");

    setControlsBusy(0, false, "Increased speed to x1.5.", "");
    expect(status).not.toHaveAttribute("data-aqe-tooltip-content");
  });
});
